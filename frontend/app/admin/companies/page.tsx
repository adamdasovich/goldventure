'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';

interface ScrapedPerson {
  full_name: string;
  title: string;
  role_type: string;
  biography?: string;
  photo_url?: string;
  linkedin_url?: string;
}

interface ScrapedDocument {
  title: string;
  document_type: string;
  source_url: string;
  year?: number;
}

interface ScrapedNews {
  title: string;
  source_url: string;
  publication_date?: string;
}

interface ScrapedProject {
  name: string;
  description?: string;
  location?: string;
}

interface ScrapedCompany {
  name: string;
  legal_name?: string;
  ticker_symbol?: string;
  exchange?: string;
  tagline?: string;
  description?: string;
  logo_url?: string;
  ir_contact_email?: string;
  general_email?: string;
  general_phone?: string;
  street_address?: string;
  linkedin_url?: string;
  twitter_url?: string;
  facebook_url?: string;
  youtube_url?: string;
}

interface PreviewData {
  company: ScrapedCompany;
  people: ScrapedPerson[];
  documents: ScrapedDocument[];
  news: ScrapedNews[];
  projects: ScrapedProject[];
}

interface PreviewResult {
  data: PreviewData;
  errors: string[];
  completeness_score: number;
}

export default function CompanyOnboardingPage() {
  const { accessToken } = useAuth();
  const [url, setUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [previewData, setPreviewData] = useState<PreviewResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saveResult, setSaveResult] = useState<{ success: boolean; company_id?: number; company_name?: string } | null>(null);

  const handlePreview = async () => {
    if (!url.trim()) {
      setError('Please enter a company website URL');
      return;
    }

    setIsLoading(true);
    setError(null);
    setPreviewData(null);
    setSaveResult(null);

    try {
      const response = await fetch('/api/admin/companies/scrape-preview/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ url: url.trim() }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || 'Failed to scrape website');
      }

      const data = await response.json();
      setPreviewData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!previewData) return;

    setIsSaving(true);
    setError(null);

    try {
      const response = await fetch('/api/admin/companies/scrape-save/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ url: url.trim() }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || 'Failed to save company');
      }

      const data = await response.json();
      setSaveResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    setUrl('');
    setPreviewData(null);
    setError(null);
    setSaveResult(null);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-100">Onboard New Company</h2>
          <p className="text-slate-400 mt-1">
            Enter a company website URL to automatically scrape and populate company data
          </p>
        </div>
        <div className="flex gap-3">
          <Link
            href="/admin/companies/pending"
            className="px-4 py-2 bg-gold-500 hover:bg-gold-600 text-slate-900 font-medium rounded-lg transition-colors flex items-center gap-2 text-sm"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
            Review Pending
          </Link>
          <Link
            href="/admin/companies/update"
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center gap-2 text-sm"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Update Existing
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
          <Link
            href="/admin/companies/failed"
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg transition-colors flex items-center gap-2 text-sm"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            Failed Discoveries
          </Link>
        </div>
      </div>

      {/* URL Input */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
        <div className="flex gap-4">
          <div className="flex-1">
            <label htmlFor="url" className="block text-sm font-medium text-slate-300 mb-2">
              Company Website URL
            </label>
            <input
              type="url"
              id="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://www.companywebsite.com"
              className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-gold-500"
              disabled={isLoading || isSaving}
            />
          </div>
          <div className="flex items-end gap-2">
            <button
              onClick={handlePreview}
              disabled={isLoading || isSaving}
              className="px-6 py-2 bg-gold-500 hover:bg-gold-600 text-slate-900 font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Scraping...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  Preview
                </>
              )}
            </button>
            {previewData && (
              <button
                onClick={handleReset}
                className="px-4 py-2 border border-slate-600 text-slate-300 hover:bg-slate-700 rounded-lg transition-colors"
              >
                Reset
              </button>
            )}
          </div>
        </div>

        {error && (
          <div className="mt-4 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400">
            {error}
          </div>
        )}
      </div>

      {/* Save Success Message */}
      {saveResult?.success && (
        <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center">
              <svg className="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-emerald-400">Company Saved Successfully!</h3>
              <p className="text-slate-300">
                <strong>{saveResult.company_name}</strong> has been added to the database.
              </p>
              <Link
                href={`/companies/${saveResult.company_id}`}
                className="inline-flex items-center gap-1 text-gold-400 hover:text-gold-300 mt-2"
              >
                View Company Profile
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Preview Results */}
      {previewData && !saveResult && (
        <div className="space-y-6">
          {/* Completeness Score */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-slate-100">Data Completeness Score</h3>
                <p className="text-slate-400 text-sm mt-1">
                  Based on the extracted data from the website
                </p>
              </div>
              <div className="text-right">
                <div className={`text-3xl font-bold ${
                  previewData.completeness_score >= 70 ? 'text-emerald-400' :
                  previewData.completeness_score >= 40 ? 'text-yellow-400' : 'text-red-400'
                }`}>
                  {previewData.completeness_score}%
                </div>
                <div className="text-sm text-slate-400">
                  {previewData.completeness_score >= 70 ? 'Good' :
                   previewData.completeness_score >= 40 ? 'Fair' : 'Needs Review'}
                </div>
              </div>
            </div>
            <div className="mt-4 h-2 bg-slate-700 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all ${
                  previewData.completeness_score >= 70 ? 'bg-emerald-500' :
                  previewData.completeness_score >= 40 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${previewData.completeness_score}%` }}
              />
            </div>
          </div>

          {/* Company Info */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-slate-100 mb-4">Company Information</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-slate-500 uppercase tracking-wider">Name</label>
                <p className="text-slate-200">{previewData.data.company.name || 'N/A'}</p>
              </div>
              <div>
                <label className="text-xs text-slate-500 uppercase tracking-wider">Ticker / Exchange</label>
                <p className="text-slate-200">
                  {previewData.data.company.ticker_symbol || 'N/A'}
                  {previewData.data.company.exchange && ` (${previewData.data.company.exchange})`}
                </p>
              </div>
              <div className="col-span-2">
                <label className="text-xs text-slate-500 uppercase tracking-wider">Tagline</label>
                <p className="text-slate-200">{previewData.data.company.tagline || 'N/A'}</p>
              </div>
              <div className="col-span-2">
                <label className="text-xs text-slate-500 uppercase tracking-wider">Description</label>
                <p className="text-slate-200 text-sm">{previewData.data.company.description || 'N/A'}</p>
              </div>
              {previewData.data.company.logo_url && (
                <div className="col-span-2">
                  <label className="text-xs text-slate-500 uppercase tracking-wider">Logo</label>
                  <img
                    src={previewData.data.company.logo_url}
                    alt="Company Logo"
                    className="mt-2 h-16 object-contain bg-white rounded p-2"
                  />
                </div>
              )}
            </div>

            {/* Contact Info */}
            {(previewData.data.company.ir_contact_email || previewData.data.company.general_phone) && (
              <div className="mt-6 pt-4 border-t border-slate-700">
                <h4 className="text-sm font-medium text-slate-300 mb-3">Contact Information</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  {previewData.data.company.ir_contact_email && (
                    <div>
                      <label className="text-xs text-slate-500">IR Email</label>
                      <p className="text-slate-200">{previewData.data.company.ir_contact_email}</p>
                    </div>
                  )}
                  {previewData.data.company.general_phone && (
                    <div>
                      <label className="text-xs text-slate-500">Phone</label>
                      <p className="text-slate-200">{previewData.data.company.general_phone}</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Social Media */}
            {(previewData.data.company.linkedin_url || previewData.data.company.twitter_url) && (
              <div className="mt-4 flex gap-3">
                {previewData.data.company.linkedin_url && (
                  <a href={previewData.data.company.linkedin_url} target="_blank" rel="noopener noreferrer" className="text-slate-400 hover:text-slate-200">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
                    </svg>
                  </a>
                )}
                {previewData.data.company.twitter_url && (
                  <a href={previewData.data.company.twitter_url} target="_blank" rel="noopener noreferrer" className="text-slate-400 hover:text-slate-200">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                    </svg>
                  </a>
                )}
              </div>
            )}
          </div>

          {/* People */}
          {previewData.data.people.length > 0 && (
            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-slate-100 mb-4">
                Team Members ({previewData.data.people.length})
              </h3>
              <div className="grid gap-3">
                {previewData.data.people.slice(0, 10).map((person, index) => (
                  <div key={index} className="flex items-center gap-3 p-3 bg-slate-900/50 rounded-lg">
                    {person.photo_url ? (
                      <img src={person.photo_url} alt={person.full_name} className="w-10 h-10 rounded-full object-cover" />
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-slate-700 flex items-center justify-center">
                        <span className="text-slate-400 text-sm">{person.full_name[0]}</span>
                      </div>
                    )}
                    <div>
                      <p className="text-slate-200 font-medium">{person.full_name}</p>
                      <p className="text-slate-400 text-sm">{person.title || person.role_type}</p>
                    </div>
                  </div>
                ))}
                {previewData.data.people.length > 10 && (
                  <p className="text-slate-500 text-sm">...and {previewData.data.people.length - 10} more</p>
                )}
              </div>
            </div>
          )}

          {/* Documents */}
          {previewData.data.documents.length > 0 && (
            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-slate-100 mb-4">
                Documents Found ({previewData.data.documents.length})
              </h3>
              <div className="space-y-2">
                {previewData.data.documents.slice(0, 10).map((doc, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <div>
                        <p className="text-slate-200 text-sm">{doc.title}</p>
                        <p className="text-slate-500 text-xs">{doc.document_type} {doc.year && `(${doc.year})`}</p>
                      </div>
                    </div>
                  </div>
                ))}
                {previewData.data.documents.length > 10 && (
                  <p className="text-slate-500 text-sm">...and {previewData.data.documents.length - 10} more</p>
                )}
              </div>
            </div>
          )}

          {/* News */}
          {previewData.data.news.length > 0 && (
            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-slate-100 mb-4">
                News Releases ({previewData.data.news.length})
              </h3>
              <div className="space-y-2">
                {previewData.data.news.slice(0, 5).map((item, index) => (
                  <div key={index} className="p-3 bg-slate-900/50 rounded-lg">
                    <p className="text-slate-200 text-sm">{item.title}</p>
                    {item.publication_date && (
                      <p className="text-slate-500 text-xs mt-1">{item.publication_date}</p>
                    )}
                  </div>
                ))}
                {previewData.data.news.length > 5 && (
                  <p className="text-slate-500 text-sm">...and {previewData.data.news.length - 5} more</p>
                )}
              </div>
            </div>
          )}

          {/* Projects */}
          {previewData.data.projects.length > 0 && (
            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-slate-100 mb-4">
                Projects ({previewData.data.projects.length})
              </h3>
              <div className="space-y-2">
                {previewData.data.projects.map((project, index) => (
                  <div key={index} className="p-3 bg-slate-900/50 rounded-lg">
                    <p className="text-slate-200 font-medium">{project.name}</p>
                    {project.location && (
                      <p className="text-slate-400 text-sm mt-1">{project.location}</p>
                    )}
                    {project.description && (
                      <p className="text-slate-500 text-sm mt-1">{project.description}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Errors/Warnings */}
          {previewData.errors.length > 0 && (
            <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-yellow-400 mb-2">Warnings</h3>
              <ul className="space-y-1">
                {previewData.errors.map((err, index) => (
                  <li key={index} className="text-yellow-300 text-sm">- {err}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Save Button */}
          <div className="flex justify-end gap-4">
            <button
              onClick={handleReset}
              className="px-6 py-2 border border-slate-600 text-slate-300 hover:bg-slate-700 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="px-6 py-2 bg-emerald-500 hover:bg-emerald-600 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isSaving ? (
                <>
                  <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Saving...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Save Company
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
