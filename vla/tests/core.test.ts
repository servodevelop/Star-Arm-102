import { setLocale } from "../src/lib/i18n";
setLocale("zh");
import { test } from "node:test";
import assert from "node:assert/strict";
import { forwardKinematics } from "../src/vendor/star-arm/kinematics";
import {
  checksum,
  pack,
  PacketParser,
  parseMonitor,
  ServoProtocol,
} from "../src/vendor/star-arm/protocol";
import {
  SerialServoBus,
  type SerialPortLike,
} from "../src/vendor/star-arm/serial";
import {
  DEFAULT_MAPPING,
  assertJoints,
  inverse,
  modelAngles,
  posture,
  servoAngles,
  toRadians,
  WORK_POSE,
} from "../src/lib/model";
import { Robot } from "../src/lib/robot";

test("关节范围检查使用用户指定的 0.5° 容差，保留实际反馈", () => {
  const robot = new Robot(() => { });
  const actual = [-0.3, -0.3, -59.6, -60.6, -1.1, 0.1];
  robot.state.actual = posture(actual);
  assert.deepEqual(robot.preview(actual).joints_deg, actual);
  assert.doesNotThrow(() => assertJoints([0, -0.5, -60, -60, 0, 0]));
  assert.throws(() => assertJoints([0, -0.51, -60, -60, 0, 0]), /J2/);
  assert.throws(() => ServoProtocol.syncMultiTurnAngleByInterval([NaN], {
    servoIds: [0], interval: 1000, tAcc: 100, tDec: 100, power: 0,
  }), /32 位/);
});

test("FL 模型与舵机正逆转换，J4 仅反向一次", () => {
  const q = [15, 20, -50, 35, -10, 40];
  assert.deepEqual(
    servoAngles(q, DEFAULT_MAPPING),
    [15, 20, -50, -35, -10, 40],
  );
  assert.deepEqual(
    servoAngles(WORK_POSE, DEFAULT_MAPPING),
    [0, 0, -60, 60, 0, 0],
  );
  assert.deepEqual(
    modelAngles(servoAngles(q, DEFAULT_MAPPING), DEFAULT_MAPPING),
    q,
  );
});
test("位置逆解回到可达正解，不把预览当成回读", () => {
  for (const q of [
    WORK_POSE,
    [20, 30, -70, 25, 15, -10],
    [-20, 40, -90, 40, -20, 25],
  ]) {
    const expected = posture(q).tcp_mm;
    const solution = inverse(
      expected,
      q.map((v, i) => v + (i === 0 ? 2 : 0)),
    );
    assert.equal(solution.success, true);
    const actual = posture(solution.joints_deg!).tcp_mm;
    assert.ok(Math.hypot(...actual.map((v, i) => v - expected[i])) <= 1);
  }
  const unreachable = inverse([5000, 5000, 5000], WORK_POSE);
  assert.equal(unreachable.success, false);
  assert.equal(unreachable.reason, "unreachable");
  assert.equal(unreachable.iterations, 0);
  assert.equal(inverse([NaN, 0, 0], WORK_POSE).reason, "invalid-input");
  assert.equal(forwardKinematics(toRadians(WORK_POSE)).points.length, 7);
});
test("TypeScript 正解与厂商工作台三组固定结果一致", () => {
  // Independent oracle captured from star-arm-studio 71114a0 before the port.
  const cases = [
    {
      q: [0, 0, 0, 0, 0, 0],
      p: [0.17381011719858666, -0.0041368250041138345, 0.11903722947795524],
    },
    {
      q: [0, 0, -60, 60, 0, 0],
      p: [-0.18483757324337438, -0.004140333590936588, 0.3569258701652952],
    },
    {
      q: [20, 30, -70, 25, 15, -10],
      p: [0.021072774060977725, -0.05358594847903302, 0.4060248580760893],
    },
  ];
  for (const { q, p } of cases)
    assert.ok(
      Math.hypot(
        ...forwardKinematics(toRadians(q)).position.map((v, i) => v - p[i]),
      ) < 1e-12,
    );
});
test("厂商同步指令固定向量：原始负角与 32 位时长保持正确", () => {
  const frame = ServoProtocol.syncMultiTurnAngleByInterval([-12.3], {
    servoIds: [3],
    interval: 2000,
    tAcc: 500,
    tDec: 500,
    power: 1200,
  });
  const expected = [
    0x12, 0x4c, 25, 18, 14, 15, 1, 3, 0x85, 0xff, 0xff, 0xff, 0xd0, 7, 0, 0,
    0xf4, 1, 0xf4, 1, 0xb0, 4,
  ];
  assert.deepEqual([...frame], [...expected, checksum(expected)]);
});
function monitorFrame(id: number, angle: number) {
  const p = new Uint8Array(16),
    v = new DataView(p.buffer);
  v.setUint8(0, id);
  v.setUint16(1, 12000, true);
  v.setUint16(5, 123, true);
  v.setInt32(10, Math.round(angle * 10), true);
  return pack(22, p, true);
}
test("解析真实协议的分片、噪声、错误校验和及乱序响应", () => {
  const parser = new PacketParser(),
    first = monitorFrame(5, -1.2),
    second = monitorFrame(0, 13.4);
  const bad = first.slice();
  bad[bad.length - 1] ^= 1;
  assert.deepEqual(
    parser.push(Uint8Array.from([0x12, 0x4c, ...first.slice(0, 8)])),
    [],
  );
  const packets = parser.push(
    Uint8Array.from([...first.slice(8), ...bad, ...second]),
  );
  assert.deepEqual(
    packets.map(parseMonitor).map((m) => [m!.id, m!.angle]),
    [
      [5, -1.2],
      [0, 13.4],
    ],
  );
});

function virtualPort() {
  let controller: ReadableStreamDefaultController<Uint8Array>;
  const frames: Uint8Array[] = [],
    angles = [0, 0, -60, 60, 0, 0, 0];
  const port: SerialPortLike = {
    readable: new ReadableStream({
      start(c) {
        controller = c;
      },
    }),
    writable: new WritableStream({
      write(frame: Uint8Array) {
        frames.push(frame.slice());
        if (frame[2] === 25 && frame[4] === 22) {
          for (const id of [...frame.slice(7, -1)].reverse())
            controller.enqueue(monitorFrame(id, angles[id]));
        }
        if (frame[2] === 25 && frame[4] === 14) {
          const v = new DataView(
            frame.buffer,
            frame.byteOffset,
            frame.byteLength,
          );
          for (let i = 0; i < frame[6]; i++)
            angles[frame[7 + i * 15]] = v.getInt32(8 + i * 15, true) / 10;
        }
      },
    }),
    async open() { },
    async close() { },
  };
  return { port, frames, end: () => controller.close() };
}
test("后台回读保持就绪，实际动作仍标记执行中，所有回读共用串口队列", { timeout: 5000 }, async () => {
  const virtual = virtualPort();
  const bus = new SerialServoBus("test");
  const connect = bus.connect.bind(bus);
  bus.connect = (_port, options) => connect(virtual.port, options);
  const feedback = bus.feedback.bind(bus);
  let activeReads = 0;
  let maxReads = 0;
  bus.feedback = async (...args) => {
    activeReads++;
    maxReads = Math.max(maxReads, activeReads);
    try { return await feedback(...args); }
    finally { activeReads--; }
  };
  const busy: boolean[] = [];
  let samples = 0;
  let previousSample: number | null = null;
  let enoughSamples!: () => void;
  const polled = new Promise<void>((resolve) => { enoughSamples = resolve; });
  const robot = new Robot((state) => {
    busy.push(state.busy);
    if (state.sampledAt !== null && state.sampledAt !== previousSample) {
      previousSample = state.sampledAt;
      if (++samples >= 3) enoughSamples();
    }
  }, bus);
  try {
    await robot.connect(1000000);
    await polled;
    assert.ok(busy.every((value) => !value));
    assert.ok(virtual.frames.every((frame) => frame[4] === 22));
    assert.deepEqual(robot.state.actual!.joints_deg, WORK_POSE);
    const beforeMotion = busy.length;
    await robot.move(WORK_POSE, 1);
    assert.ok(busy.slice(beforeMotion).includes(true));
    assert.equal(robot.state.busy, false);
    const beforeReads = busy.length;
    await Promise.all([robot.refresh(), robot.refresh(), robot.refresh()]);
    assert.ok(busy.slice(beforeReads).every((value) => !value));
    assert.equal(maxReads, 1);
  } finally {
    await robot.disconnect();
  }
});
test("串口驱动契约（虚拟设备）：只读连接，预览不写，六轴不改变夹爪，取消清空后续动作", async () => {
  const virtual = virtualPort(),
    bus = new SerialServoBus("test");
  await bus.connect(virtual.port);
  const robot = new Robot(() => { }, bus);
  await robot.refresh();
  assert.deepEqual(robot.state.actual!.joints_deg, WORK_POSE);
  const before = virtual.frames.length;
  robot.preview([0, 0, -55, 60, 0, 0]);
  assert.equal(virtual.frames.length, before);
  await robot.move([0, 0, -55, 60, 0, 0], 1);
  assert.equal(robot.state.gripper_deg, 0);
  const operation = robot.move([5, 0, -55, 60, 0, 0], 30000);
  const rejected = assert.rejects(operation);
  await new Promise((r) => setTimeout(r, 5));
  const queued = robot.move([10, 0, -55, 60, 0, 0], 1);
  const rejectedQueue = assert.rejects(queued);
  await robot.stop();
  await rejected;
  await rejectedQueue;
  assert.equal(virtual.frames.filter((f) => f[2] === 24).length, 7);
  assert.equal(robot.state.actual!.joints_deg[0], 5);
  await robot.disconnect();
});
test("串口打开失败保留原始错误，清理不再次关闭未打开端口", async () => {
  const virtual = virtualPort();
  let closed = 0;
  virtual.port.open = async () => {
    throw Error("original open failure");
  };
  virtual.port.close = async () => {
    closed++;
    throw Error("already closed");
  };
  const bus = new SerialServoBus("test");
  await assert.rejects(bus.connect(virtual.port), /original open failure/);
  assert.equal(closed, 0);
  assert.equal(bus.connected, false);
});

test("工作位使用一条七轴同步指令，闭合夹爪且不改变六轴的默认功率", async () => {
  const virtual = virtualPort(),
    bus = new SerialServoBus("test");
  await bus.connect(virtual.port);
  const robot = new Robot(() => { }, bus);
  await robot.gripper(30, 1, 500);
  const before = virtual.frames.length;
  await robot.workPose(1, 600);
  const commands = virtual.frames
    .slice(before)
    .filter((f) => f[2] === 25 && f[4] === 14);
  assert.equal(commands.length, 1);
  const frame = commands[0],
    v = new DataView(frame.buffer, frame.byteOffset, frame.byteLength);
  assert.equal(frame[6], 7);
  assert.deepEqual(
    Array.from({ length: 7 }, (_, i) => v.getInt32(8 + i * 15, true) / 10),
    [0, 0, -60, 60, 0, 0, 0],
  );
  assert.deepEqual(
    Array.from({ length: 7 }, (_, i) => v.getUint16(20 + i * 15, true)),
    [0, 0, 0, 0, 0, 0, 600],
  );
  assert.equal(robot.state.gripper_deg, 0);
  await robot.disconnect();
});

test("串口读流结束后释放旧锁，允许重新连接并回读", async () => {
  const first = virtualPort();
  let lost!: () => void;
  const disconnected = new Promise<void>((resolve) => {
    lost = resolve;
  });
  const bus = new SerialServoBus("test", { onLost: lost });
  await bus.connect(first.port);
  await bus.feedback([0, 6]);
  first.end();
  await disconnected;
  assert.equal(bus.connected, false);
  const second = virtualPort();
  await bus.connect(second.port);
  assert.equal(bus.connected, true);
  assert.deepEqual((await bus.feedback([0, 6])).missingIds, []);
  assert.equal(first.port.readable!.locked, false);
  assert.equal(first.port.writable!.locked, false);
  await bus.disconnect();
});
