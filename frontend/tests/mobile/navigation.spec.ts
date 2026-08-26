import { test, expect } from "@playwright/test";
import { visit } from "./helpers";

// SiteHeader (the app shell) vs SiteNav (the static SEO/report routes).
const HEADER_ROUTES = [
  "/",
  "/companies",
  "/properties",
  "/metals",
  "/dashboard",
];
const STATIC_NAV_ROUTES = ["/guides", "/about", "/reports/weekly"];

test.describe("SiteHeader mobile menu", () => {
  for (const route of HEADER_ROUTES) {
    test(`${route} exposes the full nav behind the trigger`, async ({
      page,
    }, testInfo) => {
      await visit(page, route);

      const trigger = page.locator('button[aria-controls="site-menu"]');
      await expect(trigger, "mobile nav trigger is rendered").toBeVisible();

      const tb = (await trigger.boundingBox())!;
      expect(
        tb.width,
        "trigger width meets the 44px touch floor",
      ).toBeGreaterThanOrEqual(44);
      expect(
        tb.height,
        "trigger height meets the 44px touch floor",
      ).toBeGreaterThanOrEqual(44);
      expect(
        tb.x + tb.width,
        "trigger is inside the viewport",
      ).toBeLessThanOrEqual(testInfo.project.use.viewport!.width + 1);

      await trigger.tap();
      const menu = page.locator("#site-menu");
      await expect(menu).toBeVisible();

      // Every top-level destination, not just a lone "Home" escape hatch.
      const links = menu.locator("a");
      expect(
        await links.count(),
        "menu lists the full destination set",
      ).toBeGreaterThanOrEqual(8);

      const vw = testInfo.project.use.viewport!.width;
      for (let i = 0; i < (await links.count()); i++) {
        const b = (await links.nth(i).boundingBox())!;
        expect(
          b.x,
          `menu link ${i} starts inside the viewport`,
        ).toBeGreaterThanOrEqual(-1);
        expect(
          b.x + b.width,
          `menu link ${i} ends inside the viewport`,
        ).toBeLessThanOrEqual(vw + 1);
      }

      // The page behind must not scroll while the panel is open.
      expect(
        await page.evaluate(() => getComputedStyle(document.body).overflow),
      ).toBe("hidden");

      await trigger.tap();
      await expect(menu).toBeHidden();
      expect(
        await page.evaluate(() => getComputedStyle(document.body).overflow),
      ).not.toBe("hidden");
    });
  }
});

test.describe("SiteNav on the static routes", () => {
  for (const route of STATIC_NAV_ROUTES) {
    test(`${route} keeps its destinations reachable`, async ({ page }, testInfo) => {
      await visit(page, route);

      // These are server-rendered SEO pages, so the nav is plain markup with
      // almost no client JS. Which half shows is a width question: the strip
      // covers everything below `lg`, because the inline row measured 576px
      // and did not fit a 667px landscape phone.
      const vw = testInfo.project.use.viewport!.width;
      const strip = page.locator('nav[aria-label="Site sections"]');
      const inline = page.locator("nav.glass-nav div.hidden").first();

      if (vw < 1024) {
        await expect(strip, "chip strip is rendered below lg").toBeVisible();
        expect(await strip.locator("a").count()).toBeGreaterThanOrEqual(4);

        // It may scroll sideways; it may not clip silently.
        const scrolls = await strip.evaluate((el) => ({
          overflowX: getComputedStyle(el).overflowX,
          canScroll: el.scrollWidth > el.clientWidth + 1,
        }));
        if (scrolls.canScroll) expect(scrolls.overflowX).toBe("auto");
      } else {
        await expect(inline, "inline link row is rendered at or above lg").toBeVisible();
        expect(await inline.locator("a").count()).toBeGreaterThanOrEqual(4);
      }
    });
  }
});
