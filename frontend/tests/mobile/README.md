# Mobile regression suite

Guards the class of bug that made the site unusable on a phone in August 2026:
navigation that ran off the side of the viewport, modals that clipped their own
content into unreachable space, and touch targets under the 44px floor.

## Running it

```bash
# against a local production build (next build && next start on :3000)
npm run test:mobile

# against production
BASE_URL=https://juniorminingintelligence.com npm run test:mobile

# one width only
npm run test:mobile -- --project=375px

# one file
npm run test:mobile -- tests/mobile/modals.spec.ts

# after a failure
npm run test:mobile:report
```

Uses the locally installed Chrome by default, so there is no 300MB browser
download. For a pinned browser in CI:

```bash
PW_CHANNEL= npx playwright install chromium
PW_CHANNEL= npm run test:mobile
```

Widths covered: **320** (narrowest phone still in use), **375** (iPhone SE/8
baseline), **390** (current handset), and **667x375 landscape** — landscape is
not decorative here, it is where a tall modal fails first.

## What each file guards

| File                    | Guards                                                                                                                                                                            |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `overflow.spec.ts`      | No element escapes the viewport on 25 public routes. Also re-checks five routes with the `overflow-x: clip` guard lifted.                                                         |
| `navigation.spec.ts`    | The mobile trigger exists, is 44px, opens the full destination list, locks the page behind it, and closes cleanly. Covers both `SiteHeader` and the JS-free `SiteNav` chip strip. |
| `modals.spec.ts`        | Login and register fit the viewport, cap to it, scroll internally, and can be reached top and bottom. Read-only — never submits.                                                  |
| `touch-targets.spec.ts` | 44px floor for controls that bypass `ui/Button`, and a 16px floor on form controls so iOS Safari does not auto-zoom.                                                              |

## Two traps worth knowing

**`scrollWidth` does not detect overflow on this site.** `globals.css` sets
`body { overflow-x: clip }` as a backstop, which suppresses `scrollWidth`
growth — the document reports a tidy 375px while an element sits hundreds of
pixels off-screen. That is how the `/metals` metal selector (660px, ten buttons
in a non-wrapping row) survived a full static review and three deploys.
`findEscapees()` in `helpers.ts` measures per-element geometry instead, and
skips anything inside a container that scrolls or clips on purpose.

**`networkidle` never fires on `/properties`.** It holds a WebSocket open.
`visit()` waits on DOM readiness plus a short settle instead. Do not "fix" it
back to `networkidle`.

## Adding an exception

`touch-targets.spec.ts` has an `ALLOWED` list. Every entry carries a reason.
Keep it short and argued — an entry there is a decision, not a snooze button.

## Analytics are blocked

`helpers.visit()` calls `blockAnalytics()` before every navigation, aborting
requests to googletagmanager, google-analytics, doubleclick and googleadservices.

This matters because the suite is meant to be pointed at production. A run on
2026-08-24 added ~1,000 sessions to GA4 from a single IP — mobile Safari, ~4
second sessions, 0% engagement, walking `PUBLIC_ROUTES` in order. That was 94%
of the week's traffic and it landed mid paid-ads test, so both conversion rate
and channel mix were unreadable until it was traced.

If you add a spec, navigate through `visit()`. A bare `page.goto()` bypasses
the block and starts polluting again silently.
