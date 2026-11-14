import { test, expect } from "@playwright/test";

test("English default, Chinese switch, persistence, errors and responsive layout", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  const language = page.getByRole("combobox", { name: "Language / 语言" });
  await expect(
    page.getByRole("heading", { name: "See, decide, act." }),
  ).toBeVisible();
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(
    page.getByRole("button", { name: "Configuration saved", exact: true }),
  ).toBeEnabled();
  for (const locale of ["zh", "en"] as const) {
    await language.selectOption(locale);
    await expect(page.locator("html")).toHaveAttribute(
      "lang",
      locale === "zh" ? "zh-CN" : "en",
    );
    const summary =
      locale === "zh" ? "关节目标与夹爪" : "Joint targets and gripper";
    await page.getByText(summary, { exact: true }).click();
    await page
      .getByLabel(locale === "zh" ? "J2 目标角度" : "J2 target angle")
      .fill("-1000");
    await page
      .getByRole("button", {
        name: locale === "zh" ? "预览目标" : "Preview target",
        exact: true,
      })
      .click();
    await expect(page.locator("[data-sonner-toast]").last()).toContainText(
      locale === "zh" ? "超出原模型范围" : "outside the original model range",
    );
    for (const width of [1440, 390]) {
      await page.setViewportSize({ width, height: 1080 });
      await expect
        .poll(() =>
          page.evaluate(
            () => document.documentElement.scrollWidth <= innerWidth,
          ),
        )
        .toBe(true);
    }
    await page.setViewportSize({ width: 1440, height: 1080 });
    await page.getByText(summary, { exact: true }).click();
    await page.reload();
    await expect(language).toHaveValue(locale);
    await expect(page.locator("title")).toHaveCount(1);
    await expect(page).toHaveTitle(
      locale === "zh"
        ? "vla-arms-agent · AI 机械臂"
        : "vla-arms-agent · AI robot arm",
    );
  }
  await page.getByText("Model and motion settings", { exact: true }).click();
  await expect(page.getByLabel("AI model", { exact: true })).toBeVisible();
  await expect(
    page.getByLabel("AI reasoning effort", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Save AI settings" }),
  ).toBeVisible();
  expect(errors).toEqual([]);
});

test("switching language translates restored tool state but preserves user and assistant prose", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("button", { name: "Configuration saved", exact: true }),
  ).toBeEnabled();
  await page.evaluate(async () => {
    const db = await new Promise<IDBDatabase>((resolve, reject) => {
      const request = indexedDB.open("vla-arms-agent", 1);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
    await new Promise<void>((resolve, reject) => {
      const transaction = db.transaction("data", "readwrite");
      transaction.objectStore("data").put(
        {
          messages: [],
          active: true,
          pending: [],
          entries: [
            { id: "1", kind: "user", text: "请保留这句中文", at: 1 },
            { id: "2", kind: "assistant", text: "Original model reply", at: 2 },
            { id: "3", kind: "tool", text: "gripper · Running", at: 3 },
          ],
        },
        "session",
      );
      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error);
    });
    db.close();
  });
  await page.reload();
  await expect(
    page.getByText("gripper · Interrupted; check state", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Language / 语言" })
    .selectOption("zh");
  await expect(
    page.getByText("gripper · 已中断，待核对", { exact: true }),
  ).toBeVisible();
  await expect(page.getByText("请保留这句中文", { exact: true })).toBeVisible();
  await expect(
    page.getByText("Original model reply", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("上轮任务已中断；重新连接设备后可在当前会话继续", {
      exact: true,
    }),
  ).toBeVisible();
});
