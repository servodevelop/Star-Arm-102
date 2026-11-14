// Observe a task started through the real page. No model or device commands.
// Physical success is reviewed from the saved images, separately from AI text.
import { chromium } from "@playwright/test";
import { mkdirSync, readFileSync, writeFileSync, existsSync, readdirSync } from "node:fs";
import { resolve } from "node:path";

if (process.argv[2] === "summary") {
  const root = resolve("temp/five-rounds");
  const reports = readdirSync(root).filter((f) => /^round-\d+$/.test(f))
    .sort((a, b) => Number(a.split("-")[1]) - Number(b.split("-")[1]))
    .map((dir) => JSON.parse(readFileSync(resolve(root, dir, "report.json"), "utf8")));
  if (reports.some((r) => r.physical_success == null || !r.pick_places?.length))
    throw Error("Review placements from images and fill their confirmation timestamps first");
  for (const r of reports) {
    const total = r.pick_places.reduce((sum, p) => sum + p.elapsed_ms, r.return_to_work_ms);
    if (total !== r.total_ms) throw Error(`Round ${r.round}: phase times do not add up`);
  }
  const seconds = (ms) => (ms / 1000).toFixed(1);
  const grabs = reports.flatMap((r) => r.pick_places);
  const passed = reports.filter((r) => r.physical_success).length;
  const retries = reports.reduce((sum, r) => sum + r.grasp_retries, 0);
  const attempts = reports.reduce((sum, r) => sum + r.grasp_attempts, 0);
  const total = reports.reduce((sum, r) => sum + r.total_ms, 0);
  const modelTime = reports.reduce((sum, r) => sum + r.model_request_ms, 0);
  const mean = (values) => values.reduce((sum, v) => sum + v, 0) / values.length;
  const table = reports.flatMap((r) => r.pick_places.map((p, index) => `| ${r.round} | ${index + 1} | ${p.destination} | ${seconds(p.elapsed_ms)} | ${p.note ?? "完成"} |`)).join("\n");
  const roundTable = reports.map((r) => `| ${r.round} | ${seconds(r.return_to_work_ms)} | ${seconds(r.total_ms)} | ${r.physical_success ? "完成" : "失败"} |`).join("\n");
  const report = `# 真实网页抓放测试报告\n\n← [vla-arms-agent](../README.zh.md) · <sub>[English](GRASP_TEST_REPORT.md) / **简体中文**</sub>\n\n测试日期：${new Date(reports[0].started_at).toLocaleDateString("sv-SE", { timeZone: "Asia/Shanghai" })}。\n\n` +
    `## 结果\n\n本次 ${reports.length} 轮任务完成 ${passed} 轮，共 ${grabs.length} 次完成抓放（含追加纠偏）。整轮完成率 ${(100 * passed / reports.length).toFixed(0)}%。实际夹取尝试 ${attempts} 次，其中 ${grabs.length} 次完成搬运（${(100 * grabs.length / attempts).toFixed(1)}%），${retries} 次滑脱后由 AI 自主重抓恢复；已排除回工作位的闭爪指令。未人工移动物体或代替执行动作。成功按抓住、搬运并释放至目标区域核对，放置精度不作为验收条件。\n\n` +
    `## 单次抓放耗时\n\n单位：秒。到中心框、到红框分别记录；追加纠偏抓放单独列出，未将整轮时间平分。\n\n| 轮次 | 本轮第几次 | 目标 | 耗时 | 结果与备注 |\n| --- | ---: | --- | ---: | --- |\n${table}\n\n` +
    `| 轮次 | 回工作位并闭爪累计 | 整轮合计 | 最终结果 |\n| --- | ---: | ---: | --- |\n${roundTable}\n\n` +
    `第一次平均 ${seconds(mean(reports.map((r) => r.pick_places[0].elapsed_ms)))} 秒，第二次平均 ${seconds(mean(reports.map((r) => r.pick_places[1].elapsed_ms)))} 秒。全部单次抓放平均 ${seconds(mean(grabs.map((p) => p.elapsed_ms)))} 秒，范围 ${seconds(Math.min(...grabs.map((p) => p.elapsed_ms)))}～${seconds(Math.max(...grabs.map((p) => p.elapsed_ms)))} 秒。\n\n` +
    `## 计时与条件\n\n第一次从网页发送任务开始，至中心框放置确认；第二次从该确认开始，至红框放置确认。取图、模型判断、姿态调整、执行、释放和结果确认均计入对应抓放，回工作位单列。追加纠偏从重新开始抓取的决策开始，至本次放置确认，包含过程中的重抓耗时。边界使用网页会话时间戳，并核对对应过程画面。两轮之间的人工审查等待不计入执行耗时。\n\n` +
    `使用同一真实网页、同一会话，Star Arm 102-FL 从臂，外部与腕部相机均绑定 1280×720、30 FPS，按需切换采集。模型 ${[...new Set(reports.map((r) => r.model))].join("、")}，思考强度 ${[...new Set(reports.map((r) => r.effort))].join("、")}。\n\n` +
    reports.filter((r) => r.prompt_note).map((r) => `- 第 ${r.round} 轮提示词：${r.prompt_note}。\n`).join("") + "\n" +
    `整轮执行累计 ${seconds(total)} 秒，模型请求累计 ${seconds(modelTime)} 秒，占 ${(100 * modelTime / total).toFixed(1)}%；其余包含相机、串口动作、运动等待与前端处理。\n\n` +
    `原始时间戳、实际反馈、工具结果和图像保存在 \`temp/five-rounds/round-*/\`。记录与汇总脚本为 [task-report.mjs](../tests/task-report.mjs)，使用方法见 [测试说明](../tests/README.zh.md)。\n`;
  const target = resolve("docs/GRASP_TEST_REPORT.zh.md");
  writeFileSync(target, report);
  console.log(JSON.stringify({ report: target, rounds: reports.length, passed, pick_places: grabs.length, retries, average_pick_place_ms: mean(grabs.map((p) => p.elapsed_ms)) }));
  process.exit(0);
}

const round = Number(process.argv[2]);
if (!Number.isInteger(round) || round < 1) throw Error("Usage: node tests/task-report.mjs <round>");
const output = resolve(`temp/five-rounds/round-${round}`);
mkdirSync(output, { recursive: true });
const browser = await chromium.connectOverCDP(process.env.CDP_URL ?? "http://127.0.0.1:9227");
const origin = new URL(process.env.ARM_URL ?? "http://localhost:8780").origin;
const page = browser.contexts().flatMap((c) => c.pages()).find((p) => p.url().startsWith(origin + "/"));
if (!page) throw Error("Open the deployed page with tests/live-control.mjs first");

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
async function capture(label) {
  const frames = await page.evaluate(() => [...document.querySelectorAll("video")].map((v) => {
    if (!v.videoWidth || v.readyState < 2 || !v.srcObject) return null;
    const canvas = document.createElement("canvas");
    canvas.width = v.videoWidth;
    canvas.height = v.videoHeight;
    canvas.getContext("2d").drawImage(v, 0, 0);
    return canvas.toDataURL("image/jpeg", .9);
  }));
  frames.forEach((frame, i) => {
    if (frame) writeFileSync(resolve(output, `${label}-${i === 0 ? "external" : "wrist"}.jpg`), Buffer.from(frame.split(",")[1], "base64"));
  });
}

try {
  const initial = await session();
  const start = initial.entries.findLast((e) => e.kind === "user");
  if (!start) throw Error("Start a task through the page first");
  const progressFile = resolve(output, "progress.json");
  const events = existsSync(progressFile) ? JSON.parse(readFileSync(progressFile, "utf8")) : [];
  let previous = "";
  let notified = 0;
  let image = readdirSync(output).filter((f) => f.endsWith(".jpg")).length;
  console.log(JSON.stringify({ round, started_at: start.at, task: start.text, output }));
  for (;;) {
    const state = await page.evaluate((text) => {
      const nodes = [...document.querySelectorAll(".ai-card [data-entry-order]")]
        .sort((a, b) => Number(a.dataset.entryOrder) - Number(b.dataset.entryOrder));
      const from = nodes.findLastIndex((n) => n.classList.contains("user") && n.querySelector(".entry-text")?.textContent === text);
      const entries = nodes.slice(from).map((n) => n.querySelector(".entry-text, summary")?.textContent ?? "");
      return { active: [...document.querySelectorAll(".badge")].some((n) => n.textContent === "正在处理"), entries };
    }, start.text);
    const marker = JSON.stringify(state.entries);
    if (marker !== previous) {
      previous = marker;
      events.push({ at: Date.now(), entries: state.entries });
      const latest = state.entries.at(-1) ?? "";
      if (latest.endsWith(" · 已完成") || !state.active) {
        await capture(`step-${String(++image).padStart(3, "0")}`);
      }
      writeFileSync(resolve(output, "progress.json"), JSON.stringify(events, null, 2));
    }
    if (Date.now() - notified >= 30_000) {
      console.log(JSON.stringify({ round, elapsed_s: Math.round((Date.now() - start.at) / 1000), recent: state.entries.slice(-3) }));
      notified = Date.now();
    }
    if (!state.active) break;
    await page.waitForTimeout(1000);
  }
  await page.waitForTimeout(300);
  const saved = await session();
  const entries = saved.entries.slice(saved.entries.findIndex((e) => e.id === start.id));
  const tools = entries.filter((e) => e.kind === "tool");
  const networkFile = resolve("temp/live/network.json");
  const network = existsSync(networkFile) ? JSON.parse(readFileSync(networkFile, "utf8")).filter((r) => r.started_at >= start.at && r.started_at <= entries.at(-1).at) : [];
  const report = {
    round, task: start.text, started_at: start.at, ended_at: entries.at(-1).at,
    total_ms: entries.at(-1).at - start.at,
    model: await page.getByLabel("AI 模型", { exact: true }).inputValue(),
    effort: await page.getByLabel("AI 思考强度").inputValue(),
    tool_calls: tools.length,
    tool_counts: Object.fromEntries([...new Set(tools.map((e) => e.text.split(" · ")[0]))].map((name) => [name, tools.filter((e) => e.text.startsWith(name + " · ")).length])),
    tool_failures: tools.filter((e) => !e.text.endsWith(" · 已完成")).map((e) => ({ text: e.text, detail: e.detail })),
    model_requests: network.length,
    model_request_ms: network.reduce((sum, r) => sum + r.ms, 0),
    system_hashes: [...new Set(network.map((r) => r.system_sha256))],
    final_reply: entries.findLast((e) => e.kind === "assistant")?.text,
    statuses: entries.filter((e) => e.kind === "status").map((e) => e.text),
    actual_joints: await page.locator(".joint-readings").innerText(),
    feedback: await page.locator(".stats").innerText(),
    physical_success: null,
  };
  await capture("final");
  writeFileSync(resolve(output, "entries.json"), JSON.stringify(entries, null, 2));
  writeFileSync(resolve(output, "report.json"), JSON.stringify(report, null, 2));
  console.log(JSON.stringify({ completed: true, round, total_ms: report.total_ms, tool_calls: report.tool_calls, final_reply: report.final_reply, requires_image_review: true, output }));
} finally { await browser.close(); }
