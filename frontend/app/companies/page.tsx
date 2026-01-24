'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { companyAPI, type Company } from '@/lib/api';
import LogoMono from '@/components/LogoMono';
import { useAuth } from '@/contexts/AuthContext';

// Commodity filter options grouped by category
const COMMODITY_GROUPS = {
  'Precious Metals': [
    { value: 'gold', label: 'Gold' },
    { value: 'silver', label: 'Silver' },
    { value: 'platinum', label: 'Platinum Group Metals' },
    { value: 'palladium', label: 'Palladium' },
  ],
  'Critical/Battery Minerals': [
    { value: 'lithium', label: 'Lithium' },
    { value: 'cobalt', label: 'Cobalt' },
    { value: 'nickel', label: 'Nickel' },
    { value: 'graphite', label: 'Graphite' },
    { value: 'manganese', label: 'Manganese' },
    { value: 'rare_earths', label: 'Rare Earth Elements' },
  ],
  'Base Metals': [
    { value: 'copper', label: 'Copper' },
    { value: 'zinc', label: 'Zinc' },
    { value: 'lead', label: 'Lead' },
    { value: 'iron_ore', label: 'Iron Ore' },
    { value: 'tin', label: 'Tin' },
  ],
  'Energy/Specialty': [
    { value: 'uranium', label: 'Uranium' },
    { value: 'vanadium', label: 'Vanadium' },
    { value: 'tungsten', label: 'Tungsten' },
    { value: 'molybdenum', label: 'Molybdenum' },
    { value: 'antimony', label: 'Antimony' },
    { value: 'niobium', label: 'Niobium' },
    { value: 'tantalum', label: 'Tantalum' },
  ],
  'Other': [
    { value: 'multi_metal', label: 'Multi-Metal' },
    { value: 'other', label: 'Other' },
  ],
};

const PAGE_SIZE = 9;

export default function CompaniesPage() {
  const { user, accessToken } = useAuth();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCommodities, setSelectedCommodities] = useState<string[]>([]);
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [showCommodityDropdown, setShowCommodityDropdown] = useState(false);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  const fetchCompanies = useCallback(async () => {
    try {
      setLoading(true);
      const response = await companyAPI.getAll({
        search: searchQuery || undefined,
        commodity: selectedCommodities.length > 0 ? selectedCommodities.join(',') : undefined,
        page: currentPage,
        page_size: PAGE_SIZE,
      });
      setCompanies(response.results || []);
      setTotalCount(response.count || 0);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch companies');
    } finally {
      setLoading(false);
    }
  }, [searchQuery, selectedCommodities, currentPage]);

  useEffect(() => {
    fetchCompanies();
  }, [fetchCompanies]);

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, selectedCommodities]);

  const handleDelete = async (companyId: number, companyName: string, e: React.MouseEvent) => {
    e.stopPropagation();

    if (!confirm(`Are you sure you want to delete ${companyName}? This action cannot be undone.`)) {
      return;
    }

    setDeletingId(companyId);
    try {
      const response = await fetch(`/api/companies/${companyId}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to delete company');
      }

      // Refresh the list
      fetchCompanies();
      alert(`${companyName} has been deleted successfully.`);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete company');
    } finally {
      setDeletingId(null);
    }
  };

  const toggleCommodity = (commodity: string) => {
    setSelectedCommodities(prev =>
      prev.includes(commodity)
        ? prev.filter(c => c !== commodity)
        : [...prev, commodity]
    );
  };

  const clearCommodities = () => {
    setSelectedCommodities([]);
  };

  const getExchangeBadgeVariant = (exchange: string) => {
    const variants: Record<string, 'gold' | 'copper' | 'slate'> = {
      'TSX': 'gold',
      'TSXV': 'copper',
      'NYSE': 'gold',
      'NASDAQ': 'gold',
    };
    return variants[exchange.toUpperCase()] || 'slate';
  };

  const totalPages = Math.ceil(totalCount / PAGE_SIZE);

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
            Comprehensive database of junior mining companies exploring gold, silver, lithium, copper, rare earths & critical minerals with detailed resource estimates and project data
          </p>
        </div>
      </section>

      {/* Search and Filters */}
      <section className="py-8 px-4 sm:px-6 lg:px-8 bg-gradient-slate">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col gap-4">
            {/* Top row: Search, Commodity Filter, View Toggle */}
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

              {/* Commodity Filter Dropdown */}
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setShowCommodityDropdown(!showCommodityDropdown)}
                  className="flex items-center gap-2 px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-lg text-white hover:border-gold-400 transition-colors"
                >
                  <svg className="w-5 h-5 text-gold-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                  </svg>
                  <span>
                    {selectedCommodities.length > 0
                      ? `${selectedCommodities.length} Commodity${selectedCommodities.length > 1 ? ' Types' : ''}`
                      : 'Filter by Commodity'}
                  </span>
                  <svg className={`w-4 h-4 transition-transform ${showCommodityDropdown ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {showCommodityDropdown && (
                  <div className="absolute top-full left-0 mt-2 w-80 max-h-96 overflow-y-auto bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-50">
                    <div className="p-3 border-b border-slate-700 flex justify-between items-center">
                      <span className="text-sm text-slate-400">Select Commodities</span>
                      {selectedCommodities.length > 0 && (
                        <button
                          type="button"
                          onClick={clearCommodities}
                          className="text-xs text-gold-400 hover:text-gold-300"
                        >
                          Clear All
                        </button>
                      )}
                    </div>
                    {Object.entries(COMMODITY_GROUPS).map(([group, commodities]) => (
                      <div key={group} className="p-2">
                        <div className="text-xs font-semibold text-gold-400 uppercase tracking-wide px-2 py-1">
                          {group}
                        </div>
                        {commodities.map(({ value, label }) => (
                          <label
                            key={value}
                            className="flex items-center gap-2 px-2 py-1.5 hover:bg-slate-700/50 rounded cursor-pointer"
                          >
                            <input
                              type="checkbox"
                              checked={selectedCommodities.includes(value)}
                              onChange={() => toggleCommodity(value)}
                              className="w-4 h-4 rounded border-slate-600 text-gold-500 focus:ring-gold-500 bg-slate-700"
                            />
                            <span className="text-sm text-slate-300">{label}</span>
                          </label>
                        ))}
                      </div>
                    ))}
                  </div>
                )}
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
                  {totalCount} {totalCount === 1 ? 'company' : 'companies'}
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

            {/* Selected commodity tags */}
            {selectedCommodities.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {selectedCommodities.map(commodity => {
                  const commodityLabel = Object.values(COMMODITY_GROUPS)
                    .flat()
                    .find(c => c.value === commodity)?.label || commodity;
                  return (
                    <span
                      key={commodity}
                      className="inline-flex items-center gap-1 px-3 py-1 bg-gold-500/20 text-gold-400 rounded-full text-sm"
                    >
                      {commodityLabel}
                      <button
                        type="button"
                        onClick={() => toggleCommodity(commodity)}
                        className="hover:text-gold-300"
                        title={`Remove ${commodityLabel} filter`}
                        aria-label={`Remove ${commodityLabel} filter`}
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </span>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Click outside to close dropdown */}
      {showCommodityDropdown && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowCommodityDropdown(false)}
        />
      )}

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
              {Array.from({ length: PAGE_SIZE }).map((_, idx) => (
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
              {companies.length > 0 ? (
                companies.map((company, idx) => (
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
                      <div className="mt-3 pt-3 border-t border-slate-700 flex items-center justify-between">
                        {company.website && (
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
                        )}
                        {user?.is_superuser && (
                          <button
                            type="button"
                            onClick={(e) => handleDelete(company.id, company.name, e)}
                            disabled={deletingId === company.id}
                            className="text-xs text-red-400 hover:text-red-300 flex items-center gap-1 disabled:opacity-50"
                            title="Delete company"
                          >
                            {deletingId === company.id ? (
                              <svg className="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                              </svg>
                            ) : (
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                            )}
                          </button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))
              ) : (
                <div className="col-span-full text-center py-12">
                  <div className="text-slate-400 text-lg">
                    {searchQuery || selectedCommodities.length > 0
                      ? 'No companies found matching your filters'
                      : 'No companies found'}
                  </div>
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
                        {user?.is_superuser && (
                          <th className="text-left py-4 px-6 text-sm font-semibold text-gold-400">Actions</th>
                        )}
                      </tr>
                    </thead>
                    <tbody>
                      {companies.length > 0 ? (
                        companies.map((company) => (
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
                                  title={`Visit ${company.name} website`}
                                  aria-label={`Visit ${company.name} website`}
                                >
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                  </svg>
                                </a>
                              ) : (
                                <span className="text-slate-600">—</span>
                              )}
                            </td>
                            {user?.is_superuser && (
                              <td className="py-4 px-6">
                                <button
                                  type="button"
                                  onClick={(e) => handleDelete(company.id, company.name, e)}
                                  disabled={deletingId === company.id}
                                  className="text-red-400 hover:text-red-300 disabled:opacity-50"
                                  title="Delete company"
                                >
                                  {deletingId === company.id ? (
                                    <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                    </svg>
                                  ) : (
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                    </svg>
                                  )}
                                </button>
                              </td>
                            )}
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={user?.is_superuser ? 6 : 5} className="py-12 text-center text-slate-400">
                            {searchQuery || selectedCommodities.length > 0
                              ? 'No companies found matching your filters'
                              : 'No companies found'}
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-8 flex justify-center items-center gap-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </Button>

              {/* Page numbers */}
              {Array.from({ length: totalPages }, (_, i) => i + 1)
                .filter(page => {
                  // Show first, last, current, and adjacent pages
                  if (page === 1 || page === totalPages) return true;
                  if (Math.abs(page - currentPage) <= 1) return true;
                  return false;
                })
                .map((page, idx, arr) => {
                  const showEllipsis = idx > 0 && page - arr[idx - 1] > 1;
                  return (
                    <span key={page} className="flex items-center">
                      {showEllipsis && <span className="px-2 text-slate-500">...</span>}
                      <Button
                        variant={currentPage === page ? 'primary' : 'secondary'}
                        size="sm"
                        onClick={() => setCurrentPage(page)}
                        className="min-w-[40px]"
                      >
                        {page}
                      </Button>
                    </span>
                  );
                })}

              <Button
                variant="secondary"
                size="sm"
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Button>
            </div>
          )}

          {/* Page info */}
          {totalCount > 0 && (
            <div className="mt-4 text-center text-sm text-slate-400">
              Showing {((currentPage - 1) * PAGE_SIZE) + 1} - {Math.min(currentPage * PAGE_SIZE, totalCount)} of {totalCount} companies
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
