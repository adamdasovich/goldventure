'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { ArrowLeft, Calendar, Clock, Users, Video, MessageSquare, Plus, X, Save } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import LogoMono from '@/components/LogoMono';
import { LoginModal, RegisterModal } from '@/components/auth';
import { useAuth } from '@/contexts/AuthContext';

interface Company {
  id: number;
  name: string;
  ticker_symbol: string;
}

interface Speaker {
  name: string;
  title: string;
  bio: string;
  is_primary: boolean;
}

export default function CreateEventPage() {
  const router = useRouter();
  const params = useParams();
  const { user, logout } = useAuth();
  const [company, setCompany] = useState<Company | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    topic: '',
    agenda: '',
    scheduled_start: '',
    scheduled_end: '',
    timezone: 'America/Toronto',
    duration_minutes: 60,
    format: 'video' as 'video' | 'text',
    max_participants: 500,
    is_recorded: true,
  });

  const [speakers, setSpeakers] = useState<Speaker[]>([]);
  const [showAddSpeaker, setShowAddSpeaker] = useState(false);
  const [newSpeaker, setNewSpeaker] = useState<Speaker>({
    name: '',
    title: '',
    bio: '',
    is_primary: false,
  });

  useEffect(() => {
    if (!user || !user.is_staff) {
      router.push(`/companies/${params.id}`);
      return;
    }
    fetchCompany();
  }, [params.id, user]);

  const fetchCompany = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/api'}/companies/${params.id}/`);
      if (response.ok) {
        const data = await response.json();
        setCompany(data);
      }
    } catch (error) {
      console.error('Error fetching company:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
    }));
  };

  const handleAddSpeaker = () => {
    console.log('handleAddSpeaker called, newSpeaker:', newSpeaker);

    if (!newSpeaker.name || !newSpeaker.title || !newSpeaker.bio) {
      const missing = [];
      if (!newSpeaker.name) missing.push('Speaker Name');
      if (!newSpeaker.title) missing.push('Title/Role');
      if (!newSpeaker.bio) missing.push('Bio');

      alert(`Please fill in all required fields:\n${missing.join(', ')}`);
      return;
    }

    setSpeakers([...speakers, newSpeaker]);
    setNewSpeaker({
      name: '',
      title: '',
      bio: '',
      is_primary: false,
    });
    setShowAddSpeaker(false);
  };

  const handleRemoveSpeaker = (index: number) => {
    setSpeakers(speakers.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const token = localStorage.getItem('accessToken');

      // Create the event
      const eventResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/api'}/events/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          ...formData,
          company: params.id,
          status: 'scheduled',
          speakers: speakers,  // Include speakers in the event creation payload
        }),
      });

      if (!eventResponse.ok) {
        const errorData = await eventResponse.json().catch(() => null);
        const errorMessage = errorData
          ? JSON.stringify(errorData, null, 2)
          : `HTTP ${eventResponse.status}: ${eventResponse.statusText}`;
        console.error('Event creation failed:', errorMessage);
        throw new Error(`Failed to create event: ${errorMessage}`);
      }

      const event = await eventResponse.json();

      // Redirect to the event page
      router.push(`/companies/${params.id}/events/${event.id}`);
    } catch (error) {
      console.error('Error creating event:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      alert(`Failed to create event:\n\n${errorMessage}\n\nCheck the browser console for more details.`);
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

  if (!company) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-slate-300">Company not found</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800">
      {/* Navigation */}
      <nav className="glass-nav sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-24">
            <div className="flex items-center space-x-3 cursor-pointer" onClick={() => router.push('/')}>
              <LogoMono className="h-18" />
            </div>
            <div className="flex items-center space-x-4">
              <Button variant="ghost" size="sm" onClick={() => router.push('/')}>Dashboard</Button>
              <Button variant="ghost" size="sm" onClick={() => router.push('/companies')}>Companies</Button>
              <Button variant="ghost" size="sm" onClick={() => router.push('/metals')}>Metals</Button>
              <Button variant="ghost" size="sm" onClick={() => router.push('/financial-hub')}>Financial Hub</Button>

              {user ? (
                <div className="flex items-center space-x-3">
                  <span className="text-sm text-slate-300">
                    Welcome, {user.full_name || user.username}
                  </span>
                  <Button variant="ghost" size="sm" onClick={logout}>
                    Logout
                  </Button>
                </div>
              ) : (
                <>
                  <Button variant="ghost" size="sm" onClick={() => setShowLogin(true)}>
                    Login
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => setShowRegister(true)}>
                    Register
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Auth Modals */}
      {showLogin && (
        <LoginModal
          onClose={() => setShowLogin(false)}
          onSwitchToRegister={() => {
            setShowLogin(false);
            setShowRegister(true);
          }}
        />
      )}
      {showRegister && (
        <RegisterModal
          onClose={() => setShowRegister(false)}
          onSwitchToLogin={() => {
            setShowRegister(false);
            setShowLogin(true);
          }}
        />
      )}

      {/* Header */}
      <section className="relative py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <button
            onClick={() => router.push(`/companies/${params.id}`)}
            className="flex items-center gap-2 text-slate-300 hover:text-white mb-6 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to {company.name}
          </button>

          <div className="mb-8">
            <h1 className="text-4xl font-bold text-white mb-2">Create Speaker Event</h1>
            <p className="text-slate-300">Create a new speaking event for {company.name} ({company.ticker_symbol})</p>
          </div>
        </div>
      </section>

      {/* Form */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
        <form onSubmit={handleSubmit}>
          <div className="grid lg:grid-cols-3 gap-8">
            {/* Main Form */}
            <div className="lg:col-span-2 space-y-6">
              {/* Basic Information */}
              <Card variant="glass-card">
                <CardHeader>
                  <CardTitle className="text-gold-400">Basic Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Event Title *
                    </label>
                    <input
                      type="text"
                      name="title"
                      value={formData.title}
                      onChange={handleInputChange}
                      required
                      className="w-full px-4 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-gold-400"
                      placeholder="Q4 2024 Results & Strategic Update"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Topic *
                    </label>
                    <input
                      type="text"
                      name="topic"
                      value={formData.topic}
                      onChange={handleInputChange}
                      required
                      className="w-full px-4 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-gold-400"
                      placeholder="Quarterly Results & Future Strategy"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Description *
                    </label>
                    <textarea
                      name="description"
                      value={formData.description}
                      onChange={handleInputChange}
                      required
                      rows={4}
                      className="w-full px-4 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-gold-400"
                      placeholder="Join us for an exclusive investor presentation..."
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Agenda
                    </label>
                    <textarea
                      name="agenda"
                      value={formData.agenda}
                      onChange={handleInputChange}
                      rows={8}
                      className="w-full px-4 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-gold-400 font-mono text-sm"
                      placeholder="**Event Agenda:**&#10;&#10;1. Introduction (5 min)&#10;2. Main Presentation (20 min)&#10;3. Q&A Session (20 min)"
                    />
                    <p className="text-xs text-slate-400 mt-1">Supports Markdown formatting</p>
                  </div>
                </CardContent>
              </Card>

              {/* Schedule */}
              <Card variant="glass-card">
                <CardHeader>
                  <CardTitle className="text-gold-400 flex items-center gap-2">
                    <Calendar className="w-5 h-5" />
                    Schedule
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        Start Date & Time *
                      </label>
                      <input
                        type="datetime-local"
                        name="scheduled_start"
                        value={formData.scheduled_start}
                        onChange={handleInputChange}
                        required
                        className="w-full px-4 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-gold-400"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        End Date & Time *
                      </label>
                      <input
                        type="datetime-local"
                        name="scheduled_end"
                        value={formData.scheduled_end}
                        onChange={handleInputChange}
                        required
                        className="w-full px-4 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-gold-400"
                      />
                    </div>
                  </div>

                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        Duration (minutes) *
                      </label>
                      <input
                        type="number"
                        name="duration_minutes"
                        value={formData.duration_minutes}
                        onChange={handleInputChange}
                        required
                        min="15"
                        max="480"
                        className="w-full px-4 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-gold-400"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        Timezone *
                      </label>
                      <select
                        name="timezone"
                        value={formData.timezone}
                        onChange={handleInputChange}
                        className="w-full px-4 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-gold-400"
                      >
                        <option value="America/Toronto">America/Toronto (EST/EDT)</option>
                        <option value="America/Vancouver">America/Vancouver (PST/PDT)</option>
                        <option value="America/New_York">America/New_York (EST/EDT)</option>
                        <option value="America/Chicago">America/Chicago (CST/CDT)</option>
                        <option value="America/Denver">America/Denver (MST/MDT)</option>
                        <option value="America/Los_Angeles">America/Los_Angeles (PST/PDT)</option>
                        <option value="UTC">UTC</option>
                      </select>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Speakers */}
              <Card variant="glass-card">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-gold-400 flex items-center gap-2">
                      <Users className="w-5 h-5" />
                      Speakers
                    </CardTitle>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowAddSpeaker(true)}
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Add Speaker
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {speakers.length === 0 ? (
                    <p className="text-slate-400 text-center py-8">
                      No speakers added yet. Click "Add Speaker" to add speakers.
                    </p>
                  ) : (
                    <div className="space-y-4">
                      {speakers.map((speaker, index) => (
                          <div
                            key={index}
                            className="flex items-start justify-between p-4 bg-slate-800/50 border border-slate-700 rounded-lg"
                          >
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <h4 className="font-semibold text-white">
                                  {speaker.name}
                                </h4>
                                {speaker.is_primary && (
                                  <Badge variant="gold" className="text-xs">Primary</Badge>
                                )}
                              </div>
                              <p className="text-sm text-gold-400 mb-2">{speaker.title}</p>
                              <p className="text-sm text-slate-300 line-clamp-2">{speaker.bio}</p>
                            </div>
                            <button
                              type="button"
                              onClick={() => handleRemoveSpeaker(index)}
                              className="text-red-400 hover:text-red-300 transition-colors ml-4"
                            >
                              <X className="w-5 h-5" />
                            </button>
                          </div>
                      ))}
                    </div>
                  )}

                  {/* Add Speaker Form */}
                  {showAddSpeaker && (
                    <div className="mt-4 p-4 bg-slate-900/50 border border-gold-400/30 rounded-lg space-y-4">
                      <h4 className="font-semibold text-white mb-3">Add New Speaker</h4>

                      <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                          Speaker Name *
                        </label>
                        <input
                          type="text"
                          value={newSpeaker.name}
                          onChange={(e) => setNewSpeaker({...newSpeaker, name: e.target.value})}
                          className="w-full px-4 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-gold-400"
                          placeholder="John Smith"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                          Title/Role *
                        </label>
                        <input
                          type="text"
                          value={newSpeaker.title}
                          onChange={(e) => setNewSpeaker({...newSpeaker, title: e.target.value})}
                          className="w-full px-4 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-gold-400"
                          placeholder="Chief Executive Officer"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                          Bio *
                        </label>
                        <textarea
                          value={newSpeaker.bio}
                          onChange={(e) => setNewSpeaker({...newSpeaker, bio: e.target.value})}
                          rows={3}
                          className="w-full px-4 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-gold-400"
                          placeholder="Brief biography of the speaker..."
                        />
                      </div>

                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          id="is_primary"
                          checked={newSpeaker.is_primary}
                          onChange={(e) => setNewSpeaker({...newSpeaker, is_primary: e.target.checked})}
                          className="w-4 h-4 text-gold-400 bg-slate-800 border-slate-700 rounded focus:ring-gold-400"
                        />
                        <label htmlFor="is_primary" className="ml-2 text-sm text-slate-300">
                          Primary Speaker
                        </label>
                      </div>

                      <div className="flex gap-2">
                        <Button
                          type="button"
                          variant="primary"
                          size="sm"
                          onClick={handleAddSpeaker}
                        >
                          Add Speaker
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setShowAddSpeaker(false);
                            setNewSpeaker({
                              name: '',
                              title: '',
                              bio: '',
                              is_primary: false,
                            });
                          }}
                        >
                          Cancel
                        </Button>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Event Settings */}
              <Card variant="glass-card">
                <CardHeader>
                  <CardTitle className="text-gold-400">Event Settings</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Format *
                    </label>
                    <select
                      name="format"
                      value={formData.format}
                      onChange={handleInputChange}
                      className="w-full px-4 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-gold-400"
                    >
                      <option value="video">Video Stream</option>
                      <option value="text">Text Chat</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Max Participants
                    </label>
                    <input
                      type="number"
                      name="max_participants"
                      value={formData.max_participants}
                      onChange={handleInputChange}
                      min="0"
                      className="w-full px-4 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-gold-400"
                    />
                    <p className="text-xs text-slate-400 mt-1">Leave as 0 for unlimited</p>
                  </div>

                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="is_recorded"
                      name="is_recorded"
                      checked={formData.is_recorded}
                      onChange={handleInputChange}
                      className="w-4 h-4 text-gold-400 bg-slate-800 border-slate-700 rounded focus:ring-gold-400"
                    />
                    <label htmlFor="is_recorded" className="ml-2 text-sm text-slate-300">
                      Record this event
                    </label>
                  </div>
                </CardContent>
              </Card>

              {/* Submit */}
              <Card variant="glass-card">
                <CardContent className="space-y-3">
                  <Button
                    type="submit"
                    variant="primary"
                    className="w-full"
                    disabled={submitting || speakers.length === 0}
                  >
                    {submitting ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Creating Event...
                      </>
                    ) : (
                      <>
                        <Save className="w-4 h-4 mr-2" />
                        Create Event
                      </>
                    )}
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    className="w-full"
                    onClick={() => router.push(`/companies/${params.id}`)}
                  >
                    Cancel
                  </Button>
                  {speakers.length === 0 && (
                    <p className="text-xs text-red-400 text-center">
                      Please add at least one speaker
                    </p>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
