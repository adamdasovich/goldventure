"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import LogoMono from "@/components/LogoMono";

const adminNavItems = [
  {
    href: "/admin/store",
    label: "Dashboard",
    icon: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6",
  },
  {
    href: "/admin/store/products",
    label: "Products",
    icon: "M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4",
  },
  {
    href: "/admin/store/orders",
    label: "Orders",
    icon: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01",
  },
  {
    href: "/admin/store/categories",
    label: "Categories",
    icon: "M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z",
  },
  {
    href: "/admin/news-flags",
    label: "News Flags",
    icon: "M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9",
  },
  {
    href: "/admin/news-flags-reports",
    label: "Report Flags",
    icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
  },
];

export default function AdminLayoutClient({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [navOpen, setNavOpen] = useState(false);
  const router = useRouter();
  const { user, isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/auth/login?redirect=" + encodeURIComponent(pathname));
    }
  }, [isLoading, isAuthenticated, router, pathname]);

  useEffect(() => {
    if (
      !isLoading &&
      isAuthenticated &&
      user &&
      !user.is_staff &&
      !user.is_superuser
    ) {
      router.push("/");
    }
  }, [isLoading, isAuthenticated, user, router]);

  /* Close on navigation. React's "adjusting state when a prop changes"
     pattern rather than an effect: setState during render of the same
     component is sanctioned and re-runs before the browser paints, where an
     effect renders the stale value first and then immediately re-renders.
     https://react.dev/learn/you-might-not-need-an-effect */
  const [lastPath, setLastPath] = useState(pathname);
  if (pathname !== lastPath) {
    setLastPath(pathname);
    setNavOpen(false);
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-2 border-gold-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!isAuthenticated || (!user?.is_staff && !user?.is_superuser)) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-slate-100 mb-4">
            Access Denied
          </h1>
          <p className="text-slate-400">
            You need admin privileges to access this area.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 lg:flex">
      {/* Scrim — only below lg, where the sidebar is a drawer */}
      {navOpen && (
        <div
          onClick={() => setNavOpen(false)}
          className="fixed inset-0 bg-black/60 z-30 lg:hidden"
          aria-hidden="true"
        />
      )}

      {/* Sidebar. Fixed w-64 left only 119px of a 375px screen for the
          admin tables, so below lg it slides in over the content instead. */}
      <aside
        id="admin-nav"
        className={`fixed inset-y-0 left-0 z-40 w-64 bg-slate-800 border-r border-slate-700 flex flex-col transition-transform duration-200 motion-reduce:transition-none lg:static lg:translate-x-0 lg:bg-slate-800/50 ${
          navOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Logo */}
        <div className="p-4 border-b border-slate-700">
          <Link href="/" className="flex items-center">
            <LogoMono className="h-8" />
          </Link>
          <p className="text-xs text-slate-500 mt-1">Store Admin</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4">
          <ul className="space-y-1">
            {adminNavItems.map((item) => {
              const isActive =
                pathname === item.href ||
                (item.href !== "/admin/store" &&
                  pathname.startsWith(item.href));
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                      isActive
                        ? "bg-gold-500/20 text-gold-400 border border-gold-500/40"
                        : "text-slate-400 hover:text-slate-200 hover:bg-slate-700/50"
                    }`}
                  >
                    <svg
                      className="w-5 h-5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1.5}
                        d={item.icon}
                      />
                    </svg>
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Back to Store */}
        <div className="p-4 border-t border-slate-700">
          <Link
            href="/store"
            className="flex items-center gap-2 text-sm text-slate-400 hover:text-gold-400 transition-colors"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 19l-7-7m0 0l7-7m-7 7h18"
              />
            </svg>
            Back to Store
          </Link>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 min-w-0 overflow-auto">
        {/* Top Bar */}
        <header className="bg-slate-800/30 border-b border-slate-700 px-3 sm:px-6 py-3 sm:py-4">
          <div className="flex items-center justify-between gap-3">
            <button
              onClick={() => setNavOpen((o) => !o)}
              aria-label={navOpen ? "Close admin menu" : "Open admin menu"}
              aria-expanded={navOpen}
              aria-controls="admin-nav"
              className="lg:hidden -ml-2 p-3 rounded-lg text-slate-300 hover:text-gold-400 hover:bg-slate-700/50"
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
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
            <h1 className="text-lg font-semibold text-slate-100 flex-1 min-w-0 truncate">
              Store Management
            </h1>
            <div className="flex items-center gap-4">
              <span className="text-sm text-slate-400">
                {user?.full_name || user?.username}
              </span>
              <div className="w-8 h-8 rounded-full bg-gold-500/20 flex items-center justify-center">
                <span className="text-gold-400 text-sm font-medium">
                  {(user?.full_name || user?.username || "A")[0].toUpperCase()}
                </span>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="p-3 sm:p-6">{children}</div>
      </main>
    </div>
  );
}
