import { test } from "node:test";
import assert from "node:assert/strict";
import { streamText, tool } from "ai";
import { MockLanguageModelV4 } from "ai/test";
import { z } from "zod";
import { networkRecovery, networkRetries, networkRetryDelayMs, resilientModel, transientNetworkError } from "../src/lib/network";

test("网络恢复遵守 15 次、10 秒间隔，取消可立即结束等待", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  const controller = new AbortController();
  const attempts: number[] = [], errors: string[] = [];
  const recovery = networkRecovery(controller.signal, async (s) => { attempts.push(s.attempt); errors.push(s.error); });
  for (let i = 1; i <= networkRetries; i++) {
    let done = false;
    const error = i === 1 ? { message: "Failed to fetch" } : i === 2 ? { value: { response: { error: { message: "socket closed" } } } } : Error("Failed to fetch");
    const retry = recovery.retry(error).then(() => { done = true; });
    await Promise.resolve();
    t.mock.timers.tick(networkRetryDelayMs - 1);
    await Promise.resolve();
    assert.equal(done, false);
    t.mock.timers.tick(1);
    await retry;
  }
  assert.equal(attempts.length, 15);
  assert.deepEqual(errors.slice(0, 2), ["Failed to fetch", "socket closed"]);
  await assert.rejects(recovery.retry(Error("Failed to fetch")), /Failed to fetch/);
  const waiting = networkRecovery(controller.signal).retry(Error("Failed to fetch"));
  const rejected = assert.rejects(waiting, { name: "AbortError" });
  controller.abort();
  await rejected;
  assert.equal(transientNetworkError({ statusCode: 401 }), false);
  assert.equal(transientNetworkError({ name: "AbortError", message: "stream closed" }), false);
  assert.equal(transientNetworkError({ message: "stream ended without a terminal response event" }), true);
});

test("模型流中断后丢弃未确认的工具调用，重试成功只执行一次", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  let executions = 0;
  let retryStarted!: () => void;
  const retrying = new Promise<void>((resolve) => { retryStarted = resolve; });
  const call = { type: "tool-call", toolCallId: "same-call", toolName: "move", input: "{}" } as const;
  const mock = new MockLanguageModelV4({
    doStream: [
      { stream: new ReadableStream({ start(c) {
        c.enqueue(call);
        // No terminal event: the middleware must detect this as a broken stream.
        c.close();
      } }) },
      { stream: new ReadableStream({ start(c) {
        c.enqueue(call);
        c.enqueue({
          type: "finish", finishReason: { unified: "tool-calls", raw: "tool_calls" },
          usage: {
            inputTokens: { total: 1, noCache: 1, cacheRead: 0, cacheWrite: 0 },
            outputTokens: { total: 1, text: 1, reasoning: 0 },
          },
        });
        c.close();
      } }) },
    ],
  });
  const result = streamText({
    model: resilientModel(mock, new AbortController().signal, async () => { retryStarted(); }),
    prompt: "测试动作；仅使用计数器，不连接设备",
    tools: { move: tool({ inputSchema: z.object({}), execute: () => { executions++; return { done: true }; } }) },
    streamRetries: networkRetries,
    maxRetries: 0,
    onError: () => {}, // Expected first-attempt stream fault.
  });
  const consumed = result.consumeStream();
  await retrying;
  assert.equal(executions, 0);
  await Promise.resolve();
  await Promise.resolve();
  t.mock.timers.tick(networkRetryDelayMs);
  await consumed;
  assert.equal(await result.finishReason, "tool-calls");
  assert.equal(mock.doStreamCalls.length, 2);
  assert.equal(executions, 1);
});
