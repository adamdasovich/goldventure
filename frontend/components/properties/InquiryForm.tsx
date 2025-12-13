'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface InquiryFormProps {
  listingId: number;
  listingTitle: string;
  prospectorName: string;
  accessToken: string | null;
  isAuthenticated: boolean;
  onLoginRequired: () => void;
}

const INQUIRY_TYPES = [
  { value: 'general', label: 'General Inquiry' },
  { value: 'site_visit', label: 'Request Site Visit' },
  { value: 'offer', label: 'Make an Offer' },
  { value: 'technical', label: 'Technical Questions' },
  { value: 'documents', label: 'Request Documents' },
];

export function InquiryForm({
  listingId,
  listingTitle,
  prospectorName,
  accessToken,
  isAuthenticated,
  onLoginRequired,
}: InquiryFormProps) {
  const [inquiryType, setInquiryType] = useState('general');
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!isAuthenticated) {
      onLoginRequired();
      return;
    }

    if (!message.trim()) {
      setError('Please enter a message');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/properties/inquiries/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          listing: listingId,
          inquiry_type: inquiryType,
          subject: subject || `${INQUIRY_TYPES.find(t => t.value === inquiryType)?.label} - ${listingTitle}`,
          message: message.trim(),
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || errorData.error || 'Failed to send inquiry');
      }

      setSuccess(true);
      setMessage('');
      setSubject('');
      setInquiryType('general');
    } catch (err) {
      console.error('Failed to send inquiry:', err);
      setError(err instanceof Error ? err.message : 'Failed to send inquiry');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <Card className="p-6">
        <div className="text-center">
          <div className="w-16 h-16 bg-green-600/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-white mb-2">Inquiry Sent!</h3>
          <p className="text-slate-400 text-sm mb-4">
            Your message has been sent to {prospectorName}. They will respond to your registered email address.
          </p>
          <Button variant="secondary" size="sm" onClick={() => setSuccess(false)}>
            Send Another Inquiry
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-white mb-4">Contact Prospector</h3>

      {!isAuthenticated ? (
        <div className="text-center py-4">
          <p className="text-slate-400 mb-4">Sign in to contact the prospector about this property.</p>
          <Button variant="primary" onClick={onLoginRequired}>
            Sign In to Inquire
          </Button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Inquiry Type</label>
            <select
              value={inquiryType}
              onChange={(e) => setInquiryType(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:ring-2 focus:ring-gold-500 focus:border-transparent"
            >
              {INQUIRY_TYPES.map((type) => (
                <option key={type.value} value={type.value}>{type.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Subject (optional)</label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="Brief subject line"
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Message *</label>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              rows={5}
              placeholder="Introduce yourself and explain your interest in this property..."
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent resize-none"
              required
            />
          </div>

          {error && (
            <div className="bg-red-900/20 border border-red-700 rounded-lg p-3 text-red-400 text-sm">
              {error}
            </div>
          )}

          <Button
            type="submit"
            variant="primary"
            className="w-full"
            disabled={loading || !message.trim()}
          >
            {loading ? 'Sending...' : 'Send Inquiry'}
          </Button>

          <p className="text-xs text-slate-500 text-center">
            Your contact information will be shared with the prospector.
          </p>
        </form>
      )}
    </Card>
  );
}
