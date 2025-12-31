'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';

interface FormErrors {
  [key: string]: string[];
}

export default function NewCompanyPage() {
  const router = useRouter();
  const { accessToken, user } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});
  const [success, setSuccess] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    website_url: '',
    presentation: '',
    company_size: '',
    industry: '',
    location: '',
    contact_email: '',
    brief_description: ''
  });

  useEffect(() => {
    if (!accessToken) {
      router.push('/login?redirect=/companies/new');
    }
  }, [accessToken, router]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error for this field when user starts typing
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrors({});

    try {
      const response = await fetch('/api/companies/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (!response.ok) {
        console.error('Submission failed:', JSON.stringify(data, null, 2));
        if (data.errors) {
          setErrors(data.errors);
        } else if (data.status) {
          setErrors({ _general: data.status });
        } else {
          setErrors({ _general: [data.error || data.detail || 'Failed to submit company'] });
        }
        return;
      }

      setSuccess(true);
      setTimeout(() => {
        router.push('/companies');
      }, 2000);
    } catch (error) {
      setErrors({ _general: ['An unexpected error occurred. Please try again.'] });
    } finally {
      setIsSubmitting(false);
    }
  };

  const getCharCount = (field: keyof typeof formData) => formData[field].length;

  if (!accessToken) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-slate-400">Redirecting to login...</div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-12">
        <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-8 text-center">
          <div className="w-16 h-16 rounded-full bg-emerald-500/20 flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-emerald-400 mb-2">Company Submitted!</h2>
          <p className="text-slate-300">
            Your company has been submitted and is pending review. You'll be notified once it's approved.
          </p>
          <p className="text-slate-500 text-sm mt-4">Redirecting to companies page...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <div className="mb-8">
        <Link href="/companies" className="text-gold-400 hover:text-gold-300 flex items-center gap-2 mb-4">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Companies
        </Link>
        <h1 className="text-3xl font-bold text-slate-100">Submit a Company</h1>
        <p className="text-slate-400 mt-2">
          Submit a junior mining company for review. All submissions will be reviewed by our team before being published.
        </p>
      </div>

      {errors._general && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400">
          {errors._general.map((err, idx) => (
            <p key={idx}>{err}</p>
          ))}
        </div>
      )}

      {errors._conditional && (
        <div className="mb-6 p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg text-yellow-400">
          {errors._conditional.map((err, idx) => (
            <p key={idx}>{err}</p>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Company Name */}
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-slate-300 mb-2">
            Company Name <span className="text-red-400">*</span>
          </label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            className={`w-full px-4 py-2 bg-slate-900 border ${errors.name ? 'border-red-500' : 'border-slate-600'} rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-gold-500`}
            placeholder="e.g., Acme Mining Corp"
          />
          {errors.name && (
            <p className="mt-1 text-sm text-red-400">{errors.name[0]}</p>
          )}
          <p className="mt-1 text-xs text-slate-500">{getCharCount('name')}/100 characters</p>
        </div>

        {/* Website URL */}
        <div>
          <label htmlFor="website_url" className="block text-sm font-medium text-slate-300 mb-2">
            Website URL <span className="text-slate-500 text-xs">(Optional if presentation provided)</span>
          </label>
          <input
            type="text"
            id="website_url"
            name="website_url"
            value={formData.website_url}
            onChange={handleChange}
            className={`w-full px-4 py-2 bg-slate-900 border ${errors.website_url ? 'border-red-500' : 'border-slate-600'} rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-gold-500`}
            placeholder="example.com or https://example.com"
          />
          {errors.website_url && (
            <p className="mt-1 text-sm text-red-400">{errors.website_url[0]}</p>
          )}
        </div>

        {/* Company Presentation */}
        <div>
          <label htmlFor="presentation" className="block text-sm font-medium text-slate-300 mb-2">
            Company Presentation <span className="text-slate-500 text-xs">(Optional if website URL provided, minimum 200 characters)</span>
          </label>
          <textarea
            id="presentation"
            name="presentation"
            value={formData.presentation}
            onChange={handleChange}
            rows={6}
            className={`w-full px-4 py-2 bg-slate-900 border ${errors.presentation ? 'border-red-500' : 'border-slate-600'} rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-gold-500`}
            placeholder="Provide detailed information about the company, its projects, team, and objectives..."
          />
          {errors.presentation && (
            <p className="mt-1 text-sm text-red-400">{errors.presentation[0]}</p>
          )}
          <p className="mt-1 text-xs text-slate-500">{getCharCount('presentation')}/2000 characters</p>
        </div>

        {/* Company Size */}
        <div>
          <label htmlFor="company_size" className="block text-sm font-medium text-slate-300 mb-2">
            Company Size <span className="text-red-400">*</span>
          </label>
          <select
            id="company_size"
            name="company_size"
            value={formData.company_size}
            onChange={handleChange}
            className={`w-full px-4 py-2 bg-slate-900 border ${errors.company_size ? 'border-red-500' : 'border-slate-600'} rounded-lg text-slate-100 focus:outline-none focus:border-gold-500`}
          >
            <option value="">Select company size</option>
            <option value="1-10">1-10 employees</option>
            <option value="11-50">11-50 employees</option>
            <option value="51-200">51-200 employees</option>
            <option value="201-500">201-500 employees</option>
            <option value="501-1000">501-1000 employees</option>
            <option value="1000+">1000+ employees</option>
          </select>
          {errors.company_size && (
            <p className="mt-1 text-sm text-red-400">{errors.company_size[0]}</p>
          )}
        </div>

        {/* Industry */}
        <div>
          <label htmlFor="industry" className="block text-sm font-medium text-slate-300 mb-2">
            Industry/Sector <span className="text-red-400">*</span>
          </label>
          <input
            type="text"
            id="industry"
            name="industry"
            value={formData.industry}
            onChange={handleChange}
            className={`w-full px-4 py-2 bg-slate-900 border ${errors.industry ? 'border-red-500' : 'border-slate-600'} rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-gold-500`}
            placeholder="e.g., Gold Mining, Base Metals, Rare Earth Elements"
          />
          {errors.industry && (
            <p className="mt-1 text-sm text-red-400">{errors.industry[0]}</p>
          )}
          <p className="mt-1 text-xs text-slate-500">{getCharCount('industry')}/100 characters</p>
        </div>

        {/* Location */}
        <div>
          <label htmlFor="location" className="block text-sm font-medium text-slate-300 mb-2">
            Location/Headquarters <span className="text-red-400">*</span>
          </label>
          <input
            type="text"
            id="location"
            name="location"
            value={formData.location}
            onChange={handleChange}
            className={`w-full px-4 py-2 bg-slate-900 border ${errors.location ? 'border-red-500' : 'border-slate-600'} rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-gold-500`}
            placeholder="e.g., Vancouver, Canada"
          />
          {errors.location && (
            <p className="mt-1 text-sm text-red-400">{errors.location[0]}</p>
          )}
          <p className="mt-1 text-xs text-slate-500">{getCharCount('location')}/100 characters</p>
        </div>

        {/* Contact Email */}
        <div>
          <label htmlFor="contact_email" className="block text-sm font-medium text-slate-300 mb-2">
            Contact Email <span className="text-red-400">*</span>
          </label>
          <input
            type="email"
            id="contact_email"
            name="contact_email"
            value={formData.contact_email}
            onChange={handleChange}
            className={`w-full px-4 py-2 bg-slate-900 border ${errors.contact_email ? 'border-red-500' : 'border-slate-600'} rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-gold-500`}
            placeholder="info@example.com"
          />
          {errors.contact_email && (
            <p className="mt-1 text-sm text-red-400">{errors.contact_email[0]}</p>
          )}
        </div>

        {/* Brief Description */}
        <div>
          <label htmlFor="brief_description" className="block text-sm font-medium text-slate-300 mb-2">
            Brief Description <span className="text-red-400">*</span>
          </label>
          <textarea
            id="brief_description"
            name="brief_description"
            value={formData.brief_description}
            onChange={handleChange}
            rows={4}
            className={`w-full px-4 py-2 bg-slate-900 border ${errors.brief_description ? 'border-red-500' : 'border-slate-600'} rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-gold-500`}
            placeholder="Provide a brief overview of the company (elevator pitch)..."
          />
          {errors.brief_description && (
            <p className="mt-1 text-sm text-red-400">{errors.brief_description[0]}</p>
          )}
          <p className="mt-1 text-xs text-slate-500">{getCharCount('brief_description')}/500 characters (minimum 100)</p>
        </div>

        <div className="flex justify-end gap-4 pt-4">
          <Link
            href="/companies"
            className="px-6 py-2 border border-slate-600 text-slate-300 hover:bg-slate-700 rounded-lg transition-colors"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-6 py-2 bg-gold-500 hover:bg-gold-600 text-slate-900 font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isSubmitting ? (
              <>
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Submitting...
              </>
            ) : (
              'Submit Company'
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
