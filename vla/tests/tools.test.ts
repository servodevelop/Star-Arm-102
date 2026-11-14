import { setLocale } from "../src/lib/i18n";
setLocale("zh");
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRobotTools } from "../src/lib/tools";
import { Robot } from "../src/lib/robot";
import { Cameras, type Role } from "../src/lib/cameras";
import { WORK_POSE, posture } from "../src/lib/model";
import { DEFAULT_AI, type Entry } from "../src/lib/types";

const options = { toolCallId: "test", messages: [], context: {} };
function setup() {
  const events: string[] = [],
    entries: Entry[] = [];
  const robot = new Robot(() => {
    events.push("preview");
  });
  const cameras = new Cameras();
  cameras.available = () => ["external", "wrist"];
  cameras.activate = async (role: Role) => {
    events.push(`camera:${role}`);
    return { width: 1280, height: 720, frameRate: 30 };
  };
  cameras.capture = (role: Role) => {
    events.push(`image:${role}`);
    return {
      role,
      captured_at: new Date().toISOString(),
      width: 1280,
      height: 720,
      dataURL: "data:image/jpeg;base64,AA==",
    };
  };
  const result = {
    command_sent: true,
    actual: {
      sampled_at: 1,
      joints_deg: WORK_POSE,
      tcp_mm: [100, 0, 200],
      tool_axes_in_base: [
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
      ],
      tool_axis_elevation_deg: [0, 0, 90],
      servo_deg: [0, 0, -60, 60, 0, 0, 0],
      gripper_deg: 0,
      gripper_power_mw: 0,
    },
    target_error_deg: [0, 0, 0, 0, 0, 0],
  };
  const tools = createRobotTools({
    robot,
    cameras,
    settings: DEFAULT_AI,
    signal: new AbortController().signal,
    record: (kind, text) => {
      const e = { id: String(entries.length), kind, text, at: Date.now() };
      entries.push(e);
      return e;
    },
    changed: () => {},
  });
  return { robot, cameras, tools, events, entries, result };
}

test("并发调用时预览不等待运动，设备与取图按调用顺序执行", async () => {
  const s = setup();
  let finish!: () => void;
  const gate = new Promise<void>((r) => {
    finish = r;
  });
  s.robot.move = async () => {
    s.events.push("move:start");
    await gate;
    s.events.push("move:end");
    return s.result;
  };
  s.robot.gripper = async () => {
    s.events.push("gripper");
    return s.result;
  };
  const moving = s.tools.move_joints.execute!(
    {
      joints_deg: WORK_POSE,
    },
    options,
  );
  const observing = s.tools.observe_camera.execute!({ role: "wrist" }, options);
  const gripping = s.tools.gripper.execute!({ angle_deg: 0, observe: false }, options);
  await new Promise<void>((r) => setImmediate(r));
  await s.tools.preview_joints.execute!({ poses_deg: [WORK_POSE] }, options);
  assert.deepEqual(s.events, ["move:start", "preview"]);
  finish();
  const [motion] = await Promise.all([moving, observing, gripping]);
  assert.deepEqual(s.events, [
    "move:start",
    "preview",
    "move:end",
    "camera:external",
    "image:external",
    "camera:wrist",
    "image:wrist",
    "camera:wrist",
    "image:wrist",
    "gripper",
  ]);
  if (Symbol.asyncIterator in motion) throw Error("测试预期最终工具结果");
  const output = await s.tools.move_joints.toModelOutput!({
    output: motion,
    input: { joints_deg: WORK_POSE },
    toolCallId: "test",
  });
  assert.equal(output.type, "content");
  if (output.type === "content") {
    assert.equal(output.value.filter((p) => p.type === "file").length, 2);
    const text = output.value.find((p) => p.type === "text");
    assert.ok(
      text?.type === "text" && text.text.includes('"command_sent":true'),
    );
  }
  assert.ok(s.entries.every((e) => !e.detail?.includes("base64")));
});

test("动作后取图失败保留已执行结果，不重复运动", async () => {
  const s = setup();
  let count = 0;
  s.robot.move = async () => {
    count++;
    return s.result;
  };
  s.cameras.capture = () => {
    throw Error("camera stopped");
  };
  const result = await s.tools.move_joints.execute!(
    {
      joints_deg: WORK_POSE,
    },
    options,
  );
  assert.equal(count, 1);
  assert.ok(
    result &&
      typeof result === "object" &&
      "command_sent" in result &&
      result.command_sent,
  );
  assert.ok(result && typeof result === "object" && "observation_errors" in result);
  assert.deepEqual(result.observation_errors, { external: "camera stopped", wrist: "camera stopped" });
  assert.equal(s.entries[0].text, "move_joints · 已完成");
});

test("工具图片类型与实际数据一致，兼容历史 JPEG 和当前 WebP", async () => {
  const s = setup();
  for (const mediaType of ["image/jpeg", "image/webp"]) {
    s.cameras.capture = (role) => ({
      role, captured_at: "test", width: 1280, height: 720,
      dataURL: `data:${mediaType};base64,AA==`,
    });
    const result = await s.tools.observe_camera.execute!({ role: "external" }, options);
    if (Symbol.asyncIterator in result) throw Error("Expected final camera result");
    const output = await s.tools.observe_camera.toModelOutput!({ output: result, input: { role: "external" }, toolCallId: "test" });
    assert.equal(output.type, "content");
    if (output.type === "content") {
      const image = output.value.find((part) => part.type === "file");
      assert.equal(image?.mediaType, mediaType);
    }
  }
});

test("批量预览逐项返回有效姿态和错误，不发送运动", async () => {
  const s = setup();
  const result = await s.tools.preview_joints.execute!(
    {
      poses_deg: [WORK_POSE, [0, -1000, 0, 0, 0, 0], [5, 0, -60, -60, 0, 0]],
    },
    options,
  );
  assert.ok("previews" in result);
  assert.deepEqual(
    result.previews.map((p) => p.valid),
    [true, false, true],
  );
  assert.equal("points" in result.previews[2], false);
  assert.ok("tool_axis_elevation_deg" in result.previews[2]);
  assert.equal(s.robot.state.preview?.points.length, 7);
  assert.deepEqual(s.events, ["preview", "preview"]);
});

test("动作序列在 IK 失败处返回部分结果，不进入后续闭爪", async () => {
  const s = setup();
  s.robot.state.actual = posture(WORK_POSE);
  s.robot.refresh = async () => s.robot.state;
  s.robot.gripper = async (angle) => {
    s.events.push(`gripper:${angle}`);
    return s.result;
  };
  const result = await s.tools.run_sequence.execute!(
    {
      steps: [
        { action: "gripper", angle_deg: 30 },
        {
          action: "move_tcp",
          position_mm: [5000, 5000, 5000],
          relative: false,
        },
        { action: "gripper", angle_deg: 0 },
      ],
      observe: false,
    },
    options,
  );
  assert.ok("success" in result);
  assert.equal(result.success, false);
  assert.equal(result.completed_steps, 1);
  assert.ok("failed_step" in result);
  assert.equal(result.failed_step, 2);
  assert.deepEqual(s.events, ["gripper:30"]);
});

test("动作序列复用单步执行，默认只在整组结束后附带两张新图", async () => {
  const s = setup();
  s.robot.gripper = async () => {
    s.events.push("gripper");
    return s.result;
  };
  s.robot.move = async () => {
    s.events.push("move");
    return s.result;
  };
  s.robot.workPose = async () => {
    s.events.push("work");
    return s.result;
  };
  const result = await s.tools.run_sequence.execute!(
    {
      steps: [
        { action: "gripper", angle_deg: 30 },
        { action: "move_joints", joints_deg: WORK_POSE },
        { action: "work_pose" },
      ],
    },
    options,
  );
  assert.ok("success" in result);
  assert.equal(result.success, true);
  assert.equal(result.completed_steps, 3);
  assert.deepEqual(s.events, [
    "gripper",
    "move",
    "work",
    "camera:external",
    "image:external",
    "camera:wrist",
    "image:wrist",
  ]);
});
