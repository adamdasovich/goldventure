'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  ArrowLeft,
  CheckCircle,
  AlertCircle,
  Award,
  FileText,
  DollarSign,
  Building2,
  Shield
} from 'lucide-react';

interface QualificationData {
  investor_type: string;
  annual_income_individual?: number;
  annual_income_combined?: number;
  financial_assets?: number;
  net_assets?: number;
  entity_assets?: number;
  is_registered_dealer?: boolean;
  has_financial_assets_1m?: boolean;
  has_net_assets_5m?: boolean;
}

interface QualificationStatus {
  id?: number;
  status: string;
  criteria_met: string | null;
  qualified_at: string | null;
}

export default function QualificationPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [existingQualification, setExistingQualification] = useState<QualificationStatus | null>(null);
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState<QualificationData>({
    investor_type: 'individual',
  });

  useEffect(() => {
    fetchExistingQualification();
  }, []);

  const fetchExistingQualification = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/qualifications/status/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setExistingQualification(data);
      }
    } catch (error) {
      console.error('Error fetching qualification:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: keyof QualificationData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const determineCriteria = (): string | null => {
    if (formData.investor_type === 'individual') {
      if (formData.annual_income_individual && formData.annual_income_individual >= 200000) {
        return 'income_individual';
      }
      if (formData.annual_income_combined && formData.annual_income_combined >= 300000) {
        return 'income_combined';
      }
      if (formData.has_financial_assets_1m) {
        return 'financial_assets';
      }
    } else if (formData.investor_type === 'entity') {
      if (formData.has_net_assets_5m) {
        return 'entity_assets';
      }
    } else if (formData.investor_type === 'professional') {
      if (formData.is_registered_dealer) {
        return 'professional';
      }
    }
    return null;
  };

  const handleSubmit = async () => {
    setSubmitting(true);

    const criteria = determineCriteria();
    const qualified = criteria !== null;

    const payload = {
      status: qualified ? 'qualified' : 'not_qualified',
      criteria_met: criteria,
      questionnaire_responses: formData,
      qualified_at: qualified ? new Date().toISOString() : null,
    };

    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/qualifications/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        await fetchExistingQualification();
        alert(qualified
          ? 'Congratulations! You qualify as an accredited investor.'
          : 'Based on your responses, you do not currently meet the accredited investor criteria.'
        );
        router.push('/financial-hub');
      } else {
        alert('Failed to submit qualification. Please try again.');
      }
    } catch (error) {
      console.error('Error submitting qualification:', error);
      alert('An error occurred. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold-400 mx-auto mb-4"></div>
          <p className="text-slate-300">Loading...</p>
        </div>
      </div>
    );
  }

  // Show existing qualification status
  if (existingQualification && existingQualification.status !== 'pending') {
    return (
      <div className="min-h-screen">
        <section className="relative py-20 px-4 sm:px-6 lg:px-8 overflow-hidden">
          <div className="absolute inset-0 bg-linear-to-b from-slate-900 via-slate-900 to-slate-800 opacity-50"></div>
          <div className="absolute inset-0" style={{
            backgroundImage: 'radial-gradient(circle at 50% 50%, rgba(212, 161, 42, 0.1) 0%, transparent 50%)'
          }}></div>

          <div className="relative max-w-3xl mx-auto">
            <button
              onClick={() => router.push('/financial-hub')}
              className="flex items-center gap-2 text-slate-300 hover:text-white mb-8 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Financial Hub
            </button>

            <div className={`p-8 rounded-xl backdrop-blur-sm border-2 ${
              existingQualification.status === 'qualified'
                ? 'bg-green-500/10 border-green-500/30'
                : 'bg-yellow-500/10 border-yellow-500/30'
            }`}>
              <div className="flex items-start gap-4 mb-6">
                {existingQualification.status === 'qualified' ? (
                  <CheckCircle className="w-12 h-12 text-green-400" />
                ) : (
                  <AlertCircle className="w-12 h-12 text-yellow-400" />
                )}
                <div className="flex-1">
                  <h1 className="text-2xl font-bold text-white mb-2">
                    {existingQualification.status === 'qualified'
                      ? 'Qualified as Accredited Investor'
                      : 'Not Currently Qualified'
                    }
                  </h1>
                  <p className="text-slate-300">
                    {existingQualification.status === 'qualified'
                      ? 'You have been qualified as an accredited investor and can participate in financing opportunities.'
                      : 'Based on your submitted information, you do not currently meet the accredited investor criteria.'
                    }
                  </p>
                </div>
              </div>

              {existingQualification.status === 'qualified' && existingQualification.qualified_at && (
                <div className="mt-6 p-4 bg-slate-800/50 rounded-lg">
                  <p className="text-sm text-slate-300">
                    <strong>Qualified on:</strong> {new Date(existingQualification.qualified_at).toLocaleDateString()}
                  </p>
                  {existingQualification.criteria_met && (
                    <p className="text-sm text-slate-300 mt-2">
                      <strong>Criteria met:</strong> {existingQualification.criteria_met.replace(/_/g, ' ').toUpperCase()}
                    </p>
                  )}
                </div>
              )}
            </div>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative py-20 px-4 sm:px-6 lg:px-8 overflow-hidden">
        <div className="absolute inset-0 bg-linear-to-b from-slate-900 via-slate-900 to-slate-800 opacity-50"></div>
        <div className="absolute inset-0" style={{
          backgroundImage: 'radial-gradient(circle at 50% 50%, rgba(212, 161, 42, 0.1) 0%, transparent 50%)'
        }}></div>

        <div className="relative max-w-3xl mx-auto">
          <button
            onClick={() => router.push('/financial-hub')}
            className="flex items-center gap-2 text-slate-300 hover:text-white mb-8 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Financial Hub
          </button>

          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl font-bold mb-4 text-gradient-gold animate-fade-in leading-tight pb-2">
              Accredited Investor Qualification
            </h1>
            <p className="text-lg text-slate-300">
              Complete this questionnaire to determine if you qualify as an accredited investor under Canadian securities regulations.
            </p>
          </div>
        </div>
      </section>

      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 -mt-8">{/* Overlap section */}

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-slate-300">
              Step {step} of 2
            </span>
            <span className="text-sm text-slate-400">
              {step === 1 ? 'Investor Type' : 'Financial Information'}
            </span>
          </div>
          <div className="w-full bg-slate-700/50 rounded-full h-2">
            <div
              className="h-2 rounded-full transition-all duration-300"
              style={{
                width: `${(step / 2) * 100}%`,
                background: 'linear-gradient(90deg, #d4af37 0%, #f4c430 100%)'
              }}
            />
          </div>
        </div>

        {/* Form */}
        <div className="backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl p-8">
          {step === 1 && (
            <div>
              <h2 className="text-2xl font-semibold text-white mb-6">
                What type of investor are you?
              </h2>

              <div className="space-y-4">
                {[
                  { value: 'individual', icon: DollarSign, label: 'Individual Investor', desc: 'Individual person investing personal funds' },
                  { value: 'entity', icon: Building2, label: 'Entity/Corporation', desc: 'Company or organization making investments' },
                  { value: 'professional', icon: Shield, label: 'Registered Professional', desc: 'Registered dealer or adviser' }
                ].map((type) => {
                  const Icon = type.icon;
                  const isSelected = formData.investor_type === type.value;

                  return (
                    <button
                      key={type.value}
                      onClick={() => handleInputChange('investor_type', type.value)}
                      className={`w-full p-6 rounded-lg border-2 transition-all text-left ${
                        isSelected
                          ? 'border-gold-400 bg-gold-400/10'
                          : 'border-slate-600 hover:border-slate-500'
                      }`}
                    >
                      <div className="flex items-start gap-4">
                        <div className={`p-3 rounded-lg ${isSelected ? 'bg-gold-400' : 'bg-slate-700'}`}>
                          <Icon className={`w-6 h-6 ${isSelected ? 'text-slate-900' : 'text-slate-300'}`} />
                        </div>
                        <div className="flex-1">
                          <h3 className="font-semibold text-white mb-1">
                            {type.label}
                          </h3>
                          <p className="text-sm text-slate-300">
                            {type.desc}
                          </p>
                        </div>
                        {isSelected && (
                          <CheckCircle className="w-6 h-6 text-gold-400" />
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>

              <button
                onClick={() => setStep(2)}
                className="mt-8 w-full px-6 py-3 bg-gold-400 text-slate-900 font-semibold rounded-lg hover:bg-gold-500 transition-all"
              >
                Continue
              </button>
            </div>
          )}

          {step === 2 && formData.investor_type === 'individual' && (
            <div>
              <h2 className="text-2xl font-semibold text-white mb-6">
                Financial Information
              </h2>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Annual Income (Individual) - Last 2 Years
                  </label>
                  <input
                    type="number"
                    value={formData.annual_income_individual || ''}
                    onChange={(e) => handleInputChange('annual_income_individual', parseFloat(e.target.value))}
                    className="w-full px-4 py-2 border border-slate-600 rounded-lg bg-slate-700 text-white focus:border-gold-400 focus:ring-1 focus:ring-gold-400"
                    placeholder="e.g., 250000"
                  />
                  <p className="mt-1 text-sm text-slate-400">
                    Qualifies if ≥ $200,000
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Annual Income (Combined with Spouse) - Last 2 Years
                  </label>
                  <input
                    type="number"
                    value={formData.annual_income_combined || ''}
                    onChange={(e) => handleInputChange('annual_income_combined', parseFloat(e.target.value))}
                    className="w-full px-4 py-2 border border-slate-600 rounded-lg bg-slate-700 text-white focus:border-gold-400 focus:ring-1 focus:ring-gold-400"
                    placeholder="e.g., 350000"
                  />
                  <p className="mt-1 text-sm text-slate-400">
                    Qualifies if ≥ $300,000
                  </p>
                </div>

                <div className="pt-4 border-t border-slate-600">
                  <label className="flex items-start gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.has_financial_assets_1m || false}
                      onChange={(e) => handleInputChange('has_financial_assets_1m', e.target.checked)}
                      className="mt-1 w-5 h-5 text-gold-400 border-slate-600 rounded focus:ring-gold-400"
                    />
                    <div>
                      <span className="block font-medium text-white">
                        I have financial assets of at least $1,000,000
                      </span>
                      <span className="block text-sm text-slate-300 mt-1">
                        Financial assets exclude principal residence value
                      </span>
                    </div>
                  </label>
                </div>
              </div>

              <div className="mt-8 flex gap-4">
                <button
                  onClick={() => setStep(1)}
                  className="flex-1 px-6 py-3 border-2 border-slate-600 text-slate-300 font-semibold rounded-lg hover:bg-slate-700 transition-colors"
                >
                  Back
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={submitting}
                  className="flex-1 px-6 py-3 bg-gold-400 text-slate-900 font-semibold rounded-lg hover:bg-gold-500 transition-all disabled:opacity-50"
                >
                  {submitting ? 'Submitting...' : 'Submit Qualification'}
                </button>
              </div>
            </div>
          )}

          {step === 2 && formData.investor_type === 'entity' && (
            <div>
              <h2 className="text-2xl font-semibold text-white mb-6">
                Entity Financial Information
              </h2>

              <div className="space-y-6">
                <div>
                  <label className="flex items-start gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.has_net_assets_5m || false}
                      onChange={(e) => handleInputChange('has_net_assets_5m', e.target.checked)}
                      className="mt-1 w-5 h-5 text-gold-400 border-slate-600 rounded focus:ring-gold-400"
                    />
                    <div>
                      <span className="block font-medium text-white">
                        Entity has net assets of at least $5,000,000
                      </span>
                      <span className="block text-sm text-slate-300 mt-1">
                        As shown in the most recent financial statements
                      </span>
                    </div>
                  </label>
                </div>
              </div>

              <div className="mt-8 flex gap-4">
                <button
                  onClick={() => setStep(1)}
                  className="flex-1 px-6 py-3 border-2 border-slate-600 text-slate-300 font-semibold rounded-lg hover:bg-slate-700 transition-colors"
                >
                  Back
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={submitting}
                  className="flex-1 px-6 py-3 bg-gold-400 text-slate-900 font-semibold rounded-lg hover:bg-gold-500 transition-all disabled:opacity-50"
                >
                  {submitting ? 'Submitting...' : 'Submit Qualification'}
                </button>
              </div>
            </div>
          )}

          {step === 2 && formData.investor_type === 'professional' && (
            <div>
              <h2 className="text-2xl font-semibold text-white mb-6">
                Professional Registration
              </h2>

              <div className="space-y-6">
                <div>
                  <label className="flex items-start gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.is_registered_dealer || false}
                      onChange={(e) => handleInputChange('is_registered_dealer', e.target.checked)}
                      className="mt-1 w-5 h-5 text-gold-400 border-slate-600 rounded focus:ring-gold-400"
                    />
                    <div>
                      <span className="block font-medium text-white">
                        I am a registered dealer or adviser under securities legislation
                      </span>
                      <span className="block text-sm text-slate-300 mt-1">
                        Registered with a Canadian securities regulator
                      </span>
                    </div>
                  </label>
                </div>
              </div>

              <div className="mt-8 flex gap-4">
                <button
                  onClick={() => setStep(1)}
                  className="flex-1 px-6 py-3 border-2 border-slate-600 text-slate-300 font-semibold rounded-lg hover:bg-slate-700 transition-colors"
                >
                  Back
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={submitting}
                  className="flex-1 px-6 py-3 bg-gold-400 text-slate-900 font-semibold rounded-lg hover:bg-gold-500 transition-all disabled:opacity-50"
                >
                  {submitting ? 'Submitting...' : 'Submit Qualification'}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Information Box */}
        <div className="mt-8 p-6 backdrop-blur-sm bg-slate-800/30 border border-gold-400/20 rounded-xl">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-6 h-6 text-gold-400 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-white mb-2">
                Important Information
              </h3>
              <ul className="space-y-1 text-sm text-slate-300">
                <li>• Your information is kept confidential and secure</li>
                <li>• This assessment is based on Canadian securities regulations</li>
                <li>• Qualification may require document verification</li>
                <li>• You can update your information at any time</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
