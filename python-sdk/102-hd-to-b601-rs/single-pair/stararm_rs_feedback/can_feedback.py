"""只收不发的 SocketCAN 监听：以真实 CAN 帧时间检查新鲜度，避开 SDK 无时间戳缓存。"""
import math
import time
from dataclasses import dataclass

from .config import NAMES


class FeedbackError(RuntimeError):
    pass


@dataclass(frozen=True)
class State:
    pos: float
    vel: float
    torq: float
    temperature: float
    mode: int
    faults: int
    received_at: float


class CANFeedback:
    # 对应官方 B601-RS：J1–J3 rs-06，J4–J7 rs-00。
    LIMITS = {"rs-06": (4 * math.pi, 50., 36.), "rs-00": (4 * math.pi, 33., 14.)}

    def __init__(self, robot, cfg, *, bus=None, clock=time.monotonic, wall_clock=time.time):
        self.cfg, self.clock, self.wall_clock = cfg, clock, wall_clock
        if robot.config.can_adapter != "socketcan":
            raise ValueError("RS feedback currently requires can_adapter=socketcan")
        self.by_id, self.states = {}, {}
        self.latched_fault = None
        for name in NAMES:
            motor_id, host_id = robot.config.motor_can_ids[name]
            if (type(motor_id) is not int or type(host_id) is not int
                    or not 1 <= motor_id <= 255 or not 0 <= host_id <= 255
                    or motor_id in self.by_id):
                raise ValueError("unique RS motor IDs and 8-bit host IDs required")
            model = robot.motor_model_mapping[name]
            if model not in self.LIMITS:
                raise ValueError(f"Unsupported RS model: {model}")
            self.by_id[motor_id] = (name, host_id, self.LIMITS[model])
        if bus is None:
            import can
            # 同一个 SocketCAN 接口允许独立接收 socket。此对象从不调用 send()。
            bus = can.Bus(interface="socketcan", channel=robot.config.port,
                          receive_own_messages=False, can_filters=[
                              {"can_id": kind << 24, "can_mask": 0x1F000000, "extended": True}
                              for kind in (2, 21, 24)])
        self.bus = bus

    def ingest(self, msg):
        if (not msg.is_extended_id or msg.is_error_frame or msg.is_remote_frame
                or len(msg.data) != 8):
            return
        arb = msg.arbitration_id
        kind, motor_id, host_id = (arb >> 24) & 31, (arb >> 8) & 255, arb & 255
        entry = self.by_id.get(motor_id)
        if entry is None or host_id != entry[1] or kind not in (2, 21, 24):
            return
        # python-can SocketCAN 的 timestamp 为内核接收的 Unix 秒数；不能用排队出队时间冒充接收时间。
        age = self.wall_clock() - msg.timestamp
        if not math.isfinite(age) or age < -.02 or age > self.cfg.feedback_timeout_s:
            return
        name, _, (pmax, vmax, tmax) = entry
        if kind == 21:
            # fault + warning 非零时锁存，中断会话；不靠下一帧正常数据自动清故障。
            if any(msg.data):
                self.latched_fault = f"{name}: RS fault/warning report {bytes(msg.data).hex()}"
            return
        raw = [int.from_bytes(msg.data[i:i+2], "big") for i in range(0, 8, 2)]
        state = State((raw[0] / 32767 - 1) * pmax,
                      (raw[1] / 32767 - 1) * vmax,
                      (raw[2] / 32767 - 1) * tmax,
                      raw[3] * .1, (arb >> 22) & 3, (arb >> 16) & 63,
                      self.clock() - max(0., age))
        # 运行状态是 2；故障位在扩展 CAN ID bit16..21，不能沿用 DM status_code==1。
        if state.faults or state.mode != 2 or state.temperature >= self.cfg.max_temperature_c:
            self.latched_fault = (f"{name}: mode={state.mode}, faults=0x{state.faults:02x}, "
                                  f"temperature={state.temperature:.1f}C")
        previous = self.states.get(name)
        if previous is None or state.received_at >= previous.received_at:
            self.states[name] = state

    def snapshot(self):
        # 有界处理，避免其他设备 CAN 流量使控制循环永久陷在 drain 中。
        for _ in range(512):
            msg = self.bus.recv(timeout=0)
            if msg is None:
                break
            self.ingest(msg)
        else:
            raise FeedbackError("CAN receive queue overloaded")
        if self.latched_fault:
            raise FeedbackError(self.latched_fault)
        now = self.clock()
        missing = [n for n in NAMES if n not in self.states or
                   not 0 <= now - self.states[n].received_at <= self.cfg.feedback_timeout_s]
        if missing:
            raise FeedbackError(f"RS feedback missing/stale: {', '.join(missing)}")
        return dict(self.states)

    def close(self):
        self.bus.shutdown()
