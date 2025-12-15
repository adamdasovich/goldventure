'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import LogoMono from '@/components/LogoMono';
import { LoginModal } from '@/components/auth/LoginModal';
import { speakingEventAPI } from '@/lib/api';
import type { SpeakingEvent } from '@/types/api';
import {
  Calendar,
  MapPin,
  Video,
  Users,
  Trash2,
  Edit2,
  Eye,
  EyeOff,
  ArrowLeft,
  Plus,
  X,
  ExternalLink,
  Clock,
  Globe,
  Star
} from 'lucide-react';

const EVENT_TYPES = [
  { value: 'conference', label: 'Conference' },
  { value: 'webinar', label: 'Webinar' },
  { value: 'investor_day', label: 'Investor Day' },
  { value: 'site_visit', label: 'Site Visit' },
  { value: 'earnings_call', label: 'Earnings Call' },
  { value: 'presentation', label: 'Presentation' },
  { value: 'interview', label: 'Interview' },
  { value: 'other', label: 'Other' },
];

const TIMEZONES = [
  { value: 'America/New_York', label: 'Eastern Time (ET)' },
  { value: 'America/Chicago', label: 'Central Time (CT)' },
  { value: 'America/Denver', label: 'Mountain Time (MT)' },
  { value: 'America/Los_Angeles', label: 'Pacific Time (PT)' },
  { value: 'America/Toronto', label: 'Toronto (ET)' },
  { value: 'America/Vancouver', label: 'Vancouver (PT)' },
  { value: 'Europe/London', label: 'London (GMT/BST)' },
  { value: 'Europe/Paris', label: 'Paris (CET)' },
  { value: 'Australia/Sydney', label: 'Sydney (AEST)' },
  { value: 'UTC', label: 'UTC' },
];

export default function EventsPage() {
  const { user, accessToken, isAuthenticated } = useAuth();
  const [events, setEvents] = useState<SpeakingEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [showLogin, setShowLogin] = useState(false);
  const [showEventModal, setShowEventModal] = useState(false);
  const [editingEvent, setEditingEvent] = useState<SpeakingEvent | null>(null);
  const [filter, setFilter] = useState<'all' | 'upcoming' | 'past'>('all');
  const [saving, setSaving] = useState(false);

  // Form state
  const [formData, setFormData] = useState<{
    title: string;
    description: string;
    event_type: SpeakingEvent['event_type'];
    event_date: string;
    event_end_date: string;
    timezone: string;
    location: string;
    venue_name: string;
    is_virtual: boolean;
    virtual_link: string;
    registration_url: string;
    presentation_url: string;
    speakers: string;
    is_published: boolean;
    is_featured: boolean;
  }>({
    title: '',
    description: '',
    event_type: 'conference',
    event_date: '',
    event_end_date: '',
    timezone: 'America/Toronto',
    location: '',
    venue_name: '',
    is_virtual: false,
    virtual_link: '',
    registration_url: '',
    presentation_url: '',
    speakers: '',
    is_published: false,
    is_featured: false,
  });

  useEffect(() => {
    if (accessToken) {
      fetchEvents();
    } else {
      setLoading(false);
    }
  }, [accessToken]);

  const fetchEvents = async () => {
    if (!accessToken) return;

    try {
      setLoading(true);
      const data = await speakingEventAPI.getMyEvents(accessToken);
      setEvents(data.results || []);
    } catch (error) {
      console.error('Error fetching events:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!accessToken) return;

    try {
      setSaving(true);

      const payload = {
        ...formData,
        event_end_date: formData.event_end_date || undefined,
      };

      if (editingEvent) {
        await speakingEventAPI.update(accessToken, editingEvent.id, payload);
      } else {
        await speakingEventAPI.create(accessToken, payload);
      }

      await fetchEvents();
      resetForm();
      setShowEventModal(false);
    } catch (error) {
      console.error('Error saving event:', error);
      alert('Failed to save event. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!accessToken) return;
    if (!confirm('Are you sure you want to delete this event?')) return;

    try {
      await speakingEventAPI.delete(accessToken, id);
      await fetchEvents();
    } catch (error) {
      console.error('Error deleting event:', error);
      alert('Failed to delete event. Please try again.');
    }
  };

  const handleTogglePublish = async (event: SpeakingEvent) => {
    if (!accessToken) return;

    try {
      if (event.is_published) {
        await speakingEventAPI.unpublish(accessToken, event.id);
      } else {
        await speakingEventAPI.publish(accessToken, event.id);
      }
      await fetchEvents();
    } catch (error) {
      console.error('Error toggling publish:', error);
      alert('Failed to update event. Please try again.');
    }
  };

  const handleEdit = (event: SpeakingEvent) => {
    setEditingEvent(event);
    setFormData({
      title: event.title,
      description: event.description || '',
      event_type: event.event_type,
      event_date: event.event_date.slice(0, 16), // Format for datetime-local
      event_end_date: event.event_end_date ? event.event_end_date.slice(0, 16) : '',
      timezone: event.timezone,
      location: event.location || '',
      venue_name: event.venue_name || '',
      is_virtual: event.is_virtual,
      virtual_link: event.virtual_link || '',
      registration_url: event.registration_url || '',
      presentation_url: event.presentation_url || '',
      speakers: event.speakers || '',
      is_published: event.is_published,
      is_featured: event.is_featured,
    });
    setShowEventModal(true);
  };

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      event_type: 'conference',
      event_date: '',
      event_end_date: '',
      timezone: 'America/Toronto',
      location: '',
      venue_name: '',
      is_virtual: false,
      virtual_link: '',
      registration_url: '',
      presentation_url: '',
      speakers: '',
      is_published: false,
      is_featured: false,
    });
    setEditingEvent(null);
  };

  const getEventTypeIcon = (type: string) => {
    switch (type) {
      case 'webinar':
      case 'earnings_call':
        return <Video className="w-5 h-5 text-gold-400" />;
      case 'site_visit':
        return <MapPin className="w-5 h-5 text-gold-400" />;
      case 'investor_day':
        return <Users className="w-5 h-5 text-gold-400" />;
      default:
        return <Calendar className="w-5 h-5 text-gold-400" />;
    }
  };

  const isUpcoming = (date: string) => new Date(date) > new Date();

  const filteredEvents = events.filter((event) => {
    if (filter === 'upcoming') return isUpcoming(event.event_date);
    if (filter === 'past') return !isUpcoming(event.event_date);
    return true;
  });

  // Not logged in
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <Card variant="glass-card" className="max-w-md w-full mx-4">
          <CardContent className="py-8 text-center">
            <Calendar className="w-16 h-16 text-gold-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-white mb-2">Sign In Required</h2>
            <p className="text-slate-400 mb-6">Please sign in to manage your speaking events.</p>
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

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white">Speaking Events</h1>
            <p className="text-slate-400">Create and manage conferences, webinars, and presentations</p>
          </div>
          <Button variant="primary" onClick={() => { resetForm(); setShowEventModal(true); }}>
            <Plus className="w-4 h-4 mr-2" /> Create Event
          </Button>
        </div>

        {/* Filter */}
        <div className="flex flex-wrap gap-2 mb-8">
          <Button
            variant={filter === 'all' ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setFilter('all')}
          >
            All ({events.length})
          </Button>
          <Button
            variant={filter === 'upcoming' ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setFilter('upcoming')}
          >
            Upcoming ({events.filter((e) => isUpcoming(e.event_date)).length})
          </Button>
          <Button
            variant={filter === 'past' ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setFilter('past')}
          >
            Past ({events.filter((e) => !isUpcoming(e.event_date)).length})
          </Button>
        </div>

        {/* Events List */}
        {filteredEvents.length === 0 ? (
          <Card variant="glass" className="py-16 text-center">
            <Calendar className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">No events yet</h3>
            <p className="text-slate-400 mb-6">Create your first speaking event to get started</p>
            <Button variant="primary" onClick={() => { resetForm(); setShowEventModal(true); }}>
              <Plus className="w-4 h-4 mr-2" /> Create Event
            </Button>
          </Card>
        ) : (
          <div className="space-y-4">
            {filteredEvents.map((event) => (
              <Card key={event.id} variant="glass" className="p-6">
                <div className="flex flex-col lg:flex-row lg:items-center gap-4">
                  {/* Event Icon & Date */}
                  <div className="flex items-start gap-4">
                    <div className="w-16 h-16 bg-gold-500/20 rounded-lg flex flex-col items-center justify-center flex-shrink-0">
                      <span className="text-gold-400 text-sm font-medium">
                        {new Date(event.event_date).toLocaleDateString('en-US', { month: 'short' })}
                      </span>
                      <span className="text-white text-xl font-bold">
                        {new Date(event.event_date).getDate()}
                      </span>
                    </div>

                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="text-xl font-semibold text-white">{event.title}</h3>
                        {event.is_featured && <Star className="w-4 h-4 text-gold-400" />}
                      </div>

                      <div className="flex flex-wrap items-center gap-3 text-slate-400 text-sm mb-2">
                        <span className="flex items-center gap-1">
                          {getEventTypeIcon(event.event_type)}
                          {EVENT_TYPES.find((t) => t.value === event.event_type)?.label}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          {new Date(event.event_date).toLocaleTimeString('en-US', {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                        {event.is_virtual ? (
                          <span className="flex items-center gap-1">
                            <Globe className="w-4 h-4" /> Virtual
                          </span>
                        ) : event.location && (
                          <span className="flex items-center gap-1">
                            <MapPin className="w-4 h-4" /> {event.location}
                          </span>
                        )}
                      </div>

                      <div className="flex flex-wrap gap-2">
                        <Badge variant={event.is_published ? 'gold' : 'slate'}>
                          {event.is_published ? <Eye className="w-3 h-3 mr-1" /> : <EyeOff className="w-3 h-3 mr-1" />}
                          {event.is_published ? 'Published' : 'Draft'}
                        </Badge>
                        {!isUpcoming(event.event_date) && (
                          <Badge variant="slate">Past Event</Badge>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 lg:ml-auto">
                    {event.registration_url && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => window.open(event.registration_url, '_blank')}
                      >
                        <ExternalLink className="w-4 h-4 mr-1" /> Register
                      </Button>
                    )}
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleTogglePublish(event)}
                    >
                      {event.is_published ? 'Unpublish' : 'Publish'}
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => handleEdit(event)}>
                      <Edit2 className="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => handleDelete(event.id)}>
                      <Trash2 className="w-4 h-4 text-red-400" />
                    </Button>
                  </div>
                </div>

                {event.description && (
                  <p className="text-slate-400 mt-4 line-clamp-2">{event.description}</p>
                )}
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Event Modal */}
      {showEventModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <Card variant="glass-card" className="max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-white">
                {editingEvent ? 'Edit Event' : 'Create Event'}
              </CardTitle>
              <Button variant="ghost" size="sm" onClick={() => { setShowEventModal(false); resetForm(); }}>
                <X className="w-5 h-5" />
              </Button>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Event Title *</label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    required
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-gold-500 focus:outline-none"
                    placeholder="Enter event title"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Description</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    rows={3}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-gold-500 focus:outline-none"
                    placeholder="Enter event description"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">Event Type *</label>
                    <select
                      value={formData.event_type}
                      onChange={(e) => setFormData({ ...formData, event_type: e.target.value as SpeakingEvent['event_type'] })}
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-gold-500 focus:outline-none"
                    >
                      {EVENT_TYPES.map((type) => (
                        <option key={type.value} value={type.value}>{type.label}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">Timezone *</label>
                    <select
                      value={formData.timezone}
                      onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-gold-500 focus:outline-none"
                    >
                      {TIMEZONES.map((tz) => (
                        <option key={tz.value} value={tz.value}>{tz.label}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">Start Date & Time *</label>
                    <input
                      type="datetime-local"
                      value={formData.event_date}
                      onChange={(e) => setFormData({ ...formData, event_date: e.target.value })}
                      required
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-gold-500 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">End Date & Time</label>
                    <input
                      type="datetime-local"
                      value={formData.event_end_date}
                      onChange={(e) => setFormData({ ...formData, event_end_date: e.target.value })}
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-gold-500 focus:outline-none"
                    />
                  </div>
                </div>

                <div className="flex items-center gap-2 mb-2">
                  <input
                    type="checkbox"
                    id="is_virtual"
                    checked={formData.is_virtual}
                    onChange={(e) => setFormData({ ...formData, is_virtual: e.target.checked })}
                    className="rounded border-slate-600 bg-slate-800 text-gold-500 focus:ring-gold-500"
                  />
                  <label htmlFor="is_virtual" className="text-slate-300">This is a virtual event</label>
                </div>

                {formData.is_virtual ? (
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">Virtual Meeting Link</label>
                    <input
                      type="url"
                      value={formData.virtual_link}
                      onChange={(e) => setFormData({ ...formData, virtual_link: e.target.value })}
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-gold-500 focus:outline-none"
                      placeholder="https://zoom.us/j/..."
                    />
                  </div>
                ) : (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-1">Location</label>
                      <input
                        type="text"
                        value={formData.location}
                        onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                        className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-gold-500 focus:outline-none"
                        placeholder="City, Country"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-1">Venue Name</label>
                      <input
                        type="text"
                        value={formData.venue_name}
                        onChange={(e) => setFormData({ ...formData, venue_name: e.target.value })}
                        className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-gold-500 focus:outline-none"
                        placeholder="Convention Center"
                      />
                    </div>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Registration URL</label>
                  <input
                    type="url"
                    value={formData.registration_url}
                    onChange={(e) => setFormData({ ...formData, registration_url: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-gold-500 focus:outline-none"
                    placeholder="https://eventbrite.com/..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Presentation URL</label>
                  <input
                    type="url"
                    value={formData.presentation_url}
                    onChange={(e) => setFormData({ ...formData, presentation_url: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-gold-500 focus:outline-none"
                    placeholder="Link to slides or recording"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Speakers</label>
                  <input
                    type="text"
                    value={formData.speakers}
                    onChange={(e) => setFormData({ ...formData, speakers: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-gold-500 focus:outline-none"
                    placeholder="John Smith (CEO), Jane Doe (CFO)"
                  />
                </div>

                <div className="flex items-center gap-6">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.is_published}
                      onChange={(e) => setFormData({ ...formData, is_published: e.target.checked })}
                      className="rounded border-slate-600 bg-slate-800 text-gold-500 focus:ring-gold-500"
                    />
                    <span className="text-slate-300">Publish immediately</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.is_featured}
                      onChange={(e) => setFormData({ ...formData, is_featured: e.target.checked })}
                      className="rounded border-slate-600 bg-slate-800 text-gold-500 focus:ring-gold-500"
                    />
                    <span className="text-slate-300">Featured</span>
                  </label>
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <Button type="button" variant="ghost" onClick={() => { setShowEventModal(false); resetForm(); }}>
                    Cancel
                  </Button>
                  <Button type="submit" variant="primary" disabled={saving}>
                    {saving ? 'Saving...' : editingEvent ? 'Update Event' : 'Create Event'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
