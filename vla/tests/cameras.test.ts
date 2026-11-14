import { test } from "node:test";
import assert from "node:assert/strict";
import { Cameras, CAMERA_STARTUP_MS } from "../src/lib/cameras";

test("开启相机期间关闭不会回写采集中，播放失败释放设备后可重新开启", async () => {
  const original = Object.getOwnPropertyDescriptor(globalThis, "navigator");
  let stops = 0;
  const track = {
    readyState: "live",
    stop() { stops++; this.readyState = "ended"; },
    getSettings: () => ({ width: 1280, height: 720, frameRate: 30 }),
    addEventListener() { },
  };
  const stream = { getTracks: () => [track], getVideoTracks: () => [track] };
  Object.defineProperty(globalThis, "navigator", {
    configurable: true, value: {
      mediaDevices: { getUserMedia: async () => { track.readyState = "live"; return stream; } },
    }
  });
  try {
    const statuses: string[] = [];
    const cameras = new Cameras((_role, status) => statuses.push(status));
    let finish!: () => void;
    const video = { srcObject: null, play: () => new Promise<void>((r) => { finish = r; }) };
    cameras.attach("wrist", video as unknown as HTMLVideoElement);
    const binding = { deviceId: "test", label: "test", width: 1280, height: 720, fps: 30 };
    const starting = cameras.start("wrist", binding);
    await Promise.resolve();
    cameras.stop("wrist");
    finish();
    await starting;
    assert.deepEqual(cameras.available(), []);
    assert.equal(statuses.at(-1), "未开启");
    assert.equal(video.srcObject, null);
    video.play = async () => { throw Error("play failed"); };
    await assert.rejects(cameras.start("wrist", binding), /play failed/);
    assert.equal(stops, 2);
    assert.deepEqual(cameras.available(), []);
    video.play = async () => { };
    await cameras.start("wrist", binding);
    assert.deepEqual(cameras.available(), ["wrist"]);
    cameras.stopAll();
    assert.equal(stops, 3);
  } finally {
    if (original) Object.defineProperty(globalThis, "navigator", original);
    else Reflect.deleteProperty(globalThis, "navigator");
  }
});


test("动作后双图沿用采集方式：单路时轮流取图，双路时保留两路，失败按视角返回", async () => {
  const cameras = new Cameras();
  const binding = { deviceId: "test", label: "test", width: 1280, height: 720, fps: 30 };
  cameras.bindings = { external: binding, wrist: { ...binding, deviceId: "wrist" } };
  let active: ("external" | "wrist")[] = ["external"];
  const events: string[] = [];
  cameras.available = () => active;
  cameras.activate = async (role, exclusive) => {
    events.push(`${role}:${exclusive}`);
    active = exclusive ? [role] : [...new Set([...active, role])];
    return {};
  };
  cameras.capture = (role) => ({ role, captured_at: "test", width: 1280, height: 720, dataURL: "data:image/webp;base64,AA==" });
  const signal = new AbortController().signal;
  const sequential = await cameras.capturePair(signal);
  assert.deepEqual(events, ["wrist:true", "external:true"]);
  assert.deepEqual(sequential.observations.map((f) => f.role), ["wrist", "external"]);
  assert.deepEqual(active, ["external"]);
  active = ["external", "wrist"]; events.length = 0;
  const dual = await cameras.capturePair(signal);
  assert.deepEqual(events, ["external:false", "wrist:false"]);
  assert.equal(dual.observations.length, 2);
  assert.deepEqual(active, ["external", "wrist"]);
  const capture = cameras.capture;
  cameras.capture = (role) => { if (role === "wrist") throw Error("全黑图"); return capture(role); };
  const partial = await cameras.capturePair(signal);
  assert.deepEqual(partial.observations.map((f) => f.role), ["external"]);
  assert.equal(partial.observation_errors?.wrist, "全黑图");
});

test("取图拒绝全黑帧与错误相机来源，正常暗图保留原分辨率和 WebP90", async () => {
  const previous = ["navigator", "document"].map((key) => [key, Object.getOwnPropertyDescriptor(globalThis, key)] as const);
  const track = { readyState: "live", stop() {}, addEventListener() {}, getSettings: () => ({ deviceId: "external-device" }) };
  const stream = { getVideoTracks: () => [track], getTracks: () => [track] };
  let pixels = new Uint8ClampedArray([0, 0, 0, 255, 0, 0, 0, 255]);
  const canvas = { width: 0, height: 0,
    getContext: () => ({ drawImage() {}, getImageData: () => ({ data: pixels }) }),
    toDataURL: (type: string, quality: number) => { assert.equal(type, "image/webp"); assert.equal(quality, .9); return "data:image/webp;base64,AA=="; },
  };
  Object.defineProperty(globalThis, "navigator", { configurable: true, value: { mediaDevices: { getUserMedia: async () => stream } } });
  Object.defineProperty(globalThis, "document", { configurable: true, value: { createElement: () => canvas } });
  try {
    const cameras = new Cameras();
    const binding = { deviceId: "external-device", label: "external", width: 2, height: 1, fps: 30 };
    cameras.bindings.external = binding;
    const video = { srcObject: null as unknown, videoWidth: 2, videoHeight: 1, readyState: 2, play: async () => {} };
    cameras.attach("external", video as HTMLVideoElement);
    await cameras.start("external", binding);
    assert.throws(() => cameras.capture("external"), /全黑图/);
    pixels = new Uint8ClampedArray([1, 0, 0, 255, 0, 0, 0, 255]);
    const frame = cameras.capture("external");
    assert.equal(frame.width, 2); assert.equal(frame.height, 1);
    assert.equal(frame.role, "external");
    video.srcObject = {};
    assert.throws(() => cameras.capture("external"), /来源/);
    video.srcObject = stream;
    cameras.bindings.external = { ...binding, deviceId: "other-camera" };
    assert.throws(() => cameras.capture("external"), /来源/);
  } finally {
    for (const [key, descriptor] of previous)
      if (descriptor) Object.defineProperty(globalThis, key, descriptor);
      else Reflect.deleteProperty(globalThis, key);
  }
});


test("请求未绑定的单路相机不会关闭另一路有效预览", async () => {
  const camera = new Cameras();
  camera.available = () => ["external"];
  const stopped: string[] = [];
  camera.stop = (role) => { stopped.push(role); };
  await assert.rejects(camera.activate("wrist", true), /相机绑定/);
  camera.bindings.wrist = { deviceId: "", label: "", width: 1280, height: 720, fps: 30 };
  await assert.rejects(camera.activate("wrist", true), /相机绑定/);
  assert.deepEqual(stopped, []);
});


test("相机在启动等待后才就绪，等待期间断线不会回写采集中", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  const previous = Object.getOwnPropertyDescriptor(globalThis, "navigator");
  let ended = () => {};
  const track = { readyState: "live", stop() { this.readyState = "ended"; },
    addEventListener(_name: string, callback: () => void) { ended = callback; },
    getSettings: () => ({ width: 1280, height: 720, frameRate: 30 }),
  };
  const stream = { getTracks: () => [track], getVideoTracks: () => [track] };
  Object.defineProperty(globalThis, "navigator", { configurable: true, value: { mediaDevices: {
    getUserMedia: async () => { track.readyState = "live"; return stream; },
  } } });
  try {
    const statuses: string[] = [], cameras = new Cameras((_role, status) => statuses.push(status));
    cameras.attach("external", { srcObject: null, play: async () => {}, videoWidth: 1280, videoHeight: 720, readyState: 4 } as unknown as HTMLVideoElement);
    const binding = { deviceId: "external", label: "external", width: 1280, height: 720, fps: 30 };
    const first = cameras.start("external", binding);
    await Promise.resolve(); await Promise.resolve();
    assert.deepEqual(cameras.available(), []);
    assert.throws(() => cameras.capture("external"), /没有有效画面/);
    track.readyState = "ended"; ended();
    t.mock.timers.tick(CAMERA_STARTUP_MS); await first;
    assert.deepEqual(cameras.available(), []);
    assert.equal(statuses.at(-1), "信号已断开");
    const next = cameras.start("external", binding);
    await Promise.resolve(); await Promise.resolve();
    t.mock.timers.tick(CAMERA_STARTUP_MS - 1);
    assert.deepEqual(cameras.available(), []);
    t.mock.timers.tick(1); await next;
    assert.deepEqual(cameras.available(), ["external"]);
    cameras.stopAll();
  } finally {
    if (previous) Object.defineProperty(globalThis, "navigator", previous);
    else Reflect.deleteProperty(globalThis, "navigator");
  }
});
