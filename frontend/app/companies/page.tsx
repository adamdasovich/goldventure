'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { companyAPI, type Company } from '@/lib/api';
import LogoMono from '@/components/LogoMono';
import { useAuth } from '@/contexts/AuthContext';

export default function CompaniesPage() {
  const { user } = useAuth();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');

  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    try {
      setLoading(true);
      const response = await companyAPI.getAll();
      setCompanies(response.results || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch companies');
    } finally {
      setLoading(false);
    }
  };

  const filteredCompanies = companies.filter(company =>
    company.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    company.ticker_symbol.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getExchangeBadgeVariant = (exchange: string) => {
    const variants: Record<string, 'gold' | 'copper' | 'slate'> = {
      'TSX': 'gold',
      'TSXV': 'copper',
      'NYSE': 'gold',
      'NASDAQ': 'gold',
    };
    return variants[exchange] || 'slate';
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
              <Button variant="primary" size="sm">Companies</Button>
              <Button variant="ghost" size="sm" onClick={() => window.location.href = '/metals'}>Metals</Button>
              <Button variant="ghost" size="sm">Sign In</Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative py-20 px-4 sm:px-6 lg:px-8">
        <div className="absolute inset-0 bg-linear-to-b from-slate-900 via-slate-900 to-slate-800 opacity-50"></div>
        <div className="absolute inset-0" style={{
          backgroundImage: 'radial-gradient(circle at 50% 50%, rgba(212, 161, 42, 0.1) 0%, transparent 50%)'
        }}></div>

        <div className="relative max-w-7xl mx-auto text-center">
          <Badge variant="gold" className="mb-6">
            Junior Mining Companies
          </Badge>
          <h1 className="text-5xl md:text-6xl font-bold mb-6 text-gradient-gold animate-fade-in leading-tight pb-2">
            Explore Mining Companies
          </h1>
          <p className="text-xl text-slate-300 max-w-3xl mx-auto mb-12 animate-slide-in-up">
            Comprehensive database of junior gold mining companies with detailed resource estimates and project data
          </p>
        </div>
      </section>

      {/* Search and Filters */}
      <section className="py-8 px-4 sm:px-6 lg:px-8 bg-gradient-slate">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
            {/* Search Bar */}
            <div className="flex-1 w-full md:max-w-md">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search by name or ticker..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-gold-400 transition-colors"
                />
                <svg className="absolute right-3 top-3.5 w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </div>

            {/* View Toggle and Stats */}
            <div className="flex items-center gap-4">
              {user && (
                <Link href="/companies/new">
                  <Button variant="primary" size="sm" className="flex items-center gap-2">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    Add Company
                  </Button>
                </Link>
              )}
              <div className="text-slate-400 text-sm">
                {filteredCompanies.length} {filteredCompanies.length === 1 ? 'company' : 'companies'}
              </div>
              <div className="flex gap-2">
                <Button
                  variant={viewMode === 'grid' ? 'primary' : 'secondary'}
                  size="sm"
                  onClick={() => setViewMode('grid')}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                  </svg>
                </Button>
                <Button
                  variant={viewMode === 'table' ? 'primary' : 'secondary'}
                  size="sm"
                  onClick={() => setViewMode('table')}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                  </svg>
                </Button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Companies List */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          {error && (
            <div className="text-center text-red-400 mb-8">
              {error}
            </div>
          )}

          {loading ? (
            // Loading State
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {Array.from({ length: 6 }).map((_, idx) => (
                <Card key={idx} variant="glass-card">
                  <CardContent className="py-6">
                    <div className="h-6 bg-slate-700 rounded w-32 mb-3 animate-pulse"></div>
                    <div className="h-4 bg-slate-700 rounded w-24 mb-4 animate-pulse"></div>
                    <div className="h-4 bg-slate-700 rounded w-full mb-2 animate-pulse"></div>
                    <div className="h-4 bg-slate-700 rounded w-3/4 animate-pulse"></div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : viewMode === 'grid' ? (
            // Grid View
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredCompanies.length > 0 ? (
                filteredCompanies.map((company, idx) => (
                  <Card
                    key={company.id}
                    variant="glass-card"
                    className="animate-slide-in-up hover:scale-105 transition-transform cursor-pointer"
                    style={{ animationDelay: `${idx * 50}ms` }}
                    onClick={() => window.location.href = `/companies/${company.id}`}
                  >
                    <CardHeader>
                      <div className="flex items-start justify-between mb-2">
                        <CardTitle className="text-lg text-gold-400">{company.name}</CardTitle>
                        <Badge variant={getExchangeBadgeVariant(company.exchange)}>
                          {company.exchange}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2 mb-3">
                        <span className="text-sm font-mono text-slate-400">{company.ticker_symbol}</span>
                      </div>
                      <CardDescription className="line-clamp-2">
                        {company.description || 'Junior gold mining company focused on exploration and development.'}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-400">Projects</span>
                        <span className="text-white font-semibold">{company.project_count || 0}</span>
                      </div>
                      {company.website && (
                        <div className="mt-3 pt-3 border-t border-slate-700">
                          <a
                            href={company.website}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-gold-400 hover:text-gold-300 flex items-center gap-1"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <span>Visit Website</span>
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                          </a>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))
              ) : (
                <div className="col-span-full text-center py-12">
                  <div className="text-slate-400 text-lg">No companies found matching "{searchQuery}"</div>
                </div>
              )}
            </div>
          ) : (
            // Table View
            <Card variant="glass-strong">
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="border-b border-slate-700">
                      <tr>
                        <th className="text-left py-4 px-6 text-sm font-semibold text-gold-400">Company</th>
                        <th className="text-left py-4 px-6 text-sm font-semibold text-gold-400">Ticker</th>
                        <th className="text-left py-4 px-6 text-sm font-semibold text-gold-400">Exchange</th>
                        <th className="text-left py-4 px-6 text-sm font-semibold text-gold-400">Projects</th>
                        <th className="text-left py-4 px-6 text-sm font-semibold text-gold-400">Website</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredCompanies.length > 0 ? (
                        filteredCompanies.map((company) => (
                          <tr
                            key={company.id}
                            className="border-b border-slate-800 hover:bg-slate-800/50 transition-colors cursor-pointer"
                            onClick={() => window.location.href = `/companies/${company.id}`}
                          >
                            <td className="py-4 px-6 text-white font-medium">{company.name}</td>
                            <td className="py-4 px-6 text-slate-300 font-mono text-sm">{company.ticker_symbol}</td>
                            <td className="py-4 px-6">
                              <Badge variant={getExchangeBadgeVariant(company.exchange)} className="text-xs">
                                {company.exchange}
                              </Badge>
                            </td>
                            <td className="py-4 px-6 text-slate-300">{company.project_count || 0}</td>
                            <td className="py-4 px-6">
                              {company.website ? (
                                <a
                                  href={company.website}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-gold-400 hover:text-gold-300 text-sm"
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                  </svg>
                                </a>
                              ) : (
                                <span className="text-slate-600">—</span>
                              )}
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={5} className="py-12 text-center text-slate-400">
                            No companies found matching "{searchQuery}"
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </section>
    </div>
  );
}
