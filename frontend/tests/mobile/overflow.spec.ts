import { test, expect } from "@playwright/test";
import {
  PUBLIC_ROUTES,
  visit,
  findEscapees,
  describeEscapees,
} from "./helpers";

/**
 * The regression this suite exists for: 44 pages once hand-rolled their
 * navigation as a single unbreakable flex row 400-1065px wide, which ran off
 * the side of every phone and took Login and Register with it.
 */
test.describe("no horizontal overflow", () => {
  for (const route of PUBLIC_ROUTES) {
    test(`${route} keeps every element inside the viewport`, async ({
      page,
    }) => {
      await visit(page, route);
      const escapees = await findEscapees(page);
      expect(escapees, describeEscapees(route, escapees)).toEqual([]);
    });
  }
});

test.describe("the clip guard is a backstop, not the fix", () => {
  // globals.css sets `body { overflow-x: clip }`. It must stay a guard rail:
  // if a page only fits *because* of it, this fails and points at the culprit.
  for (const route of ["/", "/companies", "/metals", "/properties", "/store"]) {
    test(`${route} still fits with the guard lifted`, async ({ page }) => {
      await visit(page, route);
      await page.evaluate(() => {
        document.documentElement.style.setProperty(
          "overflow-x",
          "visible",
          "important",
        );
        document.body.style.setProperty("overflow-x", "visible", "important");
        void document.body.offsetWidth;
      });
      await page.waitForTimeout(300);

      const escapees = await findEscapees(page);
      expect(escapees, describeEscapees(route, escapees)).toEqual([]);
    });
  }
});
