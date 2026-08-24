"use client";

import { useState, useRef, useEffect } from "react";
import { claudeAPI, type ChatMessage } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

interface CompanyChatbotProps {
  companyId: number;
  companyName: string;
}

export default function CompanyChatbot({
  companyId,
  companyName,
}: CompanyChatbotProps) {
  const { accessToken } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // Scroll the chat's own message container, NOT the window. scrollIntoView()
  // scrolls every scrollable ancestor (including <html>), which would yank the
  // whole page to the chatbot when messages change.
  useEffect(() => {
    const container = messagesContainerRef.current;
    if (container) {
      container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
    }
  }, [messages]);

  // Core send logic - usable both from the input form and from a one-click
  // suggested-prompt chip.
  const sendMessage = async (text: string) => {
    const userMessage = text.trim();
    if (!userMessage || isLoading) return;

    setInput("");

    // Add user message to chat
    const newMessages: ChatMessage[] = [
      ...messages,
      { role: "user", content: userMessage },
    ];
    setMessages(newMessages);
    setIsLoading(true);

    try {
      // Call company-specific chat API
      const response = await claudeAPI.companyChat(
        companyId,
        {
          message: userMessage,
          conversation_history: messages,
        },
        accessToken || undefined,
      );

      // Add assistant response
      setMessages([
        ...newMessages,
        { role: "assistant", content: response.message },
      ]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages([
        ...newMessages,
        {
          role: "assistant",
          content:
            "Sorry, I encountered an error processing your request. Please try again.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  // Company-aware starter prompts that showcase the analytics tools.
  const suggestedQuestions = [
    `How has ${companyName}'s gold resource grown over time?`,
    `Does ${companyName}'s news actually move its stock price?`,
    `Show unusual trading volume for ${companyName}`,
    `What is ${companyName}'s dilution history?`,
    `Key metallurgy and recovery results for ${companyName}`,
    "What are the latest news releases?",
  ];

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-[calc(1.5rem+env(safe-area-inset-bottom))] right-4 sm:right-6 max-w-[calc(100vw-2rem)] bg-gradient-to-r from-gold-500 to-copper-500 hover:from-gold-600 hover:to-copper-600 text-black font-semibold px-5 sm:px-6 py-3 rounded-full shadow-lg flex items-center gap-2 transition-all hover:scale-105 z-50"
      >
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
            d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
          />
        </svg>
        {/* The company name is what overruns a 375px screen, and it also
            collides with the forum button pinned to the other corner. */}
        <span className="hidden sm:inline">Ask about {companyName}</span>
        <span className="sm:hidden">Ask</span>
      </button>
    );
  }

  return (
    <div className="fixed z-50 inset-x-3 bottom-[calc(0.75rem+env(safe-area-inset-bottom))] sm:inset-x-auto sm:right-6 sm:bottom-6 sm:w-96">
      <Card variant="glass-card" className="shadow-2xl">
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <svg
              className="w-5 h-5 text-gold-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
              />
            </svg>
            {companyName} Assistant
          </CardTitle>
          <button
            onClick={() => setIsOpen(false)}
            className="text-slate-400 hover:text-white transition-colors"
          >
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
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </CardHeader>

        <CardContent className="p-0">
          {/* Chat Messages */}
          <div
            ref={messagesContainerRef}
            className="h-[min(24rem,50dvh)] overflow-y-auto overscroll-contain px-4 py-2 space-y-3"
          >
            {messages.length === 0 && (
              <div className="text-center py-8">
                <div className="text-slate-400 mb-4">
                  Ask me anything about {companyName}!
                </div>
                <div className="space-y-2">
                  <div className="text-xs text-slate-500 uppercase tracking-wide">
                    Suggested Questions:
                  </div>
                  {suggestedQuestions.map((question, index) => (
                    <button
                      key={index}
                      onClick={() => sendMessage(question)}
                      disabled={isLoading}
                      className="block w-full text-left px-3 py-2 rounded bg-slate-800/50 hover:bg-slate-700/50 hover:text-gold-400 text-sm text-slate-300 transition-colors disabled:opacity-50"
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    message.role === "user"
                      ? "bg-gradient-to-r from-gold-600 to-copper-600 text-black"
                      : "bg-slate-800 text-slate-100"
                  }`}
                >
                  <div className="text-sm whitespace-pre-wrap">
                    {message.content}
                  </div>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-slate-800 text-slate-100 rounded-lg px-4 py-2">
                  <div className="flex gap-1">
                    <div
                      className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0ms" }}
                    ></div>
                    <div
                      className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
                      style={{ animationDelay: "150ms" }}
                    ></div>
                    <div
                      className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
                      style={{ animationDelay: "300ms" }}
                    ></div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input Form */}
          <form
            onSubmit={handleSubmit}
            className="border-t border-slate-700 p-4"
          >
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask a question..."
                disabled={isLoading}
                className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-gold-500 disabled:opacity-50"
              />
              <Button
                type="submit"
                disabled={isLoading || !input.trim()}
                variant="primary"
                className="px-4"
              >
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
                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                  />
                </svg>
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
