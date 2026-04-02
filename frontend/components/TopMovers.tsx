"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { marketAPI, type TopMover } from "@/lib/api";

export default function TopMovers() {
  const [movers, setMovers] = useState<TopMover[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchMovers = useCallback(async () => {
    try {
      const data = await marketAPI.getTopMovers(5, 7);
      setMovers(data.movers);
      setError(false);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMovers();
  }, [fetchMovers]);

  if (loading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className="h-10 bg-slate-700/30 rounded-lg animate-pulse"
          />
        ))}
      </div>
    );
  }

  if (error || movers.length === 0) {
    return (
      <div className="text-center py-6 text-slate-500">
        <p className="text-sm">No stock data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-1.5">
      {movers.map((m) => (
        <Link
          key={m.company_id}
          href={`/companies/${m.company_id}`}
          className="group flex items-center justify-between px-3 py-2 rounded-lg bg-slate-800/40 hover:bg-slate-800/70 transition-colors"
        >
          <div className="flex-1 min-w-0 mr-3">
            <p className="text-sm font-medium text-slate-200 truncate group-hover:text-gold-400 transition-colors">
              {m.company_name}
            </p>
            <p className="text-xs text-slate-500">{m.ticker}</p>
          </div>
          <div className="text-right flex-shrink-0">
            <p className="text-sm font-semibold text-slate-200">
              ${m.price.toFixed(2)}{" "}
              <span className="text-[10px] text-slate-500">{m.currency}</span>
            </p>
            <p
              className={`text-xs font-medium ${
                m.change_percent >= 0 ? "text-emerald-400" : "text-red-400"
              }`}
            >
              {m.change_percent >= 0 ? "+" : ""}
              {m.change_percent.toFixed(2)}%
            </p>
          </div>
        </Link>
      ))}
      <p className="text-[10px] text-slate-600 text-center pt-1">
        7-day price change · Market data delayed
      </p>
    </div>
  );
}
