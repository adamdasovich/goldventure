'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import LogoMono from '@/components/LogoMono';
import { LoginModal, RegisterModal } from '@/components/auth';
import { useAuth } from '@/contexts/AuthContext';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Inquiry {
  id: number;
  listing: number;
  listing_title: string;
  listing_slug: string;
  inquirer: number;
  inquirer_name: string;
  inquirer_email: string;
  inquiry_type: string;
  inquiry_type_display: string;
  message: string;
  status: 'new' | 'read' | 'responded' | 'closed';
  status_display: string;
  response: string | null;
  responded_at: string | null;
  created_at: string;
  updated_at: string;
}

export default function InboxPage() {
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const { user, logout, accessToken, isLoading } = useAuth();

  const [inquiries, setInquiries] = useState<Inquiry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedInquiry, setSelectedInquiry] = useState<Inquiry | null>(null);
  const [responseText, setResponseText] = useState('');
  const [responding, setResponding] = useState(false);
  const [filter, setFilter] = useState<'all' | 'received' | 'sent'>('all');

  // Check if inquiry was received (user is prospector) or sent (user is inquirer)
  const isReceivedInquiry = (inquiry: Inquiry) => {
    // If user sent it, inquirer_name would match user's username
    return inquiry.inquirer_name !== user?.username;
  };

  // Fetch inquiries
  useEffect(() => {
    if (!accessToken) return;

    const fetchInquiries = async () => {
      setLoading(true);
      try {
        const response = await fetch(`${API_URL}/properties/inquiries/`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          const inquiriesList = Array.isArray(data) ? data : data.results || [];
          setInquiries(inquiriesList);
        } else {
          console.error('Failed to load inquiries:', response.status, response.statusText);
          setError('Failed to load inquiries');
        }
      } catch (err) {
        console.error('Failed to fetch inquiries:', err);
        setError('Failed to load inquiries');
      } finally {
        setLoading(false);
      }
    };

    fetchInquiries();
  }, [accessToken]);

  // Mark as read when selecting an inquiry
  const handleSelectInquiry = async (inquiry: Inquiry) => {
    setSelectedInquiry(inquiry);
    setResponseText(inquiry.response || '');

    // Mark as read if new and user is the prospector (received inquiry)
    if (inquiry.status === 'new' && isReceivedInquiry(inquiry)) {
      try {
        await fetch(`${API_URL}/properties/inquiries/${inquiry.id}/mark_read/`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${accessToken}`,
          },
        });
        // Update local state
        setInquiries(prev => prev.map(i =>
          i.id === inquiry.id ? { ...i, status: 'read', status_display: 'Read' } : i
        ));
      } catch (err) {
        console.error('Failed to mark as read:', err);
      }
    }
  };

  // Send response
  const handleRespond = async () => {
    if (!selectedInquiry || !responseText.trim()) return;

    setResponding(true);
    try {
      const response = await fetch(`${API_URL}/properties/inquiries/${selectedInquiry.id}/respond/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ response: responseText.trim() }),
      });

      if (response.ok) {
        const updatedInquiry = await response.json();
        setInquiries(prev => prev.map(i =>
          i.id === selectedInquiry.id ? updatedInquiry : i
        ));
        setSelectedInquiry(updatedInquiry);
      } else {
        const errorData = await response.json();
        alert(errorData.error || 'Failed to send response');
      }
    } catch (err) {
      console.error('Failed to respond:', err);
      alert('Failed to send response');
    } finally {
      setResponding(false);
    }
  };

  // Filter inquiries
  const filteredInquiries = inquiries.filter(inquiry => {
    if (filter === 'received') return isReceivedInquiry(inquiry);
    if (filter === 'sent') return !isReceivedInquiry(inquiry);
    return true;
  });

  // Count new inquiries
  const newCount = inquiries.filter(i => i.status === 'new' && isReceivedInquiry(i)).length;

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffHours < 1) return 'Just now';
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'new':
        return <Badge variant="gold">New</Badge>;
      case 'read':
        return <Badge variant="slate">Read</Badge>;
      case 'responded':
        return <Badge variant="success">Responded</Badge>;
      case 'closed':
        return <Badge variant="info">Closed</Badge>;
      default:
        return <Badge variant="slate">{status}</Badge>;
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-gold-500"></div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen">
        {/* Navigation */}
        <nav className="glass-nav sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-24">
              <div className="flex items-center space-x-3 cursor-pointer" onClick={() => window.location.href = '/'}>
                <LogoMono className="h-16" />
              </div>
              <div className="flex items-center space-x-4">
                <Button variant="ghost" size="sm" onClick={() => window.location.href = '/properties'}>Properties</Button>
                <Button variant="ghost" size="sm" onClick={() => setShowLogin(true)}>Login</Button>
                <Button variant="primary" size="sm" onClick={() => setShowRegister(true)}>Register</Button>
              </div>
            </div>
          </div>
        </nav>

        {/* Auth Modals */}
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

        <div className="max-w-4xl mx-auto py-16 px-4 text-center">
          <h1 className="text-3xl font-bold text-white mb-4">Sign In Required</h1>
          <p className="text-slate-400 mb-8">Please sign in to view your inbox.</p>
          <Button variant="primary" onClick={() => setShowLogin(true)}>Sign In</Button>
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
            <div className="flex items-center space-x-3 cursor-pointer" onClick={() => window.location.href = '/'}>
              <LogoMono className="h-16" />
            </div>
            <div className="flex items-center space-x-4">
              <Button variant="ghost" size="sm" onClick={() => window.location.href = '/properties'}>Properties</Button>
              <Button variant="ghost" size="sm" onClick={() => window.location.href = '/properties/my-listings'}>My Listings</Button>
              <span className="text-sm text-slate-300">Welcome, {user.full_name || user.username}</span>
              <Button variant="ghost" size="sm" onClick={logout}>Logout</Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Auth Modals */}
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

      {/* Main Content */}
      <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">
              Inbox
              {newCount > 0 && (
                <span className="ml-2 bg-gold-500 text-black text-sm font-medium px-2 py-1 rounded-full">
                  {newCount} new
                </span>
              )}
            </h1>
            <p className="text-slate-400 mt-1">Manage inquiries about your properties</p>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 mb-6">
          <Button
            variant={filter === 'received' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setFilter('received')}
          >
            Received ({inquiries.filter(i => isReceivedInquiry(i)).length})
          </Button>
          <Button
            variant={filter === 'sent' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setFilter('sent')}
          >
            Sent ({inquiries.filter(i => !isReceivedInquiry(i)).length})
          </Button>
          <Button
            variant={filter === 'all' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setFilter('all')}
          >
            All ({inquiries.length})
          </Button>
        </div>

        {error && (
          <Card className="bg-red-900/20 border-red-700 mb-6">
            <div className="p-4 text-red-400">{error}</div>
          </Card>
        )}

        <div className="flex flex-col lg:flex-row gap-6">
          {/* Inquiry List */}
          <div className="lg:w-1/3">
            {loading ? (
              <Card className="p-8">
                <div className="flex justify-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-gold-500"></div>
                </div>
              </Card>
            ) : filteredInquiries.length === 0 ? (
              <Card className="p-8 text-center">
                <svg className="mx-auto h-12 w-12 text-slate-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                </svg>
                <h3 className="text-lg font-medium text-white mb-2">No inquiries yet</h3>
                <p className="text-slate-400 text-sm">
                  {filter === 'received'
                    ? 'You haven\'t received any inquiries on your listings yet.'
                    : filter === 'sent'
                    ? 'You haven\'t sent any inquiries yet.'
                    : 'No inquiries to display.'}
                </p>
              </Card>
            ) : (
              <div className="space-y-2">
                {filteredInquiries.map((inquiry) => (
                  <Card
                    key={inquiry.id}
                    className={`p-4 cursor-pointer transition-all hover:border-gold-500/50 ${
                      selectedInquiry?.id === inquiry.id ? 'border-gold-500 bg-slate-800/50' : ''
                    } ${inquiry.status === 'new' && isReceivedInquiry(inquiry) ? 'border-l-4 border-l-gold-500' : ''}`}
                    onClick={() => handleSelectInquiry(inquiry)}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          {getStatusBadge(inquiry.status)}
                          <Badge variant="copper" className="text-xs">{inquiry.inquiry_type_display}</Badge>
                        </div>
                        <h4 className="font-medium text-white truncate">
                          {isReceivedInquiry(inquiry) ? inquiry.inquirer_name : inquiry.listing_title}
                        </h4>
                        <p className="text-sm text-slate-400 truncate">
                          {isReceivedInquiry(inquiry)
                            ? `Re: ${inquiry.listing_title}`
                            : `To: Property Owner`}
                        </p>
                        <p className="text-xs text-slate-500 mt-1">{formatDate(inquiry.created_at)}</p>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>

          {/* Inquiry Detail */}
          <div className="lg:w-2/3">
            {selectedInquiry ? (
              <Card className="p-6">
                {/* Header */}
                <div className="flex items-start justify-between mb-6 pb-4 border-b border-slate-700">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      {getStatusBadge(selectedInquiry.status)}
                      <Badge variant="copper">{selectedInquiry.inquiry_type_display}</Badge>
                    </div>
                    <h2 className="text-xl font-semibold text-white">
                      {isReceivedInquiry(selectedInquiry)
                        ? `From: ${selectedInquiry.inquirer_name}`
                        : `To: Property Owner`}
                    </h2>
                    <p className="text-slate-400 mt-1">
                      Regarding: <a href={`/properties/${selectedInquiry.listing_slug}`} className="text-gold-500 hover:underline">{selectedInquiry.listing_title}</a>
                    </p>
                    {isReceivedInquiry(selectedInquiry) && (
                      <p className="text-sm text-slate-500 mt-1">
                        Contact: {selectedInquiry.inquirer_email}
                      </p>
                    )}
                  </div>
                  <span className="text-sm text-slate-500">{formatDate(selectedInquiry.created_at)}</span>
                </div>

                {/* Original Message */}
                <div className="mb-6">
                  <h3 className="text-sm font-medium text-slate-300 mb-2">Message:</h3>
                  <div className="bg-slate-800/50 rounded-lg p-4">
                    <p className="text-white whitespace-pre-wrap">{selectedInquiry.message}</p>
                  </div>
                </div>

                {/* Response Section */}
                {selectedInquiry.response && (
                  <div className="mb-6">
                    <h3 className="text-sm font-medium text-slate-300 mb-2">
                      Response {selectedInquiry.responded_at && `(${formatDate(selectedInquiry.responded_at)})`}:
                    </h3>
                    <div className="bg-gold-500/10 border border-gold-500/30 rounded-lg p-4">
                      <p className="text-white whitespace-pre-wrap">{selectedInquiry.response}</p>
                    </div>
                  </div>
                )}

                {/* Reply Form (only for received inquiries that haven't been responded to) */}
                {isReceivedInquiry(selectedInquiry) && selectedInquiry.status !== 'responded' && selectedInquiry.status !== 'closed' && (
                  <div>
                    <h3 className="text-sm font-medium text-slate-300 mb-2">Your Response:</h3>
                    <textarea
                      value={responseText}
                      onChange={(e) => setResponseText(e.target.value)}
                      rows={5}
                      placeholder="Write your response to this inquiry..."
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent resize-none"
                    />
                    <div className="flex justify-end mt-4">
                      <Button
                        variant="primary"
                        onClick={handleRespond}
                        disabled={responding || !responseText.trim()}
                      >
                        {responding ? 'Sending...' : 'Send Response'}
                      </Button>
                    </div>
                    <p className="text-xs text-slate-500 mt-2">
                      Your response will be sent to {selectedInquiry.inquirer_email}
                    </p>
                  </div>
                )}

                {/* Already responded message */}
                {isReceivedInquiry(selectedInquiry) && selectedInquiry.status === 'responded' && (
                  <div className="bg-green-900/20 border border-green-700 rounded-lg p-4 text-center">
                    <p className="text-green-400">You have already responded to this inquiry.</p>
                  </div>
                )}

                {/* Sent inquiry - waiting for response */}
                {!isReceivedInquiry(selectedInquiry) && !selectedInquiry.response && (
                  <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 text-center">
                    <p className="text-slate-400">Waiting for response from the property owner.</p>
                  </div>
                )}
              </Card>
            ) : (
              <Card className="p-12 text-center">
                <svg className="mx-auto h-16 w-16 text-slate-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                <h3 className="text-lg font-medium text-white mb-2">Select an inquiry</h3>
                <p className="text-slate-400">Choose an inquiry from the list to view details and respond.</p>
              </Card>
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-slate-800 mt-12">
        <div className="max-w-7xl mx-auto text-center text-slate-400 text-sm">
          <p>&copy; {new Date().getFullYear()} GoldVenture. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
