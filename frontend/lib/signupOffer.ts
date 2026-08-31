/**
 * What a brand-new registration actually grants, read from the backend.
 *
 * Registration calls deliver_welcome() -> PlatformSubscription.grant_free_month(),
 * but only while WELCOME_FREE_MONTH_ENABLED is on. That is an env var on the
 * server. Hardcoding "free month" into landing-page copy means flipping that var
 * turns the copy into a lie with nothing to catch it, so the copy asks instead.
 *
 * Fetch this server-side and pass it down, so the CTA is correct in the initial
 * HTML — paid search traffic should not see the wrong offer flash and change.
 */

export interface SignupOffer {
  free_trial_enabled: boolean;
  free_trial_days: number;
  free_trial_tier: string;
  free_trial_unlimited_chat: boolean;
  fallback_tier: string;
  fallback_chat_limit: number;
}

/**
 * Used when the endpoint cannot be reached. Deliberately assumes the promo is
 * OFF: understating the offer costs a little conversion, overstating it means
 * promising a month of Prospector that registration will not grant.
 */
export const SIGNUP_OFFER_FALLBACK: SignupOffer = {
  free_trial_enabled: false,
  free_trial_days: 0,
  free_trial_tier: "explorer",
  free_trial_unlimited_chat: false,
  fallback_tier: "explorer",
  fallback_chat_limit: 5,
};

const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

/** Server-side fetch. Never throws — falls back to the conservative offer. */
export async function fetchSignupOffer(): Promise<SignupOffer> {
  try {
    const res = await fetch(`${API_BASE_URL}/platform/signup-offer/`, {
      next: { revalidate: 300 },
    });
    if (!res.ok) return SIGNUP_OFFER_FALLBACK;
    const data = (await res.json()) as Partial<SignupOffer>;
    if (typeof data.free_trial_enabled !== "boolean") {
      return SIGNUP_OFFER_FALLBACK;
    }
    return { ...SIGNUP_OFFER_FALLBACK, ...data } as SignupOffer;
  } catch {
    return SIGNUP_OFFER_FALLBACK;
  }
}

/**
 * Client-side variant, for components that cannot be server-rendered.
 *
 * ChatInterface is mounted globally by AssistantProvider and is a client
 * component, so it cannot receive the offer as a server prop the way
 * /companies does. Same conservative fallback: an unreachable endpoint means
 * we assume the promo is off rather than promise a trial that registration
 * will not grant.
 */
export async function fetchSignupOfferClient(): Promise<SignupOffer> {
  try {
    const res = await fetch(`${API_BASE_URL}/platform/signup-offer/`);
    if (!res.ok) return SIGNUP_OFFER_FALLBACK;
    const data = (await res.json()) as Partial<SignupOffer>;
    if (typeof data.free_trial_enabled !== "boolean") {
      return SIGNUP_OFFER_FALLBACK;
    }
    return { ...SIGNUP_OFFER_FALLBACK, ...data } as SignupOffer;
  } catch {
    return SIGNUP_OFFER_FALLBACK;
  }
}
