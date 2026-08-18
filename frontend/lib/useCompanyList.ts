"use client";

import { useEffect, useState } from "react";

import { companyAPI } from "@/lib/api";
import type { PickableCompany } from "@/components/ui/CompanyPicker";

/**
 * The full company list, fetched once per page load and shared.
 *
 * Some tools (Portfolio X-Ray, Peer Comparison) accept companies but return no
 * `available_companies` list of their own, which is why they ended up asking
 * users to type raw database IDs. There are only a few hundred companies, so
 * pulling the whole list once is cheaper than wiring a search-as-you-type
 * endpoint, and it lets the picker filter instantly.
 */

let cache: PickableCompany[] | null = null;
let inflight: Promise<PickableCompany[]> | null = null;

async function loadCompanies(): Promise<PickableCompany[]> {
  if (cache) return cache;
  if (inflight) return inflight;

  inflight = companyAPI
    .getAll({ page_size: 500 })
    .then((res) => {
      const rows = (res?.results ?? []).map((c) => ({
        id: c.id,
        name: c.name,
        ticker: c.ticker_symbol ?? undefined,
        exchange: c.exchange ?? undefined,
      }));
      rows.sort((a, b) => a.name.localeCompare(b.name));
      cache = rows;
      return rows;
    })
    .finally(() => {
      inflight = null;
    });

  return inflight;
}

export function useCompanyList(): {
  companies: PickableCompany[];
  loading: boolean;
  error: string | null;
} {
  const [companies, setCompanies] = useState<PickableCompany[]>(cache ?? []);
  const [loading, setLoading] = useState(cache === null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (cache) return;
    let cancelled = false;

    loadCompanies()
      .then((rows) => {
        if (!cancelled) setCompanies(rows);
      })
      .catch(() => {
        if (!cancelled) setError("Could not load the company list.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return { companies, loading, error };
}
