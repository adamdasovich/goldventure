"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import Link from "next/link";
import Image from "next/image";
import ChatInterface from "@/components/ChatInterface";
import NewsArticles from "@/components/NewsArticles";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import LogoMono from "@/components/LogoMono";
import HeroCards from "@/components/HeroCards";
import { LoginModal, RegisterModal } from "@/components/auth";
import { useAuth } from "@/contexts/AuthContext";
import { CartButton } from "@/components/store";
import MetalsTicker from "@/components/MetalsTicker";

/* ─── Navigation ───
   Top-level nav is kept to four items. Secondary destinations live in the
   "Tools" dropdown so a first-time visitor isn't faced with 11 choices. */
const PRIMARY_NAV = [
  { href: "/companies", label: "Companies" },
  { href: "/properties", label: "Prospector's Exchange" },
  { href: "/guides", label: "Guides" },
];

const TOOLS_MENU = [
  {
    href: "/investor-tools",
    label: "Investor Tools",
    desc: "10 screeners & analyzers",
  },
  {
    href: "/metals",
    label: "Metals Prices",
    desc: "Live gold, silver & more",
  },
  {
    href: "/closed-financings",
    label: "Financing Tracker",
    desc: "Private placements & deals",
  },
  {
    href: "/financial-hub",
    label: "Financial Hub",
    desc: "Invest in private deals",
  },
  {
    href: "/store",
    label: "Store",
    desc: "Reports & field gear",
  },
];

/* ─── Feature cards ───
   `badge: "Live"` marks the real-time, WebSocket-powered features so they
   visibly stand out in the grid. */
const FEATURES: {
  title: string;
  description: string;
  icon: string;
  href: string;
  badge?: string;
}[] = [
  {
    title: "Company Database",
    description:
      "Profiles for 500+ junior miners — projects, resource estimates, financing history, and news, all in one place.",
    icon: "M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4",
    href: "/companies",
  },
  {
    title: "Live Company Forums",
    badge: "Live",
    description:
      "Every company has a real-time discussion board. Investors and management talk directly, and new posts appear instantly — like a group chat.",
    icon: "M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.86 9.86 0 01-4-.8L3 21l1.8-4A8.84 8.84 0 013 12c0-4.418 4.03-8 9-8s9 3.582 9 8z",
    href: "/companies",
  },
  {
    title: "Speaking Events",
    badge: "Live",
    description:
      "Join live online presentations from company management. Watch by video, ask questions, upvote the best ones, and react in real time.",
    icon: "M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z",
    href: "/companies",
  },
  {
    title: "Prospector's Exchange",
    badge: "Live",
    description:
      "A marketplace of mineral properties for sale. Message owners directly through private, real-time chat to negotiate deals.",
    icon: "M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z",
    href: "/properties",
  },
  {
    title: "15 Investor Tools",
    description:
      "Screeners and calculators — rank companies by ore grade, compare them side by side, scan drill results, and more.",
    icon: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z",
    href: "/investor-tools",
  },
  {
    title: "Financing Tracker",
    description:
      "See which companies are raising capital — active and recently closed private placements and deals across the sector.",
    icon: "M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
    href: "/closed-financings",
  },
  {
    title: "Real-Time Metals",
    description:
      "Live prices for gold, silver, platinum, and palladium, plus the day's top-moving mining stocks.",
    icon: "M13 7h8m0 0v8m0-8l-8 8-4-4-6 6",
    href: "/metals",
  },
];

interface HomeClientProps {
  initialArticles?: any[];
}

export default function HomeClient({ initialArticles }: HomeClientProps) {
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [toolsOpen, setToolsOpen] = useState(false);
  const [isVibrating, setIsVibrating] = useState(false);
  const { user, logout } = useAuth();
  const newsSectionRef = useRef<HTMLElement>(null);
  const chatSectionRef = useRef<HTMLElement>(null);
  const toolsRef = useRef<HTMLDivElement>(null);

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

  // Close mobile menu on resize
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1024) setMobileMenuOpen(false);
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Lock body scroll when mobile menu is open
  useEffect(() => {
    document.body.style.overflow = mobileMenuOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileMenuOpen]);

  // Close the Tools dropdown when clicking outside it
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (toolsRef.current && !toolsRef.current.contains(e.target as Node)) {
        setToolsOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <div className="min-h-screen">
      {/* ════════ Navigation ════════ */}
      <nav
        className="glass-nav sticky top-0 z-50"
        role="navigation"
        aria-label="Main navigation"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-20 lg:h-24">
            <Link
              href="/"
              className="flex items-center space-x-3 flex-shrink-0"
            >
              <LogoMono className="h-12 lg:h-16" />
            </Link>

            {/* Desktop Nav */}
            <div className="hidden lg:flex items-center space-x-1">
              {PRIMARY_NAV.map((link) => (
                <Link key={link.href} href={link.href}>
                  <Button variant="ghost" size="sm">
                    {link.label}
                  </Button>
                </Link>
              ))}

              {/* Tools dropdown */}
              <div className="relative" ref={toolsRef}>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setToolsOpen((o) => !o)}
                  aria-expanded={toolsOpen ? "true" : "false"}
                  aria-haspopup="true"
                >
                  Tools
                  <svg
                    className={`w-4 h-4 ml-1 transition-transform ${
                      toolsOpen ? "rotate-180" : ""
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </Button>
                {toolsOpen && (
                  <div className="absolute left-0 mt-2 w-64 bg-slate-800/95 border border-slate-700/50 rounded-xl shadow-2xl backdrop-blur-sm overflow-hidden">
                    {TOOLS_MENU.map((item) => (
                      <Link
                        key={item.href}
                        href={item.href}
                        onClick={() => setToolsOpen(false)}
                        className="block px-4 py-3 hover:bg-gold-500/10 transition-colors"
                      >
                        <p className="text-sm font-medium text-slate-200">
                          {item.label}
                        </p>
                        <p className="text-xs text-slate-400">{item.desc}</p>
                      </Link>
                    ))}
                  </div>
                )}
              </div>

              <Link href="/pricing">
                <Button variant="ghost" size="sm">
                  Pricing
                </Button>
              </Link>

              {user && (
                <Link href="/dashboard">
                  <Button variant="ghost" size="sm">
                    Dashboard
                  </Button>
                </Link>
              )}

              <CartButton />

              {user ? (
                <div className="flex items-center space-x-3 ml-3 pl-3 border-l border-slate-700">
                  <span className="text-sm text-slate-300">
                    {user.full_name || user.username}
                  </span>
                  <Button variant="ghost" size="sm" onClick={logout}>
                    Logout
                  </Button>
                </div>
              ) : (
                <div className="flex items-center space-x-2 ml-3 pl-3 border-l border-slate-700">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowLogin(true)}
                  >
                    Login
                  </Button>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => setShowRegister(true)}
                  >
                    Register
                  </Button>
                </div>
              )}
            </div>

            {/* Mobile: cart + hamburger */}
            <div className="flex items-center space-x-2 lg:hidden">
              <CartButton />
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="p-2 rounded-lg text-slate-300 hover:text-gold-400 hover:bg-slate-800/50 transition-colors"
                aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
                aria-expanded={mobileMenuOpen}
              >
                {mobileMenuOpen ? (
                  <svg
                    className="w-6 h-6"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                ) : (
                  <svg
                    className="w-6 h-6"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 6h16M4 12h16M4 18h16"
                    />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="lg:hidden mobile-nav-overlay border-t border-slate-700/50 animate-slide-in-up">
            <div className="px-4 py-4 space-y-1">
              {PRIMARY_NAV.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className="block px-4 py-3 rounded-lg text-slate-300 hover:text-gold-400 hover:bg-slate-800/50 transition-colors"
                >
                  {link.label}
                </Link>
              ))}

              <p className="px-4 pt-3 pb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
                Tools
              </p>
              {TOOLS_MENU.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className="block px-4 py-3 rounded-lg text-slate-300 hover:text-gold-400 hover:bg-slate-800/50 transition-colors"
                >
                  {item.label}
                </Link>
              ))}

              <Link
                href="/pricing"
                onClick={() => setMobileMenuOpen(false)}
                className="block px-4 py-3 mt-1 rounded-lg text-gold-400 hover:bg-slate-800/50 transition-colors"
              >
                Pricing
              </Link>
              {user && (
                <Link
                  href="/dashboard"
                  onClick={() => setMobileMenuOpen(false)}
                  className="block px-4 py-3 rounded-lg text-slate-300 hover:text-gold-400 hover:bg-slate-800/50 transition-colors"
                >
                  Dashboard
                </Link>
              )}

              <div className="pt-3 mt-3 border-t border-slate-700/50 space-y-2">
                {user ? (
                  <>
                    <p className="px-4 text-sm text-slate-400">
                      Welcome, {user.full_name || user.username}
                    </p>
                    <button
                      onClick={() => {
                        logout();
                        setMobileMenuOpen(false);
                      }}
                      className="block w-full text-left px-4 py-3 rounded-lg text-slate-300 hover:text-gold-400 hover:bg-slate-800/50 transition-colors"
                    >
                      Logout
                    </button>
                  </>
                ) : (
                  <div className="flex gap-2 px-4">
                    <Button
                      variant="ghost"
                      size="md"
                      className="flex-1"
                      onClick={() => {
                        setShowLogin(true);
                        setMobileMenuOpen(false);
                      }}
                    >
                      Login
                    </Button>
                    <Button
                      variant="primary"
                      size="md"
                      className="flex-1"
                      onClick={() => {
                        setShowRegister(true);
                        setMobileMenuOpen(false);
                      }}
                    >
                      Register
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </nav>

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

          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4 text-gradient-gold animate-fade-in leading-tight pb-1">
            Research junior mining stocks in minutes, not hours
          </h1>
          <p className="text-base sm:text-lg text-slate-300 animate-slide-in-up mb-6">
            Profiles, financials, and news for {stats.companies}+ small gold,
            silver, and critical-minerals companies — plus an AI assistant that
            answers your questions instantly.
          </p>

          {/* Primary CTAs */}
          <div className="flex flex-col sm:flex-row flex-wrap gap-3 justify-center animate-slide-in-up">
            <Button
              variant="primary"
              size="md"
              onClick={scrollToFeatures}
              className="cta-glow w-full sm:w-auto"
            >
              Platform Features
            </Button>
            <Link href="/companies">
              <Button
                variant="secondary"
                size="sm"
                className="w-full sm:w-auto"
              >
                Explore Companies
              </Button>
            </Link>
            <Button
              variant="secondary"
              size="sm"
              onClick={scrollToChat}
              className="w-full sm:w-auto"
            >
              AI Assistant
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={scrollToHappening}
              className="w-full sm:w-auto"
            >
              Happening Now
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={scrollToNews}
              className="w-full sm:w-auto"
            >
              Mining News
            </Button>
            <Link href="/open-financings">
              <Button
                variant="secondary"
                size="sm"
                className="w-full sm:w-auto"
              >
                Open Financings
              </Button>
            </Link>
            <Link href="/closed-financings">
              <Button
                variant="secondary"
                size="sm"
                className="w-full sm:w-auto"
              >
                Closed Financings
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* ════════ AI Chat Interface Section ════════ */}
      <section
        ref={chatSectionRef}
        id="chat-section"
        className="py-16 md:py-20 px-4 sm:px-6 lg:px-8 bg-gradient-slate"
      >
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-gradient-gold mb-4">
              Ask Anything About Mining Companies
            </h2>
            <p className="text-slate-300 text-lg max-w-2xl mx-auto">
              Plain-English answers about exploration projects, resource
              reports, property listings, and company financials.
            </p>
          </div>

          <ChatInterface />
        </div>
      </section>

      {/* Section Divider */}
      <div className="section-divider"></div>

      {/* ════════ Features Showcase ════════ */}
      <section
        id="features"
        className="py-16 md:py-20 px-4 sm:px-6 lg:px-8 scroll-mt-24"
      >
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <Badge variant="gold" className="mb-4">
              Platform Features
            </Badge>
            <h2 className="text-3xl sm:text-4xl font-bold text-gradient-gold mb-4">
              Everything You Need for Mining Research
            </h2>
            <p className="text-slate-300 text-lg max-w-2xl mx-auto">
              From AI research and live company forums to real-time market data,
              our platform gives you the edge in junior mining investment.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map((feature, i) => (
              <Link key={i} href={feature.href} className="group block">
                <div
                  className={`glass-card feature-card rounded-xl p-5 h-full ${
                    feature.badge
                      ? "border-gold-500/40 ring-1 ring-gold-500/20"
                      : ""
                  }`}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-gold-500/15 border border-gold-500/30 feature-icon">
                      <svg
                        className="w-5 h-5 text-gold-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        aria-hidden="true"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d={feature.icon}
                        />
                      </svg>
                    </div>
                    {feature.badge && (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gold-500/15 border border-gold-500/40 text-xs font-semibold text-gold-400">
                        <span className="w-1.5 h-1.5 bg-gold-400 rounded-full animate-pulse"></span>
                        {feature.badge}
                      </span>
                    )}
                  </div>
                  <h3 className="text-lg font-semibold text-slate-200 group-hover:text-gold-400 transition-colors mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-sm text-slate-400 leading-relaxed">
                    {feature.description}
                  </p>
                </div>
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
        className="py-16 md:py-20 px-4 sm:px-6 lg:px-8 bg-gradient-slate"
      >
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <Badge variant="slate" className="mb-4">
              Updated 3x Daily
            </Badge>
            <h2 className="text-3xl sm:text-4xl font-bold text-gradient-gold mb-4">
              Latest Mining News
            </h2>
            <p className="text-slate-300 text-lg max-w-2xl mx-auto">
              Exploration discoveries, market updates, and industry developments
              across gold, silver, lithium, copper &amp; critical minerals.
            </p>
          </div>

          <div className="backdrop-blur-sm bg-slate-800/30 border border-slate-700/50 rounded-xl p-6">
            <NewsArticles
              initialLimit={8}
              showLoadMore={true}
              initialArticles={initialArticles?.slice(0, 8)}
            />
          </div>
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
                  className="text-sm text-slate-400 hover:text-gold-400 transition-colors"
                >
                  {link.label}
                </Link>
              ))}
              <Link
                href="/pricing"
                className="text-sm text-slate-400 hover:text-gold-400 transition-colors"
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
                className="p-2 rounded-lg text-slate-400 hover:text-gold-400 hover:bg-slate-800/50 transition-colors"
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
                className="p-2 rounded-lg text-slate-400 hover:text-gold-400 hover:bg-slate-800/50 transition-colors"
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
                className="p-2 rounded-lg text-slate-400 hover:text-gold-400 hover:bg-slate-800/50 transition-colors"
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
                className="hover:text-gold-400 transition-colors"
              >
                About
              </Link>
              <Link
                href="/glossary"
                className="hover:text-gold-400 transition-colors"
              >
                Glossary
              </Link>
              <Link
                href="/guides"
                className="hover:text-gold-400 transition-colors"
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
