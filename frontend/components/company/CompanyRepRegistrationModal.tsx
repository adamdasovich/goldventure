'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { accessRequestAPI } from '@/lib/api';
import type { AccessRequestRole, CompanyAccessRequest } from '@/types/api';

interface CompanyRepRegistrationModalProps {
  companyId: number;
  companyName: string;
  accessToken: string | null;
  onClose: () => void;
  onSubmitSuccess: (request: CompanyAccessRequest) => void;
}

const ROLE_OPTIONS: { value: AccessRequestRole; label: string; description: string }[] = [
  { value: 'ir_manager', label: 'IR Manager', description: 'Investor Relations Manager' },
  { value: 'ceo', label: 'CEO', description: 'Chief Executive Officer' },
  { value: 'cfo', label: 'CFO', description: 'Chief Financial Officer' },
  { value: 'marketing', label: 'Marketing', description: 'Marketing Department' },
  { value: 'communications', label: 'Communications', description: 'Corporate Communications' },
  { value: 'other', label: 'Other', description: 'Other company role' },
];

export function CompanyRepRegistrationModal({
  companyId,
  companyName,
  accessToken,
  onClose,
  onSubmitSuccess,
}: CompanyRepRegistrationModalProps) {
  const [step, setStep] = useState<'form' | 'success'>('form');
  const [role, setRole] = useState<AccessRequestRole>('ir_manager');
  const [jobTitle, setJobTitle] = useState('');
  const [workEmail, setWorkEmail] = useState('');
  const [justification, setJustification] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    if (!accessToken) {
      setError('You must be logged in to submit a request');
      return;
    }

    if (!jobTitle.trim() || !workEmail.trim() || !justification.trim()) {
      setError('Please fill in all required fields');
      return;
    }

    // Basic email validation
    if (!workEmail.includes('@') || !workEmail.includes('.')) {
      setError('Please enter a valid work email address');
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      const newRequest = await accessRequestAPI.create(accessToken, {
        company: companyId,
        role,
        job_title: jobTitle.trim(),
        work_email: workEmail.trim(),
        justification: justification.trim(),
      });

      setStep('success');
      onSubmitSuccess(newRequest);
    } catch (err) {
      console.error('Failed to submit request:', err);
      setError(err instanceof Error ? err.message : 'Failed to submit request. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (step === 'success') {
    return (
      <div className="fixed inset-0 z-50 overflow-y-auto">
        <div className="flex min-h-screen items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/70" onClick={onClose} />

          <Card className="relative z-10 w-full max-w-md p-8 text-center">
            <div className="mb-6">
              <div className="w-16 h-16 mx-auto bg-green-500/20 rounded-full flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Request Submitted!</h2>
              <p className="text-slate-400">
                Your request to represent <span className="text-gold-400 font-medium">{companyName}</span> has been submitted for review.
              </p>
            </div>

            <div className="bg-slate-800/50 rounded-lg p-4 mb-6 text-left">
              <h3 className="text-sm font-medium text-slate-300 mb-2">What happens next?</h3>
              <ul className="text-sm text-slate-400 space-y-2">
                <li className="flex items-start gap-2">
                  <svg className="w-4 h-4 text-gold-400 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <span>Our team will review your request</span>
                </li>
                <li className="flex items-start gap-2">
                  <svg className="w-4 h-4 text-gold-400 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <span>We may contact you to verify your identity</span>
                </li>
                <li className="flex items-start gap-2">
                  <svg className="w-4 h-4 text-gold-400 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <span>Once approved, you'll gain access to manage company resources</span>
                </li>
              </ul>
            </div>

            <Button variant="primary" className="w-full" onClick={onClose}>
              Got it
            </Button>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="fixed inset-0 bg-black/70" onClick={onClose} />

        <Card className="relative z-10 w-full max-w-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold text-white">Register as Company Representative</h2>
              <p className="text-sm text-slate-400 mt-1">
                Request access to manage resources for <span className="text-gold-400">{companyName}</span>
              </p>
            </div>
            <button onClick={onClose} className="text-slate-400 hover:text-white">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-900/30 border border-red-700 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}

          {/* Role Selection */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Your Role <span className="text-red-400">*</span>
            </label>
            <div className="grid grid-cols-2 gap-2">
              {ROLE_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setRole(option.value)}
                  className={`p-3 rounded-lg border text-left transition-all ${
                    role === option.value
                      ? 'border-gold-500 bg-gold-500/10 text-white'
                      : 'border-slate-700 hover:border-slate-600 text-slate-300'
                  }`}
                >
                  <div className="font-medium text-sm">{option.label}</div>
                  <div className="text-xs text-slate-500">{option.description}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Job Title */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Job Title <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              placeholder="e.g., Vice President of Investor Relations"
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
            />
          </div>

          {/* Work Email */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Work Email <span className="text-red-400">*</span>
            </label>
            <input
              type="email"
              value={workEmail}
              onChange={(e) => setWorkEmail(e.target.value)}
              placeholder="your.name@company.com"
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
            />
            <p className="text-xs text-slate-500 mt-1">
              Please use your company email address for verification
            </p>
          </div>

          {/* Justification */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Why do you need access? <span className="text-red-400">*</span>
            </label>
            <textarea
              value={justification}
              onChange={(e) => setJustification(e.target.value)}
              rows={3}
              placeholder="Please describe your role at the company and why you need access to manage resources on this platform..."
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent resize-none"
            />
          </div>

          {/* Info Box */}
          <div className="mb-4 p-4 bg-slate-800/50 rounded-lg border border-slate-700">
            <div className="flex items-start gap-3">
              <svg className="w-5 h-5 text-gold-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="text-sm text-slate-400">
                <p className="font-medium text-slate-300 mb-1">Verification Required</p>
                <p>All requests are reviewed by our team. Once approved, you'll be able to upload and manage company resources, including investor presentations, technical reports, and more.</p>
              </div>
            </div>
          </div>

          {/* Pricing Info */}
          <div className="mb-6 p-4 bg-gradient-to-r from-gold-500/10 to-copper-500/10 rounded-lg border border-gold-500/30">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold text-white">Company Portal Subscription</span>
              <Badge variant="gold" className="animate-pulse text-xs">Limited Time Offer</Badge>
            </div>
            <div className="flex items-baseline gap-1 mb-2">
              <span className="text-2xl font-bold text-gold-400">$50</span>
              <span className="text-slate-400 text-sm">/month</span>
              <span className="text-xs text-slate-500 ml-2">after 30-day free trial</span>
            </div>
            <p className="text-xs text-slate-400">
              Start your 30-day free trial today. No credit card required to register.
            </p>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <Button
              variant="ghost"
              className="flex-1"
              onClick={onClose}
              disabled={submitting}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              className="flex-1"
              onClick={handleSubmit}
              disabled={submitting || !jobTitle.trim() || !workEmail.trim() || !justification.trim()}
            >
              {submitting ? 'Submitting...' : 'Submit Request'}
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}
