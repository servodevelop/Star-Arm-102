import { test } from "node:test";
import assert from "node:assert/strict";
import type { ModelMessage } from "ai";
import { activeContext, hasCompaction } from "../src/lib/context";

const checkpoint = (id: string): ModelMessage => ({
  role: "assistant", content: [{ type: "custom", kind: "openai.compaction", providerOptions: {
    openai: { itemId: id, encryptedContent: `opaque-${id}` },
  } }],
});
test("原生压缩前完整追加历史，保留文字、所有图片和加密推理", () => {
  const history: ModelMessage[] = [
    { role: "user", content: "保持同一模型和思考强度，J4 只反向一次" },
    { role: "assistant", content: [{ type: "reasoning", text: "", providerOptions: { openai: { reasoningEncryptedContent: "opaque" } } }] },
  ];
  for (let i = 0; i < 5; i++) history.push({ role: "user", content: [
    { type: "file", mediaType: "image/webp", data: `data:image/webp;base64,${i}` },
  ] });
  const before = structuredClone(history);
  assert.deepEqual(activeContext(history), history);
  assert.deepEqual(history, before);
  assert.equal(hasCompaction(history), false);
});
test("只从最新有效原生检查点承接，密文与后续工具结果保持原样，完整历史不变", () => {
  const history: ModelMessage[] = [
    { role: "user", content: "最早任务" }, checkpoint("one"),
    { role: "assistant", content: "较早结果" }, checkpoint("two"),
    { role: "tool", content: [{ type: "tool-result", toolName: "move_tcp", toolCallId: "move", output: { type: "text", value: "IK failed" } }] },
    { role: "user", content: "以电机实际反馈继续，不能重复执行" },
  ];
  const before = structuredClone(history);
  assert.deepEqual(activeContext(history), history.slice(3));
  assert.deepEqual(history, before);
  assert.equal(hasCompaction(activeContext(history)), true);
  assert.deepEqual(activeContext(activeContext(history)), activeContext(history));
});
test("缺少原生密文时不裁剪历史，也不将普通文本当作压缩结果", () => {
  const history: ModelMessage[] = [{ role: "user", content: "重要纠正" }, {
    role: "assistant", content: [{ type: "custom", kind: "openai.compaction", providerOptions: { openai: { itemId: "invalid" } } }],
  }];
  assert.equal(hasCompaction(history), false);
  assert.deepEqual(activeContext(history), history);
});

test("切换模型时只移除原生检查点，原始图片、推理和工具反馈仍可重建上下文", async () => {
  const { withoutCompactions } = await import("../src/lib/context");
  const original: ModelMessage[] = [{ role: "user", content: "仍需放到红框" }, {
    role: "assistant", content: [{ type: "reasoning", text: "原始推理" }],
  }, checkpoint("old"), { role: "user", content: [{ type: "file", mediaType: "image/webp", data: "data:image/webp;base64,AA==" }] }];
  assert.deepEqual(withoutCompactions(original), [original[0], original[1], original[3]]);
  assert.equal(original.length, 4);
});
