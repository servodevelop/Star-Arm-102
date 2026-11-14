// Passive profiling of the real browser path. This script sends no model or
// hardware commands. Source: this project's Playwright acceptance workflow.
import { chromium } from "@playwright/test";
import { createHash } from "node:crypto";
import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const label = process.argv[2];
if (!label || !/^[a-z0-9-]+$/.test(label))
  throw Error("Usage: node tests/profile-task.mjs <label>");
const output = resolve("temp/latency-comparison", label);
await mkdir(output, { recursive: true });
const browser = await chromium.connectOverCDP(process.env.CDP_URL ?? "http://127.0.0.1:9227");
const origin = new URL(process.env.ARM_URL ?? "http://localhost:8780").origin;
const page = browser.contexts().flatMap((c) => c.pages()).find((p) => p.url().startsWith(origin + "/"));
if (!page) throw Error("Open the test browser first");
const requests = new Map();
const pending = new Set();
const clientScripts = await page.locator("script[src]").evaluateAll((nodes) => nodes.map((node) => new URL(node.src).pathname));
const hash = (value) => createHash("sha256").update(JSON.stringify(value)).digest("hex");
const cdp = await page.context().newCDPSession(page);
await cdp.send("Network.enable", { maxPostDataSize: 16 * 1024 * 1024 });

function ingest(metric, data, at) {
  metric.buffer += data;
  const lines = metric.buffer.split(/\r?\n/);
  metric.buffer = lines.pop();
  for (const line of lines) {
    if (!line.startsWith("data:")) continue;
    let event;
    try { event = JSON.parse(line.slice(5)); } catch { continue; }
    const elapsed = at - metric.started_at;
    if (event.type === "response.output_text.delta") metric.first_text_ms ??= elapsed;
    if (event.type === "response.function_call_arguments.done") metric.first_arguments_ms ??= elapsed;
    if (event.type === "response.output_item.done" && event.item?.type === "function_call") {
      metric.first_tool_ready_ms ??= elapsed;
      metric.tool_names.push(event.item.name);
    }
    if (event.response?.usage) {
      const usage = event.response.usage;
      metric.usage = {
        input_tokens: usage.input_tokens,
        input_tokens_details: usage.input_tokens_details,
        output_tokens: usage.output_tokens,
        output_tokens_details: usage.output_tokens_details,
        total_tokens: usage.total_tokens,
      };
    }
    if (/^response\.(completed|incomplete|failed)$/.test(event.type ?? "")) {
      metric.terminal_ms = elapsed;
      metric.actual_model = event.response?.model;
      metric.actual_effort = event.response?.reasoning?.effort;
      metric.response_status = event.response?.status;
      metric.service_tier = event.response?.service_tier;
    }
  }
}
function at(metric, timestamp) {
  return metric.started_at + (timestamp - metric.monotonic_start) * 1000;
}
function cleanRequests() {
  return [...requests.values()].map(({ buffer, monotonic_start, ...metric }) => metric);
}
cdp.on("Network.requestWillBeSent", (event) => {
  if (event.request.method !== "POST" || !new URL(event.request.url).pathname.endsWith("/responses")) return;
  let body;
  try { body = JSON.parse(event.request.postData ?? "{}"); } catch { body = {}; }
  const images = [...(event.request.postData ?? "").matchAll(/data:(image\/[^;]+);base64,/g)];
  requests.set(event.requestId, {
    started_at: event.wallTime * 1000,
    monotonic_start: event.timestamp,
    model: body.model,
    effort: body.reasoning?.effort,
    input_bytes: event.request.postData ? Buffer.byteLength(event.request.postData) : null,
    image_count: images.length,
    image_types: [...new Set(images.map((match) => match[1]))],
    compaction_request: body.input?.some((item) => item.type === "compaction_trigger") ?? false,
    cache_key_hash: body.prompt_cache_key ? hash(body.prompt_cache_key) : null,
    input_hashes: Array.isArray(body.input) ? body.input.map(hash) : [],
    instructions_hash: hash(body.instructions ?? body.input?.filter((item) => ["system", "developer"].includes(item.role)) ?? null),
    tools_hash: hash(body.tools ?? null),
    tool_names: [], buffer: "",
  });
});
cdp.on("Network.responseReceived", (event) => {
  const metric = requests.get(event.requestId);
  if (!metric) return;
  metric.status = event.response.status;
  metric.headers_ms = at(metric, event.timestamp) - metric.started_at;
  if (metric.compaction_request) return;
  const streaming = cdp.send("Network.streamResourceContent", { requestId: event.requestId })
    .then(({ bufferedData }) => {
      if (bufferedData) ingest(metric, Buffer.from(bufferedData, "base64").toString(), at(metric, event.timestamp));
    })
    .catch((error) => { metric.stream_timing_error = error.message; })
    .finally(() => pending.delete(streaming));
  pending.add(streaming);
});
cdp.on("Network.dataReceived", (event) => {
  const metric = requests.get(event.requestId);
  if (!metric) return;
  metric.first_data_ms ??= at(metric, event.timestamp) - metric.started_at;
  if (event.data) ingest(metric, Buffer.from(event.data, "base64").toString(), at(metric, event.timestamp));
});
cdp.on("Network.loadingFinished", (event) => {
  const metric = requests.get(event.requestId);
  if (!metric) return;
  metric.total_ms = at(metric, event.timestamp) - metric.started_at;
  if (metric.compaction_request) {
    const read = cdp.send("Network.getResponseBody", { requestId: event.requestId }).then(({ body }) => {
      const response = JSON.parse(body);
      metric.actual_model = response.model;
      metric.actual_effort = response.reasoning?.effort;
      metric.compaction_items = response.output?.filter((item) => item.type === "compaction").length ?? 0;
      if (response.usage) metric.usage = {
        input_tokens: response.usage.input_tokens, input_tokens_details: response.usage.input_tokens_details,
        output_tokens: response.usage.output_tokens, output_tokens_details: response.usage.output_tokens_details,
      };
    }).catch((error) => { metric.stream_timing_error = error.message; }).finally(() => pending.delete(read));
    pending.add(read);
  }
});
cdp.on("Network.loadingFailed", (event) => {
  const metric = requests.get(event.requestId);
  if (metric) {
    metric.total_ms = at(metric, event.timestamp) - metric.started_at;
    metric.error = event.errorText;
  }
});

async function session() {
  return page.evaluate(async () => {
    const open = indexedDB.open("vla-arms-agent", 1);
    const db = await new Promise((resolve, reject) => {
      open.onsuccess = () => resolve(open.result);
      open.onerror = () => reject(open.error);
    });
    try {
      const get = db.transaction("data").objectStore("data").get("session");
      return await new Promise((resolve, reject) => {
        get.onsuccess = () => resolve(get.result);
        get.onerror = () => reject(get.error);
      });
    } finally { db.close(); }
  });
}
async function capture(name) {
  const frames = await page.evaluate(() => [...document.querySelectorAll("video")].map((video) => {
    if (!video.srcObject || video.readyState < 2 || !video.videoWidth) return null;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    return canvas.toDataURL("image/jpeg", .9);
  }));
  await Promise.all(frames.map((frame, index) => frame && writeFile(
    resolve(output, `${name}-${index === 0 ? "external" : "wrist"}.jpg`),
    Buffer.from(frame.split(",")[1], "base64"),
  )));
}

try {
  if (await page.getByText("正在处理", { exact: true }).count()) throw Error("Start the profiler before the task");
  const profilingStartedAt = Date.now();
  const initial = await session();
  let baseline = initial?.entries.length ?? 0;
  const observed = new Map();
  let started = false, image = 0, notified = 0;
  console.log(JSON.stringify({ ready: true, label, output }));
  for (;;) {
    const state = await page.evaluate((baseline) => ({
      active: [...document.querySelectorAll(".badge")].some((node) => node.textContent === "正在处理"),
      entryCount: document.querySelectorAll("[data-entry-order]").length,
      entries: [...document.querySelectorAll("[data-entry-order]")]
        .filter((node) => +node.dataset.entryOrder >= baseline)
        .map((node) => ({ order: +node.dataset.entryOrder, kind: node.classList.contains("tool-entry") ? "tool" : node.classList.contains("user") ? "user" : "text", text: node.querySelector(".entry-text, summary")?.textContent ?? "" })),
    }), baseline);
    if (state.entryCount < baseline) baseline = 0;
    if (state.active || state.entries.some((entry) => entry.kind === "user")) started = true;
    let changed = false;
    for (const entry of state.entries) {
      const previous = observed.get(entry.order);
      if (!previous || previous.text !== entry.text) {
        observed.set(entry.order, { ...entry, observed_at: Date.now() });
        if (entry.kind === "tool" && !entry.text.endsWith(" · 执行中")) changed = true;
      }
    }
    if (started && changed) await capture(`step-${String(++image).padStart(3, "0")}`);
    if (started && Date.now() - notified > 25000) {
      await writeFile(resolve(output, "progress.json"), JSON.stringify({ requests: cleanRequests(), observed_entries: [...observed.values()] }, null, 2));
      console.log(JSON.stringify({ label, requests: requests.size, recent: state.entries.slice(-3) }));
      notified = Date.now();
    }
    if (started && !state.active) break;
    await page.waitForTimeout(250);
  }
  await page.waitForTimeout(500);
  await Promise.all(pending);
  const saved = await session();
  const entries = saved.entries.filter((entry) => entry.at >= profilingStartedAt);
  const start = entries.find((entry) => entry.kind === "user");
  const end = entries.at(-1);
  const tools = entries.filter((entry) => entry.kind === "tool");
  const report = {
    label, started_at: start.at, ended_at: end.at, total_ms: end.at - start.at,
    model: await page.getByLabel("AI 模型", { exact: true }).inputValue(),
    effort: await page.getByLabel("AI 思考强度").inputValue(),
    client_bundle_hash: hash(clientScripts),
    request_count: requests.size,
    requests: cleanRequests(),
    tool_count: tools.length,
    tool_counts: Object.fromEntries([...new Set(tools.map((entry) => entry.text.split(" · ")[0]))]
      .map((name) => [name, tools.filter((entry) => entry.text.startsWith(name + " · ")).length])),
    observed_entries: [...observed.values()], entries,
    physical_success: null,
  };
  await capture("final");
  // Save the exact images delivered to the model, including the wrist image
  // from sequential capture that is no longer visible in the final preview.
  const submitted = [];
  const continued = initial?.entries.every((entry, index) => saved.entries[index]?.id === entry.id);
  for (const message of saved.messages.slice(continued ? initial?.messages.length ?? 0 : 0)) {
    if (message.role !== "tool") continue;
    for (const part of message.content) {
      if (part.type !== "tool-result" || part.output.type !== "content") continue;
      const info = JSON.parse(part.output.value.find((p) => p.type === "text")?.text ?? "{}");
      const metadata = info.observations ?? (info.role ? [info] : []);
      const images = part.output.value.filter((p) => p.type === "file");
      for (const [i, image] of images.entries()) {
        if (image.data.type !== "data") continue;
        const role = metadata[i]?.role ?? "unknown";
        const extension = image.mediaType === "image/webp" ? "webp" : image.mediaType === "image/png" ? "png" : "jpg";
        const filename = `submitted-${String(submitted.length + 1).padStart(3, "0")}-${role}.${extension}`;
        const bytes = Buffer.from(image.data.data, "base64");
        await writeFile(resolve(output, filename), bytes);
        const check = await page.evaluate(async ({ mediaType, data }) => {
          try {
            const image = await createImageBitmap(await (await fetch(`data:${mediaType};base64,${data}`)).blob());
            const canvas = document.createElement("canvas"); canvas.width = image.width; canvas.height = image.height;
            const ctx = canvas.getContext("2d"); ctx.drawImage(image, 0, 0); image.close();
            const rgba = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
            let min = 255, max = 0, sum = 0;
            for (let k = 0; k < rgba.length; k += 4) {
              const y = (rgba[k] + rgba[k + 1] + rgba[k + 2]) / 3;
              min = Math.min(min, y); max = Math.max(max, y); sum += y;
            }
            return { width: canvas.width, height: canvas.height, min, max, mean: sum / (canvas.width * canvas.height), all_black: max === 0 };
          } catch (error) { return { decode_error: error.message }; }
        }, { mediaType: image.mediaType, data: image.data.data });
        submitted.push({ filename, role, metadata: metadata[i], bytes: bytes.length, tool: part.toolName, call_id: part.toolCallId, check });
      }
    }
  }
  report.submitted_frames = submitted;
  report.submitted_image_checks_passed = submitted.length > 0 && submitted.every((f) => !f.check.decode_error && !f.check.all_black && f.check.width === f.metadata?.width && f.check.height === f.metadata?.height);
  await writeFile(resolve(output, "report.json"), JSON.stringify(report, null, 2));
  console.log(JSON.stringify({ completed: true, label, total_ms: report.total_ms, requests: requests.size, tools: tools.length, requires_image_review: true }));
} finally {
  await cdp.detach();
  await browser.close();
}
