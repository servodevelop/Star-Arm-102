"""独立线程低频读取 iqf（0x701A）；仅 type-17 参数读取，不写电机参数。"""
import math
import struct
import threading
import time

from .config import NAMES

class CurrentProbe:
    def __init__(self, robot, *, bus=None, clock=time.monotonic, wall_clock=time.time):
        self.clock,self.wall_clock=clock,wall_clock
        self.entries={n:tuple(robot.config.motor_can_ids[n]) for n in NAMES}
        self.by_id={v[0]:(n,v[1]) for n,v in self.entries.items()}
        self.values={};self.pending={};self.error=None
        self.stop=threading.Event();self.lock=threading.Lock();self.thread=None
        if bus is None:
            import can
            bus=can.Bus(interface='socketcan',channel=robot.config.port,receive_own_messages=False,
                        can_filters=[{'can_id':17<<24,'can_mask':0x1f000000,'extended':True}])
        self.bus=bus

    def ingest(self,msg):
        if not msg.is_extended_id or msg.is_error_frame or msg.is_remote_frame or len(msg.data)!=8:return
        arb=msg.arbitration_id
        if (arb>>24)&31!=17:return
        entry=self.by_id.get((arb>>8)&255)
        if entry is None or (arb&255)!=entry[1]:return
        n=entry[0]
        age=self.wall_clock()-msg.timestamp
        now=self.clock()
        pending=self.pending.get(n)
        if pending is None or not math.isfinite(age) or not -.02<=age<=.3 or now-max(0.,age)<pending:return
        if int.from_bytes(msg.data[:2],'little')!=0x701a:return
        self.pending.pop(n,None)
        if (arb>>16)&255:
            with self.lock:self.values.pop(n,None)
            return
        value=struct.unpack('<f',bytes(msg.data[4:]))[0]
        if math.isfinite(value) and abs(value)<=100:
            with self.lock:self.values[n]=(value,now-max(0.,age))

    def start(self):
        self.thread=threading.Thread(target=self.run,name='rs-iqf-readonly',daemon=True)
        self.thread.start()
        return self

    def run(self):
        import can
        index=0;next_read=0.
        try:
            while not self.stop.is_set():
                now=self.clock()
                if now>=next_read:
                    name=NAMES[index%7];index+=1
                    motor,host=self.entries[name]
                    self.pending[name]=now
                    self.bus.send(can.Message(arbitration_id=(17<<24)|(host<<8)|motor,
                                  is_extended_id=True,data=b'\x1a\x70'+bytes(6)),timeout=0.)
                    next_read=now+.05 # 总共 20 请求/s，每轴约 2.86 Hz，不等待设备回包。
                msg=self.bus.recv(timeout=.02)
                if msg is not None:self.ingest(msg)
        except Exception as e:
            self.error=str(e)

    def snapshot(self,now):
        with self.lock:
            return {n:dict(current_a=v if 0<=now-t<=1. else None,
                           current_age_s=max(0.,now-t)) for n,(v,t) in self.values.items()}

    def close(self):
        self.stop.set()
        if self.thread:self.thread.join(timeout=.3)
        self.bus.shutdown()
