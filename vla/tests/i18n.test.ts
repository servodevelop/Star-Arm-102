import { test } from "node:test";
import assert from "node:assert/strict";
import { messages } from "../src/lib/messages";
import { getLocale, setLocale, t, translate } from "../src/lib/i18n";
import { getInstructions } from "../src/lib/prompts";
import { createMotionSchemas } from "../src/lib/actions";
import { Agent } from "../src/lib/agent";
import { Robot } from "../src/lib/robot";
import { Cameras } from "../src/lib/cameras";
import { emptySession } from "../src/lib/types";

test("translations preserve parameters, unknown errors, and saved statuses in both languages", () => {
  for (const [zh, en] of Object.entries(messages)) {
    assert.ok(en.trim(), zh);
    assert.deepEqual(
      [...zh.matchAll(/\{\d+\}/g)].map((m) => m[0]).sort(),
      [...en.matchAll(/\{\d+\}/g)].map((m) => m[0]).sort(),
      zh,
    );
  }
  assert.equal(
    translate("网络重试 {0}/{1}，10 秒后继续：{2}", "en", 2, 15, "HTTP 502"),
    "Network retry 2/15, continuing in 10 seconds: HTTP 502",
  );
  assert.equal(translate("move_tcp · Running", "zh"), "move_tcp · 执行中");
  assert.equal(
    translate("move_tcp · 已中断，待核对", "en"),
    "move_tcp · Interrupted; check state",
  );
  assert.equal(
    translate("J2 is outside the original model range 0～180°", "zh"),
    "J2 超出原模型范围 0～180°",
  );
  assert.equal(translate("constructor", "en"), "constructor");
  assert.equal(translate("toString", "zh"), "toString");
  assert.equal(
    translate("upstream-specific-error", "zh"),
    "upstream-specific-error",
  );
  assert.equal(
    translate("{0}实时画面", "zh", "External camera"),
    "外部相机实时画面",
  );
});

test("language changes localize schemas without changing motion parameters or vendor mapping", () => {
  setLocale("en");
  assert.equal(getLocale(), "en");
  assert.equal(t("从臂串口未连接"), "Follower serial port is not connected");
  const en = createMotionSchemas("en"),
    zh = createMotionSchemas("zh");
  assert.match(en.jointsSchema.description!, /model angles/);
  assert.match(zh.jointsSchema.description!, /模型角/);
  const input = {
    action: "move_joints",
    joints_deg: [0, 0, -60, -60, 0, 0],
    duration_ms: 2000,
  };
  assert.deepEqual(en.motionSchema.parse(input), zh.motionSchema.parse(input));
  for (const locale of ["en", "zh"] as const) {
    const prompt = getInstructions(locale);
    assert.match(prompt, /0\.5°/);
    assert.match(prompt, /work_pose/);
    assert.match(prompt, /run_sequence/);
    assert.equal(getInstructions(locale), prompt, "prompt prefix stays stable");
  }
});

test("English in-progress records recover as interrupted without replaying actions or changing user text", () => {
  setLocale("en");
  const state = emptySession();
  state.active = true;
  state.entries = [
    { id: "1", kind: "tool", text: "move_joints · Running", at: 1 },
    { id: "2", kind: "user", text: "保持中文原文", at: 2 },
  ];
  const agent = new Agent(new Robot(() => {}), new Cameras(), () => {});
  agent.restore(state);
  assert.equal(agent.running, false);
  assert.equal(
    t(agent.session.entries[0].text),
    "move_joints · Interrupted; check state",
  );
  assert.equal(agent.session.entries[1].text, "保持中文原文");
  assert.ok(
    agent.session.entries.some((e) => e.text.includes("reconnect devices")),
  );
  assert.ok(
    agent.session.messages.some(
      (m) =>
        typeof m.content === "string" && m.content.includes("do not replay"),
    ),
  );
});

test("a running task keeps one prompt/tool language even when the interface switches", async () => {
  const originalFetch = globalThis.fetch;
  setLocale("en");
  const requests: {
    instructions?: string;
    input: { role: string; content: unknown }[];
    tools: { description?: string }[];
  }[] = [];
  globalThis.fetch = async (_url, init) => {
    requests.push(JSON.parse(String(init?.body)));
    const index = requests.length;
    const call = {
      type: "function_call",
      id: "fc-state",
      call_id: "call-state",
      name: "get_state",
      arguments: "{}",
      status: "completed",
    };
    const output = index === 1 ? [call] : [];
    const events = [
      {
        type: "response.created",
        response: {
          id: `resp-${index}`,
          created_at: index,
          model: "gpt-6-astra",
        },
      },
      ...(index === 1
        ? [
            {
              type: "response.output_item.added",
              output_index: 0,
              item: { ...call, arguments: "" },
            },
            {
              type: "response.function_call_arguments.delta",
              item_id: call.id,
              output_index: 0,
              delta: "{}",
            },
            { type: "response.output_item.done", output_index: 0, item: call },
          ]
        : []),
      {
        type: "response.completed",
        response: {
          id: `resp-${index}`,
          status: "completed",
          output,
          usage: { input_tokens: 100, output_tokens: 10 },
        },
      },
    ];
    setLocale("zh");
    return new Response(
      events.map((e) => `data: ${JSON.stringify(e)}\n\n`).join(""),
      { headers: { "content-type": "text/event-stream" } },
    );
  };
  try {
    const agent = new Agent(new Robot(() => {}), new Cameras(), () => {});
    await agent.run(
      "Read state only",
      {
        baseURL: "https://model.invalid/v1",
        model: "gpt-6-astra",
        effort: "medium",
        durationMs: 2000,
        gripperPowerMw: 0,
      },
      "test-only",
    );
    assert.equal(requests.length, 2);
    for (const request of requests) {
      const system =
        request.instructions ??
        JSON.stringify(
          request.input.filter((m) => ["system", "developer"].includes(m.role)),
        );
      assert.ok(
        system.includes(
          "Explain observations, decisions, actions, and results in English.",
        ),
      );
      assert.ok(
        request.tools.every(
          (tool) => !/[\p{Script=Han}]/u.test(tool.description ?? ""),
        ),
      );
    }
    assert.equal(agent.running, false);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
