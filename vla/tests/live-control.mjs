// Real hardware acceptance through the deployed page. No mocks or API writes.
// Run from Star-Arm-102/vla; commands arrive as JSON lines on stdin. Credentials
// are read from an authorized existing configuration only to fill the actual form.
import { chromium } from "@playwright/test";
import { createHash } from "node:crypto";
import { readFileSync, existsSync, mkdirSync, writeFileSync } from "node:fs";
import { createInterface } from "node:readline";
import { resolve } from "node:path";

const output = resolve("temp/live");
mkdirSync(output, { recursive: true });
const context = await chromium.launchPersistentContext(
  resolve("temp/live-profile"),
  {
    headless: process.env.HEADED !== "1",
    executablePath: process.env.CHROMIUM_PATH,
    viewport: { width: 1600, height: 1100 },
    locale: "zh-CN",
    permissions: ["camera"],
    args: [
      "--no-sandbox",
      "--use-fake-ui-for-media-stream",
      "--disable-features=Translate",
      "--remote-debugging-port=9227",
      "--remote-debugging-address=127.0.0.1",
    ],
  },
);
const page = await context.newPage();
const requests = [];
page.on("requestfinished", async (request) => {
  if (
    request.method() !== "POST" ||
    !new URL(request.url()).pathname.endsWith("/responses")
  )
    return;
  const timing = request.timing();
  const response = await request.response();
  const body = request.postDataJSON();
  const system =
    body.instructions ??
    (Array.isArray(body.input)
      ? body.input.filter((m) => m.role === "system" || m.role === "developer")
      : []);
  const metric = {
    started_at: timing.startTime,
    ms: Math.round(timing.responseEnd),
    status: response?.status(),
    system_sha256: createHash("sha256")
      .update(JSON.stringify(system))
      .digest("hex"),
  };
  requests.push(metric);
  writeFileSync(
    resolve(output, "network.json"),
    JSON.stringify(requests, null, 2),
  );
  console.log(JSON.stringify({ ai_request: requests.length, ...metric }));
});
page.on("pageerror", (e) =>
  console.log(JSON.stringify({ page_error: e.message })),
);
const cdp = await context.newCDPSession(page);
await cdp.send("DeviceAccess.enable");
cdp.on("DeviceAccess.deviceRequestPrompted", async (e) => {
  console.log(JSON.stringify({ serial_choices: e.devices }));
  if (e.devices.length === 1)
    await cdp.send("DeviceAccess.selectPrompt", {
      id: e.id,
      deviceId: e.devices[0].id,
    });
});
await page.goto(process.env.ARM_URL ?? "http://localhost:8780");
await page.getByRole("combobox", { name: "Language / 语言" }).selectOption("zh");
await page.getByRole("button", { name: "配置已保存" }).waitFor();
console.log(JSON.stringify({ ready: true }));
async function open(title) {
  const summary = page.getByText(title, { exact: true });
  if (await summary.evaluate((el) => !el.parentElement.open))
    await summary.click();
}
async function status() {
  return {
    badges: await page.locator(".badge").allTextContents(),
    cameras: await page.locator(".camera-status").allTextContents(),
    joints: await page.locator(".joint-readings").innerText(),
    tcp: await page.locator(".tcp-line").innerText(),
    feedback: await page.locator(".stats").innerText(),
    errors: await page.locator("[role=alert]").allTextContents(),
    entries: (
      await page
        .locator(".ai-card [data-entry-order]")
        .evaluateAll((nodes) => nodes
          .sort((a, b) => Number(a.dataset.entryOrder) - Number(b.dataset.entryOrder))
          .map((node) => node.querySelector(".entry-text, summary")?.textContent ?? ""))
    ).slice(-12),
  };
}
for await (const line of createInterface({ input: process.stdin })) {
  let input;
  try {
    input = JSON.parse(line);
    if (input.action === "connect") {
      await page.bringToFront();
      await page.getByRole("button", { name: "选择串口并连接" }).click();
      await page
        .getByRole("button", { name: "断开从臂" })
        .waitFor({ timeout: 120000 });
      await page.getByText("实际舵机反馈", { exact: true }).click();
    } else if (input.action === "cameras") {
      if (
        (await page
          .getByLabel("外部相机设备", { exact: true })
          .locator("option")
          .count()) < 3
      )
        await page.getByRole("button", { name: "授权并刷新摄像头" }).click();
      await page.waitForFunction(
        () =>
          document.querySelector('[aria-label="外部相机设备"]').options
            .length >= 3,
      );
      const choices = await page
        .getByLabel("外部相机设备", { exact: true })
        .locator("option")
        .evaluateAll((options) =>
          options.map((o) => ({ label: o.textContent, value: o.value })),
        );
      console.log(JSON.stringify({ camera_choices: choices }));
      const indices = input.indices ?? [1, 2];
      for (const [i, role] of ["外部相机", "腕部相机"].entries()) {
        await page
          .getByLabel(role + "设备", { exact: true })
          .selectOption(choices[indices[i]].value);
        if (input.resolution)
          await page
            .getByLabel(role + "分辨率", { exact: true })
            .selectOption(input.resolution);
        if (input.only !== undefined && input.only !== i) continue;
        const card = page.locator(".camera-card").nth(i);
        await card
          .getByRole("button", { name: "开启预览", exact: true })
          .click();
        await page.waitForFunction(
          (i) => document.querySelectorAll("video")[i].videoWidth > 0,
          i,
          { timeout: 30000 },
        );
      }
      if (await page.getByRole("button", { name: "保存配置" }).count())
        await page.getByRole("button", { name: "保存配置" }).click();
    } else if (input.action === "configure") {
      const envFile = resolve("../.env");
      const raw = existsSync(envFile) ? readFileSync(envFile, "utf8") : "";
      const env = (name) =>
        raw
          .match(new RegExp("^" + name + "=(.*)$", "m"))?.[1]
          ?.trim()
          .replace(/^['"]|['"]$/g, "") ?? "";
      await open("模型与动作配置");
      await page
        .getByLabel("AI API 地址")
        .fill(
          input.baseURL ||
            env("AI_API_BASE_URL") ||
            (await page.getByLabel("AI API 地址").inputValue()),
        );
      await page
        .getByLabel("AI 模型", { exact: true })
        .fill(
          input.model ||
            env("AI_MODEL") ||
            (await page.getByLabel("AI 模型", { exact: true }).inputValue()),
        );
      const proxyConfig = process.env.AI_CONFIG_FILE;
      const apiKey =
        process.env.AI_API_KEY ||
        (proxyConfig
          ? JSON.parse(
              readFileSync(proxyConfig, "utf8").match(
                /api-keys:\s*(\[[^\n]+\])/,
              )?.[1] ?? "[]",
            )[0]
          : env("AI_API_KEY"));
      if (!apiKey) throw Error("No configured API key found");
      await page.getByLabel("AI API Key").fill(apiKey);
      if (input.effort !== undefined)
        await page.getByLabel("AI 思考强度").fill(input.effort);
      if (await page.getByRole("button", { name: "保存配置" }).count())
        await page.getByRole("button", { name: "保存配置" }).click();
      if (input.check)
        await page.getByRole("button", { name: "验证连接与能力" }).click();
    } else if (input.action === "task") {
      await page.getByLabel("AI 任务", { exact: true }).fill(input.text);
      await page
        .getByRole("button", { name: /^(开始会话|追加对话)$/ })
        .click();
      const confirmation = page.getByRole("dialog", { name: "追加到当前会话？" });
      if (await confirmation.isVisible())
        await confirmation.getByRole("button", { name: "确认追加" }).click();
    } else if (input.action === "manual") {
      await open("关节目标与夹爪");
      await page.getByRole("button", { name: "使用实际角度" }).click();
      for (const [joint, angle] of Object.entries(input.joints ?? {}))
        await page
          .getByLabel(`J${joint} 目标角度`, { exact: true })
          .fill(String(angle));
      await page.getByRole("button", { name: "预览目标", exact: true }).click();
      if (input.execute)
        await page.getByRole("button", { name: "执行关节目标" }).click();
    } else if (input.action === "stop")
      await page.getByRole("button", { name: "停止 AI 与运动" }).click();
    else if (input.action === "work") {
      await open("关节目标与夹爪");
      await page.getByRole("button", { name: "回工作位", exact: true }).click();
    } else if (input.action === "screenshot") {
      await page.screenshot({
        path: resolve(output, "page.png"),
        fullPage: true,
      });
      for (const [i, role] of ["external", "wrist"].entries())
        await page
          .locator("video")
          .nth(i)
          .screenshot({ path: resolve(output, `${role}.png`) });
    } else if (input.action === "close") break;
    const current = await status();
    writeFileSync(
      resolve(output, "state.json"),
      JSON.stringify(current, null, 2),
    );
    console.log(JSON.stringify({ action: input.action, ...current }));
  } catch (e) {
    console.log(JSON.stringify({ action: input?.action, error: e.message }));
  }
}
await context.close();
process.exit(0);
