'use client';

import { use, useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useEventWebSocket } from '@/hooks/useEventWebSocket';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/contexts/AuthContext';
import { LoginModal, RegisterModal } from '@/components/auth';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function EventPage({ params }: PageProps) {
  const { id } = use(params);
  const eventId = parseInt(id);
  const router = useRouter();

  const [error, setError] = useState<string | null>(null);
  const [questionInput, setQuestionInput] = useState('');
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const questionsEndRef = useRef<HTMLDivElement>(null);
  const { user, accessToken } = useAuth();

  // Redirect if not authenticated
  useEffect(() => {
    if (!user || !accessToken) {
      setShowLogin(true);
    }
  }, [user, accessToken]);

  const {
    isConnected,
    event,
    questions,
    participants,
    recentReactions,
    submitQuestion,
    upvoteQuestion,
    sendReaction,
  } = useEventWebSocket({
    eventId,
    token: accessToken || '',
    onError: setError,
  });

  // Auto-scroll to bottom when new questions arrive
  useEffect(() => {
    questionsEndRef.current?.scrollIntoView({
      behavior: 'smooth',
      block: 'nearest',
      inline: 'nearest',
    });
  }, [questions]);

  // Clear error when connected
  useEffect(() => {
    if (isConnected) {
      setError(null);
    }
  }, [isConnected]);

  const handleSubmitQuestion = (e: React.FormEvent) => {
    e.preventDefault();
    if (questionInput.trim()) {
      submitQuestion(questionInput.trim());
      setQuestionInput('');
    }
  };

  const reactionEmojis = {
    applause: '👏',
    thumbs_up: '👍',
    fire: '🔥',
    heart: '❤️',
  };

  if (!event) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold-400"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">{event.title}</h1>
              <p className="text-slate-400">{event.description}</p>
            </div>
            <div className="flex items-center gap-3">
              {isConnected ? (
                <Badge variant="gold" className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                  Live
                </Badge>
              ) : (
                <Badge variant="slate" className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-red-400 rounded-full"></div>
                  Connecting...
                </Badge>
              )}
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <Card variant="glass-card" className="border-red-500/50 mb-4">
              <CardContent className="py-3">
                <div className="flex items-center gap-3 text-red-400">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  <span>{error}</span>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Main Content Area */}
          <div className="lg:col-span-3 space-y-6">
            {/* Video/Content Area */}
            <Card variant="glass-card">
              <CardContent className="p-0">
                {event.format === 'video' && event.video_url ? (
                  <div className="aspect-video bg-slate-950 rounded-lg overflow-hidden">
                    <iframe
                      src={event.video_url}
                      className="w-full h-full"
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                      allowFullScreen
                    ></iframe>
                  </div>
                ) : (
                  <div className="aspect-video bg-gradient-to-br from-slate-950 to-slate-900 rounded-lg flex items-center justify-center">
                    <div className="text-center">
                      <svg
                        className="w-24 h-24 mx-auto text-slate-700 mb-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                        />
                      </svg>
                      <p className="text-slate-400 text-lg">Text-based Event</p>
                      <p className="text-slate-500 text-sm mt-2">Ask questions below</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Reactions Bar */}
            <Card variant="glass-card">
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-slate-400 text-sm">React:</span>
                    <div className="flex gap-2">
                      {(Object.keys(reactionEmojis) as Array<keyof typeof reactionEmojis>).map((type) => (
                        <button
                          key={type}
                          onClick={() => sendReaction(type)}
                          className="px-4 py-2 bg-slate-800/50 hover:bg-slate-700/50 rounded-lg transition-all text-2xl"
                          title={type}
                        >
                          {reactionEmojis[type]}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Recent Reactions */}
                  <div className="flex items-center gap-1">
                    {recentReactions.slice(0, 10).map((reaction, index) => (
                      <div
                        key={`${reaction.timestamp}-${index}`}
                        className="text-2xl animate-bounce"
                        style={{ animationDelay: `${index * 100}ms` }}
                      >
                        {reactionEmojis[reaction.reaction_type]}
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Questions & Answers */}
            <Card variant="glass-card">
              <CardHeader>
                <CardTitle className="text-xl text-gold-400">Questions & Answers</CardTitle>
              </CardHeader>
              <CardContent>
                {/* Submit Question */}
                <form onSubmit={handleSubmitQuestion} className="mb-6">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={questionInput}
                      onChange={(e) => setQuestionInput(e.target.value)}
                      placeholder="Ask a question..."
                      maxLength={1000}
                      className="flex-1 px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-gold-400 transition-colors"
                    />
                    <button
                      type="submit"
                      disabled={!questionInput.trim() || !isConnected}
                      className="px-6 py-3 bg-gradient-to-r from-gold-500 to-copper-500 text-white font-semibold rounded-lg hover:from-gold-600 hover:to-copper-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Ask
                    </button>
                  </div>
                  <div className="text-xs text-slate-500 mt-2">
                    {questionInput.length}/1000 characters
                  </div>
                </form>

                {/* Questions List */}
                <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
                  {questions.length === 0 ? (
                    <div className="text-center py-12">
                      <svg
                        className="w-16 h-16 mx-auto text-slate-600 mb-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                      </svg>
                      <p className="text-slate-400 text-sm">No questions yet. Be the first to ask!</p>
                    </div>
                  ) : (
                    <>
                      {questions.map((question) => (
                        <Card
                          key={question.id}
                          variant="glass-card"
                          className={question.is_featured ? 'border-gold-500/50' : ''}
                        >
                          <CardContent className="p-4">
                            <div className="flex items-start gap-3">
                              {/* User Avatar */}
                              <div className="flex-shrink-0">
                                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gold-400 to-copper-400 flex items-center justify-center text-white font-bold">
                                  {question.user.full_name.charAt(0).toUpperCase()}
                                </div>
                              </div>

                              {/* Question Content */}
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="font-semibold text-white text-sm">
                                    {question.user.full_name}
                                  </span>
                                  {question.is_featured && (
                                    <Badge variant="gold" className="text-xs">
                                      Featured
                                    </Badge>
                                  )}
                                  <Badge
                                    variant={
                                      question.status === 'answered'
                                        ? 'gold'
                                        : question.status === 'approved'
                                        ? 'copper'
                                        : 'slate'
                                    }
                                    className="text-xs"
                                  >
                                    {question.status}
                                  </Badge>
                                </div>
                                <p className="text-slate-300 text-sm mb-2">{question.content}</p>
                                <div className="flex items-center gap-4">
                                  <button
                                    onClick={() => upvoteQuestion(question.id)}
                                    className="flex items-center gap-1 text-xs text-slate-400 hover:text-gold-400 transition-colors"
                                  >
                                    <svg
                                      className="w-4 h-4"
                                      fill="none"
                                      stroke="currentColor"
                                      viewBox="0 0 24 24"
                                    >
                                      <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M5 15l7-7 7 7"
                                      />
                                    </svg>
                                    {question.upvotes}
                                  </button>
                                  <span className="text-xs text-slate-500">
                                    {new Date(question.created_at).toLocaleTimeString()}
                                  </span>
                                </div>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                      <div ref={questionsEndRef} />
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar - Participants */}
          <div className="lg:col-span-1">
            <Card variant="glass-card" className="sticky top-4">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">Participants</CardTitle>
                  <Badge variant="gold" className="text-xs">
                    {participants.length}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-[600px] overflow-y-auto pr-2 custom-scrollbar">
                  {participants.map((participant) => (
                    <div
                      key={participant.id}
                      className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-800/50 transition-colors"
                    >
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gold-400 to-copper-400 flex items-center justify-center text-white font-bold text-sm">
                        {participant.full_name.charAt(0).toUpperCase()}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold text-white text-sm truncate">
                          {participant.full_name}
                        </div>
                        <div className="text-xs text-slate-400 truncate">@{participant.username}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Custom Scrollbar Styles */}
      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(15, 23, 42, 0.3);
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(212, 175, 55, 0.3);
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(212, 175, 55, 0.5);
        }
      `}</style>

      {/* Auth Modals */}
      {showLogin && (
        <LoginModal
          onClose={() => {
            setShowLogin(false);
            router.push('/');
          }}
          onSwitchToRegister={() => {
            setShowLogin(false);
            setShowRegister(true);
          }}
        />
      )}
      {showRegister && (
        <RegisterModal
          onClose={() => {
            setShowRegister(false);
            router.push('/');
          }}
          onSwitchToLogin={() => {
            setShowRegister(false);
            setShowLogin(true);
          }}
        />
      )}
    </div>
  );
}
