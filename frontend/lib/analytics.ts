// Lightweight gtag conversion helpers.
//
// GA4 (and, if NEXT_PUBLIC_GOOGLE_ADS_ID is set, the Google Ads tag) is loaded
// once by components/GoogleAnalytics.tsx. These fire the standard GA4 events —
// `sign_up` and `purchase` — which Google Ads imports as conversions after you
// link the GA4 property. If you also create native Google Ads conversion
// actions, drop their "send-to" labels (AW-XXXXXXX/LABEL) into the two env vars
// below and they fire directly too. Everything no-ops safely when gtag is absent.

type GtagParams = Record<string, unknown>;

function callGtag(...args: unknown[]): void {
  if (typeof window === "undefined") return;
  const w = window as unknown as { gtag?: (...a: unknown[]) => void };
  if (typeof w.gtag === "function") w.gtag(...args);
}

function track(
  eventName: string,
  params: GtagParams,
  adsSendTo?: string,
): void {
  callGtag("event", eventName, params);
  if (adsSendTo) {
    callGtag("event", "conversion", { send_to: adsSendTo, ...params });
  }
}

/** Free-account registration completed. */
export function trackSignUp(method = "email"): void {
  track("sign_up", { method }, process.env.NEXT_PUBLIC_ADS_SIGNUP_SEND_TO);
}

/** Paid subscription completed (Stripe checkout returned success). */
export function trackSubscribe(
  tier?: string,
  value?: number,
  currency = "CAD",
): void {
  const params: GtagParams = { currency };
  if (typeof value === "number") params.value = value;
  if (tier) {
    params.items = [{ item_id: tier, item_name: `${tier} subscription` }];
  }
  track("purchase", params, process.env.NEXT_PUBLIC_ADS_SUBSCRIBE_SEND_TO);
}
