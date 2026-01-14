'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface DocumentTypeSummary {
  type: string;
  display_name: string;
  document_count: number;
  chunk_count: number;
}

interface ProcessedByType {
  type: string;
  display_name: string;
  count: number;
  chunks_created: number;
}

interface ProcessedDocumentDetail {
  id: number;
  title: string;
  document_type: string;
  display_type: string;
  company_name: string;
  chunk_count: number;
  document_date: string | null;
}

interface ProcessedDocuments {
  by_type: ProcessedByType[];
  detail: ProcessedDocumentDetail[];
}

interface FailedJob {
  id: number;
  url: string;
  document_type: string;
  company_name: string;
  error_message: string;
  created_at: string;
  started_at: string | null;
}

interface ProcessingJobStats {
  total: number;
  completed: number;
  failed: number;
  pending: number;
  processing: number;
  total_chunks_created: number;
  completed_last_7_days: number;
  failed_jobs: FailedJob[];
}

interface ChromaDBStats {
  document_chunks_collection: number;
  news_chunks_collection: number;
  error?: string;
}

interface TopCompany {
  company: string;
  document_count: number;
}

interface DocumentSummary {
  summary: {
    total_processed_documents: number;
    total_chunks: number;
    news_releases_with_content: number;
  };
  by_document_type: DocumentTypeSummary[];
  processed_documents: ProcessedDocuments;
  processing_jobs: ProcessingJobStats;
  chromadb: ChromaDBStats;
  top_companies: TopCompany[];
  generated_at: string;
}

export default function DocumentSummaryPage() {
  const router = useRouter();
  const { user, accessToken, isLoading: authLoading } = useAuth();
  const [data, setData] = useState<DocumentSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Redirect non-superusers
    if (!authLoading && (!user || !user.is_superuser)) {
      router.push('/dashboard');
      return;
    }

    if (!accessToken) return;

    const fetchData = async () => {
      try {
        const response = await fetch(`${API_URL}/admin/document-summary/`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          if (response.status === 403) {
            router.push('/dashboard');
            return;
          }
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        setData(result);
      } catch (err) {
        console.error('Failed to fetch document summary:', err);
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [accessToken, user, authLoading, router]);

  // Show loading state
  if (authLoading || isLoading) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Document Processing Summary</h1>
          <p className="text-slate-400 mt-1">Loading statistics...</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="glass rounded-xl p-5">
              <div className="h-20 bg-slate-700 rounded animate-pulse" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Document Processing Summary</h1>
          <p className="text-red-400 mt-1">Error: {error}</p>
        </div>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-gold-500 text-slate-900 rounded-lg hover:bg-gold-600 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  // Main stat cards
  const statCards = [
    {
      label: 'Total Documents',
      value: data?.summary.total_processed_documents.toString() || '0',
      icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
      color: 'text-gold-400',
      bgColor: 'bg-gold-500/10',
    },
    {
      label: 'Total Chunks',
      value: data?.summary.total_chunks.toLocaleString() || '0',
      icon: 'M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4',
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/10',
    },
    {
      label: 'News Releases',
      value: data?.summary.news_releases_with_content.toLocaleString() || '0',
      icon: 'M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z',
      color: 'text-green-400',
      bgColor: 'bg-green-500/10',
    },
    {
      label: 'Jobs Completed (7d)',
      value: data?.processing_jobs.completed_last_7_days.toString() || '0',
      icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
      color: 'text-purple-400',
      bgColor: 'bg-purple-500/10',
    },
  ];

  // Document type icons
  const getDocTypeIcon = (type: string) => {
    const icons: Record<string, string> = {
      ni43101: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
      presentation: 'M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z',
      factsheet: 'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
      financial_stmt: 'M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z',
      annual_report: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z',
      mda: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
      map: 'M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7',
      other: 'M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z',
    };
    return icons[type] || icons.other;
  };

  const getDocTypeColor = (type: string) => {
    const colors: Record<string, { text: string; bg: string }> = {
      ni43101: { text: 'text-gold-400', bg: 'bg-gold-500/20' },
      presentation: { text: 'text-blue-400', bg: 'bg-blue-500/20' },
      factsheet: { text: 'text-green-400', bg: 'bg-green-500/20' },
      financial_stmt: { text: 'text-cyan-400', bg: 'bg-cyan-500/20' },
      annual_report: { text: 'text-purple-400', bg: 'bg-purple-500/20' },
      mda: { text: 'text-orange-400', bg: 'bg-orange-500/20' },
      map: { text: 'text-teal-400', bg: 'bg-teal-500/20' },
      other: { text: 'text-slate-400', bg: 'bg-slate-500/20' },
    };
    return colors[type] || colors.other;
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Document Processing Summary</h1>
          <p className="text-slate-400 mt-1">
            Overview of processed documents and ChromaDB statistics
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs text-slate-500">Last updated</p>
          <p className="text-sm text-slate-400">
            {data?.generated_at ? new Date(data.generated_at).toLocaleString() : '-'}
          </p>
        </div>
      </div>

      {/* Main Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat) => (
          <div key={stat.label} className="glass rounded-xl p-5">
            <div className="flex items-center gap-4">
              <div className={`w-12 h-12 rounded-lg ${stat.bgColor} flex items-center justify-center`}>
                <svg className={`w-6 h-6 ${stat.color}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d={stat.icon} />
                </svg>
              </div>
              <div>
                <p className="text-sm text-slate-400">{stat.label}</p>
                <p className="text-xl font-bold text-slate-100">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Document Types Breakdown */}
      <div className="glass rounded-xl p-6">
        <h2 className="text-lg font-semibold text-slate-100 mb-4">Documents by Type</h2>
        {data?.by_document_type && data.by_document_type.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {data.by_document_type.map((docType) => {
              const colors = getDocTypeColor(docType.type);
              return (
                <div key={docType.type} className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
                  <div className="flex items-center gap-3 mb-3">
                    <div className={`w-10 h-10 rounded-lg ${colors.bg} flex items-center justify-center`}>
                      <svg className={`w-5 h-5 ${colors.text}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d={getDocTypeIcon(docType.type)} />
                      </svg>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-200 truncate">{docType.display_name}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-center">
                    <div>
                      <p className="text-2xl font-bold text-slate-100">{docType.document_count}</p>
                      <p className="text-xs text-slate-500">Documents</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-slate-300">{docType.chunk_count.toLocaleString()}</p>
                      <p className="text-xs text-slate-500">Chunks</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-slate-400 text-sm">No processed documents found.</p>
        )}
      </div>

      {/* Processing Jobs Overview */}
      <div className="glass rounded-xl p-6">
        <h2 className="text-lg font-semibold text-slate-100 mb-4">Processing Jobs Overview</h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {[
            { label: 'Pending', count: data?.processing_jobs.pending || 0, color: 'bg-yellow-500' },
            { label: 'Processing', count: data?.processing_jobs.processing || 0, color: 'bg-blue-500' },
            { label: 'Completed', count: data?.processing_jobs.completed || 0, color: 'bg-green-500' },
            { label: 'Failed', count: data?.processing_jobs.failed || 0, color: 'bg-red-500' },
            { label: 'Total Jobs', count: data?.processing_jobs.total || 0, color: 'bg-slate-500' },
          ].map((status) => (
            <div key={status.label} className="text-center">
              <div className={`w-12 h-12 rounded-full ${status.color}/20 flex items-center justify-center mx-auto mb-2`}>
                <span className={`text-lg font-bold ${status.color.replace('bg-', 'text-')}`}>
                  {status.count}
                </span>
              </div>
              <p className="text-sm text-slate-400">{status.label}</p>
            </div>
          ))}
        </div>
        <div className="mt-4 pt-4 border-t border-slate-700/50">
          <p className="text-sm text-slate-400">
            Total chunks created from processing: <span className="text-slate-200 font-medium">{data?.processing_jobs.total_chunks_created?.toLocaleString() || 0}</span>
          </p>
        </div>
      </div>

      {/* Processed Documents Detail */}
      <div className="glass rounded-xl p-6">
        <h2 className="text-lg font-semibold text-slate-100 mb-4">
          <span className="inline-flex items-center gap-2">
            <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Processed Documents with Chunks
          </span>
        </h2>

        {/* Summary by Type */}
        {data?.processed_documents?.by_type && data.processed_documents.by_type.length > 0 && (
          <div className="mb-6">
            <h3 className="text-sm font-medium text-slate-400 mb-3">Summary by Document Type</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {data.processed_documents.by_type.map((item) => {
                const colors = getDocTypeColor(item.type);
                return (
                  <div key={item.type} className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50">
                    <div className="flex items-center gap-2 mb-2">
                      <div className={`w-6 h-6 rounded ${colors.bg} flex items-center justify-center`}>
                        <svg className={`w-3 h-3 ${colors.text}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={getDocTypeIcon(item.type)} />
                        </svg>
                      </div>
                      <span className="text-xs text-slate-400 truncate">{item.display_name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-lg font-bold text-slate-100">{item.count}</span>
                      <span className="text-xs text-slate-500">{item.chunks_created.toLocaleString()} chunks</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Detail Table */}
        {data?.processed_documents?.detail && data.processed_documents.detail.length > 0 ? (
          <div className="overflow-x-auto">
            <h3 className="text-sm font-medium text-slate-400 mb-3">All Processed Documents (sorted by chunk count)</h3>
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">Company</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">Document Title</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">Type</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-slate-400">Chunks</th>
                </tr>
              </thead>
              <tbody>
                {data.processed_documents.detail.map((doc) => {
                  const colors = getDocTypeColor(doc.document_type);
                  return (
                    <tr key={doc.id} className="border-b border-slate-700/50 hover:bg-slate-800/30">
                      <td className="py-3 px-4">
                        <span className="text-sm font-medium text-gold-400">{doc.company_name}</span>
                      </td>
                      <td className="py-3 px-4">
                        <span className="text-sm text-slate-200">{doc.title}</span>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`text-xs px-2 py-1 rounded ${colors.bg} ${colors.text}`}>
                          {doc.display_type}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <span className="text-sm font-bold text-green-400">{doc.chunk_count.toLocaleString()}</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <p className="text-xs text-slate-500 mt-3">Showing top 50 documents by chunk count</p>
          </div>
        ) : (
          <p className="text-slate-400 text-sm">No processed documents found.</p>
        )}
      </div>

      {/* Failed Jobs Details */}
      {data?.processing_jobs.failed_jobs && data.processing_jobs.failed_jobs.length > 0 && (
        <div className="glass rounded-xl p-6 border border-red-500/20">
          <h2 className="text-lg font-semibold text-slate-100 mb-4">
            <span className="inline-flex items-center gap-2">
              <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Failed Jobs ({data.processing_jobs.failed} total)
            </span>
          </h2>
          <div className="space-y-3">
            {data.processing_jobs.failed_jobs.map((job) => (
              <div key={job.id} className="bg-slate-800/50 rounded-lg p-4 border border-red-500/10">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <span className="text-sm font-medium text-slate-200">{job.company_name}</span>
                    <span className="mx-2 text-slate-600">|</span>
                    <span className="text-xs text-slate-400">{job.document_type}</span>
                  </div>
                  <span className="text-xs text-slate-500">
                    {new Date(job.created_at).toLocaleDateString()}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mb-2 truncate" title={job.url}>
                  {job.url}
                </p>
                <div className="bg-red-500/10 rounded p-2">
                  <p className="text-xs text-red-400 font-mono break-words">
                    {job.error_message}
                  </p>
                </div>
              </div>
            ))}
          </div>
          <p className="text-xs text-slate-500 mt-4">Showing most recent 20 failed jobs</p>
        </div>
      )}

      {/* ChromaDB & Top Companies - Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* ChromaDB Stats */}
        <div className="glass rounded-xl p-6">
          <h2 className="text-lg font-semibold text-slate-100 mb-4">ChromaDB Collections</h2>
          {data?.chromadb.error ? (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
              <p className="text-red-400 text-sm">ChromaDB error: {data.chromadb.error}</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-slate-800/50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                    <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-200">Document Chunks</p>
                    <p className="text-xs text-slate-500">document_chunks collection</p>
                  </div>
                </div>
                <p className="text-xl font-bold text-blue-400">{data?.chromadb.document_chunks_collection.toLocaleString()}</p>
              </div>
              <div className="flex items-center justify-between p-4 bg-slate-800/50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
                    <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-200">News Chunks</p>
                    <p className="text-xs text-slate-500">news_chunks collection</p>
                  </div>
                </div>
                <p className="text-xl font-bold text-green-400">{data?.chromadb.news_chunks_collection.toLocaleString()}</p>
              </div>
            </div>
          )}
        </div>

        {/* Top Companies */}
        <div className="glass rounded-xl p-6">
          <h2 className="text-lg font-semibold text-slate-100 mb-4">Top Companies by Documents</h2>
          {data?.top_companies && data.top_companies.length > 0 ? (
            <div className="space-y-2">
              {data.top_companies.map((company, idx) => (
                <div key={company.company} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-gold-500/20 flex items-center justify-center">
                      <span className="text-sm font-bold text-gold-400">{idx + 1}</span>
                    </div>
                    <p className="text-sm font-medium text-slate-200">{company.company}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-lg font-bold text-slate-100">{company.document_count}</span>
                    <span className="text-xs text-slate-500">docs</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-slate-400 text-sm">No companies with processed documents.</p>
          )}
        </div>
      </div>

      {/* Back to Dashboard Link */}
      <div className="flex justify-center">
        <button
          onClick={() => router.push('/dashboard')}
          className="text-sm text-slate-400 hover:text-gold-400 transition-colors flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to Dashboard
        </button>
      </div>
    </div>
  );
}
