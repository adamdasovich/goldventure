'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import LogoMono from '@/components/LogoMono';
import { LoginModal, RegisterModal } from '@/components/auth';
import { useAuth } from '@/contexts/AuthContext';
import { PropertyListingListItem } from '@/types/property';
import { accessRequestAPI } from '@/lib/api';
import type { CompanyAccessRequest } from '@/types/api';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface DashboardStats {
  totalListings: number;
  activeListings: number;
  totalViews: number;
  totalInquiries: number;
  pendingInquiries: number;
  watchlistCount: number;
}

interface RecentInquiry {
  id: number;
  listing_title: string;
  listing_slug: string;
  inquiry_type_display: string;
  status: string;
  status_display: string;
  subject: string;
  created_at: string;
  is_received: boolean;
}

interface NewsScrapeJob {
  id: number;
  status: string;
  is_scheduled: boolean;
  triggered_by: string;
  articles_new: number;
  created_at: string;
  completed_at: string | null;
}

export default function DashboardPage() {
  const router = useRouter();
  const { user, logout, accessToken, isLoading: authLoading } = useAuth();
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);

  const [stats, setStats] = useState<DashboardStats>({
    totalListings: 0,
    activeListings: 0,
    totalViews: 0,
    totalInquiries: 0,
    pendingInquiries: 0,
    watchlistCount: 0,
  });
  const [recentListings, setRecentListings] = useState<PropertyListingListItem[]>([]);
  const [recentInquiries, setRecentInquiries] = useState<RecentInquiry[]>([]);
  const [loading, setLoading] = useState(true);

  // News scraping state
  const [scrapeJob, setScrapeJob] = useState<NewsScrapeJob | null>(null);
  const [scrapeLoading, setScrapeLoading] = useState(false);
  const [scrapeError, setScrapeError] = useState<string | null>(null);

  // Company access requests state (for superusers)
  const [pendingAccessRequests, setPendingAccessRequests] = useState<CompanyAccessRequest[]>([]);
  const [accessRequestsLoading, setAccessRequestsLoading] = useState(false);
  const [processingRequestId, setProcessingRequestId] = useState<number | null>(null);

  // Investment interest dashboard state (for superusers)
  const [investmentDashboard, setInvestmentDashboard] = useState<{
    total_interests: number;
    total_shares_requested: number;
    total_amount_interested: string;
    recent_interests_7d: number;
    status_breakdown: { status: string; count: number; total_amount: string | null }[];
    active_financings: {
      financing_id: number;
      company_name: string;
      financing_type: string;
      target_amount: string | null;
      total_interests: number;
      total_amount: string;
      percentage_filled: string;
    }[];
  } | null>(null);
  const [investmentDashboardLoading, setInvestmentDashboardLoading] = useState(false);

  useEffect(() => {
    const fetchDashboardData = async () => {
      if (!accessToken) return;

      setLoading(true);

      try {
        // Fetch user's listings
        const listingsRes = await fetch(`${API_URL}/properties/listings/?my_listings=true`, {
          headers: { 'Authorization': `Bearer ${accessToken}` },
        });
        const listingsData = listingsRes.ok ? await listingsRes.json() : [];
        const listings = Array.isArray(listingsData) ? listingsData : listingsData.results || [];

        // Fetch watchlist
        const watchlistRes = await fetch(`${API_URL}/properties/watchlist/`, {
          headers: { 'Authorization': `Bearer ${accessToken}` },
        });
        const watchlistData = watchlistRes.ok ? await watchlistRes.json() : [];
        const watchlist = Array.isArray(watchlistData) ? watchlistData : watchlistData.results || [];

        // Fetch inquiries
        const inquiriesRes = await fetch(`${API_URL}/properties/inquiries/`, {
          headers: { 'Authorization': `Bearer ${accessToken}` },
        });
        const inquiriesData = inquiriesRes.ok ? await inquiriesRes.json() : [];
        const inquiries = Array.isArray(inquiriesData) ? inquiriesData : inquiriesData.results || [];

        // Calculate stats
        const activeListings = listings.filter((l: PropertyListingListItem) => l.status === 'active').length;
        const totalViews = listings.reduce((sum: number, l: PropertyListingListItem) => sum + (l.views_count || 0), 0);
        const pendingInquiries = inquiries.filter((i: RecentInquiry) => i.status === 'new' || i.status === 'read').length;

        setStats({
          totalListings: listings.length,
          activeListings,
          totalViews,
          totalInquiries: inquiries.length,
          pendingInquiries,
          watchlistCount: watchlist.length,
        });

        // Set recent listings (last 5)
        setRecentListings(listings.slice(0, 5));

        // Set recent inquiries (last 5)
        setRecentInquiries(inquiries.slice(0, 5).map((i: any) => ({
          id: i.id,
          listing_title: i.listing?.title || 'Unknown Listing',
          listing_slug: i.listing?.slug || '',
          inquiry_type_display: i.inquiry_type_display || i.inquiry_type,
          status: i.status,
          status_display: i.status_display || i.status,
          subject: i.subject,
          created_at: i.created_at,
          is_received: i.listing?.prospector_id === user?.id,
        })));

      } catch (err) {
        console.error('Failed to fetch dashboard data:', err);
      } finally {
        setLoading(false);
      }
    };

    if (!authLoading && accessToken) {
      fetchDashboardData();
      // Fetch pending access requests and investment dashboard for superusers
      if (user?.is_superuser) {
        fetchPendingAccessRequests();
        fetchInvestmentDashboard();
      }
    } else if (!authLoading && !accessToken) {
      setLoading(false);
    }
  }, [accessToken, authLoading, user?.id, user?.is_superuser]);

  // Fetch pending company access requests (superuser only)
  const fetchPendingAccessRequests = async () => {
    if (!accessToken || !user?.is_superuser) return;

    setAccessRequestsLoading(true);
    try {
      const response = await accessRequestAPI.getPending(accessToken);
      setPendingAccessRequests(response.results || []);
    } catch (err) {
      console.error('Failed to fetch pending access requests:', err);
    } finally {
      setAccessRequestsLoading(false);
    }
  };

  // Fetch investment interest dashboard data (superuser only)
  const fetchInvestmentDashboard = async () => {
    if (!accessToken || !user?.is_superuser) return;

    setInvestmentDashboardLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/investment-interest/admin/dashboard/`, {
        headers: { 'Authorization': `Bearer ${accessToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setInvestmentDashboard(data);
      }
    } catch (err) {
      console.error('Failed to fetch investment dashboard:', err);
    } finally {
      setInvestmentDashboardLoading(false);
    }
  };

  // Handle approve/reject access request
  const handleAccessRequestReview = async (requestId: number, action: 'approve' | 'reject') => {
    if (!accessToken) return;

    setProcessingRequestId(requestId);
    try {
      await accessRequestAPI.review(accessToken, requestId, action);
      // Remove from list after successful review
      setPendingAccessRequests(prev => prev.filter(r => r.id !== requestId));
    } catch (err) {
      console.error(`Failed to ${action} access request:`, err);
      alert(`Failed to ${action} request. Please try again.`);
    } finally {
      setProcessingRequestId(null);
    }
  };

  const formatPrice = (price: number | null, currency: string) => {
    if (!price) return 'Contact for Price';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency || 'CAD',
      maximumFractionDigits: 0,
    }).format(price);
  };

  // Trigger news scrape
  const triggerNewsScrape = async () => {
    if (!accessToken) return;

    setScrapeLoading(true);
    setScrapeError(null);
    setScrapeJob(null);

    try {
      const response = await fetch(`${API_URL}/news/scrape/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to trigger scrape');
      }

      const data = await response.json();
      // API returns job_id, normalize to id for consistency
      const jobData = { ...data, id: data.job_id || data.id };
      setScrapeJob(jobData);

      // Poll for status if job is running
      if (jobData.status === 'running' || jobData.status === 'pending') {
        pollScrapeStatus(jobData.id);
      }
    } catch (err: any) {
      setScrapeError(err.message || 'Failed to trigger news scrape');
    } finally {
      setScrapeLoading(false);
    }
  };

  // Poll scrape job status
  const pollScrapeStatus = async (jobId: number) => {
    const maxPolls = 60; // Max 5 minutes (60 * 5 seconds)
    let polls = 0;

    const poll = async () => {
      if (polls >= maxPolls) {
        setScrapeError('Scrape job timed out. Check server logs.');
        return;
      }

      try {
        const response = await fetch(`${API_URL}/news/scrape/status/${jobId}/`, {
          headers: { 'Authorization': `Bearer ${accessToken}` },
        });

        if (response.ok) {
          const data = await response.json();
          // API returns job data nested in 'job' object
          const jobData = data.job || data;
          setScrapeJob(jobData);

          if (jobData.status === 'completed' || jobData.status === 'failed') {
            return; // Done polling
          }
        }

        polls++;
        setTimeout(poll, 5000); // Poll every 5 seconds
      } catch (err) {
        console.error('Error polling scrape status:', err);
        polls++;
        setTimeout(poll, 5000);
      }
    };

    poll();
  };

  // Not logged in state
  if (!authLoading && !user) {
    return (
      <div className="min-h-screen">
        <nav className="glass-nav sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-24">
              <div className="flex items-center space-x-3 cursor-pointer" onClick={() => router.push('/')}>
                <LogoMono className="h-16" />
              </div>
              <div className="flex items-center space-x-4">
                <Button variant="ghost" size="sm" onClick={() => router.push('/properties')}>Properties</Button>
                <Button variant="ghost" size="sm" onClick={() => setShowLogin(true)}>Login</Button>
                <Button variant="primary" size="sm" onClick={() => setShowRegister(true)}>Register</Button>
              </div>
            </div>
          </div>
        </nav>

        {showLogin && (
          <LoginModal
            onClose={() => setShowLogin(false)}
            onSwitchToRegister={() => { setShowLogin(false); setShowRegister(true); }}
          />
        )}
        {showRegister && (
          <RegisterModal
            onClose={() => setShowRegister(false)}
            onSwitchToLogin={() => { setShowRegister(false); setShowLogin(true); }}
          />
        )}

        <div className="max-w-7xl mx-auto px-4 py-16 text-center">
          <Card className="p-8 max-w-md mx-auto">
            <h1 className="text-2xl font-bold text-white mb-4">Sign In Required</h1>
            <p className="text-slate-300 mb-6">You need to be logged in to view your dashboard.</p>
            <Button variant="primary" onClick={() => setShowLogin(true)}>
              Sign In
            </Button>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <nav className="glass-nav sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-24">
            <div className="flex items-center space-x-3 cursor-pointer" onClick={() => router.push('/')}>
              <LogoMono className="h-16" />
            </div>
            <div className="flex items-center space-x-4">
              <Button variant="ghost" size="sm" onClick={() => router.push('/properties')}>Properties</Button>
              <Button variant="ghost" size="sm" onClick={() => router.push('/companies')}>Companies</Button>
              <Button variant="ghost" size="sm" onClick={() => router.push('/metals')}>Metals</Button>
              {user && (
                <>
                  <span className="text-sm text-slate-300">
                    {user.full_name || user.username}
                  </span>
                  <Button variant="ghost" size="sm" onClick={logout}>
                    Logout
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Welcome Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            Welcome back, {user?.full_name || user?.username}
          </h1>
          <p className="text-slate-400">
            Here's an overview of your activity on GoldVenture
          </p>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-gold-500"></div>
          </div>
        )}

        {!loading && (
          <>
            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
              <Card className="p-4 text-center hover:border-gold-500/50 transition-colors cursor-pointer" onClick={() => router.push('/properties/my-listings')}>
                <div className="text-3xl font-bold text-gold-400">{stats.totalListings}</div>
                <div className="text-sm text-slate-400">Total Listings</div>
              </Card>
              <Card className="p-4 text-center hover:border-green-500/50 transition-colors cursor-pointer" onClick={() => router.push('/properties/my-listings')}>
                <div className="text-3xl font-bold text-green-400">{stats.activeListings}</div>
                <div className="text-sm text-slate-400">Active Listings</div>
              </Card>
              <Card className="p-4 text-center">
                <div className="text-3xl font-bold text-blue-400">{stats.totalViews}</div>
                <div className="text-sm text-slate-400">Total Views</div>
              </Card>
              <Card className="p-4 text-center hover:border-purple-500/50 transition-colors cursor-pointer" onClick={() => router.push('/properties/inbox')}>
                <div className="text-3xl font-bold text-purple-400">{stats.totalInquiries}</div>
                <div className="text-sm text-slate-400">Inquiries</div>
              </Card>
              <Card className="p-4 text-center hover:border-orange-500/50 transition-colors cursor-pointer" onClick={() => router.push('/properties/inbox')}>
                <div className="text-3xl font-bold text-orange-400">{stats.pendingInquiries}</div>
                <div className="text-sm text-slate-400">Pending</div>
              </Card>
              <Card className="p-4 text-center hover:border-pink-500/50 transition-colors cursor-pointer" onClick={() => router.push('/properties/watchlist')}>
                <div className="text-3xl font-bold text-pink-400">{stats.watchlistCount}</div>
                <div className="text-sm text-slate-400">Watchlist</div>
              </Card>
            </div>

            {/* Quick Actions */}
            <Card className="p-6 mb-8">
              <h2 className="text-xl font-semibold text-white mb-4">Quick Actions</h2>
              <div className="flex flex-wrap gap-3">
                <Button variant="primary" onClick={() => router.push('/properties/new')}>
                  + Create New Listing
                </Button>
                <Button variant="secondary" onClick={() => router.push('/properties/my-listings')}>
                  Manage My Listings
                </Button>
                <Button variant="secondary" onClick={() => router.push('/properties/inbox')}>
                  View Inbox
                </Button>
                <Button variant="secondary" onClick={() => router.push('/properties/watchlist')}>
                  My Watchlist
                </Button>
                <Button variant="ghost" onClick={() => router.push('/properties')}>
                  Browse Properties
                </Button>
              </div>
            </Card>

            {/* Two Column Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Recent Listings */}
              <Card className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold text-white">My Recent Listings</h2>
                  <Button variant="ghost" size="sm" onClick={() => router.push('/properties/my-listings')}>
                    View All
                  </Button>
                </div>

                {recentListings.length === 0 ? (
                  <div className="text-center py-8">
                    <p className="text-slate-400 mb-4">You haven't created any listings yet.</p>
                    <Button variant="primary" size="sm" onClick={() => router.push('/properties/new')}>
                      Create Your First Listing
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {recentListings.map((listing) => (
                      <div
                        key={listing.id}
                        className="flex items-center gap-4 p-3 rounded-lg bg-slate-800/50 hover:bg-slate-800 cursor-pointer transition-colors"
                        onClick={() => router.push(`/properties/${listing.slug}`)}
                      >
                        <div className="w-16 h-16 rounded-lg bg-slate-700 overflow-hidden flex-shrink-0">
                          {listing.hero_image ? (
                            <img src={listing.hero_image} alt={listing.title} className="w-full h-full object-cover" />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-slate-500">
                              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                              </svg>
                            </div>
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="text-white font-medium truncate">{listing.title}</h3>
                          <p className="text-sm text-slate-400">{listing.province_state}, {listing.country_display}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge variant={listing.status === 'active' ? 'gold' : 'slate'} className="text-xs">
                              {listing.status}
                            </Badge>
                            <span className="text-xs text-slate-500">{listing.views_count || 0} views</span>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-gold-400 font-semibold text-sm">
                            {formatPrice(listing.asking_price, listing.price_currency)}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>

              {/* Recent Inquiries */}
              <Card className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold text-white">Recent Inquiries</h2>
                  <Button variant="ghost" size="sm" onClick={() => router.push('/properties/inbox')}>
                    View All
                  </Button>
                </div>

                {recentInquiries.length === 0 ? (
                  <div className="text-center py-8">
                    <p className="text-slate-400">No inquiries yet.</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {recentInquiries.map((inquiry) => (
                      <div
                        key={inquiry.id}
                        className="p-3 rounded-lg bg-slate-800/50 hover:bg-slate-800 cursor-pointer transition-colors"
                        onClick={() => router.push('/properties/inbox')}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <h3 className="text-white font-medium truncate">{inquiry.subject}</h3>
                            <p className="text-sm text-slate-400 truncate">
                              Re: {inquiry.listing_title}
                            </p>
                          </div>
                          <Badge
                            variant={inquiry.status === 'new' ? 'gold' : inquiry.status === 'responded' ? 'slate' : 'copper'}
                            className="text-xs flex-shrink-0"
                          >
                            {inquiry.status_display}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2 mt-2 text-xs text-slate-500">
                          <span>{inquiry.inquiry_type_display}</span>
                          <span>•</span>
                          <span>{new Date(inquiry.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </div>

            {/* Admin Section */}
            {user?.is_superuser && (
              <Card className="p-6 mt-8 border-gold-500/30">
                <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                  <svg className="w-5 h-5 text-gold-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                  Admin Actions
                </h2>
                <div className="flex flex-wrap gap-3 mb-4">
                  <Button variant="secondary" onClick={() => router.push('/properties/review')}>
                    Review Pending Listings
                  </Button>
                  <Button
                    variant="primary"
                    onClick={triggerNewsScrape}
                    disabled={scrapeLoading || scrapeJob?.status === 'running'}
                  >
                    {scrapeLoading || scrapeJob?.status === 'running' ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Scraping News...
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4 mr-2 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                        </svg>
                        Scrape News Now
                      </>
                    )}
                  </Button>
                </div>

                {/* Scrape Status Display */}
                {scrapeError && (
                  <div className="p-3 rounded-lg bg-red-500/20 border border-red-500/50 text-red-300 text-sm mb-3">
                    <strong>Error:</strong> {scrapeError}
                  </div>
                )}

                {scrapeJob && (
                  <div className={`p-3 rounded-lg border text-sm ${
                    scrapeJob.status === 'completed' ? 'bg-green-500/20 border-green-500/50 text-green-300' :
                    scrapeJob.status === 'failed' ? 'bg-red-500/20 border-red-500/50 text-red-300' :
                    'bg-blue-500/20 border-blue-500/50 text-blue-300'
                  }`}>
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant={
                        scrapeJob.status === 'completed' ? 'gold' :
                        scrapeJob.status === 'failed' ? 'copper' : 'slate'
                      }>
                        {scrapeJob.status.toUpperCase()}
                      </Badge>
                      <span className="text-slate-400">Job #{scrapeJob.id}</span>
                    </div>
                    {scrapeJob.status === 'completed' && (
                      <div className="text-sm">
                        <span className="text-green-400 font-semibold">{scrapeJob.articles_new}</span> new articles saved
                      </div>
                    )}
                    {scrapeJob.status === 'running' && (
                      <div className="text-sm text-blue-300">
                        Scraping in progress... This may take a few minutes.
                      </div>
                    )}
                  </div>
                )}

                {/* Pending Company Access Requests */}
                <div className="mt-6 pt-6 border-t border-slate-700">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                      <svg className="w-5 h-5 text-gold-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                      </svg>
                      Company Portal Access Requests
                      {pendingAccessRequests.length > 0 && (
                        <Badge variant="copper" className="ml-2">{pendingAccessRequests.length} pending</Badge>
                      )}
                    </h3>
                    <Button variant="ghost" size="sm" onClick={fetchPendingAccessRequests} disabled={accessRequestsLoading}>
                      {accessRequestsLoading ? 'Refreshing...' : 'Refresh'}
                    </Button>
                  </div>

                  {accessRequestsLoading && pendingAccessRequests.length === 0 ? (
                    <div className="flex justify-center py-6">
                      <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-gold-500"></div>
                    </div>
                  ) : pendingAccessRequests.length === 0 ? (
                    <div className="text-center py-6 text-slate-400">
                      <svg className="w-12 h-12 mx-auto mb-2 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      No pending access requests
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {pendingAccessRequests.map((request) => (
                        <div
                          key={request.id}
                          className="p-4 rounded-lg bg-slate-800/50 border border-slate-700"
                        >
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-white font-medium">{request.user_name || request.user_email}</span>
                                <Badge variant="slate" className="text-xs">{request.role_display || request.role}</Badge>
                              </div>
                              <p className="text-sm text-gold-400 font-medium mb-1">
                                {request.company_name} {request.company_ticker && `(${request.company_ticker})`}
                              </p>
                              <p className="text-sm text-slate-400">
                                {request.job_title} • {request.work_email}
                              </p>
                              {request.justification && (
                                <p className="text-sm text-slate-500 mt-2 line-clamp-2">
                                  &quot;{request.justification}&quot;
                                </p>
                              )}
                              <p className="text-xs text-slate-500 mt-2">
                                Submitted: {new Date(request.created_at).toLocaleDateString()}
                              </p>
                            </div>
                            <div className="flex items-center gap-2 flex-shrink-0">
                              <Button
                                variant="primary"
                                size="sm"
                                onClick={() => handleAccessRequestReview(request.id, 'approve')}
                                disabled={processingRequestId === request.id}
                              >
                                {processingRequestId === request.id ? (
                                  <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white"></div>
                                ) : (
                                  <>
                                    <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                    </svg>
                                    Approve
                                  </>
                                )}
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleAccessRequestReview(request.id, 'reject')}
                                disabled={processingRequestId === request.id}
                                className="text-red-400 hover:text-red-300 hover:bg-red-500/20"
                              >
                                <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                                Reject
                              </Button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Investment Interest Dashboard */}
                <div className="mt-6 pt-6 border-t border-slate-700">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                      <svg className="w-5 h-5 text-gold-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Investment Interest Dashboard
                    </h3>
                    <Button variant="ghost" size="sm" onClick={fetchInvestmentDashboard} disabled={investmentDashboardLoading}>
                      {investmentDashboardLoading ? 'Refreshing...' : 'Refresh'}
                    </Button>
                  </div>

                  {investmentDashboardLoading && !investmentDashboard ? (
                    <div className="flex justify-center py-6">
                      <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-gold-500"></div>
                    </div>
                  ) : investmentDashboard ? (
                    <div className="space-y-4">
                      {/* Summary Stats */}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                          <p className="text-2xl font-bold text-gold-400">{investmentDashboard.total_interests}</p>
                          <p className="text-xs text-slate-400">Total Interests</p>
                        </div>
                        <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                          <p className="text-2xl font-bold text-white">
                            ${Number(investmentDashboard.total_amount_interested || 0).toLocaleString()}
                          </p>
                          <p className="text-xs text-slate-400">Total Amount</p>
                        </div>
                        <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                          <p className="text-2xl font-bold text-white">
                            {(investmentDashboard.total_shares_requested || 0).toLocaleString()}
                          </p>
                          <p className="text-xs text-slate-400">Total Shares</p>
                        </div>
                        <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                          <p className="text-2xl font-bold text-green-400">{investmentDashboard.recent_interests_7d}</p>
                          <p className="text-xs text-slate-400">Last 7 Days</p>
                        </div>
                      </div>

                      {/* Status Breakdown */}
                      {investmentDashboard.status_breakdown && investmentDashboard.status_breakdown.length > 0 && (
                        <div className="bg-slate-800/30 rounded-lg p-4">
                          <h4 className="text-sm font-medium text-white mb-3">By Status</h4>
                          <div className="flex flex-wrap gap-2">
                            {investmentDashboard.status_breakdown.map((item) => (
                              <Badge
                                key={item.status}
                                variant={item.status === 'pending' ? 'gold' : item.status === 'converted' ? 'copper' : 'slate'}
                              >
                                {item.status}: {item.count}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Active Financings with Interest */}
                      {investmentDashboard.active_financings && investmentDashboard.active_financings.length > 0 && (
                        <div className="bg-slate-800/30 rounded-lg p-4">
                          <h4 className="text-sm font-medium text-white mb-3">Active Financings</h4>
                          <div className="space-y-3">
                            {investmentDashboard.active_financings.map((financing) => (
                              <div
                                key={financing.financing_id}
                                className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg"
                              >
                                <div>
                                  <p className="text-white font-medium">{financing.company_name}</p>
                                  <p className="text-xs text-slate-400">{financing.financing_type}</p>
                                </div>
                                <div className="text-right">
                                  <p className="text-gold-400 font-semibold">{financing.total_interests} investors</p>
                                  <p className="text-xs text-slate-400">
                                    ${Number(financing.total_amount || 0).toLocaleString()} ({Number(financing.percentage_filled || 0).toFixed(0)}%)
                                  </p>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-6 text-slate-400">
                      <svg className="w-12 h-12 mx-auto mb-2 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                      No investment interest data available
                    </div>
                  )}
                </div>
              </Card>
            )}
          </>
        )}
      </div>

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-slate-800 mt-auto">
        <div className="max-w-7xl mx-auto text-center text-slate-400 text-sm">
          <p>&copy; {new Date().getFullYear()} GoldVenture. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
