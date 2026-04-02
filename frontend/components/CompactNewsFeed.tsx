"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import { Calendar, ExternalLink, Loader2 } from "lucide-react";

interface NewsArticle {
  id: number;
  title: string;
  url: string;
  source_name: string;
  published_at: string | null;
  summary: string;
  image_url: string;
}

export default function CompactNewsFeed() {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);

  const API_URL =
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(
          `${API_URL}/news/articles/?limit=6&offset=0&days=7`,
        );
        if (!res.ok) throw new Error();
        const data = await res.json();
        setArticles(data.articles || []);
      } catch {
        // silent fail — section just won't show
      } finally {
        setLoading(false);
      }
    })();
  }, [API_URL]);

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "";
    const date = new Date(dateString);
    const now = new Date();
    const diffHours = Math.floor(
      (now.getTime() - date.getTime()) / (1000 * 60 * 60),
    );
    if (diffHours < 1) return "Just now";
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="w-5 h-5 text-gold-400 animate-spin" />
      </div>
    );
  }

  if (articles.length === 0) return null;

  return (
    <div className="space-y-3">
      {articles.map((article) => (
        <a
          key={article.id}
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="group flex gap-3 p-2.5 rounded-lg bg-slate-800/40 hover:bg-slate-800/70 transition-colors"
        >
          {/* Thumbnail */}
          {article.image_url ? (
            <div className="relative w-20 h-14 flex-shrink-0 rounded-md overflow-hidden bg-slate-700/50">
              <Image
                src={article.image_url}
                alt=""
                fill
                sizes="80px"
                className="object-cover"
              />
            </div>
          ) : (
            <div className="w-20 h-14 flex-shrink-0 rounded-md bg-slate-700/30 flex items-center justify-center">
              <ExternalLink className="w-4 h-4 text-slate-600" />
            </div>
          )}

          {/* Content */}
          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-medium text-slate-200 group-hover:text-gold-400 transition-colors line-clamp-2 leading-snug">
              {article.title}
            </h4>
            <div className="flex items-center gap-2 mt-1 text-[11px] text-slate-500">
              {article.published_at && (
                <>
                  <span className="inline-flex items-center gap-0.5">
                    <Calendar className="w-3 h-3" />
                    {formatDate(article.published_at)}
                  </span>
                  <span>·</span>
                </>
              )}
              <span className="truncate">{article.source_name}</span>
            </div>
          </div>
        </a>
      ))}
    </div>
  );
}
