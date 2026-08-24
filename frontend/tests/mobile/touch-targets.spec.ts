import { test, expect } from "@playwright/test";
import { visit } from "./helpers";

/**
 * Touch target sizes.
 *
 * Two different bars, deliberately:
 *
 *   HARD  24x24 — WCAG 2.5.8 Target Size (Minimum), Level AA. Non-negotiable.
 *   GOAL  44x44 — WCAG 2.5.5 Target Size (Enhanced), Level AAA, and Apple's
 *         Human Interface Guidelines. This is what the codebase aims for.
 *
 * (An earlier pass in this repo cited 2.5.8 for the 44px figure. That was
 * wrong — 2.5.8 is 24x24. The 44px goal stands on 2.5.5/HIG instead.)
 *
 * The GOAL bar is applied as 44x44 to things that render as controls — they
 * have a background or a border, so padding them out costs nothing. For plain
 * text links it is applied to height only: a link reading "Store" cannot be
 * 44px wide without boxing it, and in a list what prevents mis-taps is the
 * row height, not the word length. WCAG's own spacing exception makes the
 * same trade.
 *
 * components/ui/Button carries a `min-h-11 min-w-11 sm:min-h-0 sm:min-w-0`
 * floor covering its ~291 call sites. This spec exists for everything that
 * bypasses the primitive — that is where the shortfall actually lived.
 */

const ROUTES = [
  "/",
  "/companies",
  "/properties",
  "/metals",
  "/pricing",
  "/store",
  "/investor-tools",
];

const HARD_MIN = 24;
const GOAL = 44;

/**
 * Deliberate exceptions, each with a reason. Keep this list short and argued —
 * an entry here is a decision, not a snooze button.
 */
const ALLOWED = [
  {
    // ProductCard wraps the whole card in the link; this inner title link is a
    // 40px slice of a target that is ~300px tall in practice.
    match: /Specimen Collection|Starter/i,
    reason: "inner title link inside a fully clickable product card",
  },
];

interface Control {
  text: string;
  tag: string;
  h: number;
  w: number;
  cls: string;
  looksLikeControl: boolean;
}

async function collect(
  page: import("@playwright/test").Page,
): Promise<Control[]> {
  return page.evaluate(() => {
    const out: Control[] = [];
    for (const el of Array.from(document.querySelectorAll("button, a[href]"))) {
      const r = el.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) continue;

      const cs = getComputedStyle(el);
      // Links rendered inline within a sentence are exempt (WCAG 2.5.8).
      if (cs.display === "inline") continue;

      const hasBg =
        cs.backgroundColor !== "rgba(0, 0, 0, 0)" &&
        cs.backgroundColor !== "transparent";
      const hasBorder =
        parseFloat(cs.borderTopWidth) > 0 ||
        parseFloat(cs.borderLeftWidth) > 0 ||
        parseFloat(cs.borderBottomWidth) > 0;

      out.push({
        text:
          (el.textContent || "").trim().slice(0, 40) ||
          `<${el.tagName.toLowerCase()}>`,
        tag: el.tagName.toLowerCase(),
        h: Math.round(r.height),
        w: Math.round(r.width),
        cls: (el.className || "").toString().slice(0, 70),
        looksLikeControl: el.tagName === "BUTTON" || hasBg || hasBorder,
      });
    }
    return out;
  });
}

const allowed = (c: Control) =>
  ALLOWED.some((a) => a.match.test(c.text) || a.match.test(c.cls));

const fmt = (list: Control[]) =>
  list
    .map(
      (v) => `  ${v.h}x${v.w}  <${v.tag}> "${v.text}"\n      class: ${v.cls}`,
    )
    .join("\n");

test.describe(`hard floor — ${HARD_MIN}x${HARD_MIN} (WCAG 2.5.8 AA)`, () => {
  for (const route of ROUTES) {
    test(`${route}`, async ({ page }) => {
      await visit(page, route);
      const bad = (await collect(page)).filter(
        (c) => !allowed(c) && (c.h < HARD_MIN || c.w < HARD_MIN),
      );
      expect(
        bad,
        `${route}: ${bad.length} below the AA floor\n${fmt(bad)}`,
      ).toEqual([]);
    });
  }
});

test.describe(`goal — ${GOAL}x${GOAL} for controls, ${GOAL} tall for text links`, () => {
  for (const route of ROUTES) {
    test(`${route}`, async ({ page }) => {
      await visit(page, route);
      const bad = (await collect(page)).filter((c) => {
        if (allowed(c)) return false;
        return c.looksLikeControl ? c.h < GOAL || c.w < GOAL : c.h < GOAL;
      });
      expect(
        bad,
        `${route}: ${bad.length} below the ${GOAL}px goal\n${fmt(bad)}`,
      ).toEqual([]);
    });
  }
});

test.describe("form controls", () => {
  // Safari on iOS auto-zooms a focused control whose font-size is under 16px,
  // and the zoom persists after blur — leaving the visitor on a magnified,
  // sideways-scrolling page for the rest of the session.
  for (const route of ["/companies", "/properties", "/store"]) {
    test(`${route} inputs are at least 16px so iOS does not zoom`, async ({
      page,
    }) => {
      await visit(page, route);

      const tooSmall = await page.evaluate(() => {
        const out: { tag: string; size: string; name: string }[] = [];
        for (const el of Array.from(
          document.querySelectorAll("input, select, textarea"),
        )) {
          const r = el.getBoundingClientRect();
          if (r.width === 0 || r.height === 0) continue;
          const size = parseFloat(getComputedStyle(el).fontSize);
          if (size >= 16) continue;
          out.push({
            tag: el.tagName.toLowerCase(),
            size: `${size}px`,
            name:
              (el as HTMLInputElement).name ||
              (el as HTMLInputElement).placeholder ||
              "",
          });
        }
        return out;
      });

      expect(
        tooSmall,
        `${route}: ${tooSmall.length} control(s) under 16px — ${JSON.stringify(tooSmall)}`,
      ).toEqual([]);
    });
  }
});
