"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/Card";
import { Input } from "./ui/Input";
import { Button } from "./ui/Button";
import { Badge } from "./ui/Badge";
import { claudeAPI, ApiError } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { LoginModal, RegisterModal } from "@/components/auth";
import {
  fetchSignupOfferClient,
  SIGNUP_OFFER_FALLBACK,
  type SignupOffer,
} from "@/lib/signupOffer";
import type { ChatMessage } from "@/types/api";

/* Short label on the chip, full question sent. Six sentence-long chips only
   fitted two per screen and read as instructions rather than options. */
export const EXAMPLE_PROMPTS: { label: string; prompt: string }[] = [
  {
    label: "Compare two companies",
    prompt: "Compare Aftermath Silver and Aston Bay stock over 6 months",
  },
  {
    label: "Sector capital raised",
    prompt: "How much capital has the mining sector raised this year?",
  },
  {
    label: "Resource growth",
    prompt: "Has Aston Bay's gold resource grown over time?",
  },
  {
    label: "Does news move price?",
    prompt: "Does Aston Bay's news move its stock price?",
  },
  {
    label: "Unusual volume",
    prompt: "Find unusual trading volume in Aftermath Silver",
  },
  {
    label: "Who explores lithium?",
    prompt: "What companies are exploring lithium?",
  },
];

interface ChatInterfaceProps {
  /** Sent once on mount — a suggestion tapped on the launcher. */
  initialPrompt?: string;
  /** Rendered as a close control in the header when present. */
  onClose?: () => void;
  className?: string;
}

export default function ChatInterface({
  initialPrompt,
  onClose,
  className = "",
}: ChatInterfaceProps = {}) {
  const { accessToken, subscription, refreshAccessToken } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [limitReached, setLimitReached] = useState(false);
  // Signed-out visitors used to get a dead end here: the assistant replied
  // "Please log in to use the AI assistant" as plain text, with nothing to
  // click. Asking the assistant a question is the highest-intent action an
  // anonymous visitor takes on this site — the hero CTA leads straight to it —
  // so that sentence was terminating the funnel at its best moment.
  const [needsAccount, setNeedsAccount] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [showLogin, setShowLogin] = useState(false);
  const [offer, setOffer] = useState<SignupOffer>(SIGNUP_OFFER_FALLBACK);

  // Fetched rather than hardcoded so the prompt cannot promise a trial that
  // WELCOME_FREE_MONTH_ENABLED has since turned off.
  useEffect(() => {
    let cancelled = false;
    fetchSignupOfferClient().then((o) => {
      if (!cancelled) setOffer(o);
    });
    return () => {
      cancelled = true;
    };
  }, []);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const composerRef = useRef<HTMLInputElement>(null);

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
      // Keep their question on screen — it is the reason they are here, and
      // seeing it sit there unanswered is what makes the ask land.
      setMessages([...messages, { role: "user", content: msg }]);
      setNeedsAccount(true);
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
      // A 401 means the stored token went stale under us (expired between
      // refreshes, or invalidated server-side). Refresh once and retry before
      // surfacing anything — the raw SimpleJWT text ("Given token not valid
      // for any token type") means nothing to a visitor.
      if (error instanceof ApiError && error.status === 401) {
        const newToken = await refreshAccessToken();
        if (newToken) {
          try {
            const response = await claudeAPI.chat(
              { message: msg, conversation_history: messages },
              newToken,
            );
            setMessages([
              ...newMessages,
              { role: "assistant", content: response.message },
            ]);
            return;
          } catch {
            // Retry failed too — fall through to the session message.
          }
        }
        // No refresh possible: refreshAccessToken() has already logged the
        // user out (and is redirecting), but leave a readable trace in case
        // the navigation is interrupted.
        setMessages([
          ...newMessages,
          {
            role: "assistant",
            content: "Your session has expired — please sign in again.",
          },
        ]);
        setNeedsAccount(true);
        return;
      }
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

  const firedInitial = useRef(false);
  useEffect(() => {
    if (initialPrompt && !firedInitial.current) {
      firedInitial.current = true;
      handleSend(initialPrompt);
    }
    // handleSend closes over state that changes every render; firing once is
    // the whole point, so the ref guard is the control rather than the deps.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialPrompt]);

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
    <>
      <Card
        id="chat-panel"
        variant="glass-strong"
        /* Height comes from the modal now; the card just fills it. Opaque
         rather than glass: over a modal scrim the translucency let the page
         bleed through and the panel looked unfinished. */
        className={`flex flex-col h-[70dvh] max-h-[70dvh] w-full !bg-slate-900 !backdrop-blur-none border border-slate-700 ${className}`}
      >
        <CardHeader className="border-b border-slate-700/50">
          {/* The upgrade pill was being squeezed to 75px by the title beside it
            and wrapping to four lines. It stacks under the title on a phone
            and sits alongside from sm up. */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="min-w-0">
              <CardTitle id="assistant-title">
                Claude Mining Assistant
              </CardTitle>
            </div>
            <div className="flex items-center gap-2 self-start sm:self-auto">
              {onClose && (
                <button
                  type="button"
                  onClick={onClose}
                  aria-label="Close assistant"
                  className="order-2 -mr-2 p-2 text-slate-400 hover:text-white transition-colors sm:order-none"
                >
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              )}
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
              {needsAccount && (
                <div className="rounded-xl border border-gold-500/40 bg-slate-900/70 p-5 animate-slide-in-up">
                  <p className="text-white font-semibold mb-1">
                    {offer.free_trial_enabled
                      ? `Create a free account to get your answer`
                      : "Create a free account to get your answer"}
                  </p>
                  <p className="text-slate-300 text-sm leading-relaxed mb-4">
                    {offer.free_trial_enabled
                      ? `It also starts a ${offer.free_trial_days}-day trial with unlimited research across every company, every investor tool, and every open financing. No credit card.`
                      : `You get ${offer.fallback_chat_limit} research questions a day, free. No credit card.`}
                  </p>
                  <div className="flex flex-col sm:flex-row gap-3">
                    <Button
                      variant="primary"
                      onClick={() => setShowRegister(true)}
                    >
                      {offer.free_trial_enabled
                        ? "Start free trial"
                        : "Create free account"}
                    </Button>
                    <button
                      type="button"
                      onClick={() => setShowLogin(true)}
                      className="text-sm text-slate-400 hover:text-gold-300 transition-colors px-3 py-2 min-h-11 text-left sm:text-center"
                    >
                      Already have an account? Sign in
                    </button>
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
              ref={composerRef}
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
