// Read-only benchmark through real forms/buttons. No injected state or mocked API.
// Source: this project's live-control/profile-task browser acceptance workflow.
import { chromium } from "@playwright/test";
import { createHash } from "node:crypto";
import { mkdir, writeFile } from "node:fs/promises";
const [label, effort = "medium", compactTokens, roundCount = "6", taskText] = process.argv.slice(2);
if (!label || !/^[a-z0-9-]+$/.test(label)) throw Error("Usage: node tests/benchmark-cache.mjs <label> [effort]");
const output = `temp/native-compaction/${label}`;
await mkdir(output, { recursive: true });
const b = await chromium.connectOverCDP(process.env.CDP_URL ?? "http://127.0.0.1:9227");
const pending = new Set(), requests = [], rounds = [];
const hash = (v) => createHash("sha256").update(JSON.stringify(v)).digest("hex");
try {
  const p = b.contexts().flatMap((c) => c.pages()).find((p) => p.url().startsWith(process.env.ARM_URL ?? "http://localhost:8780/"));
  if (await p.getByText("正在处理", { exact: true }).count()) throw Error("Another task is running");
  const model = await p.getByLabel("AI 模型", { exact: true }).inputValue();
  const client_bundle_hash = hash(await p.locator("script[src]").evaluateAll((nodes) => nodes.map((n) => new URL(n.src).pathname)));
  const threshold = p.getByLabel("原生上下文压缩阈值", { exact: true });
  const settings = p.locator(".settings");
  if (!await settings.evaluate((n) => n.open)) await settings.locator("summary").click();
  await p.getByLabel("AI 思考强度").fill(effort);
  if (compactTokens !== undefined) await threshold.fill(compactTokens);
  const native_compaction_threshold = await threshold.count() ? Number(await threshold.inputValue()) : null;
  if (await p.getByRole("button", { name: "保存配置", exact: true }).count()) await p.getByRole("button", { name: "保存配置", exact: true }).click();
  await p.getByRole("button", { name: "新会话", exact: true }).click();
  p.on("requestfinished", (request) => {
    if (request.method() !== "POST" || !new URL(request.url()).pathname.endsWith("/responses")) return;
    const work = (async () => {
      const body = request.postDataJSON(), response = await request.response();
      const raw = await response.text();
      let result;
      if (raw.trimStart().startsWith("{")) result = JSON.parse(raw);
      else for (const line of raw.split(/\r?\n/)) {
        if (!line.startsWith("data:")) continue;
        try { const event = JSON.parse(line.slice(5)); if (event.type === "response.completed") result = event.response; } catch {}
      }
      const metric = {
        started_at: request.timing().startTime, ms: request.timing().responseEnd, status: response.status(),
        model: body.model, effort: body.reasoning?.effort, actual_model: result?.model,
        cache_key_hash: body.prompt_cache_key ? hash(body.prompt_cache_key) : null,
        input_bytes: Buffer.byteLength(request.postData()),
        input_hashes: body.input?.map(hash),
        images: request.postData().match(/data:image\//g)?.length ?? 0,
        compaction_request: body.input?.some((x) => x.type === "compaction_trigger") ?? false,
        output_types: result?.output?.map((x) => x.type),
        input_tokens: result?.usage?.input_tokens, cached_tokens: result?.usage?.input_tokens_details?.cached_tokens,
        output_tokens: result?.usage?.output_tokens,
      };
      requests.push(metric);
    })().finally(() => pending.delete(work));
    pending.add(work);
  });
  const text = taskText ?? "只读取一次外部相机画面和当前关节状态，用一句话报告海绵位置；不执行任何机械臂动作。";
  for (let i = 0; i < Number(roundCount); i++) {
    const firstEntry = await p.locator("[data-entry-order]").count();
    await p.getByLabel("AI 任务", { exact: true }).fill(text);
    await p.getByRole("button", { name: /^(开始会话|追加对话)$/ }).click();
    const dialog = p.getByRole("dialog", { name: "追加到当前会话？" });
    if (await dialog.isVisible()) await dialog.getByRole("button", { name: "确认追加", exact: true }).click();
    await p.getByText("正在处理", { exact: true }).waitFor();
    await p.getByText("正在处理", { exact: true }).waitFor({ state: "hidden", timeout: 600000 });
    await p.waitForTimeout(600);
    const entries = await p.locator("[data-entry-order]").evaluateAll((nodes, first) => nodes.filter((n) => Number(n.dataset.entryOrder) >= first).map((n) => ({
      kind: n.classList.contains("tool-entry") ? "tool" : "text", text: n.querySelector(".entry-text, summary")?.textContent,
    })), firstEntry);
    if (entries.some((e) => e.kind === "tool" && !/^(get_state|observe_camera) · /.test(e.text))) throw Error("Unexpected action in read-only benchmark");
    const whole = await p.evaluate(async () => {
      const open = indexedDB.open("vla-arms-agent", 1);
      const db = await new Promise((resolve, reject) => { open.onsuccess = () => resolve(open.result); open.onerror = () => reject(open.error); });
      try {
        const get = db.transaction("data").objectStore("data").get("session");
        return await new Promise((resolve, reject) => { get.onsuccess = () => resolve(get.result.entries); get.onerror = () => reject(get.error); });
      } finally { db.close(); }
    });
    const start = whole.findLast((e) => e.kind === "user");
    if (!whole.at(-1)?.text.startsWith("本轮已结束")) throw Error(`Task did not complete: ${whole.at(-1)?.text}`);
    rounds.push({ round: i + 1, started_at: start.at, total_ms: whole.at(-1).at - start.at, entries });
    await Promise.all(pending);
    await writeFile(`${output}/report.json`, JSON.stringify({ label, model, effort, client_bundle_hash, native_compaction_threshold, task: text, rounds, requests }, null, 2));
    console.log(JSON.stringify({ label, round: i + 1, ms: rounds.at(-1).total_ms, requests: requests.length }));
  }
  if (requests.some((q) => q.model !== model || q.effort !== effort)) throw Error("Model/effort changed");
  const sum = (field) => requests.reduce((s, q) => s + (q[field] ?? 0), 0);
  console.log(JSON.stringify({ label, completed: true, model, effort, rounds: rounds.length, total_ms: rounds.reduce((s, r) => s + r.total_ms, 0), request_ms: sum("ms"), cache_ratio: sum("cached_tokens") / sum("input_tokens"), compactions: requests.filter((q) => q.compaction_request).length }));
} finally { await b.close(); }
