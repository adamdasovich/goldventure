"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useEditorChat } from "@/hooks/useEditorChat";

/**
 * Editor inbox for the homepage "Ask the Editor" widget.
 *
 * Same socket as the widget — the server decides this connection is an
 * editor from is_staff/is_superuser and sends the thread list instead of a
 * single conversation. Replies typed here land in the reader's widget
 * immediately, and every open editor tab stays in sync.
 *
 * The admin layout already gates on staff, so there is no second check here;
 * the server refuses editor-only message types regardless.
 */

function formatWhen(iso: string | null) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const mins = Math.round((Date.now() - d.getTime()) / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  if (mins < 60 * 24) return `${Math.round(mins / 60)}h ago`;
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export default function AskEditorInboxPage() {
  const { accessToken, isAuthenticated } = useAuth();
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"open" | "all">("open");
  const transcriptRef = useRef<HTMLDivElement>(null);

  const {
    isConnected,
    hasLoaded,
    threads,
    messages,
    thread,
    openThreadId,
    peerTyping,
    sendMessage,
    openThread,
    setResolved,
    setTyping,
  } = useEditorChat({
    token: isAuthenticated ? accessToken : null,
    onError: setError,
  });

  const visible = useMemo(
    () => (filter === "open" ? threads.filter((t) => !t.is_resolved) : threads),
    [threads, filter],
  );
  const totalUnread = useMemo(
    () => threads.reduce((n, t) => n + t.unread_for_editor, 0),
    [threads],
  );

  // Open the first conversation automatically so the page is never a blank
  // right-hand pane on arrival.
  useEffect(() => {
    if (hasLoaded && openThreadId === null && visible.length > 0) {
      openThread(visible[0].id);
    }
  }, [hasLoaded, openThreadId, visible, openThread]);

  useEffect(() => {
    const el = transcriptRef.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [messages, peerTyping]);

  const handleSend = useCallback(() => {
    if (!openThreadId) return;
    const body = draft.trim();
    if (!body) return;
    if (!sendMessage(body, openThreadId)) {
      setError("Not connected — the reply was not sent.");
      return;
    }
    setDraft("");
    setError(null);
    setTyping(false, openThreadId);
  }, [draft, openThreadId, sendMessage, setTyping]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-slate-100">Ask the Editor</h2>
          <p className="text-sm text-slate-400">
            Questions readers sent from the homepage widget. Replies are live.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 text-xs text-slate-400">
            <span
              className={`h-2 w-2 rounded-full ${isConnected ? "bg-emerald-400" : "bg-slate-500"}`}
              aria-hidden="true"
            />
            {isConnected ? "Live" : "Reconnecting…"}
          </span>
          {totalUnread > 0 && (
            <span className="rounded-full bg-gold-500 px-2.5 py-1 text-xs font-bold text-slate-900">
              {totalUnread} unread
            </span>
          )}
        </div>
      </div>

      {error && (
        <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
          {error}
        </p>
      )}

      <div className="grid gap-4 lg:grid-cols-[20rem_1fr]">
        {/* ─── Thread list ─────────────────────────────────────────────── */}
        <aside className="rounded-lg border border-slate-700 bg-slate-800/40">
          <div className="flex items-center gap-1 border-b border-slate-700 p-2">
            {(["open", "all"] as const).map((f) => (
              <button
                key={f}
                type="button"
                onClick={() => setFilter(f)}
                className={`rounded-lg px-3 py-2 text-sm capitalize transition-colors ${
                  filter === f
                    ? "bg-gold-500/20 text-gold-400"
                    : "text-slate-400 hover:bg-slate-700/50 hover:text-slate-200"
                }`}
              >
                {f}
              </button>
            ))}
          </div>

          <ul className="max-h-[60vh] divide-y divide-slate-700/60 overflow-y-auto">
            {!hasLoaded ? (
              <li className="p-4 text-sm text-slate-500">Loading…</li>
            ) : visible.length === 0 ? (
              <li className="p-4 text-sm text-slate-500">
                {filter === "open"
                  ? "Nothing waiting. All caught up."
                  : "No questions yet."}
              </li>
            ) : (
              visible.map((t) => (
                <li key={t.id}>
                  <button
                    type="button"
                    onClick={() => openThread(t.id)}
                    className={`w-full px-3 py-3 text-left transition-colors ${
                      openThreadId === t.id
                        ? "bg-gold-500/10"
                        : "hover:bg-slate-700/40"
                    }`}
                  >
                    <div className="flex items-baseline justify-between gap-2">
                      <span className="truncate text-sm font-semibold text-slate-100">
                        {t.user_name}
                      </span>
                      <span className="shrink-0 text-[11px] text-slate-500">
                        {formatWhen(t.last_message_at)}
                      </span>
                    </div>
                    <p className="mt-1 line-clamp-2 text-xs text-slate-400">
                      {t.last_message_preview || "—"}
                    </p>
                    <div className="mt-1.5 flex items-center gap-2">
                      {t.unread_for_editor > 0 && (
                        <span className="rounded-full bg-gold-500 px-2 py-0.5 text-[10px] font-bold text-slate-900">
                          {t.unread_for_editor} new
                        </span>
                      )}
                      {t.is_resolved && (
                        <span className="rounded-full border border-slate-600 px-2 py-0.5 text-[10px] text-slate-400">
                          resolved
                        </span>
                      )}
                    </div>
                  </button>
                </li>
              ))
            )}
          </ul>
        </aside>

        {/* ─── Conversation ────────────────────────────────────────────── */}
        <section className="flex min-h-[60vh] flex-col rounded-lg border border-slate-700 bg-slate-800/40">
          {!thread ? (
            <div className="flex flex-1 items-center justify-center p-8 text-sm text-slate-500">
              Pick a conversation on the left.
            </div>
          ) : (
            <>
              <header className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-700 px-4 py-3">
                <div className="min-w-0">
                  <p className="truncate font-semibold text-slate-100">
                    {thread.user_name}
                  </p>
                  <p className="truncate text-xs text-slate-500">
                    {thread.user_email || "no email on file"}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setResolved(thread.id, !thread.is_resolved)}
                  className="rounded-lg border border-slate-600 px-3 py-2 text-xs text-slate-300 transition-colors hover:border-gold-500/50 hover:text-gold-400"
                >
                  {thread.is_resolved ? "Reopen" : "Mark resolved"}
                </button>
              </header>

              <div
                ref={transcriptRef}
                className="flex-1 space-y-3 overflow-y-auto px-4 py-4"
              >
                {messages.map((m) => (
                  <div
                    key={m.id}
                    className={`flex ${m.is_from_editor ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-xl px-3 py-2 ${
                        m.is_from_editor
                          ? "bg-gold-500/15 text-slate-100"
                          : "bg-slate-800 text-slate-200"
                      }`}
                    >
                      <div className="mb-0.5 flex items-baseline gap-2">
                        <span className="text-[11px] font-semibold text-slate-400">
                          {m.is_from_editor ? m.sender_name : thread.user_name}
                        </span>
                        <span className="text-[10px] text-slate-500">
                          {new Date(m.created_at).toLocaleString()}
                        </span>
                      </div>
                      <p className="whitespace-pre-wrap break-words text-sm leading-relaxed">
                        {m.content}
                      </p>
                    </div>
                  </div>
                ))}
                {peerTyping !== null && peerTyping === thread.id && (
                  <p className="text-xs italic text-slate-500">
                    {thread.user_name} is typing…
                  </p>
                )}
              </div>

              <div className="border-t border-slate-700 p-3">
                <div className="flex items-end gap-2">
                  <textarea
                    value={draft}
                    onChange={(e) => {
                      setDraft(e.target.value);
                      setTyping(true, thread.id);
                    }}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        handleSend();
                      }
                    }}
                    rows={3}
                    maxLength={5000}
                    aria-label={`Reply to ${thread.user_name}`}
                    placeholder={`Reply to ${thread.user_name}…`}
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
        </section>
      </div>
    </div>
  );
}
