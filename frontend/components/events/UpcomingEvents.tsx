'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useAuth } from '@/contexts/AuthContext';

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
  company: {
    id: number;
    name: string;
    ticker_symbol: string;
  };
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
}

export function UpcomingEvents() {
  const { user } = useAuth();
  const [events, setEvents] = useState<SpeakerEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<number | null>(null);

  const isSuperuser = user && user.is_superuser;

  useEffect(() => {
    fetchUpcomingEvents();
  }, []);

  const fetchUpcomingEvents = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/events/upcoming/`);
      if (!response.ok) throw new Error('Failed to fetch events');
      const data = await response.json();
      setEvents(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load events');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteEvent = async (eventId: number, eventTitle: string, e: React.MouseEvent) => {
    e.preventDefault(); // Prevent navigation
    e.stopPropagation(); // Prevent event bubbling

    if (!confirm(`Are you sure you want to delete the event "${eventTitle}"?\n\nThis action cannot be undone.`)) {
      return;
    }

    setDeleting(eventId);
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/events/${eventId}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to delete event');
      }

      // Remove the event from the list
      setEvents(events.filter(e => e.id !== eventId));
    } catch (err) {
      console.error('Error deleting event:', err);
      alert('Failed to delete event. Please try again.');
    } finally {
      setDeleting(null);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
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

    if (diffDays > 0) return `In ${diffDays} day${diffDays > 1 ? 's' : ''}`;
    if (diffHours > 0) return `In ${diffHours} hour${diffHours > 1 ? 's' : ''}`;
    return 'Soon';
  };

  if (loading) {
    return (
      <Card variant="glass-card">
        <CardHeader>
          <CardTitle className="text-2xl text-gold-400">Upcoming Speaker Events</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold-400"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card variant="glass-card">
        <CardHeader>
          <CardTitle className="text-2xl text-gold-400">Upcoming Speaker Events</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-red-400">
            <p>{error}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (events.length === 0) {
    return (
      <Card variant="glass-card">
        <CardHeader>
          <CardTitle className="text-2xl text-gold-400">Upcoming Speaker Events</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <svg className="w-16 h-16 mx-auto text-slate-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <p className="text-slate-400">No upcoming events scheduled</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card variant="glass-card">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-2xl text-gold-400">Upcoming Speaker Events</CardTitle>
          <Badge variant="gold">{events.length} event{events.length > 1 ? 's' : ''}</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {events.map((event) => (
            <Link
              key={event.id}
              href={`/companies/${event.company.id}/events/${event.id}`}
              className="block"
            >
              <Card
                variant="glass-card"
                className="hover:border-gold-400/50 transition-all duration-200 cursor-pointer"
              >
                <CardContent className="p-4">
                  <div className="flex items-start gap-4">
                    {/* Date Badge */}
                    <div className="flex-shrink-0 text-center bg-gradient-to-br from-gold-500/20 to-copper-500/20 rounded-lg p-3 min-w-[80px]">
                      <div className="text-2xl font-bold text-gold-400">
                        {new Date(event.scheduled_start).getDate()}
                      </div>
                      <div className="text-xs text-slate-400 uppercase">
                        {new Date(event.scheduled_start).toLocaleDateString('en-US', { month: 'short' })}
                      </div>
                      <div className="text-xs text-gold-400 mt-1">
                        {getTimeUntil(event.scheduled_start)}
                      </div>
                    </div>

                    {/* Event Details */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <div>
                          <h3 className="text-lg font-semibold text-white mb-1 line-clamp-1">
                            {event.title}
                          </h3>
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-sm text-gold-400 font-medium">
                              {event.company.name}
                            </span>
                            <span className="text-slate-600">•</span>
                            <span className="text-sm text-slate-400">
                              {event.company.ticker_symbol}
                            </span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          {event.format === 'video' ? (
                            <Badge variant="copper" className="text-xs">
                              <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                              </svg>
                              Video
                            </Badge>
                          ) : (
                            <Badge variant="slate" className="text-xs">
                              <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                              </svg>
                              Text
                            </Badge>
                          )}
                          {isSuperuser && (
                            <button
                              onClick={(e) => handleDeleteEvent(event.id, event.title, e)}
                              disabled={deleting === event.id}
                              className="p-2 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20 hover:border-red-500/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                              title="Delete Event"
                            >
                              {deleting === event.id ? (
                                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                              ) : (
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                              )}
                            </button>
                          )}
                        </div>
                      </div>

                      <p className="text-sm text-slate-400 mb-3 line-clamp-2">
                        {event.description}
                      </p>

                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4 text-xs text-slate-400">
                          <div className="flex items-center gap-1">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            {formatTime(event.scheduled_start)}
                          </div>
                          <div className="flex items-center gap-1">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            {event.duration_minutes} min
                          </div>
                          <div className="flex items-center gap-1">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                            </svg>
                            {event.registered_count} registered
                          </div>
                        </div>

                        {event.speakers.length > 0 && (
                          <div className="flex items-center gap-1 text-xs text-slate-400">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                            </svg>
                            {event.speakers[0].user.full_name}
                            {event.speakers.length > 1 && ` +${event.speakers.length - 1}`}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
