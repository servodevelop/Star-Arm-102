import { test, expect } from "@playwright/test";

test("独立部署页：配置编辑、保存、刷新、预览不运动和窄屏布局", async ({
  page,
}) => {
  const exceptions: string[] = [];
  page.on("pageerror", (e) => exceptions.push(e.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "看见，判断，行动。" }),
  ).toBeVisible();
  await expect(page).toHaveTitle("vla-arms-agent · AI 机械臂");
  await expect(page.getByRole("button", { name: "配置已保存" })).toBeVisible();
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 1080 });
    expect(await page.locator(".ai-card").evaluate((card) => {
      const input = card.querySelector("textarea")!.getBoundingClientRect();
      return [".settings", ".task-intro", "#task-hint"].every((selector) =>
        card.querySelector(selector)!.getBoundingClientRect().bottom <= input.top,
      );
    })).toBe(true);
  }
  await page.setViewportSize({ width: 1440, height: 1080 });
  await page.getByLabel("默认动作时长").fill("1234");
  await page.getByRole("button", { name: "连接与观察", exact: true }).click();
  await expect(page.locator("#device-panel")).toBeHidden();
  await page.getByText("模型与动作配置", { exact: true }).click();
  await page.getByLabel("AI API 地址").fill("http://localhost:8317/v1");
  await page.getByLabel("AI 模型", { exact: true }).fill("test-model");
  await page.getByLabel("AI 思考强度").fill("high");
  await page.getByLabel("夹爪功率上限").fill("500");
  await expect(page.getByLabel("原生上下文压缩阈值", { exact: true })).toHaveValue("262144");
  await page.getByLabel("原生上下文压缩阈值", { exact: true }).fill("24576");
  await page.getByLabel("AI API Key").fill("not-a-real-secret");
  await page.getByRole("button", { name: "保存 AI 配置", exact: true }).click();
  await expect(page.getByRole("button", { name: "保存 AI 配置", exact: true })).toBeDisabled();
  await page.reload();
  await page.getByText("模型与动作配置", { exact: true }).click();
  await expect(page.getByLabel("AI 模型", { exact: true })).toHaveValue(
    "test-model",
  );
  await expect(page.getByLabel("AI API 地址")).toHaveValue("http://localhost:8317/v1");
  await expect(page.getByLabel("默认动作时长")).toHaveValue("1234");
  await expect(page.getByLabel("AI 思考强度")).toHaveValue("high");
  await expect(page.getByLabel("夹爪功率上限")).toHaveValue("500");
  await expect(page.getByLabel("AI API Key")).toHaveValue("not-a-real-secret");
  await expect(page.getByLabel("原生上下文压缩阈值", { exact: true })).toHaveValue("24576");
  await expect(page.getByLabel("AI API Key")).toHaveAttribute("type", "password");
  await page.getByLabel("AI API Key").fill("");
  await page.getByRole("button", { name: "保存 AI 配置", exact: true }).click();
  await page.reload();
  await page.getByText("模型与动作配置", { exact: true }).click();
  await expect(page.getByLabel("AI API Key")).toHaveValue("");
  await page.getByText("关节目标与夹爪", { exact: true }).click();
  await page.getByRole("button", { name: "预览目标", exact: true }).click();
  await expect(
    page.getByRole("img", { name: "实际机械臂与目标的运动学预览" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "执行关节目标" }),
  ).toBeDisabled();
  await page.locator("details").evaluateAll((panels) => panels.forEach((p) => { (p as HTMLDetailsElement).open = true; }));
  for (const width of [1920, 1440, 1024, 768, 390, 320]) {
    await page.setViewportSize({ width, height: 1000 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
  }
  expect(exceptions).toEqual([]);
});

for (const legacyName of ["vlm-arms-agent", "browser-arm"]) {
  test(`改名保留 ${legacyName} 配置和会话，已有新名称设置优先`, async ({ page }) => {
    await page.route("**/migration-seed", (route) => route.fulfill({ contentType: "text/html", body: "<title>seed</title>" }));
    await page.goto("/migration-seed");
    await page.evaluate(async (name) => {
      const request = indexedDB.open(name, 1);
      request.onupgradeneeded = () => request.result.createObjectStore("data");
      const db = await new Promise<IDBDatabase>((resolve, reject) => {
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
      });
      const camera = { deviceId: "", label: "", width: 1280, height: 720, fps: 30 };
      await new Promise<void>((resolve, reject) => {
        const tx = db.transaction("data", "readwrite");
        tx.objectStore("data").put({
          ai: { baseURL: "http://localhost:8317/v1", model: "legacy-model", effort: "medium", durationMs: 2000, gripperPowerMw: 0 },
          cameras: { external: camera, wrist: camera },
          mapping: { directions: [1, 1, 1, -1, 1, 1], offsets: [0, 0, 0, 0, 0, 0] },
          baudRate: 1000000,
        }, "config");
        tx.objectStore("data").put({
          messages: [{ role: "user", content: "历史任务" }],
          entries: [{ id: "legacy", kind: "user", text: "历史任务", at: 1 }],
        }, "session");
        tx.oncomplete = () => resolve();
        tx.onerror = () => reject(tx.error);
      });
      db.close();
    }, legacyName);
    await page.goto("/");
    await expect(page.getByRole("button", { name: "配置已保存" })).toBeVisible();
    await expect(page.getByText("历史任务", { exact: true })).toBeVisible();
    await page.getByText("模型与动作配置", { exact: true }).click();
    await expect(page.getByLabel("AI 模型", { exact: true })).toHaveValue("legacy-model");
    await expect(page.getByLabel("AI API Key")).toHaveValue("");
    await expect(page.getByLabel("外部相机分辨率")).toHaveValue("1280x720");
    await page.getByLabel("AI 模型", { exact: true }).fill("renamed-model");
    await page.getByRole("button", { name: "保存配置" }).click();
    await page.reload();
    await page.getByText("模型与动作配置", { exact: true }).click();
    await expect(page.getByLabel("AI 模型", { exact: true })).toHaveValue("renamed-model");
    await expect(page.getByText("历史任务", { exact: true })).toBeVisible();
  });
}

test("刷新后标记未结束任务，保留补充并恢复可发送状态", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("button", { name: "配置已保存" })).toBeVisible();
  await page.evaluate(async () => {
    const request = indexedDB.open("vla-arms-agent", 1);
    const db = await new Promise<IDBDatabase>((resolve, reject) => {
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
    await new Promise<void>((resolve, reject) => {
      const transaction = db.transaction("data", "readwrite");
      transaction.objectStore("data").put({
        messages: [], active: true, pending: ["继续前检查物体是否仍夹住"],
        entries: [
          { id: "interrupted", kind: "tool", text: "gripper · 执行中", at: 1000 },
          { id: "later", kind: "tool", text: "move_tcp · 已完成", at: 3000 },
          { id: "middle", kind: "assistant", text: "正在检查夹取位置\n".repeat(40), at: 2000 },
        ],
      }, "session");
      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error);
    });
    db.close();
  });
  await page.reload();
  await expect(page.locator(".conversation").getByText("gripper · 已中断，待核对", { exact: true })).toBeVisible();
  expect(await page.locator(".ai-card").evaluate((card) =>
    Boolean(card.firstElementChild?.classList.contains("settings")),
  )).toBe(true);
  expect(await page.locator(".conversation [data-entry-order]").evaluateAll((nodes) =>
    nodes.map((node) => node.getAttribute("data-entry-order")),
  )).toEqual(["0", "2", "1", "3"]);
  const flow = page.locator(".conversation");
  await expect.poll(() => flow.evaluate((node) =>
    Math.ceil(node.scrollTop + node.clientHeight) >= node.scrollHeight,
  )).toBe(true);
  await page.locator(".control-card > details").evaluateAll((panels) =>
    panels.forEach((panel) => { (panel as HTMLDetailsElement).open = true; }),
  );
  await flow.scrollIntoViewIfNeeded();
  await flow.hover();
  await page.mouse.wheel(0, 20000);
  await page.mouse.move(5, 5);
  await page.mouse.wheel(0, -250);
  await expect.poll(() => page.evaluate(() =>
    scrollY < document.documentElement.scrollHeight - innerHeight,
  )).toBe(true);
  const before = await page.evaluate(() => scrollY);
  const bounds = await flow.boundingBox();
  expect(bounds).not.toBeNull();
  await page.mouse.move(bounds!.x + bounds!.width / 2, Math.min(1000, bounds!.y + bounds!.height / 2));
  await page.mouse.wheel(0, 250);
  await expect.poll(() => page.evaluate(() => scrollY)).toBeGreaterThan(before);
  await expect(page.getByText("上轮任务已中断；重新连接设备后可在当前会话继续")).toBeVisible();
  await expect(page.getByText("等待任务", { exact: true })).toBeVisible();
  await page.getByLabel("AI 任务", { exact: true }).fill("继续");
  const append = page.getByRole("button", { name: "追加对话", exact: true });
  await expect(append).toBeEnabled();
  await append.click();
  const confirmation = page.getByRole("dialog", { name: "追加到当前会话？" });
  await expect(confirmation).toBeVisible();
  await expect(confirmation).toContainText("新任务建议先开启新会话");
  await confirmation.getByRole("button", { name: "取消", exact: true }).click();
  await expect(page.getByLabel("AI 任务", { exact: true })).toHaveValue("继续");
  await page.getByLabel("AI 任务", { exact: true }).press("Control+Enter");
  await expect(confirmation).toBeVisible();
  await confirmation.getByRole("button", { name: "确认追加" }).click();
  await expect(confirmation).not.toBeVisible();
  await expect(page.getByText("请填写模型地址、模型 ID 和 API Key", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "新会话", exact: true }).click();
  await expect(page.getByRole("button", { name: "开始会话", exact: true })).toBeEnabled();
  await expect(page.locator(".conversation")).toHaveCount(0);
  await expect(page.getByText("用一句话定义任务", { exact: true })).toBeVisible();
});

test("模型能力验证可从页面停止，不持续卡在正在验证", async ({ page }) => {
  await page.route("**/v1/responses", () => new Promise(() => { }));
  await page.goto("/");
  await page.getByText("模型与动作配置", { exact: true }).click();
  await page.getByLabel("AI API 地址").fill("http://localhost:8317/v1");
  await page.getByLabel("AI API Key").fill("test-only");
  await page.getByRole("button", { name: "验证连接与能力" }).click();
  await expect(page.getByRole("button", { name: "正在验证…" })).toBeVisible();
  await page.getByRole("button", { name: "停止 AI 与运动" }).click();
  await expect(page.getByRole("button", { name: "验证连接与能力" })).toBeEnabled();
  await expect(page.getByText("请求已停止", { exact: true })).toBeVisible();
});
