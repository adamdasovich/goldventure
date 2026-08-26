import { defineConfig, type ViewportSize } from "@playwright/test";

/**
 * Mobile regression suite.
 *
 * Runs against BASE_URL (default http://localhost:3000). Point it at
 * production with:
 *   BASE_URL=https://juniorminingintelligence.com npm run test:mobile
 *
 * Uses the locally installed Chrome by default so nobody has to download a
 * 300MB browser to run it. For a pinned browser in CI:
 *   PW_CHANNEL= npx playwright install chromium
 *   PW_CHANNEL= npm run test:mobile
 *
 * Analytics are blocked per-page in helpers.visit() — see blockAnalytics().
 * A production run without it puts ~1,000 zero-engagement sessions into GA4
 * from one IP, which is what happened on 2026-08-24. Do not add a spec that
 * calls page.goto() directly; it would bypass the block.
 *
 * NOTE: do NOT spread `devices["iPhone SE"]` here. Those descriptors set
 * `defaultBrowserType: "webkit"`, and webkit rejects a Chrome channel, so the
 * whole run dies with `Unsupported webkit channel "chrome"`. The mobile
 * emulation flags are set explicitly below instead.
 */
const CHANNEL = process.env.PW_CHANNEL ?? "chrome";

const IOS_UA =
  "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 " +
  "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1";

const mobile = (viewport: ViewportSize) => ({
  browserName: "chromium" as const,
  channel: CHANNEL || undefined,
  viewport,
  deviceScaleFactor: 2,
  isMobile: true,
  hasTouch: true,
  userAgent: IOS_UA,
});

export default defineConfig({
  testDir: "./tests/mobile",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 2 : 3,
  reporter: process.env.CI
    ? [["list"], ["html", { open: "never" }]]
    : [["list"]],

  use: {
    baseURL: process.env.BASE_URL || "http://localhost:3000",
    // /properties holds a WebSocket open, so `networkidle` never fires there.
    // Specs wait on DOM readiness plus a settle instead — see helpers.visit().
    actionTimeout: 15_000,
    navigationTimeout: 45_000,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },

  // The widths that matter: the narrowest phone still in use, the iPhone SE/8
  // baseline, a current handset, and landscape — landscape is not decorative,
  // it is where a tall modal fails first.
  projects: [
    { name: "320px", use: mobile({ width: 320, height: 568 }) },
    { name: "375px", use: mobile({ width: 375, height: 667 }) },
    { name: "390px", use: mobile({ width: 390, height: 844 }) },
    { name: "landscape", use: mobile({ width: 667, height: 375 }) },
  ],
});
