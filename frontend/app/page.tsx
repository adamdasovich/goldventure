"use client";

import { useState, useRef, useEffect } from "react";
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

/* ─── Nav link data ─── */
const NAV_LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/companies", label: "Companies" },
  { href: "/properties", label: "Prospector's Exchange" },
  { href: "/glossary", label: "Glossary" },
  { href: "/metals", label: "Metals" },
  { href: "/financial-hub", label: "Financial Hub" },
  { href: "/store", label: "Store" },
];

export default function Home() {
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { user, logout } = useAuth();
  const newsSectionRef = useRef<HTMLElement>(null);
  const chatSectionRef = useRef<HTMLElement>(null);

  const scrollToNews = () => {
    newsSectionRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const scrollToChat = () => {
    chatSectionRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Close mobile menu on resize to desktop
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
            {/* Logo */}
            <Link
              href="/"
              className="flex items-center space-x-3 flex-shrink-0"
            >
              <LogoMono className="h-12 lg:h-16" />
            </Link>

            {/* Desktop Nav Links */}
            <div className="hidden lg:flex items-center space-x-1">
              {NAV_LINKS.map((link) => (
                <Link key={link.href} href={link.href}>
                  <Button variant="ghost" size="sm">
                    {link.label}
                  </Button>
                </Link>
              ))}
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

        {/* Mobile Menu Dropdown */}
        {mobileMenuOpen && (
          <div className="lg:hidden mobile-nav-overlay border-t border-slate-700/50 animate-slide-in-up">
            <div className="px-4 py-4 space-y-1">
              {NAV_LINKS.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className="block px-4 py-3 rounded-lg text-slate-300 hover:text-gold-400 hover:bg-slate-800/50 transition-colors"
                >
                  {link.label}
                </Link>
              ))}
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

      {/* ════════ Hero Section ════════ */}
      <section className="relative py-16 md:py-24 px-4 sm:px-6 lg:px-8 overflow-hidden">
        {/* Layered background effects */}
        <div className="absolute inset-0 bg-gradient-to-b from-[#0a0e1a] via-slate-900 to-slate-800"></div>
        <div className="absolute inset-0 hero-grid"></div>
        <div
          className="absolute inset-0 animate-subtle-pulse"
          style={{
            backgroundImage:
              "radial-gradient(circle at 30% 40%, rgba(212, 161, 42, 0.15) 0%, transparent 50%), radial-gradient(circle at 70% 60%, rgba(184, 134, 11, 0.08) 0%, transparent 40%)",
          }}
        ></div>
        {/* Floating gold particles */}
        <div className="hero-particles"></div>
        <div
          className="absolute top-[15%] left-[10%] w-2 h-2 bg-gold-400/30 rounded-full animate-float"
          style={{ animationDelay: "1s" }}
        ></div>
        <div
          className="absolute top-[40%] right-[12%] w-3 h-3 bg-gold-500/20 rounded-full animate-float-slow"
          style={{ animationDelay: "3s" }}
        ></div>
        <div
          className="absolute bottom-[25%] left-[25%] w-1.5 h-1.5 bg-gold-300/25 rounded-full animate-float"
          style={{ animationDelay: "2s" }}
        ></div>
        <div
          className="absolute top-[70%] right-[30%] w-2 h-2 bg-gold-400/20 rounded-full animate-float-slow"
          style={{ animationDelay: "4s" }}
        ></div>

        <div className="relative max-w-7xl mx-auto">
          {/* Hero content: two-column on desktop */}
          <div className="flex flex-col lg:flex-row items-center gap-8 lg:gap-16 mb-16">
            {/* Left: Text content */}
            <div className="flex-1 text-center lg:text-left">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-gold-500/10 border border-gold-500/20 mb-6 animate-fade-in">
                <span className="w-2 h-2 bg-gold-400 rounded-full animate-pulse"></span>
                <span className="text-sm text-gold-400 font-medium">
                  AI-Powered Mining Research
                </span>
              </div>

              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-6 text-gradient-gold animate-fade-in leading-tight pb-2">
                Junior Mining Intelligence
              </h1>
              <p className="text-lg sm:text-xl text-slate-300 max-w-2xl animate-slide-in-up mb-8">
                Track 500+ TSXV/TSX mining stocks with real-time exploration
                data, NI 43-101 reports, resource estimates, and AI-powered
                project analytics across gold, silver, lithium, copper, rare
                earths & critical minerals.
              </p>

              {/* Primary CTAs */}
              <div className="flex flex-col sm:flex-row gap-3 justify-center lg:justify-start animate-slide-in-up">
                <Link href="/companies">
                  <Button
                    variant="primary"
                    size="lg"
                    className="cta-glow w-full sm:w-auto"
                  >
                    Explore Companies
                  </Button>
                </Link>
                <Button
                  variant="secondary"
                  size="lg"
                  onClick={scrollToChat}
                  className="w-full sm:w-auto"
                >
                  Ask the AI Assistant
                </Button>
              </div>
            </div>

            {/* Right: Socrates Miner + secondary CTAs */}
            <div className="flex-shrink-0 flex flex-col items-center animate-fade-in">
              <div className="relative">
                <div className="absolute inset-0 rounded-full bg-gold-500/10 blur-3xl scale-110"></div>
                <Image
                  src="/images/socrates-miner.png"
                  alt="Junior Mining Intelligence Platform - AI-Powered Mining Stock Analysis"
                  width={280}
                  height={280}
                  className="relative w-48 sm:w-56 lg:w-64 h-auto opacity-90 hover:opacity-100 transition-opacity duration-300 drop-shadow-2xl"
                  priority
                />
              </div>
              <div className="flex flex-wrap gap-2 mt-6 justify-center">
                <Link href="/properties">
                  <Button variant="ghost" size="sm">
                    Prospector&apos;s Exchange
                  </Button>
                </Link>
                <Link href="/guides">
                  <Button variant="ghost" size="sm">
                    Investment Guides
                  </Button>
                </Link>
              </div>
            </div>
          </div>

          {/* Gold accent line */}
          <div className="accent-line-animated mb-12"></div>

          {/* Three Content Cards */}
          <div className="mb-12">
            <HeroCards
              onLoginClick={() => setShowLogin(true)}
              onRegisterClick={() => setShowRegister(true)}
            />
          </div>

          {/* Secondary Navigation Buttons */}
          <div className="flex flex-wrap gap-3 justify-center mb-10">
            <Link href="/closed-financings">
              <Button variant="ghost" size="md">
                Closed Financings
              </Button>
            </Link>
            <Button variant="ghost" size="md" onClick={scrollToNews}>
              Latest News
            </Button>
          </div>

          {/* Compact Feature Cards */}
          <h3 className="text-lg font-semibold text-gradient-gold text-center mb-4">
            Everything You Need for Mining Research
          </h3>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {[
              {
                title: "Claude AI Assistant",
                desc: "Natural language queries for mining data",
                icon: "M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z",
                href: "#chat-section",
              },
              {
                title: "Resource Database",
                desc: "M&I resource tracking & NI 43-101 data",
                icon: "M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4",
                href: "/companies",
              },
              {
                title: "Metals Prices",
                desc: "Real-time precious & battery metals pricing",
                icon: "M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
                href: "/metals",
              },
              {
                title: "Project Analytics",
                desc: "Economic studies & feasibility data",
                icon: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z",
                href: "/dashboard",
              },
            ].map((f, i) => (
              <Link key={i} href={f.href} className="group block">
                <div className="glass-card rounded-xl px-4 py-3 flex items-center gap-3 hover:border-gold-400/30 transition-all">
                  <div className="w-9 h-9 rounded-lg flex-shrink-0 flex items-center justify-center bg-gold-500/15 border border-gold-500/30 group-hover:scale-110 transition-transform">
                    <svg
                      className="w-4.5 h-4.5 text-gold-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d={f.icon}
                      />
                    </svg>
                  </div>
                  <div className="min-w-0">
                    <h3 className="text-sm font-semibold text-slate-200 group-hover:text-gold-400 transition-colors">
                      {f.title}
                    </h3>
                    <p className="text-xs text-slate-500 truncate">{f.desc}</p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* ════════ Chat Interface Section ════════ */}
      <section
        ref={chatSectionRef}
        id="chat-section"
        className="py-16 md:py-20 px-4 sm:px-6 lg:px-8 bg-gradient-slate"
      >
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <Badge variant="gold" className="mb-4">
              Powered by Claude AI
            </Badge>
            <h2 className="text-3xl sm:text-4xl font-bold text-gradient-gold mb-4">
              Ask Anything About Mining Companies
            </h2>
            <p className="text-slate-300 text-lg max-w-2xl mx-auto">
              Natural language access to exploration projects, NI 43-101
              resources, prospector listings, and economic studies. Claude AI
              queries mining data in real-time via MCP servers.
            </p>
          </div>

          <ChatInterface />
        </div>
      </section>

      {/* Section Divider */}
      <div className="section-divider"></div>

      {/* ════════ News Articles Section ════════ */}
      <section
        ref={newsSectionRef}
        id="news-section"
        className="py-16 md:py-20 px-4 sm:px-6 lg:px-8"
      >
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <Badge variant="slate" className="mb-4">
              Updated 3x Daily
            </Badge>
            <h2 className="text-3xl sm:text-4xl font-bold text-gradient-gold mb-4">
              Latest Mining News & Industry Updates
            </h2>
            <p className="text-slate-300 text-lg max-w-2xl mx-auto">
              Track exploration discoveries, TSXV market updates, and industry
              developments across gold, silver, lithium, copper & critical
              minerals.
            </p>
          </div>

          <div className="backdrop-blur-sm bg-slate-800/30 border border-slate-700/50 rounded-xl p-6">
            <NewsArticles initialLimit={50} showLoadMore={true} />
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

            {/* Footer nav links */}
            <div className="flex flex-wrap gap-4 justify-center">
              {NAV_LINKS.slice(0, 5).map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="text-sm text-slate-400 hover:text-gold-400 transition-colors"
                >
                  {link.label}
                </Link>
              ))}
            </div>

            {/* Social Media Links */}
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

          {/* Divider */}
          <div className="section-divider mb-6"></div>

          {/* Bottom: tagline + badges */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-sm text-slate-500">
              AI-Powered Mining Intelligence Platform
            </p>
            <div className="flex gap-2">
              <Badge variant="slate">Next.js</Badge>
              <Badge variant="slate">Django</Badge>
              <Badge variant="slate">PostgreSQL</Badge>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
