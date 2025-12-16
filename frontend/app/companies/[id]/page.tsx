'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { companyAPI, projectAPI, newsAPI, type Company, type Project, type NewsReleasesResponse } from '@/lib/api';
import LogoMono from '@/components/LogoMono';
import CompanyChatbot from '@/components/CompanyChatbot';
import { CompanyForum } from '@/components/forum';
import { EventBanner } from '@/components/events';
import { LoginModal, RegisterModal } from '@/components/auth';
import { useAuth } from '@/contexts/AuthContext';

interface StockQuote {
  ticker: string;
  exchange: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  date: string;
  source: string;
  cached: boolean;
}

export default function CompanyDetailPage() {
  const params = useParams();
  const companyId = params.id as string;
  const { user, logout } = useAuth();

  const [company, setCompany] = useState<Company | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newsData, setNewsData] = useState<NewsReleasesResponse | null>(null);
  const [newsLoading, setNewsLoading] = useState(false);
  const [scrapingNews, setScrapingNews] = useState(false);
  const [scrapeError, setScrapeError] = useState<string | null>(null);
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [financings, setFinancings] = useState<any[]>([]);
  const [interestAggregates, setInterestAggregates] = useState<Record<number, {
    total_interest_count: number;
    total_shares_requested: number;
    total_amount_interested: string;
    percentage_filled: string;
  }>>({});
  const [stockQuote, setStockQuote] = useState<StockQuote | null>(null);
  const [stockLoading, setStockLoading] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

  useEffect(() => {
    if (companyId) {
      fetchCompanyDetails();
      fetchNewsReleases();
      fetchFinancings();
      fetchStockQuote();
    }
  }, [companyId]);

  const fetchStockQuote = async () => {
    try {
      setStockLoading(true);
      const res = await fetch(`${API_URL}/companies/${companyId}/stock-quote/`);
      if (res.ok) {
        const data = await res.json();
        setStockQuote(data);
      }
    } catch (err) {
      console.error('Failed to fetch stock quote:', err);
    } finally {
      setStockLoading(false);
    }
  };

  const fetchCompanyDetails = async () => {
    try {
      setLoading(true);
      const [companyData, projectsData] = await Promise.all([
        companyAPI.getById(parseInt(companyId)),
        companyAPI.getProjects(parseInt(companyId))
      ]);
      setCompany(companyData);
      setProjects(projectsData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch company details');
    } finally {
      setLoading(false);
    }
  };

  const fetchNewsReleases = async () => {
    try {
      setNewsLoading(true);
      const data = await newsAPI.getNewsReleases(parseInt(companyId));
      setNewsData(data);
    } catch (err) {
      console.error('Failed to fetch news releases:', err);
    } finally {
      setNewsLoading(false);
    }
  };

  const fetchFinancings = async () => {
    try {
      const res = await fetch(`${API_URL}/financings/?company=${companyId}`);
      if (res.ok) {
        const data = await res.json();
        const financingsList = data.results || data;
        setFinancings(financingsList);
        // Fetch interest aggregates for open financings
        const openFinancings = financingsList.filter(
          (f: any) => f.status === 'announced' || f.status === 'closing' || f.status === 'open'
        );
        for (const financing of openFinancings) {
          fetchInterestAggregate(financing.id);
        }
      }
    } catch (err) {
      console.error('Failed to fetch financings:', err);
    }
  };

  const fetchInterestAggregate = async (financingId: number) => {
    try {
      const res = await fetch(`${API_URL}/investment-interest/aggregate/${financingId}/`);
      if (res.ok) {
        const data = await res.json();
        setInterestAggregates(prev => ({
          ...prev,
          [financingId]: data
        }));
      }
    } catch (err) {
      console.error('Failed to fetch interest aggregate:', err);
    }
  };

  const handleScrapeNews = async () => {
    try {
      setScrapingNews(true);
      setScrapeError(null);
      const result = await newsAPI.scrapeNews(parseInt(companyId));

      if (result.status === 'success' || result.status === 'cached') {
        // Refresh news releases after scraping
        await fetchNewsReleases();
        setScrapeError(null);
      } else if (result.status === 'error') {
        // Handle error response gracefully
        setScrapeError(result.message || 'Failed to scrape news releases');
        // Still try to refresh in case some data was saved
        await fetchNewsReleases();
      }
    } catch (err) {
      console.error('Failed to scrape news:', err);
      setScrapeError(err instanceof Error ? err.message : 'An unexpected error occurred while scraping news');
    } finally {
      setScrapingNews(false);
    }
  };

  const getExchangeBadgeVariant = (exchange: string) => {
    const variants: Record<string, 'gold' | 'copper' | 'slate'> = {
      'TSX': 'gold',
      'TSXV': 'copper',
      'NYSE': 'gold',
      'NASDAQ': 'gold',
    };
    return variants[exchange] || 'slate';
  };

  const formatNumber = (num: number | null | undefined) => {
    if (!num) return '---';
    return num.toLocaleString('en-US');
  };

  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <nav className="glass-nav sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-24">
            <div className="flex items-center space-x-3">
              <div className="cursor-pointer" onClick={() => window.location.href = '/'}>
                <LogoMono className="h-18" />
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant="copper">AI-Powered</Badge>
              <Button variant="ghost" size="sm" onClick={() => window.location.href = '/'}>Home</Button>
              <Button variant="ghost" size="sm" onClick={() => window.location.href = '/'}>Dashboard</Button>
              <Button variant="ghost" size="sm" onClick={() => window.location.href = '/companies'}>Companies</Button>
              <Button variant="ghost" size="sm" onClick={() => window.location.href = '/metals'}>Metals</Button>
              <Button variant="primary" size="sm" onClick={() => window.location.href = '/company-portal'}>Company Portal</Button>

              {user ? (
                <div className="flex items-center space-x-3">
                  <span className="text-sm text-slate-300">
                    Welcome, {user.full_name || user.username}
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
                  <Button variant="primary" size="sm" onClick={() => setShowRegister(true)}>
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

      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Card variant="glass-card">
            <CardContent className="py-12 text-center">
              <div className="text-red-400 mb-4">{error}</div>
              <Button variant="secondary" onClick={() => window.location.href = '/companies'}>
                Back to Companies
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {loading ? (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Card variant="glass-card">
            <CardContent className="py-12 text-center">
              <div className="text-slate-400">Loading company details...</div>
            </CardContent>
          </Card>
        </div>
      ) : company ? (
        <>
          {/* Company Header */}
          <section className="relative py-12 px-4 sm:px-6 lg:px-8 bg-gradient-slate">
            <div className="max-w-7xl mx-auto">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <div className="flex items-center gap-4 mb-3">
                    <h1 className="text-4xl font-bold text-gradient-gold">{company.name}</h1>
                    {/* Ticker & Exchange Info */}
                    <span className="text-xl font-mono text-gold-400 font-semibold">{company.exchange.toUpperCase()}:{company.ticker_symbol}</span>
                  </div>
                  {company.description && (
                    <p className="text-slate-300 text-lg max-w-3xl">{company.description}</p>
                  )}
                </div>
                {company.website && (
                  <Button variant="primary" onClick={() => window.open(company.website, '_blank')}>
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                    Visit Website
                  </Button>
                )}
              </div>

              {/* Quick Stats - Now showing Stock Data */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-8">
                <Card variant="glass-card">
                  <CardContent className="py-4">
                    <div className="text-sm text-slate-400 mb-1">Stock Price</div>
                    {stockLoading ? (
                      <div className="text-2xl font-bold text-slate-500 animate-pulse">---</div>
                    ) : stockQuote ? (
                      <div className="text-2xl font-bold text-gold-400">${stockQuote.price.toFixed(2)}</div>
                    ) : (
                      <div className="text-2xl font-bold text-slate-500">N/A</div>
                    )}
                  </CardContent>
                </Card>
                <Card variant="glass-card">
                  <CardContent className="py-4">
                    <div className="text-sm text-slate-400 mb-1">Change</div>
                    {stockLoading ? (
                      <div className="text-2xl font-bold text-slate-500 animate-pulse">---</div>
                    ) : stockQuote ? (
                      <div className={`text-2xl font-bold ${stockQuote.change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {stockQuote.change >= 0 ? '+' : ''}{stockQuote.change_percent.toFixed(2)}%
                      </div>
                    ) : (
                      <div className="text-2xl font-bold text-slate-500">N/A</div>
                    )}
                  </CardContent>
                </Card>
                <Card variant="glass-card">
                  <CardContent className="py-4">
                    <div className="text-sm text-slate-400 mb-1">Volume</div>
                    {stockLoading ? (
                      <div className="text-2xl font-bold text-slate-500 animate-pulse">---</div>
                    ) : stockQuote ? (
                      <div className="text-2xl font-bold text-white">{stockQuote.volume.toLocaleString()}</div>
                    ) : (
                      <div className="text-2xl font-bold text-slate-500">N/A</div>
                    )}
                  </CardContent>
                </Card>
                <Card variant="glass-card">
                  <CardContent className="py-4">
                    <div className="text-sm text-slate-400 mb-1">Status</div>
                    <div className="text-2xl font-bold text-green-400">Active</div>
                  </CardContent>
                </Card>
              </div>

              {/* Speaking Events & Active Financing Section */}
              <div className="mt-8 grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-6">
                {/* Speaking Events - Left Column (wider) */}
                <div className="min-w-0">
                  <EventBanner companyId={parseInt(companyId)} />
                </div>

                {/* Active Financing Rounds - Right Column */}
                {financings.filter(f => f.status === 'announced' || f.status === 'closing' || f.status === 'open').length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-gold-400 mb-4 flex items-center gap-2">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Active Financing Rounds
                    </h3>
                    <div className="space-y-4">
                      {financings
                        .filter(f => f.status === 'announced' || f.status === 'closing' || f.status === 'open')
                        .map(financing => {
                          const aggregate = interestAggregates[financing.id];
                          return (
                            <Card key={financing.id} variant="glass-card" className="border-gold-500/30">
                              <CardContent className="p-4">
                                <div className="flex items-center justify-between mb-3">
                                  <Badge variant="gold">{financing.financing_type_display || financing.financing_type}</Badge>
                                  <Badge variant="copper">
                                    {financing.status === 'announced' ? 'Open' :
                                     financing.status === 'closing' ? 'Closing Soon' : financing.status}
                                  </Badge>
                                </div>

                                {/* Investment Interest Stats */}
                                {aggregate && aggregate.total_interest_count > 0 ? (
                                  <div className="space-y-3">
                                    <div className="grid grid-cols-2 gap-3">
                                      <div className="text-center">
                                        <p className="text-2xl font-bold text-gold-400">{aggregate.total_interest_count}</p>
                                        <p className="text-xs text-slate-400">Interested Investors</p>
                                      </div>
                                      <div className="text-center">
                                        <p className="text-2xl font-bold text-white">
                                          ${Number(aggregate.total_amount_interested).toLocaleString()}
                                        </p>
                                        <p className="text-xs text-slate-400">Total Interest</p>
                                      </div>
                                    </div>

                                    {/* Progress bar */}
                                    <div>
                                      <div className="flex justify-between text-xs mb-1">
                                        <span className="text-slate-400">Interest Level</span>
                                        <span className="text-gold-400">{Number(aggregate.percentage_filled).toFixed(0)}%</span>
                                      </div>
                                      <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                                        <div
                                          className="h-full bg-gradient-to-r from-gold-500 to-copper-500 rounded-full"
                                          style={{ width: `${Math.min(Number(aggregate.percentage_filled), 100)}%` }}
                                        ></div>
                                      </div>
                                    </div>
                                  </div>
                                ) : (
                                  <p className="text-sm text-slate-400 text-center py-2">
                                    No interests registered yet
                                  </p>
                                )}

                                <Button
                                  variant="primary"
                                  size="sm"
                                  className="w-full mt-4"
                                  onClick={() => window.location.href = `/companies/${companyId}/financing`}
                                >
                                  View Financing Details
                                </Button>
                              </CardContent>
                            </Card>
                          );
                        })}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </section>

          {/* Company Details Tabs */}
          <section className="py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-7xl mx-auto">
              {/* Projects Section */}
              <div className="mb-12">
                <div className="mb-6">
                  <h2 className="text-3xl font-bold text-gold-400 mb-2">Projects</h2>
                  <p className="text-slate-400">Active mining projects and exploration sites</p>
                </div>

                {projects.length > 0 ? (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {projects.map((project) => (
                      <Card key={project.id} variant="glass-card" className="hover:scale-105 transition-transform">
                        <CardHeader>
                          <div className="flex items-start justify-between mb-2">
                            <CardTitle className="text-xl text-gold-400">{project.name}</CardTitle>
                            {project.is_flagship && (
                              <Badge variant="gold">Flagship</Badge>
                            )}
                          </div>
                          {(project.country || project.province_state) && (
                            <div className="flex items-center gap-2 text-sm text-slate-400 mb-2">
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                              </svg>
                              <span>{[project.province_state, project.country].filter(Boolean).join(', ')}</span>
                            </div>
                          )}
                          <CardDescription className="line-clamp-2">
                            {project.description || 'Gold exploration and development project'}
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-3">
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-slate-400">Primary Commodity</span>
                              <span className="text-white font-semibold">{project.primary_commodity || 'Gold'}</span>
                            </div>
                            {project.project_stage && (
                              <div className="flex items-center justify-between text-sm">
                                <span className="text-slate-400">Stage</span>
                                <Badge variant="copper">{project.project_stage}</Badge>
                              </div>
                            )}
                            {project.total_resources_oz && (
                              <div className="pt-3 border-t border-slate-700">
                                <div className="text-xs text-slate-400 mb-1">Total Resources</div>
                                <div className="text-lg font-bold text-gold-400">
                                  {formatNumber(project.total_resources_oz)} oz Au
                                </div>
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                ) : (
                  <Card variant="glass-card">
                    <CardContent className="py-12 text-center">
                      <div className="text-slate-400">No projects data available</div>
                    </CardContent>
                  </Card>
                )}
              </div>

              {/* Company Information */}
              <div className="mb-12">
                <div className="mb-6">
                  <h2 className="text-3xl font-bold text-gold-400 mb-2">Company Information</h2>
                  <p className="text-slate-400">Corporate details and contact information</p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <Card variant="glass-card">
                    <CardHeader>
                      <CardTitle className="text-lg">Corporate Details</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="flex items-start justify-between">
                          <span className="text-slate-400 text-sm">Company Name</span>
                          <span className="text-white text-sm font-medium text-right">{company.name}</span>
                        </div>
                        <div className="flex items-start justify-between">
                          <span className="text-slate-400 text-sm">Ticker Symbol</span>
                          <span className="text-gold-400 text-sm font-mono">{company.ticker_symbol}</span>
                        </div>
                        <div className="flex items-start justify-between">
                          <span className="text-slate-400 text-sm">Exchange</span>
                          <Badge variant={getExchangeBadgeVariant(company.exchange)}>{company.exchange}</Badge>
                        </div>
                        {company.headquarters && (
                          <div className="flex items-start justify-between">
                            <span className="text-slate-400 text-sm">Headquarters</span>
                            <span className="text-white text-sm text-right">{company.headquarters}</span>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>

                  <Card variant="glass-card">
                    <CardHeader>
                      <CardTitle className="text-lg">Contact Information</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {company.website && (
                          <div className="flex items-start justify-between">
                            <span className="text-slate-400 text-sm">Website</span>
                            <a
                              href={company.website}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-gold-400 hover:text-gold-300 text-sm flex items-center gap-1"
                            >
                              <span>Visit Site</span>
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                              </svg>
                            </a>
                          </div>
                        )}
                        <div className="flex items-start justify-between">
                          <span className="text-slate-400 text-sm">Status</span>
                          <Badge variant="gold">Active</Badge>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>

              {/* Community Forum Section */}
              <div className="mb-12">
                <div className="mb-6">
                  <h2 className="text-3xl font-bold text-gold-400 mb-2">Community Forum</h2>
                  <p className="text-slate-400">Join real-time discussions with investors and analysts</p>
                </div>

                <CompanyForum companyId={parseInt(companyId)} companyName={company.name} />
              </div>

              {/* News Releases Section */}
              <div className="mb-12">
                <div className="mb-6 flex items-center justify-between">
                  <div>
                    <h2 className="text-3xl font-bold text-gold-400 mb-2">Company News Releases</h2>
                    <p className="text-slate-400">Recent updates and announcements from {company.name}</p>
                    {newsData?.last_updated && (
                      <p className="text-xs text-slate-500 mt-1">
                        Last updated: {new Date(newsData.last_updated).toLocaleString()}
                      </p>
                    )}
                    {scrapeError && (
                      <p className="text-xs text-red-400 mt-2 flex items-center gap-1">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {scrapeError}
                      </p>
                    )}
                  </div>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={handleScrapeNews}
                    disabled={scrapingNews || !company.website}
                  >
                    {scrapingNews ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Updating...
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                        Update News
                      </>
                    )}
                  </Button>
                </div>

                {newsLoading ? (
                  <Card variant="glass-card">
                    <CardContent className="py-12 text-center">
                      <div className="text-slate-400">Loading news releases...</div>
                    </CardContent>
                  </Card>
                ) : (
                  <div className="space-y-8">
                    {/* Financial News Section */}
                    <div>
                      <h3 className="text-xl font-bold text-copper-400 mb-4 flex items-center gap-2">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                        </svg>
                        Financial News
                      </h3>
                      {newsData?.financial && newsData.financial.length > 0 ? (
                        <div className="grid grid-cols-1 gap-4">
                          {newsData.financial.map((release) => (
                            <Card key={release.id} variant="glass-card">
                              <CardHeader>
                                <div className="flex items-start justify-between">
                                  <CardTitle className="text-lg text-white">{release.title}</CardTitle>
                                  <Badge variant="gold">Financial</Badge>
                                </div>
                                {release.release_date && (
                                  <div className="text-sm text-slate-400 mt-1">
                                    {new Date(release.release_date + 'T00:00:00').toLocaleDateString('en-US', {
                                      year: 'numeric',
                                      month: 'long',
                                      day: 'numeric'
                                    })}
                                  </div>
                                )}
                              </CardHeader>
                              <CardContent>
                                <p className="text-slate-300 text-sm mb-3">{release.summary}</p>
                                {release.url && (
                                  <a
                                    href={release.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-gold-400 hover:text-gold-300 text-sm flex items-center gap-1"
                                  >
                                    <span>Read Full Release</span>
                                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                    </svg>
                                  </a>
                                )}
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      ) : (
                        <Card variant="glass-card">
                          <CardContent className="py-8 text-center">
                            <div className="text-slate-400 text-sm">No financial news releases available</div>
                          </CardContent>
                        </Card>
                      )}
                    </div>

                    {/* Non-Financial News Section */}
                    <div>
                      <h3 className="text-xl font-bold text-copper-400 mb-4 flex items-center gap-2">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                        </svg>
                        Company Updates
                      </h3>
                      {newsData?.non_financial && newsData.non_financial.length > 0 ? (
                        <div className="grid grid-cols-1 gap-4">
                          {newsData.non_financial.map((release) => (
                            <Card key={release.id} variant="glass-card">
                              <CardHeader>
                                <div className="flex items-start justify-between">
                                  <CardTitle className="text-lg text-white">{release.title}</CardTitle>
                                  <Badge variant="copper">{release.release_type.replace(/_/g, ' ')}</Badge>
                                </div>
                                {release.release_date && (
                                  <div className="text-sm text-slate-400 mt-1">
                                    {new Date(release.release_date + 'T00:00:00').toLocaleDateString('en-US', {
                                      year: 'numeric',
                                      month: 'long',
                                      day: 'numeric'
                                    })}
                                  </div>
                                )}
                              </CardHeader>
                              <CardContent>
                                <p className="text-slate-300 text-sm mb-3">{release.summary}</p>
                                {release.url && (
                                  <a
                                    href={release.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-gold-400 hover:text-gold-300 text-sm flex items-center gap-1"
                                  >
                                    <span>Read Full Release</span>
                                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                    </svg>
                                  </a>
                                )}
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      ) : (
                        <Card variant="glass-card">
                          <CardContent className="py-8 text-center">
                            <div className="text-slate-400 text-sm">No company updates available</div>
                          </CardContent>
                        </Card>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </section>
        </>
      ) : null}

      {/* Company Chatbot */}
      {company && (
        <CompanyChatbot companyId={parseInt(companyId)} companyName={company.name} />
      )}
    </div>
  );
}
