import { test, expect, type Locator } from "@playwright/test";
import { visit } from "./helpers";

/**
 * An overlay that only centres its child pushes the overflow of a tall panel
 * *above the scroll origin*, where nothing can reach it — not by scrolling the
 * page, not by scrolling the overlay. RegisterModal is ~869px tall, so on a
 * 375x667 phone roughly 101px was cut off each end and registration could not
 * be completed at all. Everything here guards that.
 *
 * Read-only: opens the dialogs and measures. Never submits.
 */

async function openMenu(page: import("@playwright/test").Page) {
  await visit(page, "/companies");
  const trigger = page.locator('button[aria-controls="site-menu"]');
  await trigger.tap();
  await expect(page.locator("#site-menu")).toBeVisible();
}

async function assertFitsViewport(
  dialog: Locator,
  vw: number,
  vh: number,
  label: string,
) {
  const b = (await dialog.boundingBox())!;
  expect(b.x, `${label} starts inside the viewport`).toBeGreaterThanOrEqual(-1);
  expect(
    b.x + b.width,
    `${label} ends inside the viewport`,
  ).toBeLessThanOrEqual(vw + 1);
  expect(b.y, `${label} top is on screen`).toBeGreaterThanOrEqual(-1);
  expect(
    b.y + b.height,
    `${label} bottom is on screen (h=${Math.round(b.height)} vs viewport ${vh})`,
  ).toBeLessThanOrEqual(vh + 1);
}

test.describe("auth dialogs", () => {
  test("login box is fully on screen and submittable", async ({
    page,
  }, testInfo) => {
    const { width: vw, height: vh } = testInfo.project.use.viewport!;
    await openMenu(page);
    await page
      .locator("#site-menu button", { hasText: /^Login$/ })
      .first()
      .tap();

    const dialog = page.locator('[role="dialog"]');
    await expect(dialog).toBeVisible();
    await assertFitsViewport(dialog, vw, vh, "login box");

    const submit = dialog.locator('button[type="submit"]');
    const sb = (await submit.boundingBox())!;
    expect(sb.y, "submit button is on screen").toBeGreaterThanOrEqual(0);
    expect(sb.y + sb.height, "submit button is on screen").toBeLessThanOrEqual(
      vh + 1,
    );

    await expect(dialog).toHaveAttribute("aria-modal", "true");
    await expect(dialog).toHaveAttribute("aria-labelledby", /.+/);
  });

  test("register box caps to the viewport and scrolls internally", async ({
    page,
  }, testInfo) => {
    const { width: vw, height: vh } = testInfo.project.use.viewport!;
    await openMenu(page);
    await page
      .locator("#site-menu button", { hasText: /^Register$/ })
      .first()
      .tap();

    const dialog = page.locator('[role="dialog"]');
    await expect(dialog).toBeVisible();
    await assertFitsViewport(dialog, vw, vh, "register box");

    // Taller than the viewport is fine — unreachable is not.
    const submit = dialog.locator('button[type="submit"]');
    await dialog.evaluate((el) => (el.scrollTop = el.scrollHeight));
    await page.waitForTimeout(250);
    const sb = (await submit.boundingBox())!;
    expect(
      sb.y,
      "submit reachable by scrolling down inside the dialog",
    ).toBeGreaterThanOrEqual(0);
    expect(sb.y + sb.height).toBeLessThanOrEqual(vh + 1);

    // This is the half that used to be lost above the scroll origin.
    await dialog.evaluate((el) => (el.scrollTop = 0));
    await page.waitForTimeout(250);
    const hb = (await dialog.locator("#register-modal-title").boundingBox())!;
    expect(
      hb.y,
      "heading reachable by scrolling back up",
    ).toBeGreaterThanOrEqual(0);
    expect(hb.y + hb.height).toBeLessThanOrEqual(vh + 1);
  });

  test("dialog traps the page and releases it on close", async ({ page }) => {
    await openMenu(page);
    await page
      .locator("#site-menu button", { hasText: /^Login$/ })
      .first()
      .tap();

    const dialog = page.locator('[role="dialog"]');
    await expect(dialog).toBeVisible();
    expect(
      await page.evaluate(() => getComputedStyle(document.body).overflow),
    ).toBe("hidden");

    await page.keyboard.press("Escape");
    await expect(dialog).toBeHidden();
    expect(
      await page.evaluate(() => getComputedStyle(document.body).overflow),
    ).not.toBe("hidden");
  });

  test("switching login -> register keeps the dialog usable", async ({
    page,
  }, testInfo) => {
    const { width: vw, height: vh } = testInfo.project.use.viewport!;
    await openMenu(page);
    await page
      .locator("#site-menu button", { hasText: /^Login$/ })
      .first()
      .tap();

    const dialog = page.locator('[role="dialog"]');
    await dialog
      .locator("button", { hasText: /^Register$/ })
      .first()
      .tap();
    await expect(page.locator("#register-modal-title")).toBeVisible();
    await assertFitsViewport(
      page.locator('[role="dialog"]'),
      vw,
      vh,
      "register box after switch",
    );
  });
});
