'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import LogoMono from '@/components/LogoMono';
import LoginModal from '@/components/auth/LoginModal';
import { subscriptionAPI } from '@/lib/api';
import type { CompanySubscription, SubscriptionInvoice } from '@/types/api';
import {
  CreditCard,
  CheckCircle,
  AlertCircle,
  Clock,
  ArrowLeft,
  FileText,
  Download,
  ExternalLink,
  Calendar,
  DollarSign,
  RefreshCw
} from 'lucide-react';

export default function SubscriptionPage() {
  const { user, accessToken, isAuthenticated } = useAuth();
  const [subscription, setSubscription] = useState<CompanySubscription | null>(null);
  const [invoices, setInvoices] = useState<SubscriptionInvoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [showLogin, setShowLogin] = useState(false);

  useEffect(() => {
    if (accessToken) {
      fetchSubscriptionData();
    } else {
      setLoading(false);
    }
  }, [accessToken]);

  const fetchSubscriptionData = async () => {
    if (!accessToken) return;

    try {
      setLoading(true);
      const [subData, invoiceData] = await Promise.all([
        subscriptionAPI.getMySubscription(accessToken).catch(() => null),
        subscriptionAPI.getInvoices(accessToken).catch(() => ({ results: [] })),
      ]);

      setSubscription(subData);
      setInvoices(invoiceData.results || []);
    } catch (error) {
      console.error('Error fetching subscription data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStartTrial = async () => {
    if (!accessToken) {
      setShowLogin(true);
      return;
    }

    try {
      setActionLoading(true);
      const successUrl = `${window.location.origin}/company-portal/subscription?success=true`;
      const cancelUrl = `${window.location.origin}/company-portal/subscription?canceled=true`;
      const response = await subscriptionAPI.createCheckout(accessToken, successUrl, cancelUrl);
      window.location.href = response.checkout_url;
    } catch (error) {
      console.error('Error creating checkout session:', error);
      alert('Failed to start checkout. Please try again.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleManageBilling = async () => {
    if (!accessToken) return;

    try {
      setActionLoading(true);
      const response = await subscriptionAPI.openBillingPortal(accessToken, window.location.href);
      window.location.href = response.portal_url;
    } catch (error) {
      console.error('Error opening billing portal:', error);
      alert('Failed to open billing portal. Please try again.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancelSubscription = async () => {
    if (!accessToken) return;

    if (!confirm('Are you sure you want to cancel your subscription? You will still have access until the end of your billing period.')) {
      return;
    }

    try {
      setActionLoading(true);
      const updatedSub = await subscriptionAPI.cancel(accessToken);
      setSubscription(updatedSub);
      alert('Your subscription has been canceled. You will have access until the end of your current billing period.');
    } catch (error) {
      console.error('Error canceling subscription:', error);
      alert('Failed to cancel subscription. Please try again.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReactivateSubscription = async () => {
    if (!accessToken) return;

    try {
      setActionLoading(true);
      const updatedSub = await subscriptionAPI.reactivate(accessToken);
      setSubscription(updatedSub);
      alert('Your subscription has been reactivated!');
    } catch (error) {
      console.error('Error reactivating subscription:', error);
      alert('Failed to reactivate subscription. Please try again.');
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
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

  const getInvoiceStatusBadge = (status: string) => {
    switch (status) {
      case 'paid':
        return <Badge variant="gold">Paid</Badge>;
      case 'open':
        return <Badge variant="copper">Open</Badge>;
      case 'draft':
        return <Badge variant="slate">Draft</Badge>;
      case 'uncollectible':
        return <Badge variant="slate">Uncollectible</Badge>;
      case 'void':
        return <Badge variant="slate">Void</Badge>;
      default:
        return <Badge variant="slate">{status}</Badge>;
    }
  };

  // Not logged in
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <Card variant="glass-card" className="max-w-md w-full mx-4">
          <CardContent className="py-8 text-center">
            <CreditCard className="w-16 h-16 text-gold-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-white mb-2">Sign In Required</h2>
            <p className="text-slate-400 mb-6">Please sign in to manage your subscription.</p>
            <Button variant="primary" onClick={() => setShowLogin(true)}>Sign In</Button>
          </CardContent>
        </Card>
        {showLogin && <LoginModal onClose={() => setShowLogin(false)} />}
      </div>
    );
  }

  // Loading
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-gold-400"></div>
      </div>
    );
  }

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
            <Button variant="ghost" onClick={() => window.location.href = '/company-portal'}>
              <ArrowLeft className="w-4 h-4 mr-2" /> Back to Portal
            </Button>
          </div>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">Subscription & Billing</h1>
          <p className="text-slate-400">Manage your subscription and view billing history</p>
        </div>

        {/* Current Subscription Status */}
        <Card variant="glass-card" className="mb-8">
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle className="text-white flex items-center gap-2">
                <CreditCard className="w-5 h-5 text-gold-400" />
                Current Plan
              </CardTitle>
              {subscription && getStatusBadge(subscription.status)}
            </div>
          </CardHeader>
          <CardContent>
            {!subscription || subscription.status === 'canceled' ? (
              <div className="text-center py-6">
                <h3 className="text-xl font-semibold text-white mb-2">No Active Subscription</h3>
                <p className="text-slate-400 mb-6">
                  Start your 30-day free trial to access all Company Portal features.
                </p>
                <div className="bg-slate-800/50 rounded-lg p-6 mb-6">
                  <div className="flex items-center justify-center gap-2 mb-4">
                    <span className="text-4xl font-bold text-gold-400">$20</span>
                    <span className="text-slate-400">/month</span>
                  </div>
                  <ul className="space-y-2 text-left max-w-xs mx-auto">
                    <li className="flex items-center gap-2 text-slate-300">
                      <CheckCircle className="w-4 h-4 text-gold-400" /> Unlimited resource uploads
                    </li>
                    <li className="flex items-center gap-2 text-slate-300">
                      <CheckCircle className="w-4 h-4 text-gold-400" /> Speaking events management
                    </li>
                    <li className="flex items-center gap-2 text-slate-300">
                      <CheckCircle className="w-4 h-4 text-gold-400" /> Investor analytics
                    </li>
                    <li className="flex items-center gap-2 text-slate-300">
                      <CheckCircle className="w-4 h-4 text-gold-400" /> 30-day free trial
                    </li>
                  </ul>
                </div>
                <Button variant="primary" size="lg" onClick={handleStartTrial} disabled={actionLoading}>
                  {actionLoading ? 'Loading...' : 'Start Free Trial'}
                </Button>
              </div>
            ) : (
              <div>
                <div className="grid md:grid-cols-2 gap-6 mb-6">
                  <div className="bg-slate-800/50 rounded-lg p-4">
                    <div className="flex items-center gap-2 text-slate-400 mb-2">
                      <DollarSign className="w-4 h-4" />
                      <span className="text-sm">Plan</span>
                    </div>
                    <p className="text-xl font-semibold text-white">Company Portal Pro</p>
                    <p className="text-slate-400">$20/month</p>
                  </div>

                  <div className="bg-slate-800/50 rounded-lg p-4">
                    <div className="flex items-center gap-2 text-slate-400 mb-2">
                      <Calendar className="w-4 h-4" />
                      <span className="text-sm">
                        {subscription.status === 'trialing' ? 'Trial Ends' : 'Next Billing Date'}
                      </span>
                    </div>
                    <p className="text-xl font-semibold text-white">
                      {subscription.status === 'trialing' && subscription.trial_end
                        ? new Date(subscription.trial_end).toLocaleDateString()
                        : subscription.current_period_end
                        ? new Date(subscription.current_period_end).toLocaleDateString()
                        : 'N/A'}
                    </p>
                    {subscription.status === 'trialing' && subscription.days_until_trial_end !== undefined && (
                      <p className="text-slate-400">{subscription.days_until_trial_end} days remaining</p>
                    )}
                  </div>
                </div>

                {subscription.cancel_at_period_end && (
                  <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4 mb-6">
                    <div className="flex items-start gap-3">
                      <AlertCircle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                      <div>
                        <p className="text-amber-400 font-medium">Subscription Canceled</p>
                        <p className="text-slate-400 text-sm">
                          Your subscription will end on {subscription.current_period_end
                            ? new Date(subscription.current_period_end).toLocaleDateString()
                            : 'the end of your billing period'}. You can reactivate anytime before then.
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex flex-wrap gap-4">
                  <Button variant="primary" onClick={handleManageBilling} disabled={actionLoading}>
                    <ExternalLink className="w-4 h-4 mr-2" />
                    {actionLoading ? 'Loading...' : 'Manage Billing'}
                  </Button>

                  {subscription.cancel_at_period_end ? (
                    <Button variant="secondary" onClick={handleReactivateSubscription} disabled={actionLoading}>
                      <RefreshCw className="w-4 h-4 mr-2" />
                      {actionLoading ? 'Loading...' : 'Reactivate Subscription'}
                    </Button>
                  ) : (
                    <Button variant="ghost" onClick={handleCancelSubscription} disabled={actionLoading}>
                      {actionLoading ? 'Loading...' : 'Cancel Subscription'}
                    </Button>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Billing History */}
        <Card variant="glass">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <FileText className="w-5 h-5 text-gold-400" />
              Billing History
            </CardTitle>
            <CardDescription>View and download your invoices</CardDescription>
          </CardHeader>
          <CardContent>
            {invoices.length === 0 ? (
              <div className="text-center py-8">
                <FileText className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                <p className="text-slate-400">No invoices yet</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-700">
                      <th className="text-left py-3 px-4 text-slate-400 font-medium">Date</th>
                      <th className="text-left py-3 px-4 text-slate-400 font-medium">Amount</th>
                      <th className="text-left py-3 px-4 text-slate-400 font-medium">Status</th>
                      <th className="text-right py-3 px-4 text-slate-400 font-medium">Invoice</th>
                    </tr>
                  </thead>
                  <tbody>
                    {invoices.map((invoice) => (
                      <tr key={invoice.id} className="border-b border-slate-800">
                        <td className="py-3 px-4 text-white">
                          {new Date(invoice.invoice_date).toLocaleDateString()}
                        </td>
                        <td className="py-3 px-4 text-white">
                          ${(invoice.amount_due / 100).toFixed(2)} {invoice.currency.toUpperCase()}
                        </td>
                        <td className="py-3 px-4">
                          {getInvoiceStatusBadge(invoice.status)}
                        </td>
                        <td className="py-3 px-4 text-right">
                          {invoice.invoice_pdf && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => window.open(invoice.invoice_pdf, '_blank')}
                            >
                              <Download className="w-4 h-4 mr-1" /> PDF
                            </Button>
                          )}
                          {invoice.hosted_invoice_url && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => window.open(invoice.hosted_invoice_url, '_blank')}
                            >
                              <ExternalLink className="w-4 h-4 mr-1" /> View
                            </Button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
