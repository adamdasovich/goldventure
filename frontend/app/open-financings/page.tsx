"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import LogoMono from "@/components/LogoMono";
import { LoginModal, RegisterModal } from "@/components/auth";
import { useAuth } from "@/contexts/AuthContext";

interface OpenFinancing {
  id: number;
  company_id: number;
  company_name: string;
  company_ticker: string;
  company_exchange: string;
  financing_type: string;
  financing_type_display: string;
  status: string | null;
  amount_raised_usd: string | null;
  price_per_share: string | null;
  shares_issued: number | null;
  has_warrants: boolean | null;
  warrant_strike_price: string | null;
  warrant_expiry_date: string | null;
  announced_date: string | null;
  closing_date: string | null;
  lead_agent: string | null;
  use_of_proceeds: string | null;
  press_release_url: string | null;
  notes: string | null;
  is_locked: boolean;
}

interface OpenFinancingsResponse {
  count: number;
  total_count: number;
  locked_count: number;
  user_tier: string;
  is_paid: boolean;
  preview_count: number;
  results: OpenFinancing[];
  financing_types: { value: string; label: string }[];
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export default function OpenFinancingsPage() {
  const router = useRouter();
  const { user, logout } = useAuth();

  const [data, setData] = useState<OpenFinancingsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);

  const [sortBy, setSortBy] = useState<string>("announced_date");
  const [sortOrder, setSortOrder] = useState<string>("desc");
  const [financingType, setFinancingType] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const accessToken =
    typeof window !== "undefined" ? localStorage.getItem("accessToken") : null;

  useEffect(() => {
    fetchOpenFinancings();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sortBy, sortOrder, financingType]);

  const fetchOpenFinancings = async () => {
    try {
      setLoading(true);

      const params = new URLSearchParams();
      params.append("sort_by", sortBy);
      params.append("sort_order", sortOrder);
      if (financingType) {
        params.append("financing_type", financingType);
      }

      const headers: Record<string, string> = {};
      if (accessToken) {
        headers["Authorization"] = `Bearer ${accessToken}`;
      }

      const response = await fetch(
        `${API_URL}/open-financings/?${params.toString()}`,
        {
          headers,
        },
      );

      if (!response.ok) {
        throw new Error("Failed to fetch open financings");
      }

      const json: OpenFinancingsResponse = await response.json();
      setData(json);
      setError(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load open financings",
      );
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: string | number) => {
    return new Intl.NumberFormat("en-CA", {
      style: "currency",
      currency: "CAD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(typeof amount === "string" ? parseFloat(amount) : amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const filteredFinancings = (data?.results || []).filter((f) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      f.company_name.toLowerCase().includes(query) ||
      f.company_ticker.toLowerCase().includes(query) ||
      f.financing_type_display.toLowerCase().includes(query)
    );
  });

  const isPaid = data?.is_paid ?? false;
  const lockedCount = data?.locked_count ?? 0;

  // Find the index of the first locked row in the filtered list — used to
  // insert the upgrade banner once, immediately above the locked section.
  const firstLockedIndex = filteredFinancings.findIndex((f) => f.is_locked);

  const financingTypes = [
    { value: "", label: "All Types" },
    ...(data?.financing_types || []),
  ];

  return (
    <div className="min-h-screen bg-slate-900">
      <nav className="glass-nav sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center space-x-3">
              <LogoMono className="h-10" />
            </Link>
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push("/")}
              >
                Home
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push("/companies")}
              >
                Companies
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => router.push("/open-financings")}
              >
                Open Financings
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push("/closed-financings")}
              >
                Closed Financings
              </Button>
              {user ? (
                <div className="flex items-center space-x-3">
                  <span className="text-sm text-slate-300">
                    {user.full_name || user.username}
                  </span>
                  <Button variant="ghost" size="sm" onClick={logout}>
                    Logout
                  </Button>
                </div>
              ) : (
                <>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowLogin(true)}
                  >
                    Login
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setShowRegister(true)}
                  >
                    Register
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

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

      {/* Hero */}
      <section className="relative py-12 px-4 sm:px-6 lg:px-8">
        <div className="absolute inset-0 bg-gradient-to-b from-slate-900 via-slate-900 to-slate-800 opacity-50"></div>
        <div
          className="absolute inset-0"
          style={{
            backgroundImage:
              "radial-gradient(circle at 50% 50%, rgba(212, 161, 42, 0.1) 0%, transparent 50%)",
          }}
        ></div>
        <div className="relative max-w-7xl mx-auto text-center">
          <Badge variant="gold" className="mb-4">
            Currently Raising
          </Badge>
          <h1 className="text-4xl md:text-5xl font-bold mb-4 text-gradient-gold leading-tight pb-2">
            Open Financings
          </h1>
          <p className="text-lg text-slate-300 max-w-2xl mx-auto mb-2">
            Junior mining companies currently raising capital — private
            placements, bought deals, flow-through offerings, and more.
          </p>
          {data && (
            <p className="text-sm text-slate-500">
              {data.total_count} open financing
              {data.total_count !== 1 ? "s" : ""}
              {!isPaid && lockedCount > 0 && (
                <>
                  {" "}
                  · Showing {data.preview_count} preview · {lockedCount} locked
                </>
              )}
            </p>
          )}
        </div>
      </section>

      {/* Filters — paid users only */}
      {isPaid && (
        <section className="py-6 px-4 sm:px-6 lg:px-8 border-b border-slate-800">
          <div className="max-w-7xl mx-auto">
            <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
              <div className="flex-1 max-w-md">
                <input
                  type="text"
                  placeholder="Search by company name or ticker..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-gold-400"
                />
              </div>
              <div className="flex flex-wrap gap-3">
                <select
                  value={financingType}
                  onChange={(e) => setFinancingType(e.target.value)}
                  className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-gold-400"
                >
                  {financingTypes.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-gold-400"
                >
                  <option value="announced_date">Date Announced</option>
                  <option value="closing_date">Closing Date</option>
                  <option value="amount">Amount Raised</option>
                  <option value="company">Company Name</option>
                </select>
                <button
                  onClick={() =>
                    setSortOrder(sortOrder === "asc" ? "desc" : "asc")
                  }
                  className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white hover:bg-slate-700 focus:outline-none focus:border-gold-400 flex items-center gap-2"
                >
                  {sortOrder === "desc" ? "Newest First" : "Oldest First"}
                </button>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Main Content */}
      <section className="py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold-400"></div>
            </div>
          ) : error ? (
            <Card variant="glass-card" className="max-w-md mx-auto">
              <CardContent className="p-6 text-center">
                <p className="text-red-400 mb-4">{error}</p>
              </CardContent>
            </Card>
          ) : filteredFinancings.length === 0 ? (
            <Card variant="glass-card" className="max-w-md mx-auto">
              <CardContent className="p-12 text-center">
                <h2 className="text-xl font-semibold text-white mb-2">
                  No Open Financings
                </h2>
                <p className="text-slate-400">
                  No financings are currently open. Check back soon — new rounds
                  appear here as companies announce them.
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {filteredFinancings.map((financing, idx) => (
                <div key={financing.id}>
                  {/* Upgrade banner — inserted once, right before the first locked row */}
                  {!isPaid &&
                    idx === firstLockedIndex &&
                    firstLockedIndex >= 0 && (
                      <UpgradeBanner lockedCount={lockedCount} />
                    )}

                  {financing.is_locked ? (
                    <LockedFinancingCard financing={financing} />
                  ) : (
                    <OpenFinancingCard
                      financing={financing}
                      formatCurrency={formatCurrency}
                      formatDate={formatDate}
                    />
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      <footer className="py-8 px-4 border-t border-slate-800 mt-12">
        <div className="max-w-7xl mx-auto text-center text-slate-400 text-sm">
          <p>
            &copy; {new Date().getFullYear()} GoldVenture. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}

function OpenFinancingCard({
  financing,
  formatCurrency,
  formatDate,
}: {
  financing: OpenFinancing;
  formatCurrency: (amount: string | number) => string;
  formatDate: (dateString: string) => string;
}) {
  return (
    <Card
      variant="glass-card"
      className="hover:border-gold-500/30 transition-all"
    >
      <CardContent className="p-6">
        <div className="flex flex-col lg:flex-row gap-6">
          <div className="flex items-start gap-4 flex-1">
            <div className="w-14 h-14 rounded-lg bg-gradient-to-br from-gold-500/20 to-copper-500/20 flex items-center justify-center">
              <span className="text-xl font-bold text-gold-400">
                {financing.company_name.charAt(0)}
              </span>
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <Link
                  href={`/companies/${financing.company_id}`}
                  className="text-lg font-semibold text-white hover:text-gold-400 transition-colors"
                >
                  {financing.company_name}
                </Link>
                <Badge variant="copper" className="text-xs">
                  {financing.company_exchange}:{financing.company_ticker}
                </Badge>
              </div>
              <div className="flex items-center gap-2 mb-2">
                <Badge variant="gold">{financing.financing_type_display}</Badge>
                {financing.has_warrants && (
                  <Badge variant="slate">With Warrants</Badge>
                )}
              </div>
              {financing.use_of_proceeds && (
                <p className="text-sm text-slate-400 line-clamp-2">
                  {financing.use_of_proceeds}
                </p>
              )}
            </div>
          </div>

          <div className="flex flex-col sm:flex-row lg:flex-col gap-4 lg:min-w-[200px] lg:text-right">
            {financing.amount_raised_usd && (
              <div>
                <p className="text-2xl font-bold text-gold-400">
                  {formatCurrency(financing.amount_raised_usd)}
                </p>
                <p className="text-xs text-slate-500">Amount Raised</p>
              </div>
            )}
            <div className="flex flex-col sm:flex-row lg:flex-col gap-2 text-sm">
              {financing.price_per_share && (
                <div>
                  <span className="text-slate-500">Price: </span>
                  <span className="text-white">
                    ${Number(financing.price_per_share).toFixed(3)}
                  </span>
                </div>
              )}
              {financing.closing_date && (
                <div>
                  <span className="text-slate-500">Closes: </span>
                  <span className="text-white">
                    {formatDate(financing.closing_date)}
                  </span>
                </div>
              )}
              {financing.announced_date && (
                <div>
                  <span className="text-slate-500">Announced: </span>
                  <span className="text-white">
                    {formatDate(financing.announced_date)}
                  </span>
                </div>
              )}
            </div>
          </div>

          <div className="flex flex-row lg:flex-col gap-2 lg:justify-start">
            <Link href={`/companies/${financing.company_id}`}>
              <Button variant="secondary" size="sm" className="w-full">
                View Company
              </Button>
            </Link>
            {financing.press_release_url && (
              <a
                href={financing.press_release_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full text-gold-400"
                >
                  Press Release
                </Button>
              </a>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function LockedFinancingCard({ financing }: { financing: OpenFinancing }) {
  return (
    <Card
      variant="glass-card"
      className="relative overflow-hidden border-slate-800/50 opacity-90"
    >
      <CardContent className="p-6">
        <div className="flex flex-col lg:flex-row gap-6">
          <div className="flex items-start gap-4 flex-1">
            <div className="w-14 h-14 rounded-lg bg-slate-800/60 flex items-center justify-center">
              <svg
                className="w-6 h-6 text-slate-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 11c0-1.657-1.343-3-3-3m6 3c0-1.657 1.343-3 3-3M12 11v6m-6-6a6 6 0 1112 0v0"
                />
              </svg>
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-lg font-semibold text-slate-300">
                  {financing.company_name}
                </span>
                <Badge variant="copper" className="text-xs">
                  {financing.company_exchange}:{financing.company_ticker}
                </Badge>
              </div>
              <div className="flex items-center gap-2 mb-2">
                <Badge variant="slate">
                  {financing.financing_type_display}
                </Badge>
              </div>
              <p
                className="text-sm text-slate-500 select-none"
                style={{ filter: "blur(4px)" }}
              >
                Use of proceeds available to subscribers — terms, pricing, and
                closing date hidden.
              </p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row lg:flex-col gap-4 lg:min-w-[200px] lg:text-right">
            <div>
              <p
                className="text-2xl font-bold text-gold-400/60 select-none"
                style={{ filter: "blur(6px)" }}
              >
                $••••••••
              </p>
              <p className="text-xs text-slate-500">Amount Raised</p>
            </div>
            <div className="flex flex-col sm:flex-row lg:flex-col gap-2 text-sm">
              <div>
                <span className="text-slate-500">Closes: </span>
                <span
                  className="text-slate-400 select-none"
                  style={{ filter: "blur(4px)" }}
                >
                  ••• ••, ••••
                </span>
              </div>
            </div>
          </div>

          <div className="flex flex-row lg:flex-col gap-2 lg:justify-start">
            <Link href="/pricing">
              <Button variant="primary" size="sm" className="w-full">
                Unlock
              </Button>
            </Link>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function UpgradeBanner({ lockedCount }: { lockedCount: number }) {
  return (
    <div className="my-6">
      <Card
        variant="glass-card"
        className="border-gold-500/40 bg-gradient-to-r from-gold-500/10 via-copper-500/10 to-gold-500/10"
      >
        <CardContent className="p-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-lg bg-gold-500/20 flex items-center justify-center flex-shrink-0">
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
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white mb-1">
                {lockedCount} more open financing{lockedCount !== 1 ? "s" : ""}{" "}
                — <span className="text-gold-400">unlock with Prospector</span>
              </h3>
              <p className="text-sm text-slate-400">
                See every open round&apos;s amount, pricing, closing date, and
                use of proceeds. Includes email alerts for new financings.
              </p>
            </div>
          </div>
          <Link href="/pricing">
            <Button variant="primary" size="lg" className="whitespace-nowrap">
              Upgrade →
            </Button>
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
