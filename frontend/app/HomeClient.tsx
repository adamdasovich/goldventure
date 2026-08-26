"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import Link from "next/link";
import Image from "next/image";
import ChatInterface from "@/components/ChatInterface";
import NewsArticles from "@/components/NewsArticles";
import { Button } from "@/components/ui/Button";
import LogoMono from "@/components/LogoMono";
import SiteHeader, { PRIMARY_NAV, TOOLS_MENU } from "@/components/SiteHeader";
import HeroCards from "@/components/HeroCards";
import SectionHeading from "@/components/SectionHeading";
import { LoginModal, RegisterModal } from "@/components/auth";
import { useAuth } from "@/contexts/AuthContext";
import MetalsTicker from "@/components/MetalsTicker";

/* ─── Platform directory ───
   Was eight description cards with icons. The titles carry the meaning and
   the detail lives on the destination pages, so only the title, the link and
   the live marker survive. */
const FEATURES: { title: string; href: string; badge?: string }[] = [
  { title: "Weekly Financial Snapshot", href: "/reports/weekly", badge: "New" },
  { title: "Company Database", href: "/companies" },
  { title: "Live Company Forums", href: "/companies", badge: "Live" },
  { title: "Speaking Events", href: "/companies", badge: "Live" },
  { title: "Prospector's Exchange", href: "/properties", badge: "Live" },
  { title: "15 Investor Tools", href: "/investor-tools" },
  { title: "Financing Tracker", href: "/closed-financings" },
  { title: "Real-Time Metals", href: "/metals" },
];

/* ─── Secondary hero links ───
   These used to be six more full-width primary-looking buttons. They are
   jump links, so they belong in a row, not the CTA stack. */
type ScrollAction = "chat" | "happening" | "news";

const SECONDARY_LINKS: {
  label: string;
  href?: string;
  action?: ScrollAction;
}[] = [
  { label: "AI Assistant", action: "chat" },
  { label: "Happening Now", action: "happening" },
  { label: "Mining News", action: "news" },
  { label: "Open Financings", href: "/open-financings" },
  { label: "Closed Financings", href: "/closed-financings" },
  { label: "Weekly Snapshot", href: "/reports/weekly" },
];

const SECONDARY_CHIP =
  "shrink-0 px-4 py-2.5 min-h-11 inline-flex items-center whitespace-nowrap " +
  "rounded-full border border-slate-600 text-slate-300 text-sm transition-colors " +
  "hover:text-gold-400 hover:border-gold-500/50";

interface HomeClientProps {
  initialArticles?: any[];
}

export default function HomeClient({ initialArticles }: HomeClientProps) {
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [isVibrating, setIsVibrating] = useState(false);
  const { user } = useAuth();
  const newsSectionRef = useRef<HTMLElement>(null);
  const chatSectionRef = useRef<HTMLElement>(null);

  // Platform stats
  const [stats, setStats] = useState({
    companies: 500,
    projects: 0,
    financings: 0,
    news_articles: 0,
  });

  useEffect(() => {
    fetch(
      `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"}/platform-stats/`,
    )
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => data && setStats(data))
      .catch(() => {});
  }, []);

  const scrollToChat = () => {
    chatSectionRef.current?.scrollIntoView({ behavior: "smooth" });
  };

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

  const scrollToHappening = () => {
    document
      .getElementById("happening-now")
      ?.scrollIntoView({ behavior: "smooth" });
  };

  const scrollToFeatures = () => {
    document.getElementById("features")?.scrollIntoView({ behavior: "smooth" });
  };

  const scrollToNews = () => {
    newsSectionRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const SCROLL_ACTIONS: Record<ScrollAction, () => void> = {
    chat: scrollToChat,
    happening: scrollToHappening,
    news: scrollToNews,
  };

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
      <section className="relative py-10 md:py-16 px-4 sm:px-6 lg:px-8 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-[#0a0e1a] via-slate-900 to-slate-800"></div>
        <div className="absolute inset-0 hero-grid"></div>
        <div
          className="absolute inset-0 animate-subtle-pulse"
          style={{
            backgroundImage:
              "radial-gradient(circle at 30% 40%, rgba(212, 161, 42, 0.15) 0%, transparent 50%), radial-gradient(circle at 70% 60%, rgba(184, 134, 11, 0.08) 0%, transparent 40%)",
          }}
        ></div>
        <div className="hero-particles"></div>

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

          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-3 text-gradient-gold animate-fade-in leading-tight text-balance pb-1">
            Junior mining research, in minutes
          </h1>
          <p className="text-base sm:text-lg text-slate-300 animate-slide-in-up mb-6 max-w-xl mx-auto">
            Profiles, financials and news on {stats.companies}+ juniors, with an
            AI assistant that answers questions about any of them.
          </p>

          {/* Two primary CTAs. There were eight, all the same weight and all
              full width on a phone — about 780px of stacked buttons before a
              visitor saw any content, and no signal about where to start. */}
          <div className="flex flex-col sm:flex-row gap-3 justify-center animate-slide-in-up">
            <Button
              variant="primary"
              size="md"
              onClick={scrollToFeatures}
              className="cta-glow w-full sm:w-auto"
            >
              Platform Features
            </Button>
            <Link href="/companies" className="w-full sm:w-auto">
              <Button variant="secondary" size="md" className="w-full">
                Explore Companies
              </Button>
            </Link>
          </div>

          {/* The other six are jump links, not calls to action, so they read
              as a compact row: swipeable below sm, wrapped above. */}
          <div className="mt-5 animate-slide-in-up">
            <div className="flex gap-2 overflow-x-auto scrollbar-none sm:flex-wrap sm:justify-center sm:overflow-visible -mx-4 px-4 sm:mx-0 sm:px-0">
              {SECONDARY_LINKS.map((item) =>
                item.href ? (
                  <Link
                    key={item.label}
                    href={item.href}
                    className={SECONDARY_CHIP}
                  >
                    {item.label}
                  </Link>
                ) : (
                  <button
                    key={item.label}
                    type="button"
                    onClick={SCROLL_ACTIONS[item.action!]}
                    className={SECONDARY_CHIP}
                  >
                    {item.label}
                  </button>
                ),
              )}
            </div>
          </div>
        </div>
      </section>

      {/* ════════ AI Chat Interface Section ════════ */}
      {/* The section heading said the same thing as the chat card's own title
          and description directly beneath it. The card is self-evidently a
          chatbot; it does not need announcing twice. */}
      <section
        ref={chatSectionRef}
        id="chat-section"
        className="py-10 md:py-14 px-4 sm:px-6 lg:px-8 bg-gradient-slate"
      >
        <div className="max-w-7xl mx-auto">
          <ChatInterface />
        </div>
      </section>

      {/* Section Divider */}
      <div className="section-divider"></div>

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

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-3">
            {FEATURES.map((feature) => (
              <Link
                key={feature.href + feature.title}
                href={feature.href}
                className="group flex items-center justify-between gap-2 rounded-lg border border-slate-700/70 bg-slate-800/40 px-3 py-3 min-h-16 transition-colors hover:border-gold-500/40 hover:bg-slate-800/70"
              >
                <span className="text-sm font-medium text-slate-200 group-hover:text-gold-400 transition-colors">
                  {feature.title}
                </span>
                {feature.badge && (
                  <span className="shrink-0 self-start rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-gold-400 bg-gold-500/10">
                    {feature.badge}
                  </span>
                )}
              </Link>
            ))}
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

      {/* ════════ Pricing CTA Section ════════ */}
      <section className="py-16 md:py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-2xl sm:text-3xl font-bold text-gradient-gold mb-4">
            Start Free — No Card Required
          </h2>
          <p className="text-slate-300 mb-6">
            5 AI questions a day and 2 investor tools, free forever. Upgrade for
            unlimited access, all 10 tools, and full data.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            {!user && (
              <Button
                variant="primary"
                size="lg"
                onClick={() => setShowRegister(true)}
                className="cta-glow w-full sm:w-auto"
              >
                Create Free Account
              </Button>
            )}
            <Link href="/pricing">
              <Button
                variant={user ? "primary" : "secondary"}
                size="lg"
                className={`w-full sm:w-auto ${user ? "cta-glow" : ""}`}
              >
                View Plans &amp; Pricing
              </Button>
            </Link>
          </div>
        </div>
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
