"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useEditorChat } from "@/hooks/useEditorChat";

/**
 * "Ask the Editor" — a floating, live conversation with a real person.
 *
 * The homepage already has an AI assistant in the hero, so this one works
 * hard to say what it *isn't*: every label points at a human editor, and the
 * panel opens with a line making the distinction explicit. Anything vaguer
 * ("Chat", "Help") would just read as a second robot.
 *
 * The socket only opens once the panel has been opened at least once —
 * mounting this on the homepage shouldn't cost every visitor a WebSocket.
 */

interface AskEditorWidgetProps {
  /** Opens the site's login modal — the widget needs a signed-in user so a
   *  reply has somewhere to go. */
  onSignInClick?: () => void;
}

function formatTime(iso: string) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function AskEditorWidget({
  onSignInClick,
}: AskEditorWidgetProps) {
  const { isAuthenticated, accessToken } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  /* Latched: once opened, keep the socket alive while the page lives so a
     reply still arrives (and badges the launcher) after the panel is shut. */
  const [hasOpened, setHasOpened] = useState(false);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);

  const transcriptRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const typingStopRef = useRef<ReturnType<typeof setTimeout> | undefined>(
    undefined,
  );

  const {
    isConnected,
    hasLoaded,
    messages,
    thread,
    peerTyping,
    sendMessage,
    markRead,
    setTyping,
  } = useEditorChat({
    token: isAuthenticated ? accessToken : null,
    enabled: hasOpened,
    onError: setError,
  });

  const unread = thread?.unread_for_user ?? 0;

  const open = useCallback(() => {
    setHasOpened(true);
    setIsOpen(true);
    setError(null);
  }, []);

  // Scroll the transcript as it grows, and again when the panel reopens.
  useEffect(() => {
    if (!isOpen) return;
    const el = transcriptRef.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [messages, isOpen, peerTyping]);

  // Reading the panel clears the badge.
  useEffect(() => {
    if (isOpen && isConnected && unread > 0) markRead();
  }, [isOpen, isConnected, unread, markRead]);

  useEffect(() => {
    if (isOpen) inputRef.current?.focus();
  }, [isOpen]);

  // Escape closes the panel, matching the site's other overlays.
  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setIsOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [isOpen]);

  const handleSend = useCallback(() => {
    const body = draft.trim();
    if (!body) return;
    if (!sendMessage(body)) {
      setError("Not connected right now — hold on a moment and try again.");
      return;
    }
    setDraft("");
    setError(null);
    setTyping(false);
  }, [draft, sendMessage, setTyping]);

  const handleDraftChange = useCallback(
    (value: string) => {
      setDraft(value);
      setTyping(true);
      if (typingStopRef.current) clearTimeout(typingStopRef.current);
      typingStopRef.current = setTimeout(() => setTyping(false), 2500);
    },
    [setTyping],
  );

  useEffect(
    () => () => {
      if (typingStopRef.current) clearTimeout(typingStopRef.current);
    },
    [],
  );

  const statusLabel = useMemo(() => {
    if (!isAuthenticated) return "Sign in to ask";
    if (!hasOpened) return "";
    return isConnected ? "Connected" : "Reconnecting…";
  }, [isAuthenticated, hasOpened, isConnected]);

  return (
    <>
      {/* ─── Launcher ───────────────────────────────────────────────────
          Bottom-right, above the mobile safe area. The homepage has no other
          floating UI, so nothing to dodge. */}
      {!isOpen && (
        <button
          type="button"
          onClick={open}
          aria-label="Ask the editor a question about this site"
          className="group fixed z-40 right-4 bottom-[calc(1rem+env(safe-area-inset-bottom))] sm:right-6 sm:bottom-6
                     flex items-center gap-2.5 rounded-full border border-gold-500/50 bg-slate-900/95
                     px-4 py-3 min-h-12 shadow-xl shadow-black/40 backdrop-blur
                     transition-colors hover:border-gold-500 hover:bg-slate-800"
        >
          <span className="relative flex h-6 w-6 shrink-0 items-center justify-center">
            <svg
              className="h-6 w-6 text-gold-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.8}
                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
              />
            </svg>
            {unread > 0 && (
              <span
                className="absolute -right-1.5 -top-1.5 flex h-4 min-w-4 items-center justify-center
                           rounded-full bg-gold-500 px-1 text-[10px] font-bold text-slate-900"
                aria-hidden="true"
              >
                {unread > 9 ? "9+" : unread}
              </span>
            )}
          </span>
          <span className="text-sm font-semibold text-slate-100 group-hover:text-white">
            Ask the Editor
          </span>
        </button>
      )}

      {/* ─── Panel ──────────────────────────────────────────────────────── */}
      {isOpen && (
        <div
          role="dialog"
          aria-modal="false"
          aria-labelledby="ask-editor-title"
          className="fixed z-50 inset-x-3 bottom-[calc(0.75rem+env(safe-area-inset-bottom))]
                     sm:inset-x-auto sm:right-6 sm:bottom-6 sm:w-[26rem]
                     flex max-h-[min(32rem,calc(100dvh-2rem))] flex-col overflow-hidden
                     rounded-xl border border-gold-500/40 bg-slate-900 shadow-2xl shadow-black/60"
        >
          {/* Header */}
          <div className="flex items-start gap-3 border-b border-slate-700 bg-slate-800/60 px-4 py-3">
            <div className="min-w-0 flex-1">
              <h2
                id="ask-editor-title"
                className="flex items-center gap-2 text-base font-bold text-gold-400"
              >
                Ask the Editor
                {statusLabel && (
                  <span className="flex items-center gap-1.5 text-[11px] font-medium text-slate-400">
                    <span
                      className={`h-1.5 w-1.5 rounded-full ${
                        isConnected ? "bg-emerald-400" : "bg-slate-500"
                      }`}
                      aria-hidden="true"
                    />
                    {statusLabel}
                  </span>
                )}
              </h2>
              <p className="mt-0.5 text-xs leading-snug text-slate-400">
                A real person — the site&apos;s editor and developer. Not the AI
                assistant.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              aria-label="Close Ask the Editor"
              className="-mr-2 -mt-1 rounded-lg p-2 text-slate-400 transition-colors hover:bg-slate-700/60 hover:text-slate-200"
            >
              <svg
                className="h-5 w-5"
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
          </div>

          {/* Signed out — the editor needs an account to reply into. */}
          {!isAuthenticated ? (
            <div className="flex flex-1 flex-col items-center justify-center gap-3 px-6 py-10 text-center">
              <p className="text-sm text-slate-300">
                Sign in and your question goes straight to the editor. Replies
                land right here.
              </p>
              <button
                type="button"
                onClick={() => {
                  setIsOpen(false);
                  onSignInClick?.();
                }}
                className="rounded-lg bg-gold-500 px-5 py-2.5 min-h-11 text-sm font-semibold text-slate-900 transition-colors hover:bg-gold-400"
              >
                Sign in to ask
              </button>
            </div>
          ) : (
            <>
              {/* Transcript */}
              <div
                ref={transcriptRef}
                className="flex-1 space-y-3 overflow-y-auto px-4 py-4"
              >
                {!hasLoaded ? (
                  <p className="py-8 text-center text-sm text-slate-500">
                    Loading your conversation…
                  </p>
                ) : messages.length === 0 ? (
                  <div className="space-y-3 py-4">
                    <p className="text-sm text-slate-300">
                      Ask anything about the site — where a number comes from,
                      why a company is missing, a bug you hit, or a feature
                      you&apos;d like.
                    </p>
                    <p className="text-xs text-slate-500">
                      One person answers these, so it may take a little while.
                      Your reply appears here and you&apos;ll see a badge on the
                      button.
                    </p>
                  </div>
                ) : (
                  messages.map((m) => (
                    <div
                      key={m.id}
                      className={`flex ${m.is_from_editor ? "justify-start" : "justify-end"}`}
                    >
                      <div
                        className={`max-w-[85%] rounded-xl px-3 py-2 ${
                          m.is_from_editor
                            ? "bg-slate-800 text-slate-200"
                            : "bg-gold-500/15 text-slate-100"
                        }`}
                      >
                        <div className="mb-0.5 flex items-baseline gap-2">
                          <span
                            className={`text-[11px] font-semibold ${
                              m.is_from_editor
                                ? "text-gold-400"
                                : "text-slate-400"
                            }`}
                          >
                            {m.is_from_editor ? "Editor" : "You"}
                          </span>
                          <span className="text-[10px] text-slate-500">
                            {formatTime(m.created_at)}
                          </span>
                        </div>
                        <p className="whitespace-pre-wrap break-words text-sm leading-relaxed">
                          {m.content}
                        </p>
                      </div>
                    </div>
                  ))
                )}

                {peerTyping !== null && (
                  <p className="text-xs italic text-slate-500">
                    The editor is typing…
                  </p>
                )}
              </div>

              {error && (
                <p className="border-t border-red-500/30 bg-red-500/10 px-4 py-2 text-xs text-red-300">
                  {error}
                </p>
              )}

              {/* Composer */}
              <div className="border-t border-slate-700 bg-slate-800/40 p-3">
                <div className="flex items-end gap-2">
                  <textarea
                    ref={inputRef}
                    value={draft}
                    onChange={(e) => handleDraftChange(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        handleSend();
                      }
                    }}
                    rows={2}
                    maxLength={5000}
                    aria-label="Your question for the editor"
                    placeholder="Ask the editor a question…"
                    className="min-h-11 flex-1 resize-none rounded-lg border border-slate-600 bg-slate-900 px-3 py-2
                               text-sm text-slate-100 placeholder-slate-500 outline-none
                               focus:border-gold-500/70 focus:ring-1 focus:ring-gold-500/40"
                  />
                  <button
                    type="button"
                    onClick={handleSend}
                    disabled={!draft.trim() || !isConnected}
                    className="shrink-0 rounded-lg bg-gold-500 px-4 py-2.5 min-h-11 text-sm font-semibold text-slate-900
                               transition-colors hover:bg-gold-400 disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    Send
                  </button>
                </div>
                <p className="mt-1.5 text-[11px] text-slate-500">
                  Enter to send · Shift+Enter for a new line
                </p>
              </div>
            </>
          )}
        </div>
      )}
    </>
  );
}
