import { test } from "node:test";
import assert from "node:assert/strict";
import { Agent, checkAI, DEFAULT_AI } from "../src/lib/agent";
import { SERVICE_TIERS } from "../src/lib/types";
import { Robot } from "../src/lib/robot";
import { Cameras } from "../src/lib/cameras";
import { setLocale } from "../src/lib/i18n";
import { streamResponse } from "./service-tier-fixture";
setLocale("en");

for (const tier of SERVICE_TIERS)
  test(`real SDK serializes service_tier=${tier} and reports the returned tier`, async () => {
    const originalFetch = globalThis.fetch;
    const requests: { service_tier: string; reasoning: { effort: string } }[] =
      [];
    const reported = tier === "fast" ? "priority" : "default";
    globalThis.fetch = async (_url, init) => {
      requests.push(JSON.parse(String(init?.body)));
      return streamResponse(1, reported);
    };
    try {
      const agent = new Agent(new Robot(() => {}), new Cameras(), () => {});
      await agent.run(
        "Text-only request",
        { ...DEFAULT_AI, serviceTier: tier, effort: "high" },
        "test-only",
      );
      assert.equal(requests.length, 1);
      assert.equal(requests[0].service_tier, tier);
      assert.equal(requests[0].reasoning.effort, "high");
      assert.equal(agent.session.usage?.serviceTier, reported);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

test("legacy settings without serviceTier keep automatic server selection", async () => {
  const originalFetch = globalThis.fetch;
  let tier: unknown;
  globalThis.fetch = async (_url, init) => {
    tier = JSON.parse(String(init?.body)).service_tier;
    return streamResponse(1, "default");
  };
  try {
    const { serviceTier: _, ...legacy } = DEFAULT_AI;
    await new Agent(new Robot(() => {}), new Cameras(), () => {}).run(
      "Text only",
      legacy,
      "test-only",
    );
    assert.equal(tier, "auto");
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("native compaction and subsequent requests retain the selected tier and cache key", async () => {
  const originalFetch = globalThis.fetch;
  const requests: {
    service_tier: string;
    prompt_cache_key: string;
    input: { type?: string }[];
  }[] = [];
  let regular = 0;
  globalThis.fetch = async (_url, init) => {
    const body = JSON.parse(String(init?.body));
    requests.push(body);
    if (
      body.input.some((p: { type: string }) => p.type === "compaction_trigger")
    )
      return Response.json({
        id: "resp-compact",
        object: "response",
        created_at: 1,
        model: DEFAULT_AI.model,
        status: "completed",
        service_tier: "ultrafast",
        output: [
          {
            type: "compaction",
            id: "cmp",
            encrypted_content: "native-checkpoint",
          },
        ],
        usage: { input_tokens: 100, output_tokens: 5, total_tokens: 105 },
      });
    regular++;
    return streamResponse(
      regular,
      "ultrafast",
      regular === 1 ? "get_state" : undefined,
    );
  };
  try {
    const agent = new Agent(new Robot(() => {}), new Cameras(), () => {});
    await agent.run(
      "Read state only",
      { ...DEFAULT_AI, serviceTier: "ultrafast", compactTokens: 50 },
      "test-only",
    );
    assert.equal(requests.length, 3);
    assert.ok(requests.every((r) => r.service_tier === "ultrafast"));
    assert.equal(new Set(requests.map((r) => r.prompt_cache_key)).size, 1);
    assert.equal(agent.session.usage?.serviceTier, "ultrafast");
    assert.ok(
      agent.session.entries.some((e) =>
        e.detail?.includes('"service_tier": "ultrafast"'),
      ),
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("connection verification uses the selected tier on both tool-calling steps", async () => {
  const originalFetch = globalThis.fetch;
  const requests: { service_tier: string }[] = [];
  globalThis.fetch = async (_url, init) => {
    requests.push(JSON.parse(String(init?.body)));
    return streamResponse(
      requests.length,
      "priority",
      requests.length === 1 ? "describe_input" : undefined,
    );
  };
  try {
    const summary = await checkAI(
      { ...DEFAULT_AI, serviceTier: "fast" },
      "test-only",
    );
    assert.equal(requests.length, 2);
    assert.ok(requests.every((r) => r.service_tier === "fast"));
    assert.match(summary, /Server tier: priority/);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
