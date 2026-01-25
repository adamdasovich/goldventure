'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';

interface ScrapedCompany {
  name: string;
  ticker_symbol?: string;
  exchange?: string;
}

interface ScrapingJobStatus {
  id: number;
  status: 'pending' | 'running' | 'success' | 'failed' | 'partial' | 'cancelled';
  started_at: string | null;
  completed_at: string | null;
  data_extracted: { company: ScrapedCompany } | null;
  error_messages: string[];
  company_id?: number;
}

export default function CompanyOnboardingPage() {
  const { accessToken } = useAuth();
  const [url, setUrl] = useState('');
  const [isOnboarding, setIsOnboarding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveResult, setSaveResult] = useState<{ success: boolean; company_id?: number; company_name?: string } | null>(null);
  const [onboardingStatus, setOnboardingStatus] = useState<string>('');
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  // Poll for onboarding job completion
  const pollOnboardingStatus = useCallback(async (jobId: number) => {
    try {
      const response = await fetch(`/api/admin/companies/scraping-jobs/${jobId}/`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to check onboarding status');
      }

      const jobData: ScrapingJobStatus = await response.json();

      if (jobData.status === 'running' || jobData.status === 'pending') {
        setOnboardingStatus(jobData.status === 'running' ? 'Scraping and saving company data...' : 'Waiting in queue...');
        return; // Keep polling
      }

      // Job completed - stop polling
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }

      setIsOnboarding(false);

      if (jobData.status === 'success') {
        // Extract company info from job data
        const companyData = jobData.data_extracted?.company;
        setSaveResult({
          success: true,
          company_id: jobData.company_id || undefined,
          company_name: companyData?.name || 'Company',
        });
        setOnboardingStatus('');
      } else if (jobData.status === 'failed') {
        setError(jobData.error_messages?.[0] || 'Onboarding failed');
        setOnboardingStatus('');
      }
    } catch (err) {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
      setIsOnboarding(false);
      setError(err instanceof Error ? err.message : 'An error occurred while checking status');
      setOnboardingStatus('');
    }
  }, [accessToken]);

  // Single-step onboarding: scrape and save in one action
  const handleOnboard = async () => {
    if (!url.trim()) {
      setError('Please enter a company website URL');
      return;
    }

    setIsOnboarding(true);
    setError(null);
    setSaveResult(null);
    setOnboardingStatus('Starting onboarding...');

    try {
      // Call scrape-save directly (scrapes AND saves in one step)
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
        throw new Error(errData.error || 'Failed to start onboarding');
      }

      const data = await response.json();

      if (data.status === 'processing' && data.job_id) {
        // Async onboarding - start polling for completion
        setOnboardingStatus('Scraping and saving company data (this may take a few minutes)...');

        // Start polling every 3 seconds
        pollIntervalRef.current = setInterval(() => {
          pollOnboardingStatus(data.job_id);
        }, 3000);

        // Also poll immediately
        pollOnboardingStatus(data.job_id);
      } else if (data.success) {
        // Synchronous save completed (legacy response)
        setSaveResult(data);
        setIsOnboarding(false);
        setOnboardingStatus('');
      } else {
        throw new Error('Unexpected response from server');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setIsOnboarding(false);
      setOnboardingStatus('');
    }
  };

  const handleReset = () => {
    // Stop any active polling
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    setUrl('');
    setError(null);
    setSaveResult(null);
    setOnboardingStatus('');
    setIsOnboarding(false);
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
            href="/admin/glossary/pending"
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors flex items-center gap-2 text-sm"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            Review Glossary Terms
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
              disabled={isOnboarding}
            />
          </div>
          <div className="flex items-end gap-2">
            <button
              onClick={handleOnboard}
              disabled={isOnboarding}
              className="px-6 py-2 bg-emerald-500 hover:bg-emerald-600 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isOnboarding ? (
                <>
                  <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  {onboardingStatus || 'Onboarding...'}
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  Onboard Company
                </>
              )}
            </button>
            {(saveResult || error) && (
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

      {/* Success Message */}
      {saveResult?.success && (
        <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center">
              <svg className="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-emerald-400">Company Onboarded Successfully!</h3>
              <p className="text-slate-300">
                <strong>{saveResult.company_name}</strong> has been added to the database. News scraping has been triggered automatically.
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

      {/* Onboarding Progress */}
      {isOnboarding && (
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-gold-500/20 flex items-center justify-center">
              <svg className="animate-spin w-6 h-6 text-gold-400" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-slate-100">Onboarding in Progress</h3>
              <p className="text-slate-400 mt-1">{onboardingStatus}</p>
              <p className="text-slate-500 text-sm mt-2">
                This process scrapes the company website, extracts data, saves to the database, and triggers news scraping. Please wait...
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
