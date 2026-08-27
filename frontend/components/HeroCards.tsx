"use client";

import { useState, useEffect } from "react";
import SectionHeading from "@/components/SectionHeading";
import Link from "next/link";
import Image from "next/image";
import { useAuth } from "@/contexts/AuthContext";
import { companyHref } from "@/lib/companyUrl";

interface UpcomingEvent {
  id: number;
  title: string;
  company_id: number;
  company_slug?: string | null;
  company_name: string;
  company_ticker: string;
  scheduled_start: string;
  scheduled_end: string | null;
  status: "live" | "upcoming";
  format: "video" | "text";
  registered_count: number;
}

interface ActiveFinancing {
  id: number;
  company_id: number;
  company_name: string;
  company_ticker: string;
  financing_type: string;
  financing_type_display: string;
  amount_raised_usd: number | null;
  closing_date: string | null;
  status: string;
}

interface FeaturedProperty {
  id: number;
  slug: string;
  title: string;
  summary: string;
  location: string;
  country: string;
  primary_mineral: string;
  total_hectares: number | null;
  asking_price: number | null;
  price_currency: string;
  listing_type: string;
  exploration_stage: string;
  primary_image_url: string | null;
  next_rotation: string | null;
  is_manual_selection: boolean;
}

interface HeroData {
  upcoming_events: UpcomingEvent[];
  active_financings: ActiveFinancing[];
  total_open_financings?: number;
  featured_property: FeaturedProperty | null;
}

interface HeroCardsProps {
  onLoginClick: () => void;
  onRegisterClick: () => void;
}

type LiveTab = "Events" | "Financings" | "Property";

export function HeroCards({ onLoginClick }: HeroCardsProps) {
  const { user } = useAuth();
  const [data, setData] = useState<HeroData | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<LiveTab | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHeroData();
  }, []);

  const fetchHeroData = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"}/hero-section/`,
      );
      if (!response.ok) throw new Error("Failed to fetch hero data");
      const heroData = await response.json();
      setData(heroData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  };

  const formatCurrency = (amount: number, currency: string = "USD") => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const getTimeUntil = (dateString: string) => {
    const now = new Date();
    const eventDate = new Date(dateString);
    const diffMs = eventDate.getTime() - now.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const diffHours = Math.floor(
      (diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60),
    );

    if (diffDays > 0) return `In ${diffDays} day${diffDays > 1 ? "s" : ""}`;
    if (diffHours > 0) return `In ${diffHours} hour${diffHours > 1 ? "s" : ""}`;
    return "Soon";
  };

  const handleCardClick = (e: React.MouseEvent, requiresAuth: boolean) => {
    if (requiresAuth && !user) {
      e.preventDefault();
      onLoginClick();
    }
  };

  // Only show this section once real data has loaded. An empty or errored
  // section reads as "broken" to a first-time visitor, so render nothing.
  const hasData =
    !!data &&
    ((data.upcoming_events?.length ?? 0) > 0 ||
      (data.active_financings?.length ?? 0) > 0 ||
      !!data.featured_property);

  if (loading || error || !hasData) return null;

  const tabs: { key: LiveTab; label: string; count: number }[] = [
    {
      key: "Events",
      label: "Events",
      count: data?.upcoming_events?.length ?? 0,
    },
    {
      key: "Financings",
      label: "Financings",
      count:
        data?.total_open_financings ?? data?.active_financings?.length ?? 0,
    },
    {
      key: "Property",
      label: "Property",
      count: data?.featured_property ? 1 : 0,
    },
  ];
  /* Start on the first tab that has something in it, so the section never
     opens on an empty state while another tab is full. */
  const activeTab =
    tab && tabs.some((t) => t.key === tab && t.count > 0)
      ? tab
      : (tabs.find((t) => t.count > 0)?.key ?? "Events");

  const property = data?.featured_property;
  const liveNow = data?.upcoming_events?.some((e) => e.status === "live");

  return (
    <section
      id="happening-now"
      className="py-10 md:py-14 px-4 sm:px-6 lg:px-8 scroll-mt-24"
    >
      <div className="max-w-4xl mx-auto">
        <SectionHeading
          eyebrow="Live on the platform"
          title="Live now"
          description="Company events running or scheduled, financing rounds still open, and this week's featured listing."
        />
        {!user && (
          <p className="-mt-4 mb-6 text-center text-sm text-slate-500">
            Create a free account to open events, financings and listings.
          </p>
        )}

        {/* Same strip as the company pages. Three columns of cards became
            three tabs over one list. */}
        <div
          role="tablist"
          aria-label="Live platform activity"
          className="-mx-4 sm:mx-0 mb-2 flex gap-1 overflow-x-auto scrollbar-none border-b border-slate-800 px-4 sm:px-0 sm:rounded-xl sm:border sm:border-slate-800 sm:bg-slate-900/60 sm:p-1"
        >
          {tabs.map((t) => {
            const isActive = t.key === activeTab;
            return (
              <button
                key={t.key}
                role="tab"
                type="button"
                {...{ "aria-selected": isActive }}
                aria-controls="live-panel"
                onClick={() => setTab(t.key)}
                className={`whitespace-nowrap px-4 py-2.5 min-h-11 text-sm font-medium rounded-lg transition-colors ${
                  isActive
                    ? "bg-gold-500/15 text-gold-300 border border-gold-500/40"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent"
                }`}
              >
                {t.label}
                {t.count > 0 && (
                  <span className="ml-2 font-mono text-xs tabular-nums text-slate-500">
                    {t.count}
                  </span>
                )}
                {t.key === "Events" && liveNow && (
                  <span
                    className="ml-1.5 inline-block h-1.5 w-1.5 rounded-full bg-red-500 align-middle animate-pulse"
                    aria-label="live now"
                  />
                )}
              </button>
            );
          })}
        </div>

        <div id="live-panel" role="tabpanel">
          {/* ── Events ── */}
          {activeTab === "Events" &&
            (data?.upcoming_events?.length ? (
              <>
                <ul className="divide-y divide-slate-800">
                  {data.upcoming_events.map((event) => (
                    <li key={event.id}>
                      <Link
                        href={companyHref({
                          id: event.company_id,
                          slug: event.company_slug,
                        })}
                        onClick={(e) => handleCardClick(e, true)}
                        className="group flex items-baseline gap-3 py-4"
                      >
                        <span className="flex-1 min-w-0">
                          <span className="block truncate font-medium text-slate-100 transition-colors group-hover:text-gold-400">
                            {event.title}
                          </span>
                          <span className="mt-1 block text-sm text-slate-400">
                            {event.company_name} &middot;{" "}
                            {formatDate(event.scheduled_start)}{" "}
                            {formatTime(event.scheduled_start)}
                          </span>
                        </span>
                        {event.status === "live" ? (
                          <span className="shrink-0 text-xs font-semibold uppercase tracking-wide text-red-400">
                            Live
                          </span>
                        ) : (
                          <span className="shrink-0 font-mono text-xs tabular-nums text-gold-400">
                            {getTimeUntil(event.scheduled_start)}
                          </span>
                        )}
                      </Link>
                    </li>
                  ))}
                </ul>
                <Link
                  href="/companies"
                  className="mt-4 inline-block py-2 text-sm text-gold-400 hover:text-gold-300"
                >
                  Browse companies &rarr;
                </Link>
              </>
            ) : (
              <p className="py-8 text-sm text-slate-400">
                No company events scheduled this week.{" "}
                <Link
                  href="/companies"
                  className="text-gold-400 hover:underline"
                >
                  Browse companies &rarr;
                </Link>
              </p>
            ))}

          {/* ── Financings ── */}
          {activeTab === "Financings" &&
            (data?.active_financings?.length ? (
              <>
                <ul className="divide-y divide-slate-800">
                  {data.active_financings.map((financing) => (
                    <li key={financing.id}>
                      <Link
                        href={`/companies/${financing.company_id}/financing`}
                        onClick={(e) => handleCardClick(e, true)}
                        className="group flex items-baseline gap-3 py-4"
                      >
                        <span className="flex-1 min-w-0">
                          <span className="block truncate font-medium text-slate-100 transition-colors group-hover:text-gold-400">
                            {financing.company_name}
                          </span>
                          <span className="mt-1 block text-sm text-slate-400">
                            {financing.company_ticker} &middot;{" "}
                            {financing.financing_type_display}
                            {financing.closing_date && (
                              <>
                                {" "}
                                &middot; closes{" "}
                                {formatDate(financing.closing_date)}
                              </>
                            )}
                          </span>
                        </span>
                        {financing.amount_raised_usd && (
                          <span className="shrink-0 font-mono text-sm tabular-nums text-gold-400">
                            {formatCurrency(financing.amount_raised_usd)}
                          </span>
                        )}
                      </Link>
                    </li>
                  ))}
                </ul>
                <Link
                  href="/open-financings"
                  className="mt-4 inline-block py-2 text-sm text-gold-400 hover:text-gold-300"
                >
                  {data.total_open_financings &&
                  data.total_open_financings > data.active_financings.length
                    ? `View all ${data.total_open_financings} open financings `
                    : "View all open financings "}
                  &rarr;
                </Link>
              </>
            ) : (
              <p className="py-8 text-sm text-slate-400">
                No open financing rounds right now.{" "}
                <Link
                  href="/closed-financings"
                  className="text-gold-400 hover:underline"
                >
                  View closed financings &rarr;
                </Link>
              </p>
            ))}

          {/* ── Featured property ── */}
          {activeTab === "Property" &&
            (property ? (
              <>
                <Link
                  href={`/properties/${property.slug}`}
                  onClick={(e) => handleCardClick(e, true)}
                  className="group flex items-start gap-4 py-4"
                >
                  {property.primary_image_url && (
                    <span className="relative block h-16 w-24 shrink-0 overflow-hidden rounded-lg">
                      <Image
                        src={property.primary_image_url}
                        alt=""
                        fill
                        sizes="96px"
                        className="object-cover"
                      />
                    </span>
                  )}
                  <span className="flex-1 min-w-0">
                    <span className="block font-medium text-slate-100 transition-colors group-hover:text-gold-400">
                      {property.title}
                    </span>
                    <span className="mt-1 block text-sm text-slate-400">
                      {property.location}, {property.country} &middot;{" "}
                      {property.primary_mineral} &middot;{" "}
                      {property.exploration_stage}
                      {property.total_hectares && (
                        <>
                          {" "}
                          &middot; {property.total_hectares.toLocaleString()} ha
                        </>
                      )}
                    </span>
                  </span>
                  {property.asking_price && (
                    <span className="shrink-0 font-mono text-sm tabular-nums text-gold-400">
                      {formatCurrency(
                        property.asking_price,
                        property.price_currency,
                      )}
                    </span>
                  )}
                </Link>
                <Link
                  href="/properties"
                  className="mt-4 inline-block py-2 text-sm text-gold-400 hover:text-gold-300"
                >
                  Browse all listings &rarr;
                </Link>
              </>
            ) : (
              <p className="py-8 text-sm text-slate-400">
                No featured property this week.{" "}
                <Link
                  href="/properties"
                  className="text-gold-400 hover:underline"
                >
                  Browse listings &rarr;
                </Link>
              </p>
            ))}
        </div>
      </div>
    </section>
  );
}

export default HeroCards;
