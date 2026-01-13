'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/contexts/AuthContext';

interface UpcomingEvent {
  id: number;
  title: string;
  company_id: number;
  company_name: string;
  company_ticker: string;
  scheduled_start: string;
  scheduled_end: string | null;
  status: 'live' | 'upcoming';
  format: 'video' | 'text';
  registered_count: number;
}

interface ActiveFinancing {
  id: number;
  company_id: number;
  company_name: string;
  company_ticker: string;
  financing_type: string;
  financing_type_display: string;
  amount_raised_usd: number | null;
  closing_date: string | null;
  status: string;
}

interface FeaturedProperty {
  id: number;
  slug: string;
  title: string;
  summary: string;
  location: string;
  country: string;
  primary_mineral: string;
  total_hectares: number | null;
  asking_price: number | null;
  price_currency: string;
  listing_type: string;
  exploration_stage: string;
  primary_image_url: string | null;
  next_rotation: string | null;
  is_manual_selection: boolean;
}

interface HeroData {
  upcoming_events: UpcomingEvent[];
  active_financings: ActiveFinancing[];
  featured_property: FeaturedProperty | null;
}

interface HeroCardsProps {
  onLoginClick: () => void;
  onRegisterClick: () => void;
}

export function HeroCards({ onLoginClick, onRegisterClick }: HeroCardsProps) {
  const { user } = useAuth();
  const [data, setData] = useState<HeroData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHeroData();
  }, []);

  const fetchHeroData = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/hero-section/`);
      if (!response.ok) throw new Error('Failed to fetch hero data');
      const heroData = await response.json();
      setData(heroData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  const formatCurrency = (amount: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const getTimeUntil = (dateString: string) => {
    const now = new Date();
    const eventDate = new Date(dateString);
    const diffMs = eventDate.getTime() - now.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const diffHours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));

    if (diffDays > 0) return `In ${diffDays} day${diffDays > 1 ? 's' : ''}`;
    if (diffHours > 0) return `In ${diffHours} hour${diffHours > 1 ? 's' : ''}`;
    return 'Soon';
  };

  const handleCardClick = (e: React.MouseEvent, requiresAuth: boolean, href: string) => {
    if (requiresAuth && !user) {
      e.preventDefault();
      onLoginClick();
    }
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[1, 2, 3].map((i) => (
          <Card key={i} variant="glass-card" className="animate-pulse">
            <CardContent className="p-6">
              <div className="h-8 bg-slate-700/50 rounded mb-4"></div>
              <div className="h-32 bg-slate-700/30 rounded"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-400">
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* Card 1: Upcoming Speaking Events */}
      <Card variant="glass-card" className="hover:border-gold-400/50 transition-all duration-300">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg text-gold-400 flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              Upcoming Events
            </CardTitle>
            {data?.upcoming_events.some(e => e.status === 'live') && (
              <Badge variant="gold" className="bg-red-500 border-red-500 animate-pulse text-xs">
                Live Now
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="pt-2">
          {data?.upcoming_events && data.upcoming_events.length > 0 ? (
            <div className="max-h-[280px] overflow-y-auto space-y-3 pr-1">
              {data.upcoming_events.map((event) => (
                <Link
                  key={event.id}
                  href={`/companies/${event.company_id}`}
                  onClick={(e) => handleCardClick(e, true, `/companies/${event.company_id}`)}
                  className="block"
                >
                  <div className={`p-3 rounded-lg transition-all ${
                    event.status === 'live'
                      ? 'bg-red-500/10 border border-red-500/30 hover:bg-red-500/20'
                      : 'bg-slate-800/50 hover:bg-slate-700/50'
                  }`}>
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <h4 className="text-sm font-medium text-white truncate">{event.title}</h4>
                        <p className="text-xs text-slate-400 mt-1">{event.company_name}</p>
                      </div>
                      {event.status === 'live' ? (
                        <Badge variant="gold" className="bg-red-500 border-red-500 text-xs flex-shrink-0">
                          <span className="w-1.5 h-1.5 bg-white rounded-full mr-1 animate-pulse"></span>
                          Live
                        </Badge>
                      ) : (
                        <span className="text-xs text-gold-400 flex-shrink-0">{getTimeUntil(event.scheduled_start)}</span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 mt-2 text-xs text-slate-500">
                      <span>{formatDate(event.scheduled_start)}</span>
                      <span>•</span>
                      <span>{formatTime(event.scheduled_start)}</span>
                    </div>
                  </div>
                </Link>
              ))}
              {data.upcoming_events.length > 3 && (
                <p className="text-xs text-slate-500 text-center mt-2">
                  +{data.upcoming_events.length - 3} more events
                </p>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500">
              <svg className="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <p className="text-sm">No upcoming events this week</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Card 2: Available Financing Opportunities */}
      <Card variant="glass-card" className="hover:border-gold-400/50 transition-all duration-300">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg text-gold-400 flex items-center gap-2">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Financing Opportunities
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-2">
          {data?.active_financings && data.active_financings.length > 0 ? (
            <div className="max-h-[280px] overflow-y-auto space-y-3 pr-1">
              {data.active_financings.map((financing) => (
                <Link
                  key={financing.id}
                  href={`/companies/${financing.company_id}/financing`}
                  onClick={(e) => handleCardClick(e, true, `/companies/${financing.company_id}/financing`)}
                  className="block"
                >
                  <div className="p-3 rounded-lg bg-slate-800/50 hover:bg-slate-700/50 transition-all">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <h4 className="text-sm font-medium text-white truncate">{financing.company_name}</h4>
                        <p className="text-xs text-slate-400 mt-1">{financing.company_ticker}</p>
                      </div>
                      <Badge variant="copper" className="text-xs flex-shrink-0">
                        {financing.financing_type_display}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between mt-2">
                      {financing.amount_raised_usd && (
                        <span className="text-sm font-semibold text-gold-400">
                          {formatCurrency(financing.amount_raised_usd)}
                        </span>
                      )}
                      {financing.closing_date && (
                        <span className="text-xs text-slate-500">
                          Closes: {formatDate(financing.closing_date)}
                        </span>
                      )}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500">
              <svg className="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-sm">No active financing opportunities</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Card 3: Featured Prospector's Listing */}
      <Card variant="glass-card" className="hover:border-gold-400/50 transition-all duration-300 relative overflow-hidden">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg text-gold-400 flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              Featured Property
            </CardTitle>
            <Badge variant="gold" className="text-xs">Featured</Badge>
          </div>
        </CardHeader>
        <CardContent className="pt-2">
          {data?.featured_property ? (
            <Link
              href={`/properties/${data.featured_property.slug}`}
              onClick={(e) => handleCardClick(e, true, `/properties/${data.featured_property!.slug}`)}
              className="block"
            >
              <div className="max-h-[280px] overflow-y-auto space-y-3 pr-1">
                {/* Property Image */}
                {data.featured_property.primary_image_url ? (
                  <div className="relative h-32 rounded-lg overflow-hidden">
                    <img
                      src={data.featured_property.primary_image_url}
                      alt={data.featured_property.title}
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-slate-900/80 to-transparent"></div>
                    <div className="absolute bottom-2 left-2 right-2">
                      <h4 className="text-sm font-semibold text-white truncate">{data.featured_property.title}</h4>
                    </div>
                  </div>
                ) : (
                  <div className="h-32 rounded-lg bg-gradient-to-br from-gold-500/20 to-copper-500/20 flex items-center justify-center">
                    <div className="text-center">
                      <svg className="w-8 h-8 mx-auto text-gold-400/50 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                      </svg>
                      <h4 className="text-sm font-semibold text-white truncate px-2">{data.featured_property.title}</h4>
                    </div>
                  </div>
                )}

                {/* Property Details */}
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-xs text-slate-400">
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    </svg>
                    <span>{data.featured_property.location}, {data.featured_property.country}</span>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <Badge variant="slate" className="text-xs">
                      {data.featured_property.primary_mineral}
                    </Badge>
                    <Badge variant="slate" className="text-xs">
                      {data.featured_property.exploration_stage}
                    </Badge>
                  </div>

                  {data.featured_property.asking_price && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold text-gold-400">
                        {formatCurrency(data.featured_property.asking_price, data.featured_property.price_currency)}
                      </span>
                      <span className="text-xs text-slate-500">
                        {data.featured_property.listing_type}
                      </span>
                    </div>
                  )}

                  {data.featured_property.total_hectares && (
                    <p className="text-xs text-slate-500">
                      {data.featured_property.total_hectares.toLocaleString()} hectares
                    </p>
                  )}
                </div>
              </div>
            </Link>
          ) : (
            <div className="text-center py-8 text-slate-500">
              <svg className="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              </svg>
              <p className="text-sm">No featured property available</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default HeroCards;
