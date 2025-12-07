'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import {
  Calendar,
  Clock,
  Users,
  Video,
  MessageSquare,
  ArrowLeft,
  CheckCircle,
  AlertCircle,
  ThumbsUp,
  Heart,
  Flame,
  Sparkles,
  User,
  Send
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import LogoMono from '@/components/LogoMono';
import { LoginModal, RegisterModal } from '@/components/auth';
import { useAuth } from '@/contexts/AuthContext';

interface Speaker {
  id: number;
  user: {
    id: number;
    username: string;
    full_name: string;
  };
  title: string;
  bio: string;
  is_primary: boolean;
}

interface Question {
  id: number;
  user: {
    username: string;
    full_name: string;
  };
  content: string;
  status: string;
  answer: string;
  upvotes: number;
  is_featured: boolean;
  created_at: string;
  answered_at: string | null;
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
  agenda: string;
  scheduled_start: string;
  scheduled_end: string;
  duration_minutes: number;
  format: 'video' | 'text';
  status: string;
  max_participants: number | null;
  registered_count: number;
  attended_count: number;
  stream_url: string;
  is_recorded: boolean;
  recording_url: string;
  transcript_url: string;
  speakers: Speaker[];
  is_registered: boolean;
  can_register: boolean;
}

export default function EventDetailPage() {
  const router = useRouter();
  const params = useParams();
  const { user, logout } = useAuth();
  const [event, setEvent] = useState<SpeakerEvent | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [questionContent, setQuestionContent] = useState('');
  const [submittingQuestion, setSubmittingQuestion] = useState(false);
  const [streamUrl, setStreamUrl] = useState('');
  const [submittingStreamUrl, setSubmittingStreamUrl] = useState(false);
  const [showStreamUrlForm, setShowStreamUrlForm] = useState(false);
  const [reactionCounts, setReactionCounts] = useState<Record<string, number>>({
    applause: 0,
    thumbs_up: 0,
    fire: 0,
    heart: 0,
  });
  const [showReactionAnimation, setShowReactionAnimation] = useState<string | null>(null);

  useEffect(() => {
    if (params.eventId) {
      fetchEventDetails();
      fetchQuestions();
      fetchReactionCounts();
    }
  }, [params.eventId]);

  const fetchEventDetails = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      const headers: HeadersInit = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://api.juniorgoldminingintelligence.com/api'}/events/${params.eventId}/`, {
        headers,
      });

      if (response.ok) {
        const data = await response.json();
        setEvent(data);
      }
    } catch (error) {
      console.error('Error fetching event:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchQuestions = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://api.juniorgoldminingintelligence.com/api'}/event-questions/?event=${params.eventId}`);
      if (response.ok) {
        const data = await response.json();
        // Handle both array response and paginated response
        const questionsArray = Array.isArray(data) ? data : (data.results || []);
        setQuestions(questionsArray);
      }
    } catch (error) {
      console.error('Error fetching questions:', error);
    }
  };

  const handleRegister = async () => {
    if (!user) {
      setShowLogin(true);
      return;
    }

    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://api.juniorgoldminingintelligence.com/api'}/events/${params.eventId}/register/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        fetchEventDetails();
      }
    } catch (error) {
      console.error('Error registering for event:', error);
    }
  };

  const handleUnregister = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://api.juniorgoldminingintelligence.com/api'}/events/${params.eventId}/unregister/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        fetchEventDetails();
      }
    } catch (error) {
      console.error('Error unregistering from event:', error);
    }
  };

  const handleEndEvent = async () => {
    if (!confirm('Are you sure you want to end this live event?')) {
      return;
    }

    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://api.juniorgoldminingintelligence.com/api'}/events/${params.eventId}/`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          status: 'ended',
        }),
      });

      if (response.ok) {
        fetchEventDetails();
      }
    } catch (error) {
      console.error('Error ending event:', error);
    }
  };

  const handleGoLive = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!streamUrl.trim()) return;

    setSubmittingStreamUrl(true);
    try {
      const token = localStorage.getItem('accessToken');

      // Convert YouTube watch URL to embed URL if needed
      let embedUrl = streamUrl.trim();
      if (embedUrl.includes('youtube.com/watch?v=')) {
        const videoId = embedUrl.split('v=')[1]?.split('&')[0];
        embedUrl = `https://www.youtube.com/embed/${videoId}`;
      } else if (embedUrl.includes('youtube.com/live/') || embedUrl.includes('youtu.be/')) {
        const videoId = embedUrl.split('/').pop()?.split('?')[0];
        embedUrl = `https://www.youtube.com/embed/${videoId}`;
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://api.juniorgoldminingintelligence.com/api'}/events/${params.eventId}/`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          status: 'live',
          stream_url: embedUrl,
        }),
      });

      if (response.ok) {
        setStreamUrl('');
        setShowStreamUrlForm(false);
        fetchEventDetails();
      }
    } catch (error) {
      console.error('Error going live:', error);
    } finally {
      setSubmittingStreamUrl(false);
    }
  };

  const handleSubmitQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) {
      setShowLogin(true);
      return;
    }

    if (!questionContent.trim()) return;

    setSubmittingQuestion(true);
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://api.juniorgoldminingintelligence.com/api'}/event-questions/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          event: params.eventId,
          content: questionContent,
        }),
      });

      if (response.ok) {
        setQuestionContent('');
        fetchQuestions();
      }
    } catch (error) {
      console.error('Error submitting question:', error);
    } finally {
      setSubmittingQuestion(false);
    }
  };

  const handleUpvoteQuestion = async (questionId: number) => {
    if (!user) {
      setShowLogin(true);
      return;
    }

    try {
      const token = localStorage.getItem('accessToken');
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://api.juniorgoldminingintelligence.com/api'}/event-questions/${questionId}/upvote/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      fetchQuestions();
    } catch (error) {
      console.error('Error upvoting question:', error);
    }
  };

  const fetchReactionCounts = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://api.juniorgoldminingintelligence.com/api'}/event-reactions/?event=${params.eventId}`);
      if (response.ok) {
        const data = await response.json();
        const counts: Record<string, number> = {
          applause: 0,
          thumbs_up: 0,
          fire: 0,
          heart: 0,
        };
        // Handle both array response and paginated response
        const reactions = Array.isArray(data) ? data : (data.results || []);
        reactions.forEach((reaction: any) => {
          counts[reaction.reaction_type] = (counts[reaction.reaction_type] || 0) + 1;
        });
        setReactionCounts(counts);
      }
    } catch (error) {
      console.error('Error fetching reactions:', error);
    }
  };

  const handleReaction = async (reactionType: string) => {
    if (!user) {
      setShowLogin(true);
      return;
    }

    try {
      const token = localStorage.getItem('accessToken');
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://api.juniorgoldminingintelligence.com/api'}/event-reactions/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          event: params.eventId,
          reaction_type: reactionType,
        }),
      });

      // Update local count immediately
      setReactionCounts(prev => ({
        ...prev,
        [reactionType]: prev[reactionType] + 1,
      }));

      // Show animation
      setShowReactionAnimation(reactionType);
      setTimeout(() => setShowReactionAnimation(null), 1000);

      // Refresh counts from server
      setTimeout(() => fetchReactionCounts(), 500);
    } catch (error) {
      console.error('Error sending reaction:', error);
    }
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
      timeZoneName: 'short',
    });
  };

  const getStatusBadge = (status: string) => {
    const configs: Record<string, { color: string; label: string }> = {
      draft: { color: 'bg-slate-500/20 text-slate-300 border-slate-500/30', label: 'Draft' },
      scheduled: { color: 'bg-blue-500/20 text-blue-300 border-blue-500/30', label: 'Scheduled' },
      live: { color: 'bg-green-500/20 text-green-300 border-green-500/30 animate-pulse', label: 'Live Now' },
      ended: { color: 'bg-slate-500/20 text-slate-300 border-slate-500/30', label: 'Ended' },
      cancelled: { color: 'bg-red-500/20 text-red-300 border-red-500/30', label: 'Cancelled' },
    };

    const config = configs[status] || configs.scheduled;
    return (
      <Badge className={`${config.color} border px-3 py-1`}>
        {config.label}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold-400 mx-auto mb-4"></div>
          <p className="text-slate-300">Loading event...</p>
        </div>
      </div>
    );
  }

  if (!event) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">Event Not Found</h2>
          <p className="text-slate-300 mb-6">The event you're looking for doesn't exist.</p>
          <Button variant="primary" onClick={() => router.push('/')}>
            Go Home
          </Button>
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
            <div className="flex items-center space-x-3 cursor-pointer" onClick={() => router.push('/')}>
              <LogoMono className="h-18" />
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant="copper">AI-Powered</Badge>
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
                  <Button variant="primary" size="sm" onClick={() => setShowRegister(true)}>
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

      {/* Hero Section */}
      <section className="relative py-20 px-4 sm:px-6 lg:px-8 overflow-hidden">
        <div className="absolute inset-0 bg-linear-to-b from-slate-900 via-slate-900 to-slate-800 opacity-50"></div>
        <div className="absolute inset-0" style={{
          backgroundImage: 'radial-gradient(circle at 50% 50%, rgba(212, 161, 42, 0.1) 0%, transparent 50%)'
        }}></div>

        <div className="relative max-w-7xl mx-auto">
          <button
            onClick={() => router.push(`/companies/${event.company.id}`)}
            className="flex items-center gap-2 text-slate-300 hover:text-white mb-8 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to {event.company.name}
          </button>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Left: Event Info */}
            <div className="md:col-span-2">
              <div className="flex items-center gap-3 mb-4">
                <span className="text-gold-400 font-semibold">{event.company.name}</span>
                <span className="text-slate-600">•</span>
                <span className="text-slate-400">{event.company.ticker_symbol}</span>
                <span className="text-slate-600">•</span>
                {getStatusBadge(event.status)}
              </div>

              <h1 className="text-5xl md:text-6xl font-bold mb-6 text-gradient-gold animate-fade-in leading-tight pb-2">
                {event.title}
              </h1>

              <p className="text-xl text-slate-300 mb-8 leading-relaxed">
                {event.description}
              </p>

              {/* Event Meta */}
              <div className="flex flex-wrap gap-6 text-sm">
                <div className="flex items-center gap-2 text-slate-300">
                  <Calendar className="w-5 h-5 text-gold-400" />
                  <span>{formatDate(event.scheduled_start)}</span>
                </div>
                <div className="flex items-center gap-2 text-slate-300">
                  <Clock className="w-5 h-5 text-gold-400" />
                  <span>{formatTime(event.scheduled_start)}</span>
                </div>
                <div className="flex items-center gap-2 text-slate-300">
                  <Clock className="w-5 h-5 text-gold-400" />
                  <span>{event.duration_minutes} minutes</span>
                </div>
                <div className="flex items-center gap-2 text-slate-300">
                  {event.format === 'video' ? (
                    <>
                      <Video className="w-5 h-5 text-gold-400" />
                      <span>Video Stream</span>
                    </>
                  ) : (
                    <>
                      <MessageSquare className="w-5 h-5 text-gold-400" />
                      <span>Text Chat</span>
                    </>
                  )}
                </div>
                <div className="flex items-center gap-2 text-slate-300">
                  <Users className="w-5 h-5 text-gold-400" />
                  <span>{event.registered_count} registered</span>
                </div>
              </div>
            </div>

            {/* Right: Registration Card */}
            <div>
              <div className="backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl p-6 sticky top-32">
                <h3 className="text-xl font-bold text-white mb-4">Event Registration</h3>

                {event.status === 'live' && (
                  <div className="mb-4 p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
                    <div className="flex items-center gap-2 text-green-400 mb-2">
                      <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
                      <span className="font-semibold">Event is Live!</span>
                    </div>
                    <p className="text-sm text-slate-300">Join now to participate</p>
                  </div>
                )}

                {/* Superuser Controls */}
                {user?.is_superuser && event.status === 'scheduled' && (
                  <div className="mb-4">
                    {!showStreamUrlForm ? (
                      <Button
                        variant="primary"
                        className="w-full"
                        onClick={() => setShowStreamUrlForm(true)}
                      >
                        Go Live
                      </Button>
                    ) : (
                      <form onSubmit={handleGoLive} className="space-y-3">
                        <div>
                          <label className="block text-sm font-medium text-slate-300 mb-2">
                            YouTube Stream URL
                          </label>
                          <input
                            type="text"
                            value={streamUrl}
                            onChange={(e) => setStreamUrl(e.target.value)}
                            placeholder="https://youtube.com/live/..."
                            className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-gold-500"
                            disabled={submittingStreamUrl}
                          />
                          <p className="text-xs text-slate-400 mt-1">
                            Paste your YouTube live stream URL (watch or live URL)
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            type="submit"
                            variant="primary"
                            className="flex-1"
                            disabled={submittingStreamUrl || !streamUrl.trim()}
                          >
                            {submittingStreamUrl ? 'Starting...' : 'Start Streaming'}
                          </Button>
                          <Button
                            type="button"
                            variant="secondary"
                            onClick={() => {
                              setShowStreamUrlForm(false);
                              setStreamUrl('');
                            }}
                            disabled={submittingStreamUrl}
                          >
                            Cancel
                          </Button>
                        </div>
                      </form>
                    )}
                  </div>
                )}

                {user?.is_superuser && event.status === 'live' && (
                  <div className="mb-4">
                    <Button
                      variant="secondary"
                      className="w-full bg-red-600 hover:bg-red-700 text-white"
                      onClick={handleEndEvent}
                    >
                      End Event
                    </Button>
                  </div>
                )}

                {event.is_registered ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2 text-green-400 mb-2">
                      <CheckCircle className="w-5 h-5" />
                      <span className="font-semibold">You're registered!</span>
                    </div>
                    <p className="text-sm text-slate-300 mb-4">
                      You'll receive a reminder before the event starts.
                    </p>
                    <Button
                      variant="secondary"
                      className="w-full"
                      onClick={handleUnregister}
                    >
                      Unregister
                    </Button>
                  </div>
                ) : event.can_register ? (
                  <div className="space-y-4">
                    <p className="text-sm text-slate-300 mb-4">
                      Register to receive notifications and participate in the Q&A session.
                    </p>
                    <Button
                      variant="primary"
                      className="w-full"
                      onClick={handleRegister}
                    >
                      Register Now
                    </Button>
                  </div>
                ) : (
                  <div className="p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                    <p className="text-sm text-yellow-300">
                      {event.status === 'ended' ? 'This event has ended' : 'Registration is not available'}
                    </p>
                  </div>
                )}

                {event.max_participants && (
                  <div className="mt-4 text-xs text-slate-400">
                    <p>{event.registered_count} / {event.max_participants} participants</p>
                    <div className="w-full bg-slate-700/50 rounded-full h-2 mt-2">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-gold-400 to-gold-500"
                        style={{
                          width: `${(event.registered_count / event.max_participants) * 100}%`
                        }}
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-8 pb-16">
        {/* Live Video Stream Section */}
        {event.status === 'live' && event.stream_url && (
          <div className="mb-12">
            <div className="backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl overflow-hidden">
              <div className="bg-gradient-to-r from-red-500/20 to-red-600/20 border-b border-red-500/30 px-6 py-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                    <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                    LIVE NOW
                  </h2>
                  <Badge className="bg-red-500/20 text-red-300 border-red-500/30">
                    {event.registered_count} watching
                  </Badge>
                </div>
              </div>

              <div className="relative w-full" style={{ paddingBottom: '56.25%' }}>
                <iframe
                  src={event.stream_url}
                  className="absolute top-0 left-0 w-full h-full"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                  title="Live Event Stream"
                />
              </div>
            </div>
          </div>
        )}

        {/* Live Reactions Section - Only show if event is live or scheduled */}
        {(event.status === 'live' || event.status === 'scheduled') && (
          <div className="mb-12">
            <div className="backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                  <Sparkles className="w-6 h-6 text-gold-400" />
                  Live Reactions
                </h2>
                {event.status === 'live' && (
                  <Badge className="bg-green-500/20 text-green-300 border-green-500/30 animate-pulse">
                    Event is Live
                  </Badge>
                )}
              </div>

              <p className="text-slate-300 mb-6">
                {user ? 'Show your engagement with live reactions!' : 'Log in to send reactions'}
              </p>

              {/* Reaction Buttons */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { type: 'applause', icon: '👏', label: 'Applause', color: 'from-yellow-500/20 to-orange-500/20 border-yellow-500/30' },
                  { type: 'thumbs_up', icon: '👍', label: 'Thumbs Up', color: 'from-blue-500/20 to-cyan-500/20 border-blue-500/30' },
                  { type: 'fire', icon: '🔥', label: 'Fire', color: 'from-red-500/20 to-orange-500/20 border-red-500/30' },
                  { type: 'heart', icon: '❤️', label: 'Love It', color: 'from-pink-500/20 to-purple-500/20 border-pink-500/30' },
                ].map((reaction) => (
                  <button
                    key={reaction.type}
                    onClick={() => handleReaction(reaction.type)}
                    disabled={!user}
                    className={`relative p-6 rounded-xl border backdrop-blur-sm bg-gradient-to-br ${reaction.color} hover:scale-105 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 ${
                      showReactionAnimation === reaction.type ? 'animate-bounce' : ''
                    }`}
                  >
                    <div className="text-center">
                      <div className="text-4xl mb-2">{reaction.icon}</div>
                      <div className="text-sm font-semibold text-white mb-1">{reaction.label}</div>
                      <div className="text-2xl font-bold text-gold-400">
                        {reactionCounts[reaction.type] || 0}
                      </div>
                    </div>

                    {/* Animated emoji on click */}
                    {showReactionAnimation === reaction.type && (
                      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                        <div className="text-6xl animate-ping opacity-75">
                          {reaction.icon}
                        </div>
                      </div>
                    )}
                  </button>
                ))}
              </div>

              {/* Total Reactions Counter */}
              <div className="mt-6 text-center">
                <p className="text-slate-400 text-sm">
                  Total reactions: <span className="font-bold text-gold-400">
                    {Object.values(reactionCounts).reduce((sum, count) => sum + count, 0)}
                  </span>
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Speakers Section */}
        {event.speakers.length > 0 && (
          <div className="mb-12">
            <h2 className="text-3xl font-bold text-white mb-6">Featured Speakers</h2>
            <div className="grid md:grid-cols-2 gap-6">
              {event.speakers.map((speaker) => (
                <div
                  key={speaker.id}
                  className="backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl p-6"
                >
                  <div className="flex items-start gap-4">
                    <div className="w-16 h-16 rounded-full bg-gradient-to-br from-gold-500/20 to-copper-500/20 flex items-center justify-center flex-shrink-0">
                      <User className="w-8 h-8 text-gold-400" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="text-xl font-semibold text-white">
                          {speaker.user.full_name}
                        </h3>
                        {speaker.is_primary && (
                          <Badge className="bg-gold-500/20 text-gold-300 border-gold-500/30 text-xs">
                            Primary
                          </Badge>
                        )}
                      </div>
                      <p className="text-gold-400 text-sm mb-3">{speaker.title}</p>
                      <p className="text-slate-300 text-sm leading-relaxed">{speaker.bio}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Agenda Section */}
        {event.agenda && (
          <div className="mb-12">
            <h2 className="text-3xl font-bold text-white mb-6">Event Agenda</h2>
            <div className="backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl p-8">
              <div className="prose prose-invert prose-gold max-w-none">
                <div className="whitespace-pre-wrap text-slate-300 leading-relaxed">
                  {event.agenda}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Q&A Section */}
        <div className="mb-12">
          <h2 className="text-3xl font-bold text-white mb-6">Questions & Answers</h2>

          {/* Submit Question Form */}
          <div className="backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl p-6 mb-6">
            <h3 className="text-lg font-semibold text-white mb-4">Ask a Question</h3>
            <form onSubmit={handleSubmitQuestion}>
              <textarea
                value={questionContent}
                onChange={(e) => setQuestionContent(e.target.value)}
                placeholder={user ? "Type your question here..." : "Please log in to ask a question"}
                disabled={!user || submittingQuestion}
                className="w-full bg-slate-900/50 border border-slate-700 rounded-lg p-4 text-white placeholder-slate-500 focus:border-gold-400 focus:outline-none resize-none"
                rows={3}
              />
              <div className="flex items-center justify-between mt-4">
                <p className="text-xs text-slate-400">
                  {user ? 'Your question will be reviewed before being displayed' : 'Please log in to ask questions'}
                </p>
                <Button
                  type="submit"
                  variant="primary"
                  disabled={!user || submittingQuestion || !questionContent.trim()}
                  className="flex items-center gap-2"
                >
                  <Send className="w-4 h-4" />
                  Submit
                </Button>
              </div>
            </form>
          </div>

          {/* Questions List */}
          <div className="space-y-4">
            {questions.length === 0 ? (
              <div className="backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl p-12 text-center">
                <MessageSquare className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">No questions yet. Be the first to ask!</p>
              </div>
            ) : (
              questions.map((question) => (
                <div
                  key={question.id}
                  className="backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl p-6"
                >
                  <div className="flex items-start gap-4">
                    <button
                      onClick={() => handleUpvoteQuestion(question.id)}
                      className="flex flex-col items-center gap-1 flex-shrink-0 hover:text-gold-400 transition-colors"
                      disabled={!user}
                    >
                      <ThumbsUp className="w-5 h-5" />
                      <span className="text-sm font-semibold">{question.upvotes}</span>
                    </button>

                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="font-semibold text-white">{question.user.full_name}</span>
                        <span className="text-xs text-slate-400">
                          {new Date(question.created_at).toLocaleDateString()}
                        </span>
                        {question.is_featured && (
                          <Badge className="bg-purple-500/20 text-purple-300 border-purple-500/30 text-xs">
                            Featured
                          </Badge>
                        )}
                        {question.status === 'answered' && (
                          <Badge className="bg-green-500/20 text-green-300 border-green-500/30 text-xs">
                            Answered
                          </Badge>
                        )}
                      </div>

                      <p className="text-slate-300 mb-3">{question.content}</p>

                      {question.answer && (
                        <div className="mt-4 pl-4 border-l-2 border-gold-400">
                          <p className="text-sm font-semibold text-gold-400 mb-1">Answer:</p>
                          <p className="text-slate-300 text-sm">{question.answer}</p>
                          {question.answered_at && (
                            <p className="text-xs text-slate-400 mt-2">
                              Answered on {new Date(question.answered_at).toLocaleDateString()}
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Recording/Transcript Section */}
        {event.status === 'ended' && (event.recording_url || event.transcript_url) && (
          <div className="backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl p-8">
            <h2 className="text-2xl font-bold text-white mb-6">Event Recording & Resources</h2>
            <div className="space-y-4">
              {event.recording_url && (
                <div>
                  <h3 className="text-lg font-semibold text-white mb-2">Video Recording</h3>
                  <Button variant="primary" onClick={() => window.open(event.recording_url, '_blank')}>
                    Watch Recording
                  </Button>
                </div>
              )}
              {event.transcript_url && (
                <div>
                  <h3 className="text-lg font-semibold text-white mb-2">Event Transcript</h3>
                  <Button variant="secondary" onClick={() => window.open(event.transcript_url, '_blank')}>
                    View Transcript
                  </Button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
