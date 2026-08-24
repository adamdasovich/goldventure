"use client";

import Link from "next/link";
import SiteHeader from "@/components/SiteHeader";

export default function AccountLayoutClient({
  children,
}: {
  children: React.ReactNode;
}) {

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Navigation */}
      <SiteHeader
        userLinks={[{ href: "/account/orders", label: "My Orders" }]}
      />

      {/* Breadcrumb */}
      <div className="bg-slate-800/50 border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <nav className="flex items-center space-x-2 text-sm">
            <Link href="/" className="text-slate-400 hover:text-gold-400">
              Home
            </Link>
            <svg
              className="w-4 h-4 text-slate-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5l7 7-7 7"
              />
            </svg>
            <span className="text-slate-300">Account</span>
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
}
