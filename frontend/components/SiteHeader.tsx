"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import LogoMono from "@/components/LogoMono";
import { Button } from "@/components/ui/Button";
import { CartButton } from "@/components/store";
import { LoginModal, RegisterModal } from "@/components/auth";
import { useAuth } from "@/contexts/AuthContext";

export interface NavLink {
  href: string;
  label: string;
}

export interface ToolsLink extends NavLink {
  desc: string;
}

/* Top-level nav is kept to three items. Secondary destinations live in the
   "Tools" dropdown so a first-time visitor isn't faced with 11 choices. */
export const PRIMARY_NAV: NavLink[] = [
  { href: "/companies", label: "Companies" },
  { href: "/properties", label: "Prospector's Exchange" },
  { href: "/guides", label: "Guides" },
];

export const TOOLS_MENU: ToolsLink[] = [
  {
    href: "/investor-tools",
    label: "Investor Tools",
    desc: "10 screeners & analyzers",
  },
  { href: "/metals", label: "Metals Prices", desc: "Live gold, silver & more" },
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
  { href: "/store", label: "Store", desc: "Reports & field gear" },
];

export interface SiteHeaderProps {
  links?: NavLink[];
  toolsMenu?: ToolsLink[];
  /** Route that should render as the active item, e.g. "/companies". */
  active?: string;
  /** Signed-in-only destinations for the current area (Watchlist, Inbox). */
  userLinks?: NavLink[];
  /**
   * Pages that trigger login from elsewhere on the page (a watch button, a
   * gated panel) pass their own handlers and keep owning the modals. Omit
   * both and the header manages its own.
   */
  onLoginClick?: () => void;
  onRegisterClick?: () => void;
}

/**
 * The single navigation header for the whole site.
 *
 * Every page used to hand-roll this as one unbreakable flex row, which
 * overflowed the viewport by 60-460px on a phone and pushed Login and
 * Register off-screen. Below `lg` the links collapse into a panel behind a
 * 44px trigger; above it, nothing about the desktop layout changed.
 */
export default function SiteHeader({
  links = PRIMARY_NAV,
  toolsMenu = TOOLS_MENU,
  active,
  userLinks = [],
  onLoginClick,
  onRegisterClick,
}: SiteHeaderProps) {
  const { user, logout } = useAuth();
  const pathname = usePathname();

  const [menuOpen, setMenuOpen] = useState(false);
  const [toolsOpen, setToolsOpen] = useState(false);
  const toolsRef = useRef<HTMLDivElement>(null);

  // Only used when the page didn't pass its own handlers.
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const selfManaged = !onLoginClick && !onRegisterClick;

  const openLogin = onLoginClick ?? (() => setShowLogin(true));
  const openRegister = onRegisterClick ?? (() => setShowRegister(true));

  // The panel is display-toggled, not unmounted, on a client-side route
  // change — close it so the next page doesn't open behind an open menu.
  useEffect(() => {
    setMenuOpen(false);
    setToolsOpen(false);
  }, [pathname]);

  // Crossing into desktop leaves the panel orphaned; drop it.
  useEffect(() => {
    const onResize = () => {
      if (window.innerWidth >= 1024) setMenuOpen(false);
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  useEffect(() => {
    if (!menuOpen) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [menuOpen]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (toolsRef.current && !toolsRef.current.contains(e.target as Node)) {
        setToolsOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const closeMenu = () => setMenuOpen(false);

  return (
    <>
      <nav
        className="glass-nav sticky top-0 z-50"
        role="navigation"
        aria-label="Main navigation"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 lg:h-24">
            <Link href="/" className="flex items-center shrink-0 min-h-11">
              <LogoMono className="h-10 lg:h-14" />
            </Link>

            {/* ── Desktop ── */}
            <div className="hidden lg:flex items-center space-x-1">
              {links.map((link) => (
                <Link key={link.href} href={link.href}>
                  <Button
                    variant={active === link.href ? "primary" : "ghost"}
                    size="sm"
                  >
                    {link.label}
                  </Button>
                </Link>
              ))}

              {toolsMenu.length > 0 && (
                <div className="relative" ref={toolsRef}>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setToolsOpen((o) => !o)}
                    aria-expanded={toolsOpen}
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
                      {toolsMenu.map((item) => (
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
              )}

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

              {user &&
                userLinks.map((link) => (
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
                  <Button variant="ghost" size="sm" onClick={openLogin}>
                    Login
                  </Button>
                  <Button variant="primary" size="sm" onClick={openRegister}>
                    Register
                  </Button>
                </div>
              )}
            </div>

            {/* ── Mobile: cart + trigger ── */}
            <div className="flex items-center gap-1 lg:hidden">
              <CartButton />
              <button
                onClick={() => setMenuOpen((o) => !o)}
                className="-mr-2 p-3 rounded-lg text-slate-300 hover:text-gold-400 hover:bg-slate-800/50 transition-colors"
                aria-label={menuOpen ? "Close menu" : "Open menu"}
                aria-expanded={menuOpen}
                aria-controls="site-menu"
              >
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
                    d={
                      menuOpen
                        ? "M6 18L18 6M6 6l12 12"
                        : "M4 6h16M4 12h16M4 18h16"
                    }
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* ── Mobile panel ── */}
        {menuOpen && (
          <div
            id="site-menu"
            className="lg:hidden mobile-nav-overlay border-t border-slate-700/50 animate-slide-in-up"
          >
            <div className="px-4 py-4 space-y-1 max-h-[calc(100dvh-4rem)] overflow-y-auto overscroll-contain">
              {links.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={closeMenu}
                  className="block px-4 py-3 rounded-lg text-slate-300 hover:text-gold-400 hover:bg-slate-800/50 transition-colors"
                >
                  {link.label}
                </Link>
              ))}

              {toolsMenu.length > 0 && (
                <>
                  <p className="px-4 pt-3 pb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Tools
                  </p>
                  {toolsMenu.map((item) => (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={closeMenu}
                      className="block px-4 py-3 rounded-lg text-slate-300 hover:text-gold-400 hover:bg-slate-800/50 transition-colors"
                    >
                      {item.label}
                    </Link>
                  ))}
                </>
              )}

              <Link
                href="/pricing"
                onClick={closeMenu}
                className="block px-4 py-3 mt-1 rounded-lg text-gold-400 hover:bg-slate-800/50 transition-colors"
              >
                Pricing
              </Link>

              {user && (
                <Link
                  href="/dashboard"
                  onClick={closeMenu}
                  className="block px-4 py-3 rounded-lg text-slate-300 hover:text-gold-400 hover:bg-slate-800/50 transition-colors"
                >
                  Dashboard
                </Link>
              )}

              {user &&
                userLinks.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    onClick={closeMenu}
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
                        closeMenu();
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
                        openLogin();
                        closeMenu();
                      }}
                    >
                      Login
                    </Button>
                    <Button
                      variant="primary"
                      size="md"
                      className="flex-1"
                      onClick={() => {
                        openRegister();
                        closeMenu();
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

      {selfManaged && showLogin && (
        <LoginModal
          onClose={() => setShowLogin(false)}
          onSwitchToRegister={() => {
            setShowLogin(false);
            setShowRegister(true);
          }}
        />
      )}
      {selfManaged && showRegister && (
        <RegisterModal
          onClose={() => setShowRegister(false)}
          onSwitchToLogin={() => {
            setShowRegister(false);
            setShowLogin(true);
          }}
        />
      )}
    </>
  );
}
