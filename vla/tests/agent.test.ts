import { test } from "node:test";
import assert from "node:assert/strict";
import { Agent, DEFAULT_AI } from "../src/lib/agent";
import { Robot } from "../src/lib/robot";
import { Cameras } from "../src/lib/cameras";
import { emptySession, type Session } from "../src/lib/types";

test("恢复未结束会话：保留补充、标记中断，不重放动作", () => {
  const session = emptySession();
  session.active = true;
  session.pending = ["先检查夹取深度"];
  session.entries.push({ id: "motion", kind: "tool", text: "move_joints · 执行中", at: 1 });
  const agent = new Agent(new Robot(() => { }), new Cameras(), () => { });
  agent.restore(session);
  assert.equal(agent.running, false);
  assert.deepEqual(agent.session.pending, []);
  assert.ok(agent.session.messages.some((m) => m.content === "先检查夹取深度"));
  assert.ok(agent.session.messages.some((m) => typeof m.content === "string" && m.content.includes("不要自动重放")));
  assert.equal(agent.session.entries[0].text, "move_joints · 已中断，待核对");
  // Old IndexedDB sessions had no active/pending fields.
  agent.restore({ messages: [], entries: [] } as unknown as Session);
  assert.deepEqual(agent.session, emptySession());
});

test("任务初始化失败后解除运行状态，可继续发送", async () => {
  const cameras = new Cameras();
  cameras.available = () => { throw Error("snapshot failure"); };
  const agent = new Agent(new Robot(() => { }), cameras, () => { });
  await agent.run("观察", DEFAULT_AI, "test-only");
  assert.equal(agent.running, false);
  assert.ok(agent.session.entries.some((e) => e.text.includes("snapshot failure")));
});

test("请求中断时保留尚未处理的用户补充，恢复后可继续使用", async () => {
  const originalFetch = globalThis.fetch;
  let ready!: () => void;
  const started = new Promise<void>((r) => {
    ready = r;
  });
  // A pending transport only: no model output, network access or robot action.
  globalThis.fetch = async (_input, init) =>
    new Promise<Response>((_resolve, reject) => {
      const signal = init?.signal;
      if (!signal) {
        reject(Error("Expected abort signal"));
        return;
      }
      signal.addEventListener("abort", () => reject(signal.reason), {
        once: true,
      });
      ready();
    });
  try {
    const agent = new Agent(new Robot(() => { }), new Cameras(), () => { });
    const run = agent.run(
      "观察当前状态",
      { ...DEFAULT_AI, baseURL: "https://model.invalid/v1" },
      "test-only",
    );
    await started;
    agent.supplement("闭合前检查夹取深度和姿态");
    await agent.stop();
    await run;
    assert.equal(agent.running, false);
    assert.ok(
      agent.session.messages.some(
        (m) => m.role === "user" && m.content === "闭合前检查夹取深度和姿态",
      ),
    );
    assert.ok(agent.session.entries.some((e) => e.text.includes("已停止")));
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("同一原生压缩窗口完整追加图片并保持实际请求前缀与缓存键稳定", async () => {
  const originalFetch = globalThis.fetch;
  const requests: { input: unknown[]; prompt_cache_key: string }[] = [];
  let frame = 0;
  const cameras = new Cameras();
  cameras.available = () => ["external", "wrist"];
  cameras.activate = async () => undefined;
  cameras.capture = (role) => {
    assert.equal(role, "external", "任务初始图片只使用外部相机");
    return {
      role, captured_at: String(++frame), width: 1280, height: 720,
      dataURL: `data:image/jpeg;base64,${Buffer.from([255, 216, 255, frame]).toString("base64")}`,
    };
  };
  globalThis.fetch = async (_input, init) => {
    requests.push(JSON.parse(String(init?.body)));
    const index = requests.length;
    const item = {
      type: "function_call", id: `fc-${index}`, call_id: `call-${index}`,
      name: "observe_camera", arguments: '{"role":"external"}', status: "completed",
    };
    const events = [
      { type: "response.created", response: { id: `resp-${index}`, created_at: index, model: DEFAULT_AI.model } },
      ...(index <= 4 ? [
        { type: "response.output_item.added", output_index: 0, item: { ...item, arguments: "" } },
        { type: "response.function_call_arguments.delta", item_id: item.id, output_index: 0, delta: item.arguments },
        { type: "response.output_item.done", output_index: 0, item },
      ] : []),
      { type: "response.completed", response: { usage: { input_tokens: 1, output_tokens: 1, total_tokens: 2 } } },
    ];
    return new Response(events.map((event) => `data: ${JSON.stringify(event)}\n\n`).join(""), {
      headers: { "content-type": "text/event-stream" },
    });
  };
  try {
    const agent = new Agent(new Robot(() => {}), cameras, () => {});
    await agent.run("比较前后画面", DEFAULT_AI, "test-only");
    assert.equal(requests.length, 5);
    const images = (value: unknown) => JSON.stringify(value).match(/data:image\/jpeg;base64,/g)?.length ?? 0;
    assert.deepEqual(requests.map(images), [1, 2, 3, 4, 5]);
    for (let i = 1; i < requests.length; i++)
      assert.deepEqual(requests[i].input.slice(0, requests[i - 1].input.length), requests[i - 1].input);
    assert.ok(requests[0].prompt_cache_key);
    assert.equal(new Set(requests.map((r) => r.prompt_cache_key)).size, 1);
    for (let i = 1; i <= 5; i++)
      assert.ok(JSON.stringify(requests[4]).includes(`\"captured_at\":\"${i}\"`.replaceAll('"', '\\"')));
    await agent.run("下一项观察任务", DEFAULT_AI, "test-only");
    assert.equal(requests.length, 6);
    assert.equal(images(requests[5]), 6);
    assert.equal(requests[5].prompt_cache_key, requests[0].prompt_cache_key);
    agent.reset();
    await agent.run("新会话", DEFAULT_AI, "test-only");
    assert.notEqual(requests[6].prompt_cache_key, requests[0].prompt_cache_key);
    cameras.available = () => ["wrist"];
    agent.reset();
    await agent.run("仅腕部预览已开启，初始画面仍只使用外部相机", DEFAULT_AI, "test-only");
    assert.equal(images(requests.at(-1)), 0);
    assert.ok(agent.session.entries.at(-1)?.text.startsWith("本轮已结束"));
  } finally {
    globalThis.fetch = originalFetch;
  }
});

for (const supported of [true, false]) test(`原生压缩${supported ? "承接 SDK 密文并继续同一任务" : "未返回检查点时保留历史并明确报错"}`, async () => {
  const originalFetch = globalThis.fetch;
  const requests: { input: { type?: string; encrypted_content?: string }[]; prompt_cache_key: string }[] = [];
  let regular = 0;
  let duringCompaction = () => {};
  const cameras = new Cameras();
  cameras.available = () => ["external"];
  cameras.activate = async () => undefined;
  cameras.capture = () => ({ role: "external", captured_at: "sample", width: 1280, height: 720, dataURL: "data:image/jpeg;base64,/9j/AA==" });
  globalThis.fetch = async (_input, init) => {
    const body = JSON.parse(String(init?.body)); requests.push(body);
    if (body.input.some((item: { type: string }) => item.type === "compaction_trigger")) {
      duringCompaction();
      return Response.json({ id: "resp-cmp", object: "response", created_at: 1, model: DEFAULT_AI.model,
        status: "completed", error: null, incomplete_details: null,
        output: supported ? [{ type: "compaction", id: "cmp-one", encrypted_content: "opaque-checkpoint" }] : [],
        usage: { input_tokens: 100, output_tokens: 8, total_tokens: 108 },
      });
    }
    regular++;
    const item = { type: "function_call", id: "fc-one", call_id: "call-one", name: "observe_camera", arguments: '{"role":"external"}', status: "completed" };
    const events = [
      { type: "response.created", response: { id: `resp-${regular}`, created_at: regular, model: DEFAULT_AI.model } },
      ...(regular === 1 ? [
        { type: "response.output_item.added", output_index: 0, item: { ...item, arguments: "" } },
        { type: "response.function_call_arguments.delta", item_id: item.id, output_index: 0, delta: item.arguments },
        { type: "response.output_item.done", output_index: 0, item },
      ] : []),
      { type: "response.completed", response: { usage: { input_tokens: 100, output_tokens: 1, total_tokens: 101 } } },
    ];
    return new Response(events.map((e) => `data: ${JSON.stringify(e)}\n\n`).join(""), { headers: { "content-type": "text/event-stream" } });
  };
  try {
    const agent = new Agent(new Robot(() => {}), cameras, () => {});
    if (supported) duringCompaction = () => agent.supplement("压缩期间的新纠正需要在下一步送达");
    await agent.run("保留这个任务，不操作机械臂", { ...DEFAULT_AI, compactTokens: 2 }, "test-only");
    assert.equal(agent.running, false);
    assert.ok(agent.session.messages.some((m) => m.content === "保留这个任务，不操作机械臂"));
    assert.equal(requests.length, supported ? 3 : 2);
    assert.equal(new Set(requests.map((r) => r.prompt_cache_key)).size, 1);
    if (supported) {
      assert.ok(requests[2].input.some((x) => x.type === "compaction" && x.encrypted_content === "opaque-checkpoint"));
      assert.equal(JSON.stringify(requests[2]).includes("保留这个任务"), false);
      assert.equal(JSON.stringify(requests[2]).includes("压缩期间的新纠正"), true);
      assert.ok(agent.session.entries.some((e) => e.text === "原生上下文压缩完成，继续当前任务"));
    } else {
      assert.ok(agent.session.entries.some((e) => e.text.includes("未返回原生 compaction")));
      assert.equal(JSON.stringify(agent.session.messages).includes("opaque-checkpoint"), false);
    }
  } finally { globalThis.fetch = originalFetch; }
});



for (const reason of ["max_output_tokens", "content_filter"]) test(`模型未完整结束：${reason} 不执行截断调用，续写或恢复后只执行一次`, async () => {
  const originalFetch = globalThis.fetch;
  let requests = 0, motions = 0;
  const bodies: unknown[] = [];
  const robot = new Robot(() => {});
  robot.gripper = async () => { motions++; return { command_sent: true } as Awaited<ReturnType<Robot["gripper"]>>; };
  globalThis.fetch = async (_input, init) => {
    requests++;
    bodies.push(JSON.parse(String(init?.body)));
    const item = { type: "function_call", id: `fc-grip-${requests}`, call_id: `call-grip-${requests}`, name: "gripper", arguments: '{"angle_deg":0,"observe":false}', status: "completed" };
    const events = [
      { type: "response.created", response: { id: `resp-${requests}`, created_at: requests, model: DEFAULT_AI.model } },
      ...(requests <= 2 ? [
        { type: "response.output_item.added", output_index: 0, item: { ...item, arguments: "" } },
        { type: "response.function_call_arguments.delta", item_id: item.id, output_index: 0, delta: item.arguments },
        { type: "response.output_item.done", output_index: 0, item },
      ] : []),
      { type: requests === 1 ? "response.incomplete" : "response.completed", response: {
        ...(requests === 1 ? { incomplete_details: { reason } } : {}),
        usage: { input_tokens: 100, output_tokens: 1, total_tokens: 101 },
      } },
    ];
    return new Response(events.map((event) => `data: ${JSON.stringify(event)}\n\n`).join(""), { headers: { "content-type": "text/event-stream" } });
  };
  try {
    const agent = new Agent(robot, new Cameras(), () => {});
    await agent.run("仅验证流程，执行使用虚拟计数器", DEFAULT_AI, "test-only");
    assert.equal(agent.running, false);
    if (reason === "content_filter") {
      assert.equal(requests, 1); assert.equal(motions, 0);
      assert.ok(agent.session.entries.at(-1)?.text.includes("运行失败"));
      assert.ok(agent.session.entries.at(-1)?.text.includes("content-filter"));
      assert.equal(agent.session.entries.some((e) => e.text.startsWith("本轮已结束")), false);
      await agent.run("依据当前状态继续", DEFAULT_AI, "test-only");
    }
    assert.equal(requests, 3);
    assert.equal(motions, 1);
    assert.ok(JSON.stringify(bodies[1]).includes("SDK 未执行此调用"));
    assert.ok(JSON.stringify(bodies[2]).includes("command_sent"));
    if (reason === "max_output_tokens")
      assert.ok(JSON.stringify(bodies[1]).includes("已执行的动作不重复执行"));
    assert.ok(agent.session.entries.at(-1)?.text.startsWith("本轮已结束"));
  } finally { globalThis.fetch = originalFetch; }
});


test("动作调用中停止后可在同会话恢复，不把已开始动作误标为未执行或重放", async () => {
  const originalFetch = globalThis.fetch;
  let requests = 0, motions = 0;
  let entered!: () => void;
  const started = new Promise<void>((resolve) => { entered = resolve; });
  const robot = new Robot(() => {});
  robot.gripper = async (_angle, _duration, _power, signal) => {
    motions++; entered();
    return new Promise((_resolve, reject) => {
      if (signal?.aborted) reject(signal.reason);
      else signal?.addEventListener("abort", () => reject(signal.reason), { once: true });
    });
  };
  globalThis.fetch = async () => {
    requests++;
    const item = { type: "function_call", id: "fc-stop", call_id: "call-stop", name: "gripper", arguments: '{"angle_deg":0,"observe":false}', status: "completed" };
    const events = [
      { type: "response.created", response: { id: `resp-${requests}`, created_at: requests, model: DEFAULT_AI.model } },
      ...(requests === 1 ? [
        { type: "response.output_item.added", output_index: 0, item: { ...item, arguments: "" } },
        { type: "response.function_call_arguments.delta", item_id: item.id, output_index: 0, delta: item.arguments },
        { type: "response.output_item.done", output_index: 0, item },
      ] : []),
      { type: "response.completed", response: { usage: { input_tokens: 1, output_tokens: 1, total_tokens: 2 } } },
    ];
    return new Response(events.map((e) => `data: ${JSON.stringify(e)}\n\n`).join(""), { headers: { "content-type": "text/event-stream" } });
  };
  try {
    const agent = new Agent(robot, new Cameras(), () => {});
    const run = agent.run("仅测试虚拟动作停止", DEFAULT_AI, "test-only");
    await started; await agent.stop(); await run;
    assert.equal(motions, 1);
    assert.ok(agent.session.entries.some((e) => e.text.includes("已停止")));
    assert.equal(JSON.stringify(agent.session.messages).includes("SDK 未执行此调用"), false);
    await agent.run("仅检查当前状态，不重放动作", DEFAULT_AI, "test-only");
    assert.equal(requests, 2); assert.equal(motions, 1);
    assert.ok(agent.session.entries.at(-1)?.text.startsWith("本轮已结束"));
  } finally { globalThis.fetch = originalFetch; }
});
