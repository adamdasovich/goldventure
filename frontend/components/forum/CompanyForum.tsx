'use client';

import { useState, useEffect, useRef } from 'react';
import { useForumWebSocket } from '@/hooks/useForumWebSocket';
import { ForumMessage } from './ForumMessage';
import { MessageInput } from './MessageInput';
import { OnlineUsers } from './OnlineUsers';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/contexts/AuthContext';
import { LoginModal, RegisterModal } from '@/components/auth';

interface CompanyForumProps {
  companyId: number;
  companyName: string;
}

export function CompanyForum({ companyId, companyName }: CompanyForumProps) {
  const [error, setError] = useState<string | null>(null);
  const [currentUserId, setCurrentUserId] = useState<number | undefined>();
  const [replyToMessageId, setReplyToMessageId] = useState<number | undefined>();
  const [replyToUserName, setReplyToUserName] = useState<string | undefined>();
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { user, accessToken } = useAuth();

  // IMPORTANT: This assumes discussion ID 1 exists for company 2
  // In production, you'd fetch the discussion ID for this company from your API
  const DISCUSSION_ID = 1;

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
    discussionId: DISCUSSION_ID,
    token: accessToken || '',
    onError: setError,
  });

  // Auto-scroll to bottom when new messages arrive (within the chat container only)
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: 'smooth',
      block: 'nearest',
      inline: 'nearest'
    });
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

  // Show login prompt if user is not authenticated
  if (!user || !accessToken) {
    return (
      <>
        <Card variant="glass-card" className="border-gold-500/30">
          <CardHeader>
            <CardTitle className="text-2xl text-gold-400 mb-2">
              {companyName} Community Forum
            </CardTitle>
            <p className="text-slate-400 text-sm">
              Real-time discussion with investors and analysts
            </p>
          </CardHeader>
          <CardContent className="py-12">
            <div className="text-center max-w-md mx-auto">
              <div className="mb-6">
                <svg className="w-20 h-20 mx-auto text-gold-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                <h3 className="text-xl font-bold text-white mb-3">
                  Login Required
                </h3>
                <p className="text-slate-300 mb-6">
                  Please login or create an account to join the community discussion and connect with investors and analysts.
                </p>
              </div>
              <div className="flex items-center justify-center gap-3">
                <Button variant="ghost" onClick={() => setShowLogin(true)}>
                  Login
                </Button>
                <Button variant="primary" onClick={() => setShowRegister(true)}>
                  Create Account
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

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
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>{error}</span>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Messages Area */}
        <Card variant="glass-card">
          <CardContent className="p-4">
            <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
              {messages.length === 0 ? (
                <div className="text-center py-12">
                  <svg className="w-16 h-16 mx-auto text-slate-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
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
                      onEdit={editMessage}
                      onDelete={deleteMessage}
                      onReply={handleReply}
                    />
                  ))}
                  <div ref={messagesEndRef} />
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
