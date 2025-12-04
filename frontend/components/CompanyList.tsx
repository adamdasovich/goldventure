'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/Card';
import { Badge } from './ui/Badge';
import { companyAPI } from '@/lib/api';
import type { Company } from '@/types/api';

export default function CompanyList() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadCompanies();
  }, []);

  const loadCompanies = async () => {
    try {
      setLoading(true);
      const response = await companyAPI.getAll();
      setCompanies(response.results || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load companies');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[1, 2, 3].map((i) => (
          <Card key={i} variant="glass-card" className="h-48 animate-shimmer">
            <div />
          </Card>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <Card variant="glass" className="p-8 text-center">
        <div className="text-error text-lg mb-2">Error loading companies</div>
        <div className="text-slate-400">{error}</div>
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {companies.map((company) => (
        <Card key={company.id} variant="glass-card" className="animate-slide-in-up">
          <CardHeader>
            <div className="flex items-start justify-between mb-2">
              <Badge variant="gold">{company.ticker_symbol}</Badge>
              <Badge variant="slate">{company.exchange}</Badge>
            </div>
            <CardTitle className="text-xl">{company.name}</CardTitle>
            <div className="flex items-center gap-2 mt-2 text-sm text-slate-400">
              <span>{company.headquarters_country}</span>
              {company.project_count !== undefined && (
                <>
                  <span>•</span>
                  <span>{company.project_count} projects</span>
                </>
              )}
            </div>
          </CardHeader>

          <CardContent>
            <p className="text-sm text-slate-300 line-clamp-3">{company.description}</p>

            {company.ceo && (
              <div className="mt-4 pt-4 border-t border-slate-700/50">
                <div className="text-xs text-slate-500">CEO</div>
                <div className="text-sm text-slate-300">{company.ceo}</div>
              </div>
            )}

            {company.website && (
              <div className="mt-4">
                <a
                  href={company.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-gold-400 hover:text-gold-300 transition-smooth"
                >
                  Visit Website →
                </a>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
