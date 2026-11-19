import { test, expect } from "@playwright/test";
import { streamResponse } from "./service-tier-fixture";

test("save a service tier through the UI, apply it to validation and tasks, and show actual server feedback", async ({
  page,
}) => {
  const requests: {
    service_tier: string;
    reasoning: { effort: string };
    prompt_cache_key?: string;
  }[] = [];
  await page.route("https://model.invalid/v1/responses", async (route) => {
    if (route.request().method() === "OPTIONS") {
      await route.fulfill({
        status: 204,
        headers: {
          "access-control-allow-origin": "*",
          "access-control-allow-headers": "authorization,content-type",
        },
      });
      return;
    }
    const body = route.request().postDataJSON();
    requests.push({
      service_tier: body.service_tier,
      reasoning: body.reasoning,
      prompt_cache_key: body.prompt_cache_key,
    });
    const index = requests.length;
    const response = streamResponse(
      index,
      index <= 2 ? "priority" : "default",
      index === 1 ? "describe_input" : undefined,
    );
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      headers: { "access-control-allow-origin": "*" },
      body: await response.text(),
    });
  });
  await page.goto("/");
  await page.getByText("Model and motion settings", { exact: true }).click();
  const tier = page.getByLabel("AI service tier", { exact: true });
  await expect(tier).toHaveValue("auto");
  expect(
    await tier.locator("option").evaluateAll((ns) => ns.map((n) => (n as HTMLOptionElement).value)),
  ).toEqual(["auto", "default", "fast", "ultrafast", "priority", "flex"]);
  await page
    .getByLabel("AI API URL", { exact: true })
    .fill("https://model.invalid/v1");
  await page.getByLabel("AI API Key").fill("test-only");
  await page.getByLabel("AI model", { exact: true }).fill("gpt-6-astra");
  await page.getByLabel("AI reasoning effort").fill("high");
  await tier.selectOption("fast");
  await page
    .getByRole("button", { name: "Save AI settings", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Save AI settings", exact: true }),
  ).toBeDisabled();
  await page.reload();
  await page.getByText("Model and motion settings", { exact: true }).click();
  await expect(tier).toHaveValue("fast");
  await expect(page.getByLabel("AI reasoning effort")).toHaveValue("high");
  await page
    .getByRole("combobox", { name: "Language / 语言" })
    .selectOption("zh");
  await expect(page.getByLabel("AI 服务档位", { exact: true })).toHaveValue(
    "fast",
  );
  await expect(
    page
      .getByLabel("AI 服务档位", { exact: true })
      .locator('option[value="fast"]'),
  ).toHaveText("快速（fast）");
  await page.setViewportSize({ width: 390, height: 1080 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page
    .getByRole("combobox", { name: "Language / 语言" })
    .selectOption("en");
  await page.setViewportSize({ width: 1440, height: 1080 });
  await page
    .getByRole("button", {
      name: "Verify connection and capabilities",
      exact: true,
    })
    .click();
  await expect(page.locator("[data-sonner-toast]").last()).toContainText(
    "Server tier: priority",
  );
  await page
    .getByLabel("AI task", { exact: true })
    .fill("Reply only. No camera or robot actions.");
  await page
    .getByRole("button", { name: "Start conversation", exact: true })
    .click();
  await expect(page.locator(".conversation")).toContainText("Turn finished");
  await expect(page.getByLabel("AI request performance")).toContainText(
    "Server tier: default",
  );
  expect(requests).toHaveLength(3);
  expect(
    requests.every(
      (r) => r.service_tier === "fast" && r.reasoning.effort === "high",
    ),
  ).toBe(true);
  await tier.selectOption("auto");
  await page
    .getByRole("button", { name: "Save AI settings", exact: true })
    .click();
  await page
    .getByLabel("AI task", { exact: true })
    .fill("Continue with a text reply only.");
  await page
    .getByRole("button", { name: "Continue conversation", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Confirm and continue", exact: true })
    .click();
  await expect.poll(() => requests.length).toBe(4);
  await expect(page.locator(".section-heading .badge")).toHaveText(
    "Waiting for a task",
  );
  expect(requests[3].service_tier).toBe("auto");
  expect(requests[3].prompt_cache_key).toBe(requests[2].prompt_cache_key);
});
