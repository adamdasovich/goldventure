'use client';

import { useState, useEffect, useRef } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import LogoMono from '@/components/LogoMono';
import { LoginModal, RegisterModal } from '@/components/auth';
import { useAuth } from '@/contexts/AuthContext';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface InquiryMessage {
  id: number;
  inquiry: number;
  sender: number;
  sender_name: string;
  sender_email: string;
  message: string;
  is_read: boolean;
  is_from_prospector: boolean;
  created_at: string;
}

interface Inquiry {
  id: number;
  listing: number;
  listing_title: string;
  listing_slug: string;
  inquirer: number;
  inquirer_name: string;
  inquirer_email: string;
  inquirer_full_name?: string;
  inquiry_type: string;
  inquiry_type_display: string;
  message: string;
  status: 'new' | 'read' | 'responded' | 'closed';
  status_display: string;
  response: string | null;
  responded_at: string | null;
  prospector_name?: string;
  messages?: InquiryMessage[];
  unread_count?: number;
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
  const [conversationMessages, setConversationMessages] = useState<InquiryMessage[]>([]);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [newMessage, setNewMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [filter, setFilter] = useState<'all' | 'received' | 'sent'>('all');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Check if inquiry was received (user is prospector) or sent (user is inquirer)
  const isReceivedInquiry = (inquiry: Inquiry) => {
    return inquiry.inquirer_name !== user?.username;
  };

  // Scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
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

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [conversationMessages]);

  // Fetch conversation messages for selected inquiry
  const fetchConversation = async (inquiry: Inquiry) => {
    setLoadingMessages(true);
    try {
      const response = await fetch(`${API_URL}/properties/inquiries/${inquiry.id}/conversation/`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSelectedInquiry(data);
        setConversationMessages(data.messages || []);
      } else {
        console.error('Failed to load conversation:', response.status);
      }
    } catch (err) {
      console.error('Failed to fetch conversation:', err);
    } finally {
      setLoadingMessages(false);
    }
  };

  // Handle selecting an inquiry
  const handleSelectInquiry = async (inquiry: Inquiry) => {
    setSelectedInquiry(inquiry);
    setNewMessage('');

    // Fetch full conversation
    await fetchConversation(inquiry);

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

  // Send a new message
  const handleSendMessage = async () => {
    if (!selectedInquiry || !newMessage.trim()) return;

    setSending(true);
    try {
      const response = await fetch(`${API_URL}/properties/inquiries/${selectedInquiry.id}/send_message/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: newMessage.trim() }),
      });

      if (response.ok) {
        const newMsg = await response.json();
        setConversationMessages(prev => [...prev, newMsg]);
        setNewMessage('');

        // Update inquiry status in the list if needed
        setInquiries(prev => prev.map(i =>
          i.id === selectedInquiry.id ? { ...i, status: 'responded', status_display: 'Responded' } : i
        ));
      } else {
        const errorData = await response.json();
        alert(errorData.error || 'Failed to send message');
      }
    } catch (err) {
      console.error('Failed to send message:', err);
      alert('Failed to send message');
    } finally {
      setSending(false);
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

  const formatMessageTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatMessageDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
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

  // Group messages by date
  const groupMessagesByDate = (messages: InquiryMessage[]) => {
    const groups: { [date: string]: InquiryMessage[] } = {};
    messages.forEach(msg => {
      const date = new Date(msg.created_at).toLocaleDateString();
      if (!groups[date]) {
        groups[date] = [];
      }
      groups[date].push(msg);
    });
    return groups;
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

          {/* Conversation Detail */}
          <div className="lg:w-2/3">
            {selectedInquiry ? (
              <Card className="flex flex-col h-[calc(100vh-280px)] min-h-[500px]">
                {/* Header */}
                <div className="p-4 border-b border-slate-700">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        {getStatusBadge(selectedInquiry.status)}
                        <Badge variant="copper">{selectedInquiry.inquiry_type_display}</Badge>
                      </div>
                      <h2 className="text-lg font-semibold text-white">
                        {isReceivedInquiry(selectedInquiry)
                          ? `Conversation with ${selectedInquiry.inquirer_full_name || selectedInquiry.inquirer_name}`
                          : `Conversation with ${selectedInquiry.prospector_name || 'Property Owner'}`}
                      </h2>
                      <p className="text-sm text-slate-400">
                        Regarding: <a href={`/properties/${selectedInquiry.listing_slug}`} className="text-gold-500 hover:underline">{selectedInquiry.listing_title}</a>
                      </p>
                    </div>
                    <span className="text-xs text-slate-500">{formatDate(selectedInquiry.created_at)}</span>
                  </div>
                </div>

                {/* Messages Container */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {loadingMessages ? (
                    <div className="flex justify-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-gold-500"></div>
                    </div>
                  ) : (
                    <>
                      {/* Original Inquiry Message */}
                      <div className="flex flex-col items-start">
                        <div className="max-w-[80%]">
                          <div className="text-xs text-slate-500 mb-1">
                            {selectedInquiry.inquirer_full_name || selectedInquiry.inquirer_name} • {formatMessageDate(selectedInquiry.created_at)}
                          </div>
                          <div className="bg-slate-700 rounded-lg rounded-tl-none p-3">
                            <p className="text-white whitespace-pre-wrap text-sm">{selectedInquiry.message}</p>
                          </div>
                          <div className="text-xs text-slate-500 mt-1">{formatMessageTime(selectedInquiry.created_at)}</div>
                        </div>
                      </div>

                      {/* Legacy Response (if exists and no messages yet) */}
                      {selectedInquiry.response && conversationMessages.length === 0 && (
                        <div className="flex flex-col items-end">
                          <div className="max-w-[80%]">
                            <div className="text-xs text-slate-500 mb-1 text-right">
                              {selectedInquiry.prospector_name || 'Property Owner'} • {selectedInquiry.responded_at ? formatMessageDate(selectedInquiry.responded_at) : ''}
                            </div>
                            <div className="bg-gold-500/20 border border-gold-500/30 rounded-lg rounded-tr-none p-3">
                              <p className="text-white whitespace-pre-wrap text-sm">{selectedInquiry.response}</p>
                            </div>
                            <div className="text-xs text-slate-500 mt-1 text-right">
                              {selectedInquiry.responded_at ? formatMessageTime(selectedInquiry.responded_at) : ''}
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Conversation Messages */}
                      {Object.entries(groupMessagesByDate(conversationMessages)).map(([date, msgs]) => (
                        <div key={date}>
                          <div className="flex items-center justify-center my-4">
                            <div className="bg-slate-700 px-3 py-1 rounded-full text-xs text-slate-400">
                              {date === new Date().toLocaleDateString() ? 'Today' : formatMessageDate(msgs[0].created_at)}
                            </div>
                          </div>
                          {msgs.map((msg) => {
                            const isOwnMessage = msg.sender_name === user?.username ||
                              msg.sender_name === (user?.full_name || user?.username);
                            return (
                              <div
                                key={msg.id}
                                className={`flex flex-col mb-3 ${isOwnMessage ? 'items-end' : 'items-start'}`}
                              >
                                <div className="max-w-[80%]">
                                  <div className={`text-xs text-slate-500 mb-1 ${isOwnMessage ? 'text-right' : ''}`}>
                                    {msg.sender_name}
                                  </div>
                                  <div
                                    className={`rounded-lg p-3 ${
                                      isOwnMessage
                                        ? 'bg-gold-500/20 border border-gold-500/30 rounded-tr-none'
                                        : 'bg-slate-700 rounded-tl-none'
                                    }`}
                                  >
                                    <p className="text-white whitespace-pre-wrap text-sm">{msg.message}</p>
                                  </div>
                                  <div className={`text-xs text-slate-500 mt-1 ${isOwnMessage ? 'text-right' : ''}`}>
                                    {formatMessageTime(msg.created_at)}
                                    {isOwnMessage && msg.is_read && (
                                      <span className="ml-2 text-green-500">✓ Read</span>
                                    )}
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      ))}
                      <div ref={messagesEndRef} />
                    </>
                  )}
                </div>

                {/* Message Input */}
                <div className="p-4 border-t border-slate-700">
                  <div className="flex gap-3">
                    <textarea
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          handleSendMessage();
                        }
                      }}
                      rows={2}
                      placeholder="Type your message... (Press Enter to send, Shift+Enter for new line)"
                      className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent resize-none text-sm"
                    />
                    <Button
                      variant="primary"
                      onClick={handleSendMessage}
                      disabled={sending || !newMessage.trim()}
                      className="self-end"
                    >
                      {sending ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-black"></div>
                      ) : (
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                        </svg>
                      )}
                    </Button>
                  </div>
                  <p className="text-xs text-slate-500 mt-2">
                    {isReceivedInquiry(selectedInquiry)
                      ? `Replying to ${selectedInquiry.inquirer_email}`
                      : `Sending to property owner`}
                  </p>
                </div>
              </Card>
            ) : (
              <Card className="p-12 text-center h-[calc(100vh-280px)] min-h-[500px] flex flex-col items-center justify-center">
                <svg className="h-16 w-16 text-slate-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                <h3 className="text-lg font-medium text-white mb-2">Select a conversation</h3>
                <p className="text-slate-400">Choose an inquiry from the list to view and continue the conversation.</p>
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
