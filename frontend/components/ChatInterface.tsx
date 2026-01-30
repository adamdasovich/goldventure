'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from './ui/Card';
import { Input } from './ui/Input';
import { Button } from './ui/Button';
import { Badge } from './ui/Badge';
import { claudeAPI } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import type { ChatMessage, ToolCall } from '@/types/api';
import LogoIcon from './LogoIcon';

export default function ChatInterface() {
  const { accessToken } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [toolCalls, setToolCalls] = useState<ToolCall[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const messagesContainerRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    // Scroll within the messages container, not the whole page
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  };

  // Only auto-scroll when a new message is added, not on every render
  const prevMessagesLengthRef = useRef(0);

  useEffect(() => {
    // Only scroll if messages were actually added (not just state updates)
    if (messages.length > prevMessagesLengthRef.current) {
      scrollToBottom();
    }
    prevMessagesLengthRef.current = messages.length;
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    // Check if user is authenticated before sending
    if (!accessToken) {
      setMessages([
        ...messages,
        { role: 'user', content: input.trim() },
        { role: 'assistant', content: 'Please log in to use the chat feature.' },
      ]);
      setInput('');
      return;
    }

    const userMessage = input.trim();
    setInput('');
    setIsLoading(true);

    // Add user message to UI
    const newMessages: ChatMessage[] = [...messages, { role: 'user', content: userMessage }];
    setMessages(newMessages);

    try {
      const response = await claudeAPI.chat({
        message: userMessage,
        conversation_history: messages,
      }, accessToken);

      // Add assistant response
      setMessages([...newMessages, { role: 'assistant', content: response.message }]);
      setToolCalls(response.tool_calls);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages([
        ...newMessages,
        {
          role: 'assistant',
          content: `Error: ${error instanceof Error ? error.message : 'Failed to get response'}`,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Card variant="glass-strong" className="flex flex-col h-[600px] max-w-4xl mx-auto">
      <CardHeader className="border-b border-slate-700/50">
        <CardTitle>Claude Mining Assistant</CardTitle>
        <CardDescription>
          Ask me anything about your mining companies, projects, and resources
        </CardDescription>
      </CardHeader>

      <CardContent ref={messagesContainerRef} className="flex-1 overflow-y-auto space-y-4 py-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
            <LogoIcon className="h-24 w-24" />
            <div className="space-y-2">
              <h3 className="text-xl font-semibold text-gold-400">Start a conversation</h3>
              <p className="text-slate-400 max-w-md">
                Try asking about your companies, total resources, project details, or any mining data
              </p>
            </div>
            <div className="flex flex-wrap gap-2 justify-center max-w-2xl">
              <Badge variant="slate">What companies do I have?</Badge>
              <Badge variant="slate">Total gold resources?</Badge>
              <Badge variant="slate">Tell me about Aston Bay</Badge>
              <Badge variant="slate">What projects are in production?</Badge>
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-slide-in-up`}
              >
                <div
                  className={`max-w-[80%] px-4 py-3 rounded-[var(--radius-md)] ${
                    msg.role === 'user'
                      ? 'gradient-gold text-white'
                      : 'glass border border-slate-700'
                  }`}
                >
                  <div className="text-xs font-medium mb-1 opacity-70">
                    {msg.role === 'user' ? 'You' : 'Claude'}
                  </div>
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex justify-start animate-fade-in">
                <div className="glass border border-slate-700 px-4 py-3 rounded-[var(--radius-md)]">
                  <div className="flex items-center space-x-2">
                    <div className="animate-shimmer w-2 h-2 bg-gold-500 rounded-full"></div>
                    <div className="animate-shimmer w-2 h-2 bg-gold-500 rounded-full" style={{ animationDelay: '0.2s' }}></div>
                    <div className="animate-shimmer w-2 h-2 bg-gold-500 rounded-full" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </CardContent>

      {toolCalls.length > 0 && (
        <div className="px-6 py-3 border-t border-slate-700/50 glass-light">
          <div className="text-xs text-slate-400 mb-2">Tools used in last response:</div>
          <div className="flex flex-wrap gap-1.5">
            {toolCalls.map((tc, idx) => (
              <Badge key={idx} variant="copper">
                {tc.tool}
              </Badge>
            ))}
          </div>
        </div>
      )}

      <div className="p-6 border-t border-slate-700/50">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about companies, resources, projects..."
            disabled={isLoading}
            className="flex-1"
          />
          <Button onClick={handleSend} disabled={isLoading || !input.trim()} variant="primary">
            Send
          </Button>
        </div>
      </div>
    </Card>
  );
}
