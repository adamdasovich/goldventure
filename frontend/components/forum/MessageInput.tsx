import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';

interface MessageInputProps {
  onSendMessage: (content: string, replyTo?: number) => void;
  onTypingStart: () => void;
  onTypingStop: () => void;
  disabled?: boolean;
  replyToMessageId?: number;
  replyToUserName?: string;
  onCancelReply?: () => void;
}

export function MessageInput({
  onSendMessage,
  onTypingStart,
  onTypingStop,
  disabled = false,
  replyToMessageId,
  replyToUserName,
  onCancelReply,
}: MessageInputProps) {
  const [message, setMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout>();

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message]);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setMessage(value);

    // Handle typing indicator
    if (value.trim() && !isTyping) {
      setIsTyping(true);
      onTypingStart();
    }

    // Clear previous timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    // Stop typing after 3 seconds of inactivity
    typingTimeoutRef.current = setTimeout(() => {
      if (isTyping) {
        setIsTyping(false);
        onTypingStop();
      }
    }, 3000);
  };

  const handleSend = () => {
    const content = message.trim();
    if (!content) return;

    onSendMessage(content, replyToMessageId);
    setMessage('');

    // Stop typing indicator
    if (isTyping) {
      setIsTyping(false);
      onTypingStop();
    }

    // Clear typing timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    // Focus back on textarea
    textareaRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  useEffect(() => {
    // Cleanup timeout on unmount
    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
    };
  }, []);

  return (
    <Card variant="glass-card">
      <CardContent className="p-4">
        {/* Reply indicator */}
        {replyToMessageId && replyToUserName && (
          <div className="mb-2 flex items-center justify-between px-3 py-2 bg-slate-800 rounded-lg">
            <div className="flex items-center gap-2 text-sm">
              <svg className="w-4 h-4 text-gold-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
              </svg>
              <span className="text-slate-400">
                Replying to <span className="text-white font-semibold">{replyToUserName}</span>
              </span>
            </div>
            <button
              onClick={onCancelReply}
              className="text-slate-400 hover:text-white transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}

        {/* Message Input */}
        <div className="flex items-end gap-3">
          <div className="flex-1">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder={disabled ? 'Connecting...' : 'Type your message... (Shift+Enter for new line)'}
              disabled={disabled}
              className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm resize-none focus:outline-none focus:ring-2 focus:ring-gold-400 placeholder-slate-500 disabled:opacity-50 disabled:cursor-not-allowed"
              rows={1}
              maxLength={5000}
              style={{
                minHeight: '48px',
                maxHeight: '150px',
              }}
            />
            <div className="mt-1 text-xs text-slate-500 text-right">
              {message.length}/5000
            </div>
          </div>

          <Button
            variant="primary"
            onClick={handleSend}
            disabled={disabled || !message.trim()}
            className="h-12 px-6"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
            Send
          </Button>
        </div>

        {/* Helpful hints */}
        <div className="mt-2 text-xs text-slate-500">
          Press <kbd className="px-1 py-0.5 bg-slate-700 rounded">Enter</kbd> to send,{' '}
          <kbd className="px-1 py-0.5 bg-slate-700 rounded">Shift+Enter</kbd> for new line
        </div>
      </CardContent>
    </Card>
  );
}
