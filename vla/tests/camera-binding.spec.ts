import { test, expect } from "@playwright/test";

test("authorization belongs beside each binding and unlocks named cameras without an arm", async ({
  page,
}) => {
  // Browser API fixture reproduces the anonymous, empty-ID list observed on
  // the deployed page. Camera labels are arbitrary; no hardware is simulated as verified.
  await page.addInitScript(() => {
    let allowed = false;
    const media = new EventTarget();
    Object.assign(media, {
      enumerateDevices: async () =>
        allowed
          ? [
              {
                kind: "videoinput",
                deviceId: "logitech",
                label: "Logitech C920",
              },
              { kind: "videoinput", deviceId: "other", label: "USB camera" },
            ]
          : [{ kind: "videoinput", deviceId: "", label: "" }],
      getUserMedia: async () => {
        allowed = true;
        return { getTracks: () => [{ stop() {} }] };
      },
    });
    Object.defineProperty(navigator, "mediaDevices", {
      configurable: true,
      value: media,
    });
  });
  await page.goto("/");
  const cards = page.locator(".camera-card");
  await expect(
    page.getByRole("button", { name: "Configuration saved", exact: true }),
  ).toBeEnabled();
  await expect(page.locator(".top-actions .badge")).toHaveText(
    "Follower disconnected",
  );
  await expect(page.locator(".section-foot button")).toHaveCount(0);
  await expect(cards.locator(".camera-authorize")).toHaveCount(2);
  for (const locale of ["en", "zh"] as const) {
    await page
      .getByRole("combobox", { name: "Language / 语言" })
      .selectOption(locale);
    for (const width of [1440, 390]) {
      await page.setViewportSize({ width, height: 1080 });
      for (const card of await cards.all()) {
        const heading = card.locator(".camera-binding-heading");
        const label = await heading.locator("label").boundingBox();
        const authorize = heading.locator("button");
        await expect(authorize).toBeEnabled();
        const button = await authorize.boundingBox();
        expect(label).not.toBeNull();
        expect(button).not.toBeNull();
        expect(
          Math.abs(
            label!.y + label!.height / 2 - (button!.y + button!.height / 2),
          ),
        ).toBeLessThan(2);
      }
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
    }
  }
  await page
    .getByRole("combobox", { name: "Language / 语言" })
    .selectOption("en");
  const external = page.getByLabel("External camera device", { exact: true });
  await expect(external.locator("option")).toHaveCount(1);
  await expect(external).toHaveValue("");
  await cards
    .last()
    .getByRole("button", { name: "Authorize and refresh cameras", exact: true })
    .click();
  await expect(external.locator("option")).toHaveCount(3);
  await expect(external.locator('option[value="logitech"]')).toHaveText(
    "Logitech C920",
  );
  await external.selectOption("logitech");
  await expect(
    cards.first().getByRole("button", { name: "Start preview", exact: true }),
  ).toBeEnabled();
  await expect(page.locator(".top-actions .badge")).toHaveText(
    "Follower disconnected",
  );
});
