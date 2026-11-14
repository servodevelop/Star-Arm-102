import { t } from "./i18n";
import { SerialServoBus } from "../vendor/star-arm/serial";
import { ServoProtocol } from "../vendor/star-arm/protocol";
import {
  assertJoints,
  DEFAULT_MAPPING,
  modelAngles,
  posture,
  poseSummary,
  servoAngles,
  type Mapping,
  WORK_POSE,
} from "./model";

export type Telemetry = {
  id: number;
  angle: number;
  power: number;
  current: number;
  voltage: number;
  temperatureRaw: number;
  status: number;
};
export type RobotState = {
  connected: boolean;
  busy: boolean;
  sampledAt: number | null;
  actual: ReturnType<typeof posture> | null;
  gripper_deg: number | null;
  monitors: Telemetry[];
  preview: ReturnType<typeof posture> | null;
  error: string | null;
};
const ids = [0, 1, 2, 3, 4, 5, 6];
export function delay(ms: number, signal?: AbortSignal) {
  return new Promise<void>((resolve, reject) => {
    const abort = () => {
      clearTimeout(timer);
      reject(signal?.reason ?? new DOMException(t("已停止"), "AbortError"));
    };
    const timer = setTimeout(() => {
      signal?.removeEventListener("abort", abort);
      resolve();
    }, ms);
    if (signal?.aborted) abort();
    else signal?.addEventListener("abort", abort, { once: true });
  });
}
export class Robot {
  bus: SerialServoBus;
  mapping: Mapping = DEFAULT_MAPPING;
  state: RobotState = {
    connected: false,
    busy: false,
    sampledAt: null,
    actual: null,
    gripper_deg: null,
    monitors: [],
    preview: null,
    error: null,
  };
  private tail = Promise.resolve();
  private epoch = 0;
  private cancellation = new AbortController();
  private timer: ReturnType<typeof setTimeout> | undefined;
  constructor(
    private changed: (state: RobotState) => void,
    bus?: SerialServoBus,
  ) {
    this.bus =
      bus ??
      new SerialServoBus("Star Arm 102-FL", {
        onLost: (error: Error) => {
          this.cancellation.abort(error);
          this.epoch++;
          this.update({
            connected: false,
            error: error.message,
            actual: null,
            gripper_deg: null,
          });
        },
      });
  }
  private update(values: Partial<RobotState>) {
    this.state = { ...this.state, ...values };
    this.changed(this.state);
  }
  setMapping(mapping: Mapping) {
    this.mapping = mapping;
    if (this.state.monitors.length === 7)
      this.update({
        actual: posture(
          modelAngles(
            this.state.monitors.map((v) => v.angle),
            mapping,
          ),
        ),
        preview: null,
      });
  }
  async connect(baudRate: number) {
    this.cancellation = new AbortController();
    await this.bus.connect(null, { baudRate });
    this.update({ connected: true, actual: null, error: null });
    try {
      await this.refresh();
      this.poll();
    } catch (error) {
      await this.disconnect();
      throw error;
    }
  }
  async disconnect() {
    clearTimeout(this.timer);
    this.epoch++;
    this.cancellation.abort();
    await this.tail;
    await this.bus.disconnect();
    this.update({
      connected: false,
      actual: null,
      gripper_deg: null,
      sampledAt: null,
      monitors: [],
      preview: null,
    });
  }
  private poll() {
    clearTimeout(this.timer);
    this.timer = setTimeout(async () => {
      if (!this.state.connected) return;
      if (!this.state.busy)
        try {
          await this.refresh();
        } catch (e) {
          this.update({ error: String(e) });
        }
      if (this.state.connected) this.poll();
    }, 500);
  }
  private enqueue<T>(
    action: (signal: AbortSignal) => Promise<T>,
    external?: AbortSignal,
    markBusy = true,
  ): Promise<T> {
    const epoch = this.epoch;
    const result = this.tail.then(async () => {
      external?.throwIfAborted();
      if (epoch !== this.epoch) throw Error(t("操作已取消"));
      if (!this.bus.connected) throw Error(t("从臂串口未连接"));
      const signal = external
        ? AbortSignal.any([this.cancellation.signal, external])
        : this.cancellation.signal;
      signal.throwIfAborted();
      if (markBusy) this.update({ busy: true });
      try {
        return await action(signal);
      } finally {
        if (markBusy) this.update({ busy: false });
      }
    });
    this.tail = result.then(
      () => {},
      () => {},
    );
    return result;
  }
  private async sample(signal?: AbortSignal) {
    const result = await this.bus.feedback(ids, signal);
    if (result.missingIds.length)
      throw Error(
        t("舵机回读不完整，未响应 ID：{0}；不将目标角度当成反馈", result.missingIds.join(", ")),
      );
    const monitors = ids.map((id) => result.monitors[id]) as Telemetry[];
    this.update({
      actual: posture(
        modelAngles(
          monitors.map((v) => v.angle),
          this.mapping,
        ),
      ),
      monitors,
      gripper_deg: monitors[6].angle,
      sampledAt: Date.now(),
      error: null,
    });
    return this.state;
  }
  refresh(signal?: AbortSignal) {
    // Feedback shares the command queue without marking the arm as executing.
    return this.enqueue((inner) => this.sample(inner), signal, false);
  }
  preview(values: number[]) {
    assertJoints(values);
    const target = posture(values);
    this.update({ preview: target });
    return target;
  }
  move(values: number[], durationMs: number, signal?: AbortSignal) {
    this.preview(values);
    return this.command(
      servoAngles(values, this.mapping),
      ids.slice(0, 6),
      durationMs,
      0,
      signal,
    );
  }
  workPose(durationMs: number, gripperPowerMw = 0, signal?: AbortSignal) {
    this.preview(WORK_POSE);
    return this.command(
      [...servoAngles(WORK_POSE, this.mapping), 0],
      ids,
      durationMs,
      [...ids.slice(0, 6).map(() => 0), gripperPowerMw],
      signal,
    );
  }
  gripper(
    angle: number,
    durationMs: number,
    powerMw: number,
    signal?: AbortSignal,
  ) {
    if (!Number.isFinite(angle) || angle < 0 || angle > 90)
      throw Error(t("夹爪驱动角范围为 0～90°，0°闭合、90°最大张开"));
    return this.command([angle], [6], durationMs, powerMw, signal);
  }
  private command(
    angles: number[],
    servoIds: number[],
    duration: number,
    power: number | number[],
    signal?: AbortSignal,
  ) {
    if (!Number.isInteger(duration) || duration <= 0 || duration > 0xffffffff)
      throw Error(t("运动时长需为有效的正整数毫秒"));
    const powers = Array.isArray(power) ? power : angles.map(() => power);
    if (
      powers.length !== angles.length ||
      powers.some((p) => !Number.isInteger(p) || p < 0 || p > 65535)
    )
      throw Error(t("协议功率需为 0～65535 mW 的整数，0 使用舵机默认"));
    return this.enqueue(async (inner) => {
      const ramp = Math.min(65535, Math.floor(duration / 4));
      await this.bus.write(
        ServoProtocol.syncMultiTurnAngleByInterval(angles, {
          servoIds,
          interval: duration,
          tAcc: ramp,
          tDec: ramp,
          power,
        }),
      );
      await delay(duration, inner);
      inner.throwIfAborted();
      const actual = await this.sample(inner);
      const errors = servoIds.map(
        (id, i) => actual.monitors[id].angle - angles[i],
      );
      // Return measured motion data, not the UI's busy/preview state. Keeping
      // the latter repeats large target/geometry payloads in every AI turn.
      return {
        command_sent: true,
        actual: {
          sampled_at: actual.sampledAt,
          ...poseSummary(actual.actual!),
          servo_deg: actual.monitors.map((m) => m.angle),
          gripper_deg: actual.gripper_deg,
          gripper_power_mw: actual.monitors[6].power,
        },
        target_error_deg: errors.map((v) => Math.round(v * 10) / 10),
      };
    }, signal);
  }
  async stop() {
    this.epoch++;
    this.cancellation.abort();
    await this.tail;
    this.cancellation = new AbortController();
    if (!this.bus.connected) return;
    await this.enqueue(async () => {
      // Vendor 0x11 stops at and holds the current position; it does not open the gripper.
      for (const id of ids) await this.bus.write(ServoProtocol.lockTorque(id));
      return this.sample();
    });
  }
}
