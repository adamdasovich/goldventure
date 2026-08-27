"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import Link from "next/link";
import Image from "next/image";
import ChatLauncher from "@/components/ChatLauncher";
import { useAssistant } from "@/contexts/AssistantContext";
import NewsArticles from "@/components/NewsArticles";
import LogoMono from "@/components/LogoMono";
import SiteHeader, { PRIMARY_NAV, TOOLS_MENU } from "@/components/SiteHeader";
import HeroCards from "@/components/HeroCards";
import SectionHeading from "@/components/SectionHeading";
import PlatformMenu, { type PlatformLink } from "@/components/PlatformMenu";
import { FreeAccountCTA } from "@/components/FreeAccountCTA";
import { LoginModal, RegisterModal } from "@/components/auth";
import MetalsTicker from "@/components/MetalsTicker";
import { AVAILABLE_COUNT } from "@/app/investor-tools/tools";

/* ─── Platform directory ───
   Was eight description cards with icons. The titles carry the meaning and
   the detail lives on the destination pages, so only the title, the link and
   the live marker survive. */
// Counted from the tool catalogue, never by hand. This said "15" while 19 were
// live — the same drift that put stale counts in the sitemap and the pricing
// table, and that had /companies advertising 500+ companies against a database
// of 396.
const FEATURES: PlatformLink[] = [
  { group: "Financings", title: "Participate in Open Financings", href: "/open-financings", badge: "Live" },
  { group: "Financings", title: "Closed Financings Archive", href: "/closed-financings" },
  { group: "Financings", title: "Weekly Financial Snapshot", href: "/reports/weekly", badge: "New" },
  { group: "Research", title: "Company Database", href: "/companies" },
  { group: "Research", title: "Unlimited AI Company Research", href: "/companies" },
  { group: "Research", title: `${AVAILABLE_COUNT} Investor Tools`, href: "/investor-tools" },
  { group: "Research", title: "Your Daily Briefing", href: "/daily-briefing" },
  { group: "Live", title: "Live Company Forums", href: "/companies", badge: "Live" },
  { group: "Live", title: "Speaking Events", href: "/companies", badge: "Live" },
  // Unbadged: 0 listings on 2026-08-26, and a "Live" badge on an empty
  // marketplace sends people to an empty room.
  { group: "Live", title: "Prospector's Exchange", href: "/properties" },
  { group: "Market", title: "Real-Time Metals", href: "/metals" },
];

interface HomeClientProps {
  initialArticles?: any[];
}

export default function HomeClient({ initialArticles }: HomeClientProps) {
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [isVibrating, setIsVibrating] = useState(false);
  /* One assistant for the site, provided by ClientLayout — the header opens
     the same instance from every page. */
  const { open: openChat } = useAssistant();
  const newsSectionRef = useRef<HTMLElement>(null);

  /* Platform stats. These render server-side and on first paint, so they are
     seeded with true floors rather than zeros — /platform-stats/ currently
     reports 396 / 1358 / 297 / 1920, and the live values replace these within
     a second. Zeros here showed three em-dashes on the prerender. */
  const [stats, setStats] = useState({
    companies: 390,
    projects: 1300,
    financings: 290,
    news_articles: 1900,
  });

  useEffect(() => {
    fetch(
      `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"}/platform-stats/`,
    )
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => data && setStats(data))
      .catch(() => {});
  }, []);

  // Socrates easter egg — click the mascot for a fart sound + shimmy
  const handleSocratesFart = useCallback(() => {
    if (isVibrating) return;
    setIsVibrating(true);

    try {
      const audio = new Audio("/sounds/fart.mp3");
      audio.play();
    } catch {
      // Audio not supported
    }

    setTimeout(() => setIsVibrating(false), 1200);
  }, [isVibrating]);

  return (
    <div className="min-h-screen">
      {/* ════════ Navigation ════════ */}
      <SiteHeader
        onLoginClick={() => setShowLogin(true)}
        onRegisterClick={() => setShowRegister(true)}
      />

      {/* Auth Modals */}
      {showLogin && (
        <LoginModal
          onClose={() => setShowLogin(false)}
          onSwitchToRegister={() => {
            setShowLogin(false);
            setShowRegister(true);
          }}
        />
      )}
      {showRegister && (
        <RegisterModal
          onClose={() => setShowRegister(false)}
          onSwitchToLogin={() => {
            setShowRegister(false);
            setShowLogin(true);
          }}
        />
      )}

      {/* ════════ Metals Price Ticker ════════ */}
      <div className="bg-slate-900/80 border-b border-slate-700/30 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto py-2">
          <MetalsTicker />
        </div>
      </div>

      {/* ════════ Hero Section ════════ */}
      {/* Four stacked decorative layers came off here — a grid overlay, a
          pulsing radial wash and a particle field. Depth now comes from
          spacing and scale, which is what the 2026 reference work does. */}
      <section className="relative py-10 md:py-16 px-4 sm:px-6 lg:px-8 overflow-hidden">
        <div className="absolute inset-0 bg-linear-to-b from-[#0a0e1a] via-slate-900 to-slate-900"></div>

        <div className="relative max-w-3xl mx-auto text-center">
          {/* Socrates mascot */}
          <button
            onClick={handleSocratesFart}
            className="relative inline-block cursor-pointer bg-transparent border-0 p-0 mb-4"
            aria-label="Click Socrates the mascot"
          >
            <div className="absolute inset-0 rounded-full bg-gold-500/10 blur-3xl scale-110"></div>
            <Image
              src="/images/socrates-miner.png"
              alt="Socrates, the Junior Mining Intelligence mascot"
              width={280}
              height={280}
              className={`relative w-32 sm:w-40 h-auto mx-auto opacity-90 hover:opacity-100 transition-opacity duration-300 drop-shadow-2xl ${isVibrating ? "animate-vibrate" : ""}`}
              priority
            />
          </button>

          {/* Near-white, not gold gradient. The accent is spent on the
              figures below and the primary CTA, where it means something. */}
          <h1 className="font-display text-xl sm:text-2xl md:text-3xl font-semibold mb-4 text-gold-400 leading-tight text-balance italic tracking-tight">
            Junior mining research, in minutes
          </h1>
          <p className="text-base sm:text-lg md:text-xl text-slate-300 max-w-2xl mx-auto mb-6">
            Profiles, financials and news on {stats.companies} juniors, with an
            AI assistant that answers questions about any of them.
          </p>

          {/* The assistant is the primary action, so it sits in the hero
              rather than a section of its own below the fold. */}
          <ChatLauncher onOpen={openChat} className="mt-2" />

          {/* One thin line of real figures. These were four bordered tiles,
              which is more furniture than four numbers deserve. */}
          <dl className="mt-8 flex flex-wrap items-baseline justify-center gap-x-6 gap-y-2 text-sm">
            {[
              { label: "companies", value: stats.companies },
              { label: "projects", value: stats.projects },
              { label: "financings", value: stats.financings },
              { label: "news items", value: stats.news_articles },
            ].map((s) => (
              <div key={s.label} className="flex items-baseline gap-1.5">
                <dt className="sr-only">{s.label}</dt>
                <dd className="font-mono tabular-nums tracking-tight text-gold-400">
                  {s.value.toLocaleString()}
                </dd>
                <span aria-hidden="true" className="text-slate-500">
                  {s.label}
                </span>
              </div>
            ))}
          </dl>
        </div>
      </section>

      {/* ════════ Features Showcase ════════ */}
      {/* Eight description cards ran to 2,197px on a phone — 3.3 screens of
          feature copy between the chat and the live data people actually come
          back for. The titles carry the meaning on their own, so this is a
          directory: tap through for the detail. */}
      <section
        id="features"
        className="py-10 md:py-14 px-4 sm:px-6 lg:px-8 scroll-mt-24"
      >
        <div className="max-w-5xl mx-auto">
          <SectionHeading title="What&rsquo;s on the platform" />

          <div className="flex justify-center">
            <PlatformMenu links={FEATURES} />
          </div>
        </div>
      </section>

      {/* Section Divider */}
      <div className="section-divider"></div>

      {/* ════════ Live Platform Data (events / financings / property) ════════ */}
      <HeroCards
        onLoginClick={() => setShowLogin(true)}
        onRegisterClick={() => setShowRegister(true)}
      />

      {/* ════════ News Articles Section ════════ */}
      <section
        ref={newsSectionRef}
        id="news-section"
        className="py-10 md:py-14 px-4 sm:px-6 lg:px-8 bg-gradient-slate"
      >
        <div className="max-w-4xl mx-auto">
          <SectionHeading
            eyebrow="Updated 3&times; daily"
            title="Latest mining news"
            description="Discoveries, market moves and industry developments across gold, silver, lithium, copper and critical minerals."
          />

          {/* The articles are already cards; wrapping them in a second bordered
              panel just added a frame around a frame. */}
          <NewsArticles
            initialLimit={5}
            showLoadMore={true}
            initialArticles={initialArticles?.slice(0, 5)}
          />
        </div>
      </section>

      {/* Section Divider */}
      <div className="section-divider"></div>

      {/* ════════ Sign-up CTA ════════ */}
      {/* The banner /companies uses, rather than a section of its own with a
          heading, a paragraph and two large buttons. */}
      <section className="py-10 md:py-14 px-4 sm:px-6 lg:px-8">
        <FreeAccountCTA
          variant="banner"
          className="max-w-3xl mx-auto"
          onRegister={() => setShowRegister(true)}
          onSignIn={() => setShowLogin(true)}
        />
      </section>

      {/* ════════ Footer ════════ */}
      <footer className="glass-nav py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          {/* Top: logo + nav + social */}
          <div className="flex flex-col md:flex-row items-center justify-between gap-8 mb-8">
            <div className="flex items-center">
              <LogoMono className="h-12 lg:h-16" />
            </div>

            <div className="flex flex-wrap gap-4 justify-center">
              {[...PRIMARY_NAV, ...TOOLS_MENU].map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="inline-block py-3 -my-3 text-sm text-slate-400 hover:text-gold-400 transition-colors"
                >
                  {link.label}
                </Link>
              ))}
              <Link
                href="/pricing"
                className="inline-block py-3 -my-3 text-sm text-slate-400 hover:text-gold-400 transition-colors"
              >
                Pricing
              </Link>
            </div>

            {/* Social */}
            <div className="flex space-x-4">
              <a
                href="https://www.linkedin.com/company/juniorminingintelligence"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center min-h-11 min-w-11 rounded-lg text-slate-400 hover:text-gold-400 hover:bg-slate-800/50 transition-colors"
                aria-label="LinkedIn"
              >
                <svg
                  className="w-5 h-5"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
                </svg>
              </a>
              <a
                href="https://twitter.com/JuniorMini82636"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center min-h-11 min-w-11 rounded-lg text-slate-400 hover:text-gold-400 hover:bg-slate-800/50 transition-colors"
                aria-label="X (Twitter)"
              >
                <svg
                  className="w-5 h-5"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                </svg>
              </a>
              <a
                href="https://www.facebook.com/profile.php?id=61586276247045"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center min-h-11 min-w-11 rounded-lg text-slate-400 hover:text-gold-400 hover:bg-slate-800/50 transition-colors"
                aria-label="Facebook"
              >
                <svg
                  className="w-5 h-5"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path
                    fillRule="evenodd"
                    d="M22 12c0-5.523-4.477-10-10-10S2 6.477 2 12c0 4.991 3.657 9.128 8.438 9.878v-6.987h-2.54V12h2.54V9.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V12h2.773l-.443 2.89h-2.33v6.988C18.343 21.128 22 16.991 22 12z"
                    clipRule="evenodd"
                  />
                </svg>
              </a>
            </div>
          </div>

          <div className="section-divider mb-6"></div>

          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-sm text-slate-500">
              &copy; {new Date().getFullYear()} Junior Mining Intelligence. All
              rights reserved.
            </p>
            <div className="flex gap-4 text-sm text-slate-500">
              <Link
                href="/about"
                className="inline-block py-3 -my-3 hover:text-gold-400 transition-colors"
              >
                About
              </Link>
              <Link
                href="/glossary"
                className="inline-block py-3 -my-3 hover:text-gold-400 transition-colors"
              >
                Glossary
              </Link>
              <Link
                href="/guides"
                className="inline-block py-3 -my-3 hover:text-gold-400 transition-colors"
              >
                Guides
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
