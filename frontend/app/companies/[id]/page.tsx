'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { companyAPI, projectAPI, newsAPI, type Company, type Project, type NewsReleasesResponse } from '@/lib/api';
import LogoMono from '@/components/LogoMono';
import CompanyChatbot from '@/components/CompanyChatbot';

export default function CompanyDetailPage() {
  const params = useParams();
  const companyId = params.id as string;

  const [company, setCompany] = useState<Company | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newsData, setNewsData] = useState<NewsReleasesResponse | null>(null);
  const [newsLoading, setNewsLoading] = useState(false);
  const [scrapingNews, setScrapingNews] = useState(false);
  const [scrapeError, setScrapeError] = useState<string | null>(null);

  useEffect(() => {
    if (companyId) {
      fetchCompanyDetails();
      fetchNewsReleases();
    }
  }, [companyId]);

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
    const variants: Record<string, 'gold' | 'copper' | 'secondary'> = {
      'TSX': 'gold',
      'TSXV': 'copper',
      'NYSE': 'gold',
      'NASDAQ': 'gold',
    };
    return variants[exchange] || 'secondary';
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
              <LogoMono className="h-18 cursor-pointer" onClick={() => window.location.href = '/'} />
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant="copper">AI-Powered</Badge>
              <Button variant="ghost" size="sm" onClick={() => window.location.href = '/'}>Home</Button>
              <Button variant="ghost" size="sm" onClick={() => window.location.href = '/'}>Dashboard</Button>
              <Button variant="ghost" size="sm" onClick={() => window.location.href = '/companies'}>Companies</Button>
              <Button variant="ghost" size="sm" onClick={() => window.location.href = '/metals'}>Metals</Button>
              <Button variant="ghost" size="sm">Sign In</Button>
            </div>
          </div>
        </div>
      </nav>

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
                  <div className="flex items-center gap-3 mb-3">
                    <h1 className="text-4xl font-bold text-gradient-gold">{company.name}</h1>
                    <Badge variant={getExchangeBadgeVariant(company.exchange)}>
                      {company.exchange}: {company.ticker_symbol}
                    </Badge>
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

              {/* Quick Stats */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
                <Card variant="glass-card">
                  <CardContent className="py-4">
                    <div className="text-sm text-slate-400 mb-1">Exchange</div>
                    <div className="text-2xl font-bold text-white">{company.exchange}</div>
                  </CardContent>
                </Card>
                <Card variant="glass-card">
                  <CardContent className="py-4">
                    <div className="text-sm text-slate-400 mb-1">Ticker</div>
                    <div className="text-2xl font-bold text-gold-400 font-mono">{company.ticker_symbol}</div>
                  </CardContent>
                </Card>
                <Card variant="glass-card">
                  <CardContent className="py-4">
                    <div className="text-sm text-slate-400 mb-1">Status</div>
                    <div className="text-2xl font-bold text-green-400">Active</div>
                  </CardContent>
                </Card>
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
