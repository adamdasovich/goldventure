'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import LogoMono from '@/components/LogoMono';
import { LoginModal } from '@/components/auth/LoginModal';
import { RegisterModal } from '@/components/auth/RegisterModal';
import { subscriptionAPI, companyResourceAPI, speakingEventAPI, accessRequestAPI, companyAPI } from '@/lib/api';
import type { CompanySubscription, CompanyResource, SpeakingEvent, CompanyAccessRequest, Company, AccessRequestRole } from '@/types/api';
import {
  Building2,
  CreditCard,
  FileText,
  Calendar,
  Upload,
  Settings,
  CheckCircle,
  AlertCircle,
  Clock,
  ArrowRight,
  Sparkles,
  Shield,
  TrendingUp,
  Search,
  Send,
  XCircle
} from 'lucide-react';

// Role options for the request form
const ROLE_OPTIONS: { value: AccessRequestRole; label: string }[] = [
  { value: 'ir_manager', label: 'IR Manager' },
  { value: 'ceo', label: 'CEO' },
  { value: 'cfo', label: 'CFO' },
  { value: 'marketing', label: 'Marketing' },
  { value: 'communications', label: 'Communications' },
  { value: 'other', label: 'Other' },
];

export default function CompanyPortalPage() {
  const { user, accessToken, isAuthenticated } = useAuth();
  const [subscription, setSubscription] = useState<CompanySubscription | null>(null);
  const [resources, setResources] = useState<CompanyResource[]>([]);
  const [events, setEvents] = useState<SpeakingEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);

  // Company access request state
  const [hasCompany, setHasCompany] = useState<boolean | null>(null);
  const [pendingRequest, setPendingRequest] = useState<CompanyAccessRequest | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [companySearch, setCompanySearch] = useState('');
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [requestForm, setRequestForm] = useState({
    role: 'ir_manager' as AccessRequestRole,
    job_title: '',
    work_email: '',
    justification: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [requestError, setRequestError] = useState('');

  useEffect(() => {
    if (accessToken) {
      fetchDashboardData();
    } else {
      setLoading(false);
    }
  }, [accessToken]);

  const fetchDashboardData = async () => {
    if (!accessToken) return;

    try {
      setLoading(true);

      // First check if user has a company or pending request
      const requestStatus = await accessRequestAPI.getMyRequest(accessToken).catch(() => null);

      if (requestStatus && 'has_pending_request' in requestStatus) {
        // User doesn't have a company
        setHasCompany(requestStatus.has_company);
        setPendingRequest(null);

        // Load companies for the selection form
        const companiesData = await companyAPI.getAll().catch(() => ({ results: [] }));
        setCompanies(companiesData.results || []);
      } else if (requestStatus && 'id' in requestStatus) {
        // User has a pending request
        setHasCompany(false);
        setPendingRequest(requestStatus as CompanyAccessRequest);
      } else {
        // User has a company - load dashboard data
        setHasCompany(true);
        const [subData, resourceData, eventData] = await Promise.all([
          subscriptionAPI.getMySubscription(accessToken).catch(() => null),
          companyResourceAPI.getMyResources(accessToken).catch(() => ({ results: [] })),
          speakingEventAPI.getMyEvents(accessToken).catch(() => ({ results: [] })),
        ]);

        setSubscription(subData);
        setResources(resourceData.results || []);
        setEvents(eventData.results || []);
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      // Assume user has company to show dashboard (will show empty state)
      setHasCompany(true);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitRequest = async () => {
    if (!accessToken || !selectedCompany) return;

    if (!requestForm.job_title || !requestForm.work_email || !requestForm.justification) {
      setRequestError('Please fill in all required fields.');
      return;
    }

    try {
      setSubmitting(true);
      setRequestError('');

      const newRequest = await accessRequestAPI.create(accessToken, {
        company: selectedCompany.id,
        role: requestForm.role,
        job_title: requestForm.job_title,
        work_email: requestForm.work_email,
        justification: requestForm.justification,
      });

      setPendingRequest(newRequest);
      setSelectedCompany(null);
    } catch (error: unknown) {
      console.error('Error submitting request:', error);
      setRequestError(error instanceof Error ? error.message : 'Failed to submit request. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancelRequest = async () => {
    if (!accessToken || !pendingRequest) return;

    if (!confirm('Are you sure you want to cancel this request?')) return;

    try {
      await accessRequestAPI.cancel(accessToken, pendingRequest.id);
      setPendingRequest(null);
      setHasCompany(false);
    } catch (error) {
      console.error('Error canceling request:', error);
      alert('Failed to cancel request. Please try again.');
    }
  };

  const filteredCompanies = companies.filter(
    (c) =>
      c.name.toLowerCase().includes(companySearch.toLowerCase()) ||
      c.ticker_symbol?.toLowerCase().includes(companySearch.toLowerCase())
  );

  const handleStartTrial = async () => {
    if (!accessToken) {
      setShowLogin(true);
      return;
    }

    try {
      const successUrl = `${window.location.origin}/company-portal?success=true`;
      const cancelUrl = `${window.location.origin}/company-portal?canceled=true`;
      const response = await subscriptionAPI.createCheckout(accessToken, successUrl, cancelUrl);
      window.location.href = response.checkout_url;
    } catch (error) {
      console.error('Error creating checkout session:', error);
      alert('Failed to start checkout. Please try again.');
    }
  };

  const getSubscriptionStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge variant="gold" className="flex items-center gap-1"><CheckCircle className="w-3 h-3" /> Active</Badge>;
      case 'trialing':
        return <Badge variant="copper" className="flex items-center gap-1"><Clock className="w-3 h-3" /> Trial</Badge>;
      case 'past_due':
        return <Badge variant="slate" className="flex items-center gap-1"><AlertCircle className="w-3 h-3" /> Past Due</Badge>;
      case 'canceled':
        return <Badge variant="slate" className="flex items-center gap-1"><AlertCircle className="w-3 h-3" /> Canceled</Badge>;
      default:
        return <Badge variant="slate">{status}</Badge>;
    }
  };

  // Not logged in - show marketing page
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-slate-950">
        {/* Navigation */}
        <nav className="glass-nav sticky top-0 z-50 border-b border-gold-500/10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <a href="/" className="flex items-center space-x-3">
                <LogoMono className="h-8 w-8 text-gold-400" />
                <span className="text-xl font-bold text-gradient-gold">GoldVenture</span>
              </a>
              <div className="flex items-center gap-4">
                <Button variant="ghost" onClick={() => setShowLogin(true)}>Sign In</Button>
                <Button variant="primary" onClick={() => setShowRegister(true)}>Get Started</Button>
              </div>
            </div>
          </div>
        </nav>

        {/* Hero Section */}
        <section className="relative py-24 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto text-center">
            <Badge variant="gold" className="mb-6">Company Portal</Badge>
            <h1 className="text-4xl md:text-6xl font-bold text-white mb-6">
              Showcase Your Company to
              <span className="text-gradient-gold"> Investors</span>
            </h1>
            <p className="text-xl text-slate-300 max-w-3xl mx-auto mb-8">
              Get discovered by investors. Upload presentations, manage resources,
              create speaking events, and build your company&apos;s presence on the leading
              junior mining intelligence platform.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button variant="primary" size="lg" onClick={() => setShowRegister(true)}>
                Start Free 30-Day Trial <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
              <Button variant="secondary" size="lg" onClick={() => setShowLogin(true)}>
                Sign In
              </Button>
            </div>
            <p className="text-slate-400 mt-4 text-sm">No credit card required for trial</p>
          </div>
        </section>

        {/* Pricing Section */}
        <section className="py-20 px-4 sm:px-6 lg:px-8">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-white mb-4">Simple, Transparent Pricing</h2>
              <p className="text-slate-300">One plan with everything you need to grow your investor base</p>
            </div>

            <Card variant="glass-card" className="max-w-lg mx-auto border-gold-500/30">
              <CardHeader className="text-center pb-8 border-b border-slate-700">
                <Badge variant="gold" className="mx-auto mb-4">Most Popular</Badge>
                <CardTitle className="text-2xl text-white">Company Portal Pro</CardTitle>
                <div className="mt-4">
                  <span className="text-5xl font-bold text-gold-400">$20</span>
                  <span className="text-slate-400">/month</span>
                </div>
                <CardDescription className="mt-2">Billed monthly. Cancel anytime.</CardDescription>
              </CardHeader>
              <CardContent className="pt-8">
                <ul className="space-y-4 mb-8">
                  {[
                    'Unlimited resource uploads (presentations, documents, images)',
                    'Create and manage speaking events',
                    'Featured company placement',
                    'Investor analytics dashboard',
                    'Direct investor messaging',
                    'Priority support',
                    '30-day free trial included',
                  ].map((feature, i) => (
                    <li key={i} className="flex items-start gap-3 text-slate-300">
                      <CheckCircle className="w-5 h-5 text-gold-400 flex-shrink-0 mt-0.5" />
                      {feature}
                    </li>
                  ))}
                </ul>
                <Button variant="primary" className="w-full" size="lg" onClick={() => setShowRegister(true)}>
                  Start Free Trial
                </Button>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-20 px-4 sm:px-6 lg:px-8 bg-slate-900/50">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-white mb-4">Everything You Need</h2>
              <p className="text-slate-300">Powerful tools to manage your company&apos;s presence</p>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              <Card variant="glass" className="p-6">
                <div className="w-12 h-12 bg-gold-500/20 rounded-lg flex items-center justify-center mb-4">
                  <Upload className="w-6 h-6 text-gold-400" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">Resource Management</h3>
                <p className="text-slate-400">
                  Upload investor presentations, technical reports, maps, images, and documents.
                  Organize by category and control visibility.
                </p>
              </Card>

              <Card variant="glass" className="p-6">
                <div className="w-12 h-12 bg-gold-500/20 rounded-lg flex items-center justify-center mb-4">
                  <Calendar className="w-6 h-6 text-gold-400" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">Speaking Events</h3>
                <p className="text-slate-400">
                  Create and promote conferences, webinars, investor days, and site visits.
                  Reach investors actively looking for opportunities.
                </p>
              </Card>

              <Card variant="glass" className="p-6">
                <div className="w-12 h-12 bg-gold-500/20 rounded-lg flex items-center justify-center mb-4">
                  <TrendingUp className="w-6 h-6 text-gold-400" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">Investor Analytics</h3>
                <p className="text-slate-400">
                  Track engagement with your content. See who&apos;s viewing your presentations
                  and which resources drive the most interest.
                </p>
              </Card>
            </div>
          </div>
        </section>

        {/* Trust Section */}
        <section className="py-20 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto">
            <div className="grid md:grid-cols-3 gap-8 text-center">
              <div>
                <div className="w-16 h-16 bg-gold-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Shield className="w-8 h-8 text-gold-400" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Secure Platform</h3>
                <p className="text-slate-400">Enterprise-grade security with encrypted data storage</p>
              </div>
              <div>
                <div className="w-16 h-16 bg-gold-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Sparkles className="w-8 h-8 text-gold-400" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">AI-Powered</h3>
                <p className="text-slate-400">Claude AI helps investors discover and understand your company</p>
              </div>
              <div>
                <div className="w-16 h-16 bg-gold-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Building2 className="w-8 h-8 text-gold-400" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Industry Focus</h3>
                <p className="text-slate-400">Built specifically for junior mining companies</p>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-slate-900 to-slate-950">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-3xl font-bold text-white mb-4">Ready to Get Started?</h2>
            <p className="text-slate-300 mb-8">
              Join leading junior mining companies already using GoldVenture to connect with investors.
            </p>
            <Button variant="primary" size="lg" onClick={() => setShowRegister(true)}>
              Start Your Free Trial <ArrowRight className="ml-2 w-5 h-5" />
            </Button>
          </div>
        </section>

        {/* Modals */}
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
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-gold-400"></div>
      </div>
    );
  }

  // User has a pending access request - show status
  if (pendingRequest) {
    return (
      <div className="min-h-screen bg-slate-950">
        {/* Navigation */}
        <nav className="glass-nav sticky top-0 z-50 border-b border-gold-500/10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <a href="/" className="flex items-center space-x-3">
                <LogoMono className="h-8 w-8 text-gold-400" />
                <span className="text-xl font-bold text-gradient-gold">GoldVenture</span>
              </a>
              <div className="flex items-center gap-4">
                <span className="text-slate-400 text-sm">Welcome, {user?.full_name || user?.username}</span>
                <Button variant="ghost" onClick={() => window.location.href = '/dashboard'}>Dashboard</Button>
              </div>
            </div>
          </div>
        </nav>

        <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <Card variant="glass-card" className="border-gold-500/30">
            <CardHeader className="text-center">
              <div className="w-16 h-16 bg-gold-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <Clock className="w-8 h-8 text-gold-400" />
              </div>
              <CardTitle className="text-2xl text-white">Access Request Pending</CardTitle>
              <CardDescription className="text-slate-300 mt-2">
                Your request to access the Company Portal is being reviewed.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="bg-slate-800/50 rounded-lg p-4 space-y-3">
                <div className="flex justify-between">
                  <span className="text-slate-400">Company</span>
                  <span className="text-white font-medium">{pendingRequest.company_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Role</span>
                  <span className="text-white font-medium">{pendingRequest.role_display || pendingRequest.role}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Job Title</span>
                  <span className="text-white font-medium">{pendingRequest.job_title}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Submitted</span>
                  <span className="text-white font-medium">
                    {new Date(pendingRequest.created_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Status</span>
                  <Badge variant="copper" className="flex items-center gap-1">
                    <Clock className="w-3 h-3" /> Pending Review
                  </Badge>
                </div>
              </div>

              <p className="text-slate-400 text-sm text-center">
                An administrator will review your request and you&apos;ll be notified once it&apos;s approved.
                This typically takes 1-2 business days.
              </p>

              <div className="flex justify-center">
                <Button variant="secondary" onClick={handleCancelRequest}>
                  <XCircle className="w-4 h-4 mr-2" /> Cancel Request
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // User not associated with any company - show company selection form
  if (hasCompany === false) {
    return (
      <div className="min-h-screen bg-slate-950">
        {/* Navigation */}
        <nav className="glass-nav sticky top-0 z-50 border-b border-gold-500/10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <a href="/" className="flex items-center space-x-3">
                <LogoMono className="h-8 w-8 text-gold-400" />
                <span className="text-xl font-bold text-gradient-gold">GoldVenture</span>
              </a>
              <div className="flex items-center gap-4">
                <span className="text-slate-400 text-sm">Welcome, {user?.full_name || user?.username}</span>
                <Button variant="ghost" onClick={() => window.location.href = '/dashboard'}>Dashboard</Button>
              </div>
            </div>
          </div>
        </nav>

        <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">Company Portal Access</h1>
            <p className="text-slate-400">
              Select your company and request access to manage your company&apos;s profile.
            </p>
          </div>

          {!selectedCompany ? (
            // Company Selection Step
            <Card variant="glass-card">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Building2 className="w-5 h-5 text-gold-400" />
                  Select Your Company
                </CardTitle>
                <CardDescription>
                  Search for your company to request access
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search by company name or ticker..."
                    value={companySearch}
                    onChange={(e) => setCompanySearch(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:border-gold-500 focus:ring-1 focus:ring-gold-500 outline-none"
                  />
                </div>

                <div className="max-h-80 overflow-y-auto space-y-2">
                  {filteredCompanies.length === 0 ? (
                    <p className="text-slate-400 text-center py-8">
                      {companySearch ? 'No companies found matching your search' : 'No companies available'}
                    </p>
                  ) : (
                    filteredCompanies.map((company) => (
                      <button
                        key={company.id}
                        onClick={() => setSelectedCompany(company)}
                        className="w-full flex items-center justify-between p-4 bg-slate-800/50 hover:bg-slate-800 rounded-lg border border-transparent hover:border-gold-500/30 transition-colors text-left"
                      >
                        <div>
                          <p className="text-white font-medium">{company.name}</p>
                          <p className="text-slate-400 text-sm">
                            {company.ticker_symbol} • {company.exchange}
                          </p>
                        </div>
                        <ArrowRight className="w-5 h-5 text-slate-500" />
                      </button>
                    ))
                  )}
                </div>

                <p className="text-slate-500 text-sm text-center">
                  Don&apos;t see your company? Contact support to have it added.
                </p>
              </CardContent>
            </Card>
          ) : (
            // Request Form Step
            <Card variant="glass-card">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-white flex items-center gap-2">
                    <Send className="w-5 h-5 text-gold-400" />
                    Request Access
                  </CardTitle>
                  <Button variant="ghost" size="sm" onClick={() => setSelectedCompany(null)}>
                    Change Company
                  </Button>
                </div>
                <CardDescription>
                  Complete your request to manage <span className="text-gold-400 font-medium">{selectedCompany.name}</span>
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {requestError && (
                  <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 flex items-center gap-2 text-red-400">
                    <AlertCircle className="w-5 h-5 flex-shrink-0" />
                    {requestError}
                  </div>
                )}

                <div>
                  <label htmlFor="role-select" className="block text-sm font-medium text-slate-300 mb-1">Role *</label>
                  <select
                    id="role-select"
                    value={requestForm.role}
                    onChange={(e) => setRequestForm({ ...requestForm, role: e.target.value as AccessRequestRole })}
                    className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white focus:border-gold-500 focus:ring-1 focus:ring-gold-500 outline-none"
                  >
                    {ROLE_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Job Title *</label>
                  <input
                    type="text"
                    placeholder="e.g., Investor Relations Manager"
                    value={requestForm.job_title}
                    onChange={(e) => setRequestForm({ ...requestForm, job_title: e.target.value })}
                    className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:border-gold-500 focus:ring-1 focus:ring-gold-500 outline-none"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Work Email *</label>
                  <input
                    type="email"
                    placeholder="you@company.com"
                    value={requestForm.work_email}
                    onChange={(e) => setRequestForm({ ...requestForm, work_email: e.target.value })}
                    className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:border-gold-500 focus:ring-1 focus:ring-gold-500 outline-none"
                  />
                  <p className="text-slate-500 text-sm mt-1">Please use your official company email address</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Why do you need access? *
                  </label>
                  <textarea
                    placeholder="Explain your role and why you need access to manage this company's profile..."
                    value={requestForm.justification}
                    onChange={(e) => setRequestForm({ ...requestForm, justification: e.target.value })}
                    rows={4}
                    className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:border-gold-500 focus:ring-1 focus:ring-gold-500 outline-none resize-none"
                  />
                </div>

                <Button
                  variant="primary"
                  className="w-full"
                  size="lg"
                  onClick={handleSubmitRequest}
                  disabled={submitting}
                >
                  {submitting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white mr-2"></div>
                      Submitting...
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4 mr-2" /> Submit Request
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    );
  }

  // Logged in with company - show dashboard
  return (
    <div className="min-h-screen bg-slate-950">
      {/* Navigation */}
      <nav className="glass-nav sticky top-0 z-50 border-b border-gold-500/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <a href="/" className="flex items-center space-x-3">
              <LogoMono className="h-8 w-8 text-gold-400" />
              <span className="text-xl font-bold text-gradient-gold">GoldVenture</span>
            </a>
            <div className="flex items-center gap-4">
              <span className="text-slate-400 text-sm">Welcome, {user?.full_name || user?.username}</span>
              <Button variant="ghost" onClick={() => window.location.href = '/dashboard'}>Dashboard</Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Dashboard Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white">Company Portal</h1>
            <p className="text-slate-400">Manage your company&apos;s presence and resources</p>
          </div>
          {subscription && getSubscriptionStatusBadge(subscription.status)}
        </div>

        {/* Subscription Status Card */}
        {!subscription || subscription.status === 'canceled' ? (
          <Card variant="glass-card" className="mb-8 border-gold-500/30">
            <CardContent className="py-8">
              <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                <div>
                  <h2 className="text-2xl font-bold text-white mb-2">Start Your Free Trial</h2>
                  <p className="text-slate-300">
                    Get 30 days free access to all Company Portal features. $20/month after trial.
                  </p>
                </div>
                <Button variant="primary" size="lg" onClick={handleStartTrial}>
                  Start Free Trial <ArrowRight className="ml-2 w-5 h-5" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card variant="glass" className="mb-8">
            <CardContent className="py-6">
              <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-gold-500/20 rounded-lg flex items-center justify-center">
                    <CreditCard className="w-6 h-6 text-gold-400" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white">
                      {subscription.status === 'trialing' ? 'Trial Period' : 'Subscription Active'}
                    </h3>
                    <p className="text-slate-400 text-sm">
                      {subscription.status === 'trialing' && subscription.days_until_trial_end !== undefined
                        ? `${subscription.days_until_trial_end} days remaining in trial`
                        : subscription.current_period_end
                        ? `Renews on ${new Date(subscription.current_period_end).toLocaleDateString()}`
                        : 'Active subscription'}
                    </p>
                  </div>
                </div>
                <Button
                  variant="secondary"
                  onClick={async () => {
                    try {
                      const response = await subscriptionAPI.openBillingPortal(
                        accessToken!,
                        window.location.href
                      );
                      window.location.href = response.portal_url;
                    } catch (error) {
                      console.error('Error opening billing portal:', error);
                    }
                  }}
                >
                  Manage Billing
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Quick Actions Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card
            variant="glass"
            className="p-6 cursor-pointer hover:border-gold-500/30 transition-colors"
            onClick={() => window.location.href = '/company-portal/resources'}
          >
            <div className="w-12 h-12 bg-gold-500/20 rounded-lg flex items-center justify-center mb-4">
              <FileText className="w-6 h-6 text-gold-400" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-1">Resources</h3>
            <p className="text-slate-400 text-sm mb-3">Manage presentations & documents</p>
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold text-gold-400">{resources.length}</span>
              <ArrowRight className="w-5 h-5 text-slate-500" />
            </div>
          </Card>

          <Card
            variant="glass"
            className="p-6 cursor-pointer hover:border-gold-500/30 transition-colors"
            onClick={() => window.location.href = '/company-portal/events'}
          >
            <div className="w-12 h-12 bg-gold-500/20 rounded-lg flex items-center justify-center mb-4">
              <Calendar className="w-6 h-6 text-gold-400" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-1">Speaking Events</h3>
            <p className="text-slate-400 text-sm mb-3">Conferences & webinars</p>
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold text-gold-400">{events.length}</span>
              <ArrowRight className="w-5 h-5 text-slate-500" />
            </div>
          </Card>

          <Card
            variant="glass"
            className="p-6 cursor-pointer hover:border-gold-500/30 transition-colors"
            onClick={() => window.location.href = '/company-portal/subscription'}
          >
            <div className="w-12 h-12 bg-gold-500/20 rounded-lg flex items-center justify-center mb-4">
              <CreditCard className="w-6 h-6 text-gold-400" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-1">Subscription</h3>
            <p className="text-slate-400 text-sm mb-3">Billing & invoices</p>
            <div className="flex items-center justify-between">
              {subscription && getSubscriptionStatusBadge(subscription.status)}
              <ArrowRight className="w-5 h-5 text-slate-500" />
            </div>
          </Card>

          <Card
            variant="glass"
            className="p-6 cursor-pointer hover:border-gold-500/30 transition-colors"
            onClick={() => window.location.href = '/company-portal/settings'}
          >
            <div className="w-12 h-12 bg-gold-500/20 rounded-lg flex items-center justify-center mb-4">
              <Settings className="w-6 h-6 text-gold-400" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-1">Settings</h3>
            <p className="text-slate-400 text-sm mb-3">Company profile & preferences</p>
            <div className="flex items-center justify-between">
              <span className="text-slate-500 text-sm">Configure</span>
              <ArrowRight className="w-5 h-5 text-slate-500" />
            </div>
          </Card>
        </div>

        {/* Recent Activity */}
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Recent Resources */}
          <Card variant="glass">
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle className="text-white">Recent Resources</CardTitle>
                <Button variant="ghost" size="sm" onClick={() => window.location.href = '/company-portal/resources'}>
                  View All
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {resources.length === 0 ? (
                <div className="text-center py-8">
                  <Upload className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                  <p className="text-slate-400">No resources uploaded yet</p>
                  <Button
                    variant="primary"
                    size="sm"
                    className="mt-4"
                    onClick={() => window.location.href = '/company-portal/resources'}
                  >
                    Upload First Resource
                  </Button>
                </div>
              ) : (
                <ul className="space-y-3">
                  {resources.slice(0, 5).map((resource) => (
                    <li key={resource.id} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <FileText className="w-5 h-5 text-gold-400" />
                        <div>
                          <p className="text-white font-medium">{resource.title}</p>
                          <p className="text-slate-400 text-sm">{resource.category}</p>
                        </div>
                      </div>
                      <Badge variant={resource.is_public ? 'gold' : 'slate'}>
                        {resource.is_public ? 'Public' : 'Private'}
                      </Badge>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          {/* Upcoming Events */}
          <Card variant="glass">
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle className="text-white">Upcoming Events</CardTitle>
                <Button variant="ghost" size="sm" onClick={() => window.location.href = '/company-portal/events'}>
                  View All
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {events.length === 0 ? (
                <div className="text-center py-8">
                  <Calendar className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                  <p className="text-slate-400">No events scheduled yet</p>
                  <Button
                    variant="primary"
                    size="sm"
                    className="mt-4"
                    onClick={() => window.location.href = '/company-portal/events'}
                  >
                    Create First Event
                  </Button>
                </div>
              ) : (
                <ul className="space-y-3">
                  {events.slice(0, 5).map((event) => (
                    <li key={event.id} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <Calendar className="w-5 h-5 text-gold-400" />
                        <div>
                          <p className="text-white font-medium">{event.title}</p>
                          <p className="text-slate-400 text-sm">
                            {new Date(event.event_date).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <Badge variant={event.is_published ? 'gold' : 'slate'}>
                        {event.is_published ? 'Published' : 'Draft'}
                      </Badge>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
