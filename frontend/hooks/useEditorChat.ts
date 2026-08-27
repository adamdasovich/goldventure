import { useEffect, useRef, useState, useCallback } from "react";

/**
 * WebSocket client for "Ask the Editor" (`ws/ask-editor/`).
 *
 * One hook serves both ends of the conversation, because one consumer does:
 * a reader gets their own single thread, an editor (is_staff/is_superuser)
 * gets the whole inbox. Which one you are is decided by the server at connect
 * time and reported back as `isEditor` — never asserted by the client.
 *
 * Follows the shape of the other socket hooks in this directory: callbacks are
 * held in refs so a re-render never tears down the connection, and a closed
 * socket retries with backoff unless it was closed deliberately.
 */

export interface EditorChatMessage {
  id: number;
  thread_id: number;
  content: string;
  is_from_editor: boolean;
  is_read: boolean;
  sender_name: string;
  created_at: string;
}

export interface EditorChatThread {
  id: number;
  user_id: number;
  user_name: string;
  user_email: string;
  last_message_at: string | null;
  last_message_preview: string;
  unread_for_editor: number;
  unread_for_user: number;
  is_resolved: boolean;
}

type ServerMessage = {
  type: string;
  error?: string;
  is_editor?: boolean;
  thread?: EditorChatThread | null;
  threads?: EditorChatThread[];
  messages?: EditorChatMessage[];
  message?: EditorChatMessage;
  thread_id?: number;
  from_editor?: boolean;
  is_typing?: boolean;
};

interface UseEditorChatOptions {
  token: string | null;
  /** Skip connecting entirely — e.g. the widget has never been opened. */
  enabled?: boolean;
  onError?: (error: string) => void;
}

/** Reconnect backoff, capped. A reader who leaves the tab open overnight
 *  shouldn't hammer the server every 3s if the backend is down. */
const RECONNECT_DELAYS = [2000, 4000, 8000, 15000, 30000];
const HEARTBEAT_MS = 30000;

export function useEditorChat({
  token,
  enabled = true,
  onError,
}: UseEditorChatOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const [isEditor, setIsEditor] = useState(false);
  /** True once the server has sent initial.state, so the UI can tell
   *  "no messages yet" apart from "haven't loaded yet". */
  const [hasLoaded, setHasLoaded] = useState(false);
  const [messages, setMessages] = useState<EditorChatMessage[]>([]);
  const [thread, setThread] = useState<EditorChatThread | null>(null);
  const [threads, setThreads] = useState<EditorChatThread[]>([]);
  const [openThreadId, setOpenThreadId] = useState<number | null>(null);
  const [peerTyping, setPeerTyping] = useState<number | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const attemptRef = useRef(0);
  const closingRef = useRef(false);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | undefined>(
    undefined,
  );
  const heartbeatRef = useRef<ReturnType<typeof setInterval> | undefined>(
    undefined,
  );
  const typingClearRef = useRef<ReturnType<typeof setTimeout> | undefined>(
    undefined,
  );
  const onErrorRef = useRef(onError);
  // The editor's currently-open thread, read inside the socket's onmessage
  // closure — state would be stale there.
  const openThreadRef = useRef<number | null>(null);

  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  useEffect(() => {
    openThreadRef.current = openThreadId;
  }, [openThreadId]);

  const send = useCallback((payload: Record<string, unknown>) => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) return false;
    wsRef.current.send(JSON.stringify(payload));
    return true;
  }, []);

  const connect = useCallback(() => {
    if (!token || !enabled) return;
    if (
      wsRef.current?.readyState === WebSocket.OPEN ||
      wsRef.current?.readyState === WebSocket.CONNECTING
    ) {
      return;
    }

    closingRef.current = false;
    const base = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
    const ws = new WebSocket(
      `${base}/ws/ask-editor/?token=${encodeURIComponent(token)}`,
    );

    ws.onopen = () => {
      setIsConnected(true);
      attemptRef.current = 0;
      if (heartbeatRef.current) clearInterval(heartbeatRef.current);
      heartbeatRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "presence.ping" }));
        }
      }, HEARTBEAT_MS);
    };

    ws.onmessage = (event) => {
      let data: ServerMessage;
      try {
        data = JSON.parse(event.data);
      } catch {
        return;
      }

      switch (data.type) {
        case "connection.established":
          setIsEditor(!!data.is_editor);
          break;

        case "initial.state":
          setThreads(data.threads || []);
          setThread(data.thread ?? null);
          setMessages(data.messages || []);
          setHasLoaded(true);
          break;

        case "thread.history":
          setThread(data.thread ?? null);
          setMessages(data.messages || []);
          break;

        case "message.new": {
          const incoming = data.message;
          if (!incoming) break;

          // An editor is subscribed to every thread, so only append to the
          // transcript when the message belongs to the one on screen.
          const open = openThreadRef.current;
          const belongsHere = open === null || incoming.thread_id === open;
          if (belongsHere) {
            setMessages((prev) =>
              prev.some((m) => m.id === incoming.id)
                ? prev
                : [...prev, incoming],
            );
          }

          if (data.thread) {
            const updated = data.thread;
            setThread((prev) =>
              !prev || prev.id === updated.id ? updated : prev,
            );
            setThreads((prev) => {
              const rest = prev.filter((t) => t.id !== updated.id);
              return [updated, ...rest];
            });
          }
          setPeerTyping(null);
          break;
        }

        case "thread.updated": {
          const updated = data.thread;
          if (!updated) break;
          setThread((prev) =>
            !prev || prev.id === updated.id ? updated : prev,
          );
          setThreads((prev) =>
            prev.map((t) => (t.id === updated.id ? updated : t)),
          );
          break;
        }

        case "typing.indicator": {
          const active = data.is_typing ? (data.thread_id ?? -1) : null;
          setPeerTyping(active);
          if (typingClearRef.current) clearTimeout(typingClearRef.current);
          if (active !== null) {
            // The stop event can be lost if the peer closes the tab mid-type.
            typingClearRef.current = setTimeout(
              () => setPeerTyping(null),
              6000,
            );
          }
          break;
        }

        case "error":
          onErrorRef.current?.(data.error || "Something went wrong");
          break;
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      wsRef.current = null;
      if (heartbeatRef.current) clearInterval(heartbeatRef.current);

      if (closingRef.current) return;
      const delay =
        RECONNECT_DELAYS[
          Math.min(attemptRef.current, RECONNECT_DELAYS.length - 1)
        ];
      attemptRef.current += 1;
      reconnectRef.current = setTimeout(connect, delay);
    };

    wsRef.current = ws;
  }, [token, enabled]);

  const disconnect = useCallback(() => {
    closingRef.current = true;
    if (heartbeatRef.current) clearInterval(heartbeatRef.current);
    if (reconnectRef.current) clearTimeout(reconnectRef.current);
    if (typingClearRef.current) clearTimeout(typingClearRef.current);
    wsRef.current?.close(1000, "Closed by client");
    wsRef.current = null;
    setIsConnected(false);
  }, []);

  useEffect(() => {
    if (token && enabled) connect();
    return () => disconnect();
  }, [token, enabled, connect, disconnect]);

  /** Send a message. `threadId` is editor-only; readers omit it and the
   *  server writes to their own thread. */
  const sendMessage = useCallback(
    (content: string, threadId?: number) => {
      const body = content.trim();
      if (!body) return false;
      return send(
        threadId
          ? { type: "message.send", content: body, thread_id: threadId }
          : { type: "message.send", content: body },
      );
    },
    [send],
  );

  /** Editor-only: load one conversation's transcript. */
  const openThread = useCallback(
    (threadId: number) => {
      setOpenThreadId(threadId);
      setMessages([]);
      // The server clears the unread badge as part of opening, so there is
      // no separate read call to make here.
      send({ type: "thread.open", thread_id: threadId });
    },
    [send],
  );

  const markRead = useCallback(
    (threadId?: number) => send({ type: "thread.read", thread_id: threadId }),
    [send],
  );

  const setResolved = useCallback(
    (threadId: number, resolved: boolean) =>
      send({ type: "thread.resolve", thread_id: threadId, resolved }),
    [send],
  );

  const setTyping = useCallback(
    (typing: boolean, threadId?: number) =>
      send({
        type: typing ? "typing.start" : "typing.stop",
        thread_id: threadId,
      }),
    [send],
  );

  return {
    isConnected,
    isEditor,
    hasLoaded,
    messages,
    thread,
    threads,
    openThreadId,
    peerTyping,
    sendMessage,
    openThread,
    markRead,
    setResolved,
    setTyping,
    reconnect: connect,
  };
}
