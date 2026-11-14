import { t } from "../../lib/i18n";
// FL-only typed subset of star-arm-studio 71114a0 fashionstar_serial.js.
export interface Packet {
  code: number;
  params: Uint8Array;
}
export interface Monitor {
  id: number;
  angle: number;
  power: number;
  current: number;
  voltage: number;
  temperatureRaw: number;
  status: number;
  turn: number;
}
export const checksum = (bytes: ArrayLike<number>) =>
  Array.from(bytes).reduce((sum, v) => (sum + v) & 255, 0);
export function pack(
  code: number,
  params: number[] | Uint8Array,
  response = false,
) {
  if (params.length > 255) throw Error(t("协议参数长度超过一字节范围"));
  const frame = Uint8Array.from([
    ...(response ? [0x05, 0x1c] : [0x12, 0x4c]),
    code,
    params.length,
    ...params,
    0,
  ]);
  frame[frame.length - 1] = checksum(frame.subarray(0, -1));
  return frame;
}
export class PacketParser {
  buffer: number[] = [];
  push(chunk: Uint8Array): Packet[] {
    this.buffer.push(...chunk);
    const packets: Packet[] = [];
    while (this.buffer.length >= 5) {
      if (this.buffer[0] !== 0x05 || this.buffer[1] !== 0x1c) {
        this.buffer.shift();
        continue;
      }
      const size = this.buffer[3] + 5;
      if (this.buffer.length < size) break;
      const frame = this.buffer.slice(0, size);
      if (checksum(frame.slice(0, -1)) !== frame[size - 1]) {
        this.buffer.shift();
        continue;
      }
      this.buffer.splice(0, size);
      packets.push({
        code: frame[2],
        params: Uint8Array.from(frame.slice(4, -1)),
      });
    }
    return packets;
  }
}
export const ServoProtocol = {
  syncServoMonitor: (ids: number[]) => pack(25, [22, 1, ids.length, ...ids]),
  lockTorque: (id: number) => pack(24, [id, 0x11, 0, 0]),
  syncMultiTurnAngleByInterval(
    angles: number[],
    options: {
      servoIds: number[];
      interval: number;
      tAcc: number;
      tDec: number;
      power: number | number[];
    },
  ) {
    if (
      options.servoIds.length !== angles.length ||
      (Array.isArray(options.power) && options.power.length !== angles.length)
    )
      throw Error(t("同步指令的角度、ID 与功率条目数量不一致"));
    if (angles.some((angle) => !Number.isFinite(angle) || angle * 10 < -0x80000000 || angle * 10 > 0x7fffffff))
      throw Error(t("舵机角度超出协议 32 位有符号数范围"));
    const bytes = new Uint8Array(3 + angles.length * 15),
      v = new DataView(bytes.buffer);
    bytes.set([14, 15, angles.length]);
    options.servoIds.forEach((id, i) => {
      const o = 3 + i * 15;
      v.setUint8(o, id);
      v.setInt32(o + 1, Math.trunc(angles[i] * 10), true);
      v.setUint32(o + 5, options.interval, true);
      v.setUint16(o + 9, options.tAcc, true);
      v.setUint16(o + 11, options.tDec, true);
      v.setUint16(
        o + 13,
        Array.isArray(options.power) ? options.power[i] : options.power,
        true,
      );
    });
    return pack(25, bytes);
  },
};
export function parseMonitor(packet: Packet): Monitor | null {
  if (packet.code !== 22 || packet.params.length !== 16) return null;
  const v = new DataView(packet.params.buffer, packet.params.byteOffset, 16);
  const angle = v.getInt32(10, true),
    turn = v.getInt16(14, true);
  if (angle === -235929599 && turn === 0) return null;
  return {
    id: v.getUint8(0),
    angle: angle / 10,
    power: v.getUint16(5, true),
    current: v.getUint16(3, true),
    voltage: v.getUint16(1, true),
    temperatureRaw: v.getUint16(7, true),
    status: v.getUint8(9),
    turn,
  };
}
