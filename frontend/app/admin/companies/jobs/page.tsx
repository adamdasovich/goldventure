'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';

interface ScrapingJob {
  id: number;
  company_name_input: string;
  website_url: string;
  status: 'pending' | 'running' | 'success' | 'failed';
  started_at: string;
  completed_at: string | null;
  company_id: number | null;
  company_name: string | null;
  documents_found: number;
  people_found: number;
  news_found: number;
  initiated_by: string | null;
  error_messages: string[];
}

export default function ScrapingJobsPage() {
  const { accessToken } = useAuth();
  const [jobs, setJobs] = useState<ScrapingJob[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchJobs = async () => {
    try {
      const response = await fetch('/api/admin/companies/scraping-jobs/', {
        headers: {
          'Authorization': `Token ${accessToken}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch scraping jobs');
      }

      const data = await response.json();
      setJobs(data.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (accessToken) {
      fetchJobs();
    }
  }, [accessToken]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pending':
        return <span className="px-2 py-1 text-xs rounded-full bg-slate-500/20 text-slate-400">Pending</span>;
      case 'running':
        return <span className="px-2 py-1 text-xs rounded-full bg-blue-500/20 text-blue-400">Running</span>;
      case 'success':
        return <span className="px-2 py-1 text-xs rounded-full bg-emerald-500/20 text-emerald-400">Success</span>;
      case 'failed':
        return <span className="px-2 py-1 text-xs rounded-full bg-red-500/20 text-red-400">Failed</span>;
      default:
        return <span className="px-2 py-1 text-xs rounded-full bg-slate-500/20 text-slate-400">{status}</span>;
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString();
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-2 border-gold-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-100">Scraping Jobs</h2>
          <p className="text-slate-400 mt-1">
            History of all company scraping operations
          </p>
        </div>
        <button
          onClick={fetchJobs}
          className="px-4 py-2 border border-slate-600 text-slate-300 hover:bg-slate-700 rounded-lg transition-colors flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400">
          {error}
        </div>
      )}

      {jobs.length === 0 ? (
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-12 text-center">
          <svg className="w-12 h-12 text-slate-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <h3 className="text-lg font-semibold text-slate-300 mb-2">No Scraping Jobs</h3>
          <p className="text-slate-400">
            No company scraping jobs have been run yet.
          </p>
        </div>
      ) : (
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Company</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Results</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Started</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">By</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700">
              {jobs.map((job) => (
                <tr key={job.id} className="hover:bg-slate-700/30 transition-colors">
                  <td className="px-4 py-4">
                    <div>
                      {job.company_name ? (
                        <a
                          href={`/companies/${job.company_id}`}
                          className="text-gold-400 hover:text-gold-300 font-medium"
                        >
                          {job.company_name}
                        </a>
                      ) : (
                        <span className="text-slate-200">{job.company_name_input}</span>
                      )}
                      <p className="text-slate-500 text-xs mt-1 truncate max-w-xs">{job.website_url}</p>
                    </div>
                  </td>
                  <td className="px-4 py-4">
                    {getStatusBadge(job.status)}
                    {job.error_messages && job.error_messages.length > 0 && (
                      <p className="text-red-400 text-xs mt-1 truncate max-w-xs" title={job.error_messages.join(', ')}>
                        {job.error_messages[0]}
                      </p>
                    )}
                  </td>
                  <td className="px-4 py-4">
                    {job.status === 'success' && (
                      <div className="text-sm text-slate-400">
                        <span title="People">{job.people_found} people</span>
                        <span className="mx-1">•</span>
                        <span title="Documents">{job.documents_found} docs</span>
                        <span className="mx-1">•</span>
                        <span title="News">{job.news_found} news</span>
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-4 text-sm text-slate-400">
                    {formatDate(job.started_at)}
                  </td>
                  <td className="px-4 py-4 text-sm text-slate-400">
                    {job.initiated_by || 'System'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
