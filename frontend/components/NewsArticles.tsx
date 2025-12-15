'use client';

import { useState, useEffect, useRef } from 'react';
import { ExternalLink, Newspaper, Calendar, ChevronDown, RefreshCw, Loader2 } from 'lucide-react';

interface NewsArticle {
  id: number;
  title: string;
  url: string;
  source_name: string;
  source_id: number;
  published_at: string | null;
  author: string;
  summary: string;
  image_url: string;
}

interface NewsArticlesProps {
  initialLimit?: number;
  showLoadMore?: boolean;
}

export default function NewsArticles({ initialLimit = 10, showLoadMore = true }: NewsArticlesProps) {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

  const fetchArticles = async (newOffset: number = 0, append: boolean = false) => {
    try {
      if (append) {
        setLoadingMore(true);
      } else {
        setLoading(true);
      }

      const res = await fetch(
        `${API_URL}/news/articles/?limit=${initialLimit}&offset=${newOffset}&days=7`
      );

      if (!res.ok) {
        throw new Error('Failed to fetch news articles');
      }

      const data = await res.json();

      if (append) {
        setArticles(prev => [...prev, ...data.articles]);
      } else {
        setArticles(data.articles);
      }

      setTotal(data.total);
      setOffset(newOffset);
      setHasMore(newOffset + data.articles.length < data.total);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load news');
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  useEffect(() => {
    fetchArticles();
  }, []);

  const handleLoadMore = () => {
    fetchArticles(offset + initialLimit, true);
  };

  const handleRefresh = () => {
    setOffset(0);
    fetchArticles(0);
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Unknown date';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffHours < 1) {
      return 'Just now';
    } else if (diffHours < 24) {
      return `${diffHours}h ago`;
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return `${diffDays}d ago`;
    } else {
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      });
    }
  };

  if (loading && articles.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 text-gold-400 animate-spin" />
        <span className="ml-3 text-slate-400">Loading news articles...</span>
      </div>
    );
  }

  if (error && articles.length === 0) {
    return (
      <div className="text-center py-12">
        <Newspaper className="w-12 h-12 text-slate-500 mx-auto mb-4" />
        <p className="text-slate-400 mb-4">{error}</p>
        <button
          onClick={handleRefresh}
          className="inline-flex items-center gap-2 px-4 py-2 bg-gold-400/10 text-gold-400 rounded-lg hover:bg-gold-400/20 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Try Again
        </button>
      </div>
    );
  }

  if (articles.length === 0) {
    return (
      <div className="text-center py-12">
        <Newspaper className="w-12 h-12 text-slate-500 mx-auto mb-4" />
        <p className="text-slate-400">No news articles available at the moment.</p>
        <p className="text-sm text-slate-500 mt-2">Check back later for the latest mining industry news.</p>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="space-y-4">
      {/* Header with refresh button */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-400">{total} articles from the last 7 days</span>
        </div>
        <button
          onClick={handleRefresh}
          disabled={loading}
          className="inline-flex items-center gap-1 px-3 py-1 text-sm text-slate-400 hover:text-gold-400 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Articles List */}
      <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-slate-800">
        {articles.map((article) => (
          <a
            key={article.id}
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="group block p-4 bg-slate-800/50 border border-slate-700/50 rounded-lg hover:bg-slate-800/80 hover:border-gold-400/30 transition-all duration-200"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                {/* Title */}
                <h4 className="font-medium text-white group-hover:text-gold-400 transition-colors line-clamp-2">
                  {article.title}
                </h4>

                {/* Meta info */}
                <div className="flex items-center gap-3 mt-2 text-sm text-slate-400">
                  <span className="inline-flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5" />
                    {formatDate(article.published_at)}
                  </span>
                  <span className="text-slate-600">|</span>
                  <span className="truncate">{article.source_name}</span>
                </div>

                {/* Summary if available */}
                {article.summary && (
                  <p className="mt-2 text-sm text-slate-400 line-clamp-2">{article.summary}</p>
                )}
              </div>

              {/* External link indicator */}
              <ExternalLink className="w-4 h-4 text-slate-500 group-hover:text-gold-400 flex-shrink-0 transition-colors" />
            </div>
          </a>
        ))}

        {/* Load More Button */}
        {showLoadMore && hasMore && (
          <div className="pt-4 text-center">
            <button
              onClick={handleLoadMore}
              disabled={loadingMore}
              className="inline-flex items-center gap-2 px-6 py-3 bg-slate-800 border border-slate-700 rounded-lg text-slate-300 hover:bg-slate-700 hover:border-gold-400/30 transition-all disabled:opacity-50"
            >
              {loadingMore ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Loading...
                </>
              ) : (
                <>
                  <ChevronDown className="w-4 h-4" />
                  Load More Articles
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
