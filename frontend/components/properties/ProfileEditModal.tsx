'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/contexts/AuthContext';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ProfileData {
  id: number;
  display_name: string;
  company_name: string;
  bio: string;
  years_experience: number;
  specializations: string[];
  regions_active: string[];
  website_url: string;
  phone: string;
  profile_image_url: string;
}

interface ProfileEditModalProps {
  profileId: number;
  onClose: () => void;
  onSave: () => void;
}

export function ProfileEditModal({ profileId, onClose, onSave }: ProfileEditModalProps) {
  const { accessToken } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState<ProfileData>({
    id: 0,
    display_name: '',
    company_name: '',
    bio: '',
    years_experience: 0,
    specializations: [],
    regions_active: [],
    website_url: '',
    phone: '',
    profile_image_url: '',
  });

  // Fetch current profile data
  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await fetch(`${API_URL}/properties/prospectors/me/`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          setFormData({
            id: data.id,
            display_name: data.display_name || '',
            company_name: data.company_name || '',
            bio: data.bio || '',
            years_experience: data.years_experience || 0,
            specializations: data.specializations || [],
            regions_active: data.regions_active || [],
            website_url: data.website_url || '',
            phone: data.phone || '',
            profile_image_url: data.profile_image_url || '',
          });
        } else {
          setError('Failed to load profile');
        }
      } catch (err) {
        console.error('Failed to fetch profile:', err);
        setError('Failed to load profile');
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [accessToken]);

  const handleChange = (field: keyof ProfileData, value: string | number | string[]) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleArrayChange = (field: 'specializations' | 'regions_active', value: string) => {
    const items = value.split(',').map(item => item.trim()).filter(item => item);
    setFormData(prev => ({ ...prev, [field]: items }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/properties/prospectors/${formData.id}/`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          display_name: formData.display_name,
          company_name: formData.company_name,
          bio: formData.bio,
          years_experience: formData.years_experience,
          specializations: formData.specializations,
          regions_active: formData.regions_active,
          website_url: formData.website_url,
          phone: formData.phone,
          profile_image_url: formData.profile_image_url,
        }),
      });

      if (response.ok) {
        onSave();
        onClose();
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to save profile');
      }
    } catch (err) {
      console.error('Failed to save profile:', err);
      setError('Failed to save profile');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white">Edit Profile</h2>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {loading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-gold-500"></div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="bg-red-900/20 border border-red-700 rounded-lg p-3 text-red-400 text-sm">
                  {error}
                </div>
              )}

              {/* Display Name */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Display Name *
                </label>
                <input
                  type="text"
                  value={formData.display_name}
                  onChange={(e) => handleChange('display_name', e.target.value)}
                  required
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                />
              </div>

              {/* Company Name */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Company Name
                </label>
                <input
                  type="text"
                  value={formData.company_name}
                  onChange={(e) => handleChange('company_name', e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                  placeholder="Optional"
                />
              </div>

              {/* Bio */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Bio
                </label>
                <textarea
                  value={formData.bio}
                  onChange={(e) => handleChange('bio', e.target.value)}
                  rows={4}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                  placeholder="Tell potential buyers about your experience..."
                />
              </div>

              {/* Years Experience */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Years of Experience
                </label>
                <input
                  type="number"
                  min="0"
                  max="99"
                  value={formData.years_experience}
                  onChange={(e) => handleChange('years_experience', parseInt(e.target.value) || 0)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                />
              </div>

              {/* Specializations */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Specializations
                </label>
                <input
                  type="text"
                  value={formData.specializations.join(', ')}
                  onChange={(e) => handleArrayChange('specializations', e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                  placeholder="Gold, Silver, Copper (comma separated)"
                />
                <p className="text-xs text-slate-500 mt-1">Separate multiple items with commas</p>
              </div>

              {/* Regions Active */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Regions Active
                </label>
                <input
                  type="text"
                  value={formData.regions_active.join(', ')}
                  onChange={(e) => handleArrayChange('regions_active', e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                  placeholder="British Columbia, Ontario (comma separated)"
                />
                <p className="text-xs text-slate-500 mt-1">Separate multiple regions with commas</p>
              </div>

              {/* Phone */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Phone
                </label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => handleChange('phone', e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                  placeholder="+1 (555) 123-4567"
                />
              </div>

              {/* Website URL */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Website
                </label>
                <input
                  type="url"
                  value={formData.website_url}
                  onChange={(e) => handleChange('website_url', e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                  placeholder="https://example.com"
                />
              </div>

              {/* Profile Image URL */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Profile Image URL
                </label>
                <input
                  type="url"
                  value={formData.profile_image_url}
                  onChange={(e) => handleChange('profile_image_url', e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                  placeholder="https://example.com/photo.jpg"
                />
                <p className="text-xs text-slate-500 mt-1">Direct link to your profile photo</p>
              </div>

              {/* Actions */}
              <div className="flex gap-3 pt-4 border-t border-slate-700">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={onClose}
                  disabled={saving}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  disabled={saving}
                >
                  {saving ? 'Saving...' : 'Save Profile'}
                </Button>
              </div>
            </form>
          )}
        </div>
      </Card>
    </div>
  );
}
