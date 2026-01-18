'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import LogoMono from '@/components/LogoMono';
import { LoginModal, RegisterModal } from '@/components/auth';
import { useAuth } from '@/contexts/AuthContext';

interface ClosedFinancing {
  id: number;
  company_id: number;
  company_name: string;
  company_ticker: string;
  company_exchange: string;
  company_logo_url: string | null;
  financing_type: string;
  financing_type_display: string;
  amount_raised_usd: number;
  price_per_share: number | null;
  shares_issued: number | null;
  has_warrants: boolean;
  warrant_strike_price: number | null;
  warrant_expiry_date: string | null;
  announced_date: string;
  closing_date: string | null;
  closed_at: string;
  press_release_url: string;
  use_of_proceeds: string;
  lead_agent: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export default function ClosedFinancingsPage() {
  const router = useRouter();
  const { user, logout } = useAuth();

  const [financings, setFinancings] = useState<ClosedFinancing[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);

  // Filters and sorting
  const [sortBy, setSortBy] = useState<string>('closed_at');
  const [sortOrder, setSortOrder] = useState<string>('desc');
  const [financingType, setFinancingType] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const accessToken = typeof window !== 'undefined' ? localStorage.getItem('accessToken') : null;

  useEffect(() => {
    fetchClosedFinancings();
  }, [sortBy, sortOrder, financingType]);

  const fetchClosedFinancings = async () => {
    try {
      setLoading(true);

      const params = new URLSearchParams();
      params.append('sort_by', sortBy);
      params.append('sort_order', sortOrder);
      if (financingType) {
        params.append('financing_type', financingType);
      }

      const headers: Record<string, string> = {};
      if (accessToken) {
        headers['Authorization'] = `Bearer ${accessToken}`;
      }

      const response = await fetch(`${API_URL}/closed-financings/?${params.toString()}`, {
        headers,
      });

      if (!response.ok) {
        if (response.status === 401) {
          setShowLogin(true);
          throw new Error('Please sign in to view closed financings');
        }
        throw new Error('Failed to fetch closed financings');
      }

      const data = await response.json();
      setFinancings(data.results || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load closed financings');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-CA', {
      style: 'currency',
      currency: 'CAD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const filteredFinancings = financings.filter(f => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      f.company_name.toLowerCase().includes(query) ||
      f.company_ticker.toLowerCase().includes(query) ||
      f.financing_type_display.toLowerCase().includes(query)
    );
  });

  const financingTypes = [
    { value: '', label: 'All Types' },
    { value: 'private_placement', label: 'Private Placement' },
    { value: 'bought_deal', label: 'Bought Deal' },
    { value: 'best_efforts', label: 'Best Efforts' },
    { value: 'flow_through', label: 'Flow-Through' },
    { value: 'ipo', label: 'IPO' },
    { value: 'rights_offering', label: 'Rights Offering' },
    { value: 'other', label: 'Other' },
  ];

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Navigation */}
      <nav className="glass-nav sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center space-x-3">
              <LogoMono className="h-10" />
            </Link>
            <div className="flex items-center space-x-4">
              <Button variant="ghost" size="sm" onClick={() => router.push('/')}>
                Home
              </Button>
              <Button variant="ghost" size="sm" onClick={() => router.push('/companies')}>
                Companies
              </Button>
              <Button variant="primary" size="sm" onClick={() => router.push('/closed-financings')}>
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
                  <Button variant="ghost" size="sm" onClick={() => setShowLogin(true)}>
                    Login
                  </Button>
                  <Button variant="secondary" size="sm" onClick={() => setShowRegister(true)}>
                    Register
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
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

      {/* Hero Section */}
      <section className="relative py-12 px-4 sm:px-6 lg:px-8">
        <div className="absolute inset-0 bg-gradient-to-b from-slate-900 via-slate-900 to-slate-800 opacity-50"></div>
        <div className="absolute inset-0" style={{
          backgroundImage: 'radial-gradient(circle at 50% 50%, rgba(212, 161, 42, 0.1) 0%, transparent 50%)'
        }}></div>

        <div className="relative max-w-7xl mx-auto text-center">
          <Badge variant="gold" className="mb-4">
            Recently Closed
          </Badge>
          <h1 className="text-4xl md:text-5xl font-bold mb-4 text-gradient-gold leading-tight pb-2">
            Closed Financings
          </h1>
          <p className="text-lg text-slate-300 max-w-2xl mx-auto">
            Browse recently closed financing rounds from junior mining companies
          </p>
        </div>
      </section>

      {/* Filters Section */}
      <section className="py-6 px-4 sm:px-6 lg:px-8 border-b border-slate-800">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
            {/* Search */}
            <div className="flex-1 max-w-md">
              <input
                type="text"
                placeholder="Search by company name or ticker..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-gold-400"
              />
            </div>

            {/* Filters */}
            <div className="flex flex-wrap gap-3">
              {/* Financing Type Filter */}
              <select
                value={financingType}
                onChange={(e) => setFinancingType(e.target.value)}
                className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-gold-400"
              >
                {financingTypes.map(type => (
                  <option key={type.value} value={type.value}>{type.label}</option>
                ))}
              </select>

              {/* Sort By */}
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-gold-400"
              >
                <option value="closed_at">Date Closed</option>
                <option value="amount_raised_usd">Amount Raised</option>
                <option value="company_name">Company Name</option>
              </select>

              {/* Sort Order */}
              <button
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white hover:bg-slate-700 focus:outline-none focus:border-gold-400 flex items-center gap-2"
              >
                {sortOrder === 'desc' ? (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
                    </svg>
                    Newest First
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h9m5-4v12m0 0l-4-4m4 4l4-4" />
                    </svg>
                    Oldest First
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </section>

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
                <svg className="w-12 h-12 mx-auto text-red-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <p className="text-red-400 mb-4">{error}</p>
                <Button variant="primary" onClick={() => setShowLogin(true)}>
                  Sign In
                </Button>
              </CardContent>
            </Card>
          ) : filteredFinancings.length === 0 ? (
            <Card variant="glass-card" className="max-w-md mx-auto">
              <CardContent className="p-12 text-center">
                <svg className="w-16 h-16 mx-auto text-slate-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h2 className="text-xl font-semibold text-white mb-2">No Closed Financings</h2>
                <p className="text-slate-400">
                  {searchQuery
                    ? 'No financings match your search criteria.'
                    : 'No closed financings have been recorded yet.'}
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {/* Results count */}
              <p className="text-sm text-slate-400 mb-4">
                Showing {filteredFinancings.length} closed financing{filteredFinancings.length !== 1 ? 's' : ''}
              </p>

              {/* Financing Cards */}
              {filteredFinancings.map((financing) => (
                <Card key={financing.id} variant="glass-card" className="hover:border-gold-500/30 transition-all">
                  <CardContent className="p-6">
                    <div className="flex flex-col lg:flex-row gap-6">
                      {/* Company Info */}
                      <div className="flex items-start gap-4 flex-1">
                        {financing.company_logo_url ? (
                          <img
                            src={financing.company_logo_url}
                            alt={financing.company_name}
                            className="w-14 h-14 rounded-lg object-contain bg-white p-1.5"
                          />
                        ) : (
                          <div className="w-14 h-14 rounded-lg bg-gradient-to-br from-gold-500/20 to-copper-500/20 flex items-center justify-center">
                            <span className="text-xl font-bold text-gold-400">
                              {financing.company_name.charAt(0)}
                            </span>
                          </div>
                        )}
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

                      {/* Financing Details */}
                      <div className="flex flex-col sm:flex-row lg:flex-col gap-4 lg:min-w-[200px] lg:text-right">
                        <div>
                          <p className="text-2xl font-bold text-gold-400">
                            {formatCurrency(financing.amount_raised_usd)}
                          </p>
                          <p className="text-xs text-slate-500">Amount Raised</p>
                        </div>
                        <div className="flex flex-col sm:flex-row lg:flex-col gap-2 text-sm">
                          {financing.price_per_share && (
                            <div>
                              <span className="text-slate-500">Price: </span>
                              <span className="text-white">${Number(financing.price_per_share).toFixed(3)}</span>
                            </div>
                          )}
                          {financing.closing_date && (
                            <div>
                              <span className="text-slate-500">Closed: </span>
                              <span className="text-white">{formatDate(financing.closing_date)}</span>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Actions */}
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
                            <Button variant="ghost" size="sm" className="w-full text-gold-400">
                              Press Release
                            </Button>
                          </a>
                        )}
                      </div>
                    </div>

                    {/* Warrant Details (if applicable) */}
                    {financing.has_warrants && (financing.warrant_strike_price || financing.warrant_expiry_date) && (
                      <div className="mt-4 pt-4 border-t border-slate-700">
                        <div className="flex items-center gap-4 text-sm">
                          <span className="text-slate-500">Warrant Details:</span>
                          {financing.warrant_strike_price && (
                            <span className="text-white">
                              Strike ${Number(financing.warrant_strike_price).toFixed(3)}
                            </span>
                          )}
                          {financing.warrant_expiry_date && (
                            <span className="text-white">
                              Expires {formatDate(financing.warrant_expiry_date)}
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-slate-800 mt-12">
        <div className="max-w-7xl mx-auto text-center text-slate-400 text-sm">
          <p>&copy; {new Date().getFullYear()} GoldVenture. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
