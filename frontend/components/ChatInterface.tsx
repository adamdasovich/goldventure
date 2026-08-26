"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "./ui/Card";
import { Input } from "./ui/Input";
import { Button } from "./ui/Button";
import { Badge } from "./ui/Badge";
import { claudeAPI } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import type { ChatMessage } from "@/types/api";

/* Short label on the chip, full question sent. Six sentence-long chips only
   fitted two per screen and read as instructions rather than options. */
const EXAMPLE_PROMPTS: { label: string; prompt: string }[] = [
  { label: "Compare two companies", prompt: "Compare Aftermath Silver and Aston Bay stock over 6 months" },
  { label: "Sector capital raised", prompt: "How much capital has the mining sector raised this year?" },
  { label: "Resource growth", prompt: "Has Aston Bay's gold resource grown over time?" },
  { label: "Does news move price?", prompt: "Does Aston Bay's news move its stock price?" },
  { label: "Unusual volume", prompt: "Find unusual trading volume in Aftermath Silver" },
  { label: "Who explores lithium?", prompt: "What companies are exploring lithium?" },
];

export default function ChatInterface() {
  const { accessToken, subscription } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [limitReached, setLimitReached] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  const tier = subscription?.effective_tier || "explorer";
  const dailyLimit = subscription?.features?.daily_chat_limit ?? 5;

  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop =
        messagesContainerRef.current.scrollHeight;
    }
  };

  const prevMessagesLengthRef = useRef(0);
  useEffect(() => {
    if (messages.length > prevMessagesLengthRef.current) {
      scrollToBottom();
    }
    prevMessagesLengthRef.current = messages.length;
  }, [messages]);

  const handleSend = async (overrideMessage?: string) => {
    const msg = overrideMessage || input.trim();
    if (!msg || isLoading) return;

    if (!accessToken) {
      setMessages([
        ...messages,
        { role: "user", content: msg },
        {
          role: "assistant",
          content:
            "Please log in to use the AI assistant. It's free to get started!",
        },
      ]);
      setInput("");
      return;
    }

    if (limitReached) return;

    setInput("");
    setIsLoading(true);

    const newMessages: ChatMessage[] = [
      ...messages,
      { role: "user", content: msg },
    ];
    setMessages(newMessages);

    try {
      const response = await claudeAPI.chat(
        { message: msg, conversation_history: messages },
        accessToken,
      );
      setMessages([
        ...newMessages,
        { role: "assistant", content: response.message },
      ]);
    } catch (error: any) {
      const errMsg =
        error instanceof Error ? error.message : "Failed to get response";
      // Check if it's a rate limit error
      if (errMsg.includes("limit") || errMsg.includes("429")) {
        setLimitReached(true);
      }
      setMessages([
        ...newMessages,
        { role: "assistant", content: `Error: ${errMsg}` },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleExampleClick = (prompt: string) => {
    handleSend(prompt);
  };

  return (
    <Card
      variant="glass-strong"
      /* Fixed 600px overran a 375x667 phone once the header and ticker were
         subtracted, and stranded the composer entirely in landscape. */
      className="flex flex-col h-[min(600px,70dvh)] max-w-4xl mx-auto"
    >
      <CardHeader className="border-b border-slate-700/50">
        {/* The upgrade pill was being squeezed to 75px by the title beside it
            and wrapping to four lines. It stacks under the title on a phone
            and sits alongside from sm up. */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="min-w-0">
            <CardTitle>Claude Mining Assistant</CardTitle>
          </div>
          {dailyLimit > 0 && tier === "explorer" && (
            <Link
              href="/pricing"
              className="inline-flex shrink-0 items-center self-start min-h-11"
            >
              <Badge
                variant="slate"
                className="cursor-pointer whitespace-nowrap hover:border-gold-400/50 transition-colors"
              >
                {dailyLimit} msgs/day &middot; Upgrade
              </Badge>
            </Link>
          )}
        </div>
      </CardHeader>

      <CardContent
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto space-y-4 py-4"
      >
        {messages.length === 0 ? (
          // min-h-full, not h-full: capping the card at 70dvh made this taller
          // than its scroll container on a phone, and `justify-center` then
          // pushed the overflow above the scroll origin where it could not be
          // reached. Growing past full height keeps it all scrollable.
          <div className="flex flex-col items-center justify-center min-h-full text-center space-y-3">
            {/* The 96px logo, the "Start a conversation" heading and the
                explainer beneath it all told people what a chat box is. The
                example prompts do that better by being tappable. */}
            <p className="text-xs uppercase tracking-[0.14em] text-slate-500">
              Try one of these
            </p>
            <div className="flex flex-wrap gap-2 justify-center max-w-2xl">
              {EXAMPLE_PROMPTS.map((example) => (
                <button
                  key={example.label}
                  title={example.prompt}
                  onClick={() => handleExampleClick(example.prompt)}
                  className="px-4 py-2.5 min-h-11 inline-flex items-center text-sm rounded-full bg-slate-800/60 border border-slate-700/50 text-slate-300 hover:text-gold-400 hover:border-gold-500/30 hover:bg-gold-500/10 transition-all cursor-pointer"
                >
                  {example.label}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} animate-slide-in-up`}
              >
                <div
                  className={`max-w-[80%] px-4 py-3 rounded-[var(--radius-md)] ${
                    msg.role === "user"
                      ? "gradient-gold text-white"
                      : "glass border border-slate-700"
                  }`}
                >
                  <div className="text-xs font-medium mb-1 opacity-70">
                    {msg.role === "user" ? "You" : "Claude"}
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
                    <div
                      className="animate-shimmer w-2 h-2 bg-gold-500 rounded-full"
                      style={{ animationDelay: "0.2s" }}
                    ></div>
                    <div
                      className="animate-shimmer w-2 h-2 bg-gold-500 rounded-full"
                      style={{ animationDelay: "0.4s" }}
                    ></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </CardContent>

      {/* Limit reached banner */}
      {limitReached && tier === "explorer" && (
        <div className="px-6 py-3 bg-gold-500/10 border-t border-gold-500/20">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gold-400">
              Daily message limit reached. Upgrade for unlimited AI chat.
            </p>
            <Link href="/pricing">
              <Button variant="primary" size="sm">
                Upgrade
              </Button>
            </Link>
          </div>
        </div>
      )}

      <div className="p-6 border-t border-slate-700/50">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              limitReached
                ? "Daily limit reached — upgrade for unlimited"
                : "Ask about companies, resources, projects..."
            }
            disabled={isLoading || limitReached}
            className="flex-1"
          />
          <Button
            onClick={() => handleSend()}
            disabled={isLoading || !input.trim() || limitReached}
            variant="primary"
          >
            Send
          </Button>
        </div>
      </div>
    </Card>
  );
}
