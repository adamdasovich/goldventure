import type { Page } from "@playwright/test";

/** Routes a mobile visitor can actually reach without signing in. */
export const PUBLIC_ROUTES = [
  "/",
  "/companies",
  "/companies/commodity/gold",
  "/properties",
  "/metals",
  "/guides",
  "/guides/gold-grade-explained",
  "/guides/how-to-read-ni-43-101-report",
  "/about",
  "/pricing",
  "/dashboard",
  "/open-financings",
  "/closed-financings",
  "/glossary",
  "/financial-hub",
  "/financial-hub/education",
  "/store",
  "/store/cart",
  "/reports/weekly",
  "/reports/financings",
  "/investor-tools",
  "/investor-tools/warrant-radar",
  "/investor-tools/grade-ranker",
  "/investor-tools/liquidity-screener",
  "/investor-tools/dilution-tracker",
];

/**
 * `networkidle` never fires on /properties — it holds a WebSocket open — so
 * wait on DOM readiness and give client-side data a moment to land instead.
 */
/**
 * Analytics hosts this suite must never reach.
 *
 * The suite is designed to run against production (see README), and every
 * visit() loads the real page with the real Google tag on it. On 2026-08-24-25
 * a run put ~1,000 sessions into GA4 from one IP: mobile Safari, ~4 second
 * sessions, 0% engagement, walking PUBLIC_ROUTES in order. That is 94% of the
 * week and it landed in the middle of a paid-ads test, so conversion rate and
 * channel mix were both unreadable.
 *
 * Blocking at the network layer rather than filtering in GA4 afterwards: a
 * filter is retroactive, per-property and easy to forget, whereas a run that
 * cannot reach the collector cannot pollute anything.
 */
const ANALYTICS_HOSTS = [
  "**://www.googletagmanager.com/**",
  "**://www.google-analytics.com/**",
  "**://analytics.google.com/**",
  "**://*.analytics.google.com/**",
  "**://googleads.g.doubleclick.net/**",
  "**://www.googleadservices.com/**",
];

/** Call once per page before navigating. Idempotent. */
export async function blockAnalytics(page: Page) {
  for (const pattern of ANALYTICS_HOSTS) {
    await page.route(pattern, (route) => route.abort());
  }
}

export async function visit(page: Page, route: string) {
  // Registered before goto, so the tag never loads on the first navigation.
  await blockAnalytics(page);
  await page.goto(route, { waitUntil: "domcontentloaded" });
  await page.waitForLoadState("load").catch(() => {});
  await page.waitForTimeout(1200);
}

export interface Escapee {
  tag: string;
  cls: string;
  text: string;
  width: number;
  left: number;
  right: number;
}

/**
 * Find elements sticking out past the viewport.
 *
 * NOT scrollWidth. `body { overflow-x: clip }` in globals.css suppresses
 * scrollWidth growth, so the document reports a tidy 375px while an element
 * sits hundreds of pixels off-screen — that is exactly how the /metals metal
 * selector (660px wide, ten buttons in a non-wrapping row) survived a full
 * static review and three deploys. Measure geometry per element, and ignore
 * anything inside a container that scrolls or clips horizontally on purpose.
 */
export async function findEscapees(page: Page): Promise<Escapee[]> {
  return page.evaluate(() => {
    const innerW = window.innerWidth;
    const found: Escapee[] = [];

    for (const el of Array.from(document.querySelectorAll("body *"))) {
      const r = el.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) continue;
      if (r.right <= innerW + 2 && r.left >= -2) continue;

      const cs = getComputedStyle(el);
      // Overlays are anchored to the viewport and handled by modals.spec.ts.
      if (cs.position === "fixed") continue;

      let inScroller = false;
      for (let p = el.parentElement; p; p = p.parentElement) {
        if (p === document.body || p === document.documentElement) break;
        const ps = getComputedStyle(p);
        if (["auto", "scroll", "hidden", "clip"].includes(ps.overflowX)) {
          inScroller = true;
          break;
        }
      }
      if (inScroller) continue;

      found.push({
        tag: el.tagName.toLowerCase(),
        cls: (el.className || "").toString().slice(0, 90),
        text: (el.textContent || "").trim().slice(0, 40),
        width: Math.round(r.width),
        left: Math.round(r.left),
        right: Math.round(r.right),
      });
    }

    // widest first, one row per distinct tag+class
    const seen = new Set<string>();
    return found
      .sort((a, b) => b.width - a.width)
      .filter((e) => {
        const k = e.tag + e.cls;
        if (seen.has(k)) return false;
        seen.add(k);
        return true;
      })
      .slice(0, 6);
  });
}

export function describeEscapees(route: string, escapees: Escapee[]) {
  return [
    `${route} has ${escapees.length} element(s) outside the viewport:`,
    ...escapees.map(
      (e) =>
        `  <${e.tag}> w=${e.width} left=${e.left} right=${e.right}` +
        `\n      class: ${e.cls}` +
        `\n      text:  ${e.text}`,
    ),
  ].join("\n");
}
