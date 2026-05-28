"use client";

import { useState, useEffect, useRef } from "react";
import { useForumWebSocket } from "@/hooks/useForumWebSocket";
import { ForumMessage } from "./ForumMessage";
import { MessageInput } from "./MessageInput";
import { OnlineUsers } from "./OnlineUsers";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/contexts/AuthContext";
import { LoginModal, RegisterModal } from "@/components/auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

interface CompanyForumProps {
  companyId: number;
  companyName: string;
}

export function CompanyForum({ companyId, companyName }: CompanyForumProps) {
  const [error, setError] = useState<string | null>(null);
  const [currentUserId, setCurrentUserId] = useState<number | undefined>();
  const [replyToMessageId, setReplyToMessageId] = useState<
    number | undefined
  >();
  const [replyToUserName, setReplyToUserName] = useState<string | undefined>();
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [discussionId, setDiscussionId] = useState<number | null>(null);
  const [loadingDiscussion, setLoadingDiscussion] = useState(true);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const { user, accessToken } = useAuth();

  // Fetch the correct discussion ID for this company
  useEffect(() => {
    const fetchDiscussion = async () => {
      if (!accessToken || !companyId) {
        setLoadingDiscussion(false);
        return;
      }

      try {
        const response = await fetch(
          `${API_URL}/companies/${companyId}/discussion/`,
          {
            headers: {
              Authorization: `Bearer ${accessToken}`,
            },
          },
        );

        if (response.ok) {
          const data = await response.json();
          setDiscussionId(data.discussion_id);
        } else {
          console.error("Failed to fetch discussion");
        }
      } catch (err) {
        console.error("Error fetching discussion:", err);
      } finally {
        setLoadingDiscussion(false);
      }
    };

    fetchDiscussion();
  }, [companyId, accessToken]);

  const {
    isConnected,
    messages,
    onlineUsers,
    typingUsers,
    sendMessage,
    editMessage,
    deleteMessage,
    startTyping,
    stopTyping,
  } = useForumWebSocket({
    discussionId: discussionId || 0,
    token: accessToken || "",
    onError: setError,
  });

  // Auto-scroll to bottom when new messages arrive — scroll the forum's own
  // message container, NOT the window. scrollIntoView() would scroll every
  // scrollable ancestor (including <html>), yanking the whole page down to
  // the forum when message history loads after the company page mounts.
  useEffect(() => {
    const container = messagesContainerRef.current;
    if (container) {
      container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
    }
  }, [messages]);

  // Clear error when connected
  useEffect(() => {
    if (isConnected) {
      setError(null);
    }
  }, [isConnected]);

  // Get current user ID from auth context
  useEffect(() => {
    if (user) {
      setCurrentUserId(user.id);
    }
  }, [user]);

  const handleSendMessage = (content: string, replyTo?: number) => {
    sendMessage(content, replyTo);
    setReplyToMessageId(undefined);
    setReplyToUserName(undefined);
  };

  const handleReply = (messageId: number) => {
    const message = messages.find((m) => m.id === messageId);
    if (message) {
      setReplyToMessageId(messageId);
      setReplyToUserName(message.user.full_name);
    }
  };

  const handleCancelReply = () => {
    setReplyToMessageId(undefined);
    setReplyToUserName(undefined);
  };

  // Show login prompt if user is not authenticated. Instead of a hard wall,
  // render a read-only preview of the most recent messages so visitors can
  // see the forum is alive — proof-of-life beats "Login Required" empty
  // states for conversion.
  if (!user || !accessToken) {
    return (
      <>
        <LoggedOutForumPreview
          companyId={companyId}
          companyName={companyName}
          onLoginClick={() => setShowLogin(true)}
          onRegisterClick={() => setShowRegister(true)}
        />

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
      </>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Main Forum Area */}
      <div className="lg:col-span-3 space-y-6">
        {/* Forum Header */}
        <Card variant="glass-card">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-2xl text-gold-400 mb-2">
                  {companyName} Community Forum
                </CardTitle>
                <p className="text-slate-400 text-sm">
                  Real-time discussion with investors and analysts
                </p>
              </div>
              <div className="flex items-center gap-2">
                {isConnected ? (
                  <Badge variant="gold" className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                    Connected
                  </Badge>
                ) : (
                  <Badge variant="slate" className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-red-400 rounded-full"></div>
                    Connecting...
                  </Badge>
                )}
              </div>
            </div>
          </CardHeader>
        </Card>

        {/* Error Message */}
        {error && (
          <Card variant="glass-card" className="border-red-500/50">
            <CardContent className="py-4">
              <div className="flex items-center gap-3 text-red-400">
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
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

        {/* Messages Area */}
        <Card variant="glass-card">
          <CardContent className="p-4">
            <div
              ref={messagesContainerRef}
              className="space-y-3 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar"
            >
              {messages.length === 0 ? (
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
                      d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                    />
                  </svg>
                  <p className="text-slate-400 text-sm">
                    No messages yet. Start the conversation!
                  </p>
                </div>
              ) : (
                <>
                  {messages.map((message) => (
                    <ForumMessage
                      key={message.id}
                      message={message}
                      currentUserId={currentUserId}
                      isAdmin={
                        user?.is_superuser || user?.user_type === "admin"
                      }
                      onEdit={editMessage}
                      onDelete={deleteMessage}
                      onReply={handleReply}
                    />
                  ))}
                </>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Message Input */}
        <MessageInput
          onSendMessage={handleSendMessage}
          onTypingStart={startTyping}
          onTypingStop={stopTyping}
          disabled={!isConnected}
          replyToMessageId={replyToMessageId}
          replyToUserName={replyToUserName}
          onCancelReply={handleCancelReply}
        />
      </div>

      {/* Sidebar */}
      <div className="lg:col-span-1">
        <OnlineUsers users={onlineUsers} typingUsers={typingUsers} />
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
    </div>
  );
}

interface ForumPreviewData {
  has_discussion: boolean;
  message_count: number;
  participant_count: number;
  last_message_at: string | null;
  recent_messages: {
    id: number;
    initials: string;
    content: string;
    created_at: string;
    is_pinned: boolean;
  }[];
}

function LoggedOutForumPreview({
  companyId,
  companyName,
  onLoginClick,
  onRegisterClick,
}: {
  companyId: number;
  companyName: string;
  onLoginClick: () => void;
  onRegisterClick: () => void;
}) {
  const [data, setData] = useState<ForumPreviewData | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_URL}/companies/${companyId}/forum-preview/`)
      .then((r) => (r.ok ? r.json() : null))
      .then((json) => {
        if (cancelled) return;
        setData(json);
        setLoaded(true);
      })
      .catch(() => {
        if (cancelled) return;
        setLoaded(true);
      });
    return () => {
      cancelled = true;
    };
  }, [companyId]);

  const formatRelative = (iso: string) => {
    const diffMs = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diffMs / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  const hasActivity =
    !!data && data.has_discussion && data.recent_messages.length > 0;

  return (
    <Card variant="glass-card" className="border-gold-500/30">
      <CardContent className="p-6 md:p-8">
        {/* Activity strip — only render when there's real activity to advertise.
            An empty room with "0 messages" is worse than no strip at all. */}
        {hasActivity && (
          <div className="flex items-center gap-4 mb-6 pb-4 border-b border-slate-700/50 text-sm text-slate-300 flex-wrap">
            <span className="inline-flex items-center gap-2">
              <span
                className="w-2 h-2 rounded-full bg-green-400 motion-safe:animate-pulse"
                aria-hidden="true"
              />
              <span className="font-semibold text-white">
                {data!.message_count}
              </span>{" "}
              message{data!.message_count !== 1 ? "s" : ""}
            </span>
            {data!.participant_count > 0 && (
              <span>
                <span className="font-semibold text-white">
                  {data!.participant_count}
                </span>{" "}
                participant{data!.participant_count !== 1 ? "s" : ""}
              </span>
            )}
            {data!.last_message_at && (
              <span className="text-slate-400">
                last activity {formatRelative(data!.last_message_at)}
              </span>
            )}
          </div>
        )}

        {/* Read-only preview messages — exists primarily to prove the forum
            is alive. Usernames are reduced to initials server-side so
            anonymous visitors can't scrape participant identity. */}
        {loaded && hasActivity ? (
          <div className="space-y-3 mb-6">
            {data!.recent_messages.map((msg) => (
              <div
                key={msg.id}
                className="flex items-start gap-3 p-3 rounded-lg bg-slate-800/40 border border-slate-700/40"
              >
                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-gold-500/30 to-copper-500/30 border border-gold-500/40 flex items-center justify-center flex-shrink-0">
                  <span className="text-xs font-semibold text-gold-300">
                    {msg.initials}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span
                      className="text-sm font-medium text-slate-400 select-none"
                      style={{ filter: "blur(3px)" }}
                      aria-label="Member name hidden"
                    >
                      Member name
                    </span>
                    <span className="text-xs text-slate-500">
                      {formatRelative(msg.created_at)}
                    </span>
                  </div>
                  <p className="text-sm text-slate-200 break-words">
                    {msg.content}
                  </p>
                </div>
              </div>
            ))}
          </div>
        ) : loaded ? (
          <div className="text-center py-8 mb-6 text-slate-400">
            <p className="text-sm">
              Be the first to start the discussion about {companyName}.
            </p>
          </div>
        ) : (
          <div className="text-center py-8 mb-6 text-slate-500">
            <p className="text-sm">Loading discussion preview…</p>
          </div>
        )}

        {/* Conversion CTA */}
        <div className="rounded-xl bg-gradient-to-r from-gold-500/10 via-copper-500/10 to-gold-500/10 border border-gold-500/30 p-5 text-center">
          <h3 className="text-lg font-bold text-white mb-2">
            {hasActivity
              ? `Join ${data!.participant_count > 0 ? data!.participant_count : "the"} investor${
                  data!.participant_count === 1 ? "" : "s"
                } discussing ${companyName}`
              : `Start the conversation about ${companyName}`}
          </h3>
          <p className="text-sm text-slate-300 mb-4">
            Create a free account to read full discussions, reply to other
            investors, and see who&apos;s online in real time.
          </p>
          <div className="flex items-center justify-center gap-3 flex-wrap">
            <Button variant="ghost" onClick={onLoginClick}>
              Login
            </Button>
            <Button variant="primary" onClick={onRegisterClick}>
              Create free account
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
