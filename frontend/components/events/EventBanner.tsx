'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useAuth } from '@/contexts/AuthContext';
import { LoginModal, RegisterModal } from '@/components/auth';

interface Speaker {
  id: number;
  user: {
    id: number;
    username: string;
    full_name: string;
  };
  title: string;
  is_primary: boolean;
}

interface SpeakerEvent {
  id: number;
  title: string;
  description: string;
  topic: string;
  scheduled_start: string;
  scheduled_end: string;
  duration_minutes: number;
  format: 'video' | 'text';
  status: string;
  registered_count: number;
  max_participants: number | null;
  speakers: Speaker[];
  is_registered: boolean;
  can_register: boolean;
  banner_image: string | null;
}

interface Registration {
  id: number;
  user: {
    id: number;
    username: string;
    email: string;
    full_name: string;
  };
  status: string;
  registered_at: string;
  joined_at: string | null;
  left_at: string | null;
}

interface EventBannerProps {
  companyId: number;
}

export function EventBanner({ companyId }: EventBannerProps) {
  const [event, setEvent] = useState<SpeakerEvent | null>(null);
  const [loading, setLoading] = useState(true);
  const [registering, setRegistering] = useState(false);
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [showRegistrations, setShowRegistrations] = useState(false);
  const [registrations, setRegistrations] = useState<Registration[]>([]);
  const [loadingRegistrations, setLoadingRegistrations] = useState(false);
  const { user, accessToken } = useAuth();

  // Check if user has staff access (staff, superuser, or event creator)
  const hasStaffAccess = user && (user.is_staff || user.is_superuser);

  useEffect(() => {
    fetchUpcomingEvent();
  }, [companyId]);

  const fetchUpcomingEvent = async () => {
    try {
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      if (accessToken) {
        headers['Authorization'] = `Bearer ${accessToken}`;
      }

      // First, check for any LIVE events for this company
      const liveUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/events/?company=${companyId}&status=live`;
      console.log('Fetching live events from:', liveUrl);

      const liveResponse = await fetch(liveUrl, { headers });
      if (liveResponse.ok) {
        const liveData = await liveResponse.json();
        const liveEvents = liveData.results || liveData;

        // If there's a live event, show it (priority over scheduled)
        if (liveEvents.length > 0) {
          console.log('Found live event:', liveEvents[0]);
          setEvent(liveEvents[0]);
          setLoading(false);
          return;
        }
      }

      // If no live events, fetch scheduled events
      const url = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/events/?company=${companyId}&status=scheduled`;
      console.log('Fetching scheduled events from:', url);

      const response = await fetch(url, { headers });
      console.log('Event fetch response status:', response.status);

      if (!response.ok) throw new Error('Failed to fetch event');
      const data = await response.json();
      console.log('Event data received:', data);

      // Handle paginated response
      const events = data.results || data;
      console.log('Events array:', events);

      // Get the next upcoming event
      if (events.length > 0) {
        const now = new Date();
        const upcomingEvent = events
          .filter((e: SpeakerEvent) => new Date(e.scheduled_start) > now)
          .sort((a: SpeakerEvent, b: SpeakerEvent) =>
            new Date(a.scheduled_start).getTime() - new Date(b.scheduled_start).getTime()
          )[0];

        console.log('Selected upcoming event:', upcomingEvent);
        setEvent(upcomingEvent || null);
      } else {
        console.log('No events found');
      }
    } catch (err) {
      console.error('Failed to load event:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async () => {
    if (!event) {
      console.log('No event found');
      return;
    }

    console.log('Register clicked for event:', event.id);
    console.log('User:', user);
    console.log('Access token:', accessToken ? 'Present' : 'Missing');

    // Check if user is logged in
    if (!user || !accessToken) {
      console.log('User not logged in, showing login modal');
      setShowLogin(true);
      return;
    }

    setRegistering(true);
    console.log('Sending registration request...');
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/events/${event.id}/register/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
          },
        }
      );

      console.log('Response status:', response.status);
      const data = await response.json();
      console.log('Response data:', data);

      if (response.ok) {
        console.log('Registration successful!');
        // Refresh event data
        await fetchUpcomingEvent();
      } else {
        console.error('Registration failed:', data);
        alert(`Failed to register: ${data.error || 'Unknown error'}`);
      }
    } catch (err) {
      console.error('Failed to register:', err);
      alert('Failed to register for event. Please try again.');
    } finally {
      setRegistering(false);
    }
  };

  const handleUnregister = async () => {
    if (!event) return;

    setRegistering(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/events/${event.id}/unregister/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
          },
        }
      );

      if (response.ok) {
        // Refresh event data
        await fetchUpcomingEvent();
      }
    } catch (err) {
      console.error('Failed to unregister:', err);
    } finally {
      setRegistering(false);
    }
  };

  const fetchRegistrations = async () => {
    if (!event || !accessToken) return;

    setLoadingRegistrations(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/events/${event.id}/registrations/`,
        {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setRegistrations(data.registrations || []);
      } else {
        console.error('Failed to fetch registrations');
      }
    } catch (err) {
      console.error('Error fetching registrations:', err);
    } finally {
      setLoadingRegistrations(false);
    }
  };

  const handleViewRegistrations = async () => {
    setShowRegistrations(true);
    await fetchRegistrations();
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  const getTimeUntil = (dateString: string) => {
    const now = new Date();
    const eventDate = new Date(dateString);
    const diffMs = eventDate.getTime() - now.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const diffHours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

    if (diffDays > 0) return `${diffDays}d ${diffHours}h`;
    if (diffHours > 0) return `${diffHours}h ${diffMinutes}m`;
    if (diffMinutes > 0) return `${diffMinutes}m`;
    return 'Starting soon';
  };

  // If loading, don't show anything
  if (loading) {
    return null;
  }

  // If no event and user is staff, show "Create Event" button
  if (!event && hasStaffAccess) {
    return (
      <Card
        variant="glass-card"
        className="mb-8 border-slate-700/50"
      >
        <CardContent className="p-6">
          <div className="text-center py-8">
            <svg className="w-16 h-16 text-slate-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            <h3 className="text-xl font-semibold text-white mb-2">No Upcoming Events</h3>
            <p className="text-slate-400 mb-6">Create a speaker event for this company</p>
            <Link
              href={`/companies/${companyId}/events/create`}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-gold-500 to-gold-600 text-white font-semibold rounded-lg hover:from-gold-600 hover:to-gold-700 transition-all"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Create Event
            </Link>
          </div>
        </CardContent>
      </Card>
    );
  }

  // If no event and not staff, don't show anything
  if (!event) {
    return null;
  }

  return (
    <Card
      variant="glass-card"
      className={`mb-8 ${event.status === 'live' ? 'border-red-500/50 bg-gradient-to-r from-red-500/10 to-red-500/5 ring-2 ring-red-500/30' : 'border-gold-500/30 bg-gradient-to-r from-gold-500/5 to-copper-500/5'}`}
      id={`event-${event.id}`}
    >
      <CardContent className="p-6">
        <div className="flex items-start gap-6">
          {/* Event Icon/Image */}
          <div className="flex-shrink-0">
            {event.banner_image ? (
              <img
                src={event.banner_image}
                alt={event.title}
                className="w-32 h-32 object-cover rounded-lg"
              />
            ) : (
              <div className="w-32 h-32 bg-gradient-to-br from-gold-500/20 to-copper-500/20 rounded-lg flex items-center justify-center">
                <svg className="w-16 h-16 text-gold-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </div>
            )}
          </div>

          {/* Event Details */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-4 mb-3">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  {event.status === 'live' ? (
                    <Badge variant="gold" className="text-xs bg-red-500 border-red-500 animate-pulse">
                      <div className="w-2 h-2 bg-white rounded-full mr-1"></div>
                      LIVE NOW
                    </Badge>
                  ) : (
                    <Badge variant="gold" className="text-xs">
                      <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                      </svg>
                      Upcoming Event
                    </Badge>
                  )}
                  {event.format === 'video' && (
                    <Badge variant="copper" className="text-xs">
                      Live Video
                    </Badge>
                  )}
                </div>
                <h2 className="text-2xl font-bold text-white mb-2">
                  {event.title}
                </h2>
                <p className="text-slate-300 mb-3 line-clamp-2">
                  {event.description}
                </p>
              </div>

              {/* Countdown Timer / Live Status */}
              <div className={`flex-shrink-0 text-center rounded-lg p-4 min-w-[120px] ${event.status === 'live' ? 'bg-red-500/20 border border-red-500/50' : 'bg-slate-900/50'}`}>
                {event.status === 'live' ? (
                  <>
                    <div className="text-sm text-red-400 mb-1">Status</div>
                    <div className="text-2xl font-bold text-red-400 animate-pulse">
                      IN PROGRESS
                    </div>
                  </>
                ) : (
                  <>
                    <div className="text-sm text-slate-400 mb-1">Starts in</div>
                    <div className="text-2xl font-bold text-gold-400">
                      {getTimeUntil(event.scheduled_start)}
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Event Meta */}
            <div className="flex items-center gap-6 text-sm text-slate-300 mb-4">
              <div className="flex items-center gap-2">
                <svg className="w-5 h-5 text-gold-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <span>{formatDate(event.scheduled_start)}</span>
              </div>
              <div className="flex items-center gap-2">
                <svg className="w-5 h-5 text-gold-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>{formatTime(event.scheduled_start)} ({event.duration_minutes} min)</span>
              </div>
              <div className="flex items-center gap-2">
                <svg className="w-5 h-5 text-gold-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                <span>{event.registered_count} registered</span>
              </div>
            </div>

            {/* Speakers */}
            {event.speakers.length > 0 && (
              <div className="mb-4">
                <div className="text-sm text-slate-400 mb-2">Featured Speakers:</div>
                <div className="flex items-center gap-4">
                  {event.speakers.map((speaker) => (
                    <div key={speaker.id} className="flex items-center gap-2">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gold-400 to-copper-400 flex items-center justify-center text-white font-bold">
                        {speaker.user.full_name.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <div className="text-sm font-semibold text-white">
                          {speaker.user.full_name}
                        </div>
                        <div className="text-xs text-slate-400">
                          {speaker.title}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center gap-2">
              {event.is_registered ? (
                <>
                  <Badge variant="gold" className="px-3 py-1.5 text-sm">
                    <svg className="w-3 h-3 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Registered
                  </Badge>
                  <button
                    onClick={handleUnregister}
                    disabled={registering}
                    className="px-3 py-1.5 bg-slate-700 text-slate-300 text-sm font-medium rounded-lg hover:bg-slate-600 transition-all disabled:opacity-50"
                  >
                    {registering ? 'Cancelling...' : 'Cancel'}
                  </button>
                </>
              ) : event.can_register ? (
                <button
                  onClick={handleRegister}
                  disabled={registering}
                  className="px-4 py-1.5 bg-gradient-to-r from-gold-500 to-gold-600 text-white text-sm font-semibold rounded-lg hover:from-gold-600 hover:to-gold-700 transition-all disabled:opacity-50"
                >
                  {registering ? 'Registering...' : 'Register'}
                </button>
              ) : (
                <Badge variant="slate" className="px-3 py-1.5 text-sm">
                  Event Full
                </Badge>
              )}

              {event.status === 'live' ? (
                <Link
                  href={`/companies/${companyId}/events/${event.id}`}
                  className="px-4 py-1.5 bg-gold-500 text-white text-sm font-semibold rounded-lg hover:bg-gold-600 transition-all flex items-center gap-1.5"
                >
                  <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                  Join Live
                </Link>
              ) : (
                <Link
                  href={`/companies/${companyId}/events/${event.id}`}
                  className="px-4 py-1.5 bg-slate-700 text-slate-200 text-sm font-medium rounded-lg hover:bg-slate-600 transition-all flex items-center gap-1.5"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  View
                </Link>
              )}

              {/* Staff: View Registrations Button */}
              {hasStaffAccess && (
                <>
                  <button
                    onClick={handleViewRegistrations}
                    className="px-3 py-1.5 bg-slate-600 text-slate-200 text-sm font-medium rounded-lg hover:bg-slate-500 transition-all flex items-center gap-1.5"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                    Registrations ({event.registered_count})
                  </button>
                  <Link
                    href={`/companies/${companyId}/events/create`}
                    className="px-3 py-1.5 bg-slate-600 text-slate-200 text-sm font-medium rounded-lg hover:bg-slate-500 transition-all flex items-center gap-1.5"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Create
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </CardContent>

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

      {/* Registrations Modal */}
      {showRegistrations && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-slate-900 rounded-xl shadow-2xl max-w-4xl w-full max-h-[80vh] overflow-hidden border border-slate-700">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-slate-700">
              <div>
                <h2 className="text-2xl font-bold text-white">Event Registrations</h2>
                <p className="text-slate-400 text-sm mt-1">{event?.title}</p>
              </div>
              <button
                onClick={() => setShowRegistrations(false)}
                className="text-slate-400 hover:text-white transition-colors p-2 hover:bg-slate-800 rounded-lg"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto max-h-[calc(80vh-140px)]">
              {loadingRegistrations ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold-400"></div>
                </div>
              ) : registrations.length === 0 ? (
                <div className="text-center py-12">
                  <svg className="w-16 h-16 text-slate-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                  <p className="text-slate-400 text-lg">No registrations yet</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {registrations.map((registration, index) => (
                    <div
                      key={registration.id}
                      className="bg-slate-800 rounded-lg p-4 hover:bg-slate-750 transition-colors border border-slate-700"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4 flex-1">
                          {/* User Avatar */}
                          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-gold-400 to-copper-400 flex items-center justify-center text-white font-bold text-lg flex-shrink-0">
                            {registration.user.full_name.charAt(0).toUpperCase()}
                          </div>

                          {/* User Info */}
                          <div className="flex-1 min-w-0">
                            <h3 className="text-white font-semibold text-lg">
                              {registration.user.full_name}
                            </h3>
                            <div className="flex items-center gap-4 text-sm text-slate-400 mt-1">
                              <div className="flex items-center gap-1">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                </svg>
                                <span>{registration.user.username}</span>
                              </div>
                              <div className="flex items-center gap-1">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                </svg>
                                <span>{registration.user.email}</span>
                              </div>
                            </div>
                          </div>

                          {/* Registration Info */}
                          <div className="text-right">
                            <div className="flex items-center gap-2 text-sm text-slate-400">
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                              <span>
                                {new Date(registration.registered_at).toLocaleDateString('en-US', {
                                  month: 'short',
                                  day: 'numeric',
                                  hour: 'numeric',
                                  minute: '2-digit',
                                })}
                              </span>
                            </div>
                            <Badge
                              variant={registration.status === 'attended' ? 'gold' : 'slate'}
                              className="mt-2 text-xs"
                            >
                              {registration.status === 'registered' && (
                                <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                              )}
                              {registration.status}
                            </Badge>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-between p-6 border-t border-slate-700 bg-slate-850">
              <div className="text-slate-400 text-sm">
                Total: <span className="text-white font-semibold">{registrations.length}</span> registered
                {event?.max_participants && (
                  <span> / {event.max_participants} capacity</span>
                )}
              </div>
              <button
                onClick={() => setShowRegistrations(false)}
                className="px-4 py-2 bg-slate-700 text-white font-medium rounded-lg hover:bg-slate-600 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}
