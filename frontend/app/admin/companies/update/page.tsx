'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';

interface Company {
  id: number;
  name: string;
  ticker_symbol: string;
  exchange: string;
  website: string;
  last_scraped_at: string | null;
  data_completeness_score: number;
}

interface UpdateResult {
  success: boolean;
  company_id: number;
  company_name: string;
  completeness_score: number;
  people_count: number;
  documents_count: number;
  news_count: number;
  processing_jobs?: Array<{ id: number; type: string; url: string }>;
  processing_started?: boolean;
  errors: string[];
}

export default function UpdateCompanyPage() {
  const { accessToken } = useAuth();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [isLoadingCompanies, setIsLoadingCompanies] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateResult, setUpdateResult] = useState<UpdateResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch list of companies
  useEffect(() => {
    const fetchCompanies = async () => {
      try {
        const response = await fetch('/api/companies/', {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
          },
        });

        if (!response.ok) {
          throw new Error('Failed to fetch companies');
        }

        const data = await response.json();
        setCompanies(data.results || data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load companies');
      } finally {
        setIsLoadingCompanies(false);
      }
    };

    if (accessToken) {
      fetchCompanies();
    }
  }, [accessToken]);

  const handleUpdate = async () => {
    if (!selectedCompany || !selectedCompany.website) {
      setError('Selected company has no website URL');
      return;
    }

    if (!accessToken) {
      setError('You are not logged in. Please refresh the page and log in again.');
      return;
    }

    setIsUpdating(true);
    setError(null);
    setUpdateResult(null);

    try {
      const response = await fetch('/api/admin/companies/scrape-save/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          url: selectedCompany.website,
          update_existing: true,
        }),
      });

      if (!response.ok) {
        // Handle authentication errors
        if (response.status === 401) {
          setError('Your session has expired. Please refresh the page and log in again.');
          return;
        }
        if (response.status === 403) {
          setError('You do not have permission to update companies. Admin access required.');
          return;
        }
        const errData = await response.json();
        throw new Error(errData.error || errData.detail || 'Failed to update company');
      }

      const data = await response.json();
      setUpdateResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleReset = () => {
    setSelectedCompany(null);
    setUpdateResult(null);
    setError(null);
  };

  const filteredCompanies = companies.filter(company =>
    company.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    company.ticker_symbol?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never';
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-100">Update Existing Company</h2>
          <p className="text-slate-400 mt-1">
            Re-scrape and update company information from their website
          </p>
        </div>
        <div className="flex gap-3">
          <Link
            href="/admin/companies"
            className="px-4 py-2 bg-gold-500 hover:bg-gold-600 text-slate-900 font-medium rounded-lg transition-colors flex items-center gap-2 text-sm"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Onboard New Company
          </Link>
          <Link
            href="/admin/companies/jobs"
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg transition-colors flex items-center gap-2 text-sm"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            Job History
          </Link>
        </div>
      </div>

      {/* Company Selection */}
      {!selectedCompany && !updateResult && (
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
          <div className="mb-4">
            <label htmlFor="search" className="block text-sm font-medium text-slate-300 mb-2">
              Search Companies
            </label>
            <input
              type="text"
              id="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by name or ticker..."
              className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-gold-500"
            />
          </div>

          {isLoadingCompanies ? (
            <div className="flex items-center justify-center py-8">
              <svg className="animate-spin w-6 h-6 text-gold-500" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            </div>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {filteredCompanies.length === 0 ? (
                <p className="text-slate-500 text-center py-4">No companies found</p>
              ) : (
                filteredCompanies.map((company) => (
                  <button
                    key={company.id}
                    onClick={() => setSelectedCompany(company)}
                    className="w-full flex items-center justify-between p-4 bg-slate-900/50 hover:bg-slate-700/50 rounded-lg transition-colors text-left"
                  >
                    <div>
                      <p className="text-slate-200 font-medium">{company.name}</p>
                      <p className="text-slate-400 text-sm">
                        {company.ticker_symbol && `${company.ticker_symbol}`}
                        {company.exchange && ` (${company.exchange.toUpperCase()})`}
                      </p>
                    </div>
                    <div className="text-right">
                      <div className={`text-sm font-medium ${
                        company.data_completeness_score >= 70 ? 'text-emerald-400' :
                        company.data_completeness_score >= 40 ? 'text-yellow-400' : 'text-red-400'
                      }`}>
                        {company.data_completeness_score}% complete
                      </div>
                      <p className="text-slate-500 text-xs">
                        Last updated: {formatDate(company.last_scraped_at)}
                      </p>
                    </div>
                  </button>
                ))
              )}
            </div>
          )}
        </div>
      )}

      {/* Selected Company Confirmation */}
      {selectedCompany && !updateResult && (
        <div className="space-y-6">
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-slate-100 mb-4">Selected Company</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-slate-500 uppercase tracking-wider">Name</label>
                <p className="text-slate-200">{selectedCompany.name}</p>
              </div>
              <div>
                <label className="text-xs text-slate-500 uppercase tracking-wider">Ticker / Exchange</label>
                <p className="text-slate-200">
                  {selectedCompany.ticker_symbol || 'N/A'}
                  {selectedCompany.exchange && ` (${selectedCompany.exchange.toUpperCase()})`}
                </p>
              </div>
              <div className="col-span-2">
                <label className="text-xs text-slate-500 uppercase tracking-wider">Website URL</label>
                <p className="text-slate-200">{selectedCompany.website || 'No website URL available'}</p>
              </div>
              <div>
                <label className="text-xs text-slate-500 uppercase tracking-wider">Current Completeness</label>
                <p className={`font-medium ${
                  selectedCompany.data_completeness_score >= 70 ? 'text-emerald-400' :
                  selectedCompany.data_completeness_score >= 40 ? 'text-yellow-400' : 'text-red-400'
                }`}>
                  {selectedCompany.data_completeness_score}%
                </p>
              </div>
              <div>
                <label className="text-xs text-slate-500 uppercase tracking-wider">Last Scraped</label>
                <p className="text-slate-200">{formatDate(selectedCompany.last_scraped_at)}</p>
              </div>
            </div>

            {!selectedCompany.website && (
              <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg text-yellow-400 text-sm">
                Warning: This company has no website URL. You will need to add a website URL before updating.
              </div>
            )}
          </div>

          {error && (
            <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400">
              {error}
            </div>
          )}

          <div className="flex justify-end gap-4">
            <button
              onClick={handleReset}
              className="px-6 py-2 border border-slate-600 text-slate-300 hover:bg-slate-700 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleUpdate}
              disabled={isUpdating || !selectedCompany.website}
              className="px-6 py-2 bg-gold-500 hover:bg-gold-600 text-slate-900 font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isUpdating ? (
                <>
                  <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Updating...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Update Company
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Update Result */}
      {updateResult && (
        <div className="space-y-6">
          <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center">
                <svg className="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-emerald-400">Company Updated Successfully!</h3>
                <p className="text-slate-300">
                  <strong>{updateResult.company_name}</strong> has been updated.
                </p>
              </div>
            </div>
          </div>

          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-slate-100 mb-4">Update Summary</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-slate-900/50 rounded-lg p-4 text-center">
                <p className="text-2xl font-bold text-gold-400">{updateResult.completeness_score}%</p>
                <p className="text-slate-400 text-sm">Completeness</p>
              </div>
              <div className="bg-slate-900/50 rounded-lg p-4 text-center">
                <p className="text-2xl font-bold text-blue-400">{updateResult.people_count}</p>
                <p className="text-slate-400 text-sm">Team Members</p>
              </div>
              <div className="bg-slate-900/50 rounded-lg p-4 text-center">
                <p className="text-2xl font-bold text-purple-400">{updateResult.documents_count}</p>
                <p className="text-slate-400 text-sm">Documents</p>
              </div>
              <div className="bg-slate-900/50 rounded-lg p-4 text-center">
                <p className="text-2xl font-bold text-emerald-400">{updateResult.news_count}</p>
                <p className="text-slate-400 text-sm">News Items</p>
              </div>
            </div>

            {updateResult.processing_jobs && updateResult.processing_jobs.length > 0 && (
              <div className="mt-6 pt-4 border-t border-slate-700">
                <h4 className="text-sm font-medium text-slate-300 mb-3">Document Processing Jobs Created</h4>
                <div className="space-y-2">
                  {updateResult.processing_jobs.map((job) => (
                    <div key={job.id} className="flex items-center gap-3 p-2 bg-slate-900/50 rounded text-sm">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        job.type === 'ni43101' ? 'bg-purple-500/20 text-purple-400' :
                        job.type === 'presentation' ? 'bg-blue-500/20 text-blue-400' :
                        'bg-emerald-500/20 text-emerald-400'
                      }`}>
                        {job.type}
                      </span>
                      <span className="text-slate-400 truncate flex-1">{job.url}</span>
                    </div>
                  ))}
                </div>
                {updateResult.processing_started && (
                  <p className="text-slate-500 text-sm mt-2">
                    Document processing has started in the background.
                  </p>
                )}
              </div>
            )}

            {updateResult.errors && updateResult.errors.length > 0 && (
              <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                <p className="text-yellow-400 text-sm font-medium">Warnings:</p>
                <ul className="mt-1 space-y-1">
                  {updateResult.errors.map((err, index) => (
                    <li key={index} className="text-yellow-300 text-sm">- {err}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div className="flex justify-end gap-4">
            <button
              onClick={handleReset}
              className="px-6 py-2 border border-slate-600 text-slate-300 hover:bg-slate-700 rounded-lg transition-colors"
            >
              Update Another Company
            </button>
            <Link
              href={`/companies/${updateResult.company_id}`}
              className="px-6 py-2 bg-gold-500 hover:bg-gold-600 text-slate-900 font-medium rounded-lg transition-colors flex items-center gap-2"
            >
              View Company Profile
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </Link>
          </div>
        </div>
      )}

      {error && !selectedCompany && (
        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400">
          {error}
        </div>
      )}
    </div>
  );
}
