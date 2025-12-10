import { useEffect, useRef, useState, useCallback } from 'react';

export interface ForumUser {
  id: number;
  username: string;
  full_name: string;
  user_type: string;
}

export interface ForumMessage {
  id: number;
  discussion: number;
  user: ForumUser;
  content: string;
  reply_to: number | null;
  is_edited: boolean;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
}

export interface TypingUser {
  user: ForumUser;
  is_typing: boolean;
}

interface WebSocketMessage {
  type: string;
  message?: ForumMessage;
  error?: string;
  messages?: ForumMessage[];
  online_users?: ForumUser[];
  user?: ForumUser;
  user_id?: number;
  is_typing?: boolean;
  data?: {
    messages: ForumMessage[];
    online_users: ForumUser[];
  };
}

interface UseForumWebSocketOptions {
  discussionId: number;
  token: string;
  onError?: (error: string) => void;
}

export function useForumWebSocket({ discussionId, token, onError }: UseForumWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<ForumMessage[]>([]);
  const [onlineUsers, setOnlineUsers] = useState<ForumUser[]>([]);
  const [typingUsers, setTypingUsers] = useState<Map<number, ForumUser>>(new Map());

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | undefined>(undefined);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/ws/forum/${discussionId}/?token=${token}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);

      // Start heartbeat to maintain presence
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
      }
      heartbeatIntervalRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'presence.update' }));
        }
      }, 30000); // Every 30 seconds
    };

    ws.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);

        switch (data.type) {
          case 'initial.state':
            if (data.data) {
              setMessages(data.data.messages);
              setOnlineUsers(data.data.online_users);
            }
            break;

          case 'message.new':
            if (data.message) {
              setMessages((prev) => [...prev, data.message!]);
            }
            break;

          case 'message.edited':
            if (data.message) {
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === data.message!.id ? data.message! : msg
                )
              );
            }
            break;

          case 'message.deleted':
            // Keep the message but mark it as deleted in the UI
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === data.message?.id ? { ...msg, is_deleted: true } : msg
              )
            );
            break;

          case 'user.joined':
            if (data.user) {
              setOnlineUsers((prev) => {
                // Prevent duplicates
                if (prev.some((u) => u.id === data.user!.id)) {
                  return prev;
                }
                return [...prev, data.user!];
              });
            }
            break;

          case 'user.left':
            if (data.user_id) {
              setOnlineUsers((prev) =>
                prev.filter((user) => user.id !== data.user_id)
              );
              setTypingUsers((prev) => {
                const updated = new Map(prev);
                updated.delete(data.user_id!);
                return updated;
              });
            }
            break;

          case 'typing.indicator':
            if (data.user) {
              setTypingUsers((prev) => {
                const updated = new Map(prev);
                if (data.is_typing) {
                  updated.set(data.user!.id, data.user!);
                } else {
                  updated.delete(data.user!.id);
                }
                return updated;
              });
            }
            break;

          case 'error':
            console.error('WebSocket error:', data);
            onError?.(data.error || 'An error occurred');
            break;

          default:
            console.log('Unknown message type:', data.type);
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    ws.onerror = () => {
      // WebSocket error event doesn't provide useful error details
      // Errors will be handled in onclose event
    };

    ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      setIsConnected(false);

      // Clear heartbeat
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
      }

      // Attempt to reconnect after 3 seconds
      if (event.code !== 1000) { // Not a normal closure
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Attempting to reconnect...');
          connect();
        }, 3000);
      }
    };

    wsRef.current = ws;
  }, [discussionId, token, onError]);

  const disconnect = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected');
      wsRef.current = null;
    }
  }, []);

  const sendMessage = useCallback((content: string, replyTo?: number) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      onError?.('Not connected to server');
      return;
    }

    wsRef.current.send(
      JSON.stringify({
        type: 'message.send',
        content,
        reply_to: replyTo,
      })
    );
  }, [onError]);

  const editMessage = useCallback((messageId: number, content: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      onError?.('Not connected to server');
      return;
    }

    wsRef.current.send(
      JSON.stringify({
        type: 'message.edit',
        message_id: messageId,
        content,
      })
    );
  }, [onError]);

  const deleteMessage = useCallback((messageId: number) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      onError?.('Not connected to server');
      return;
    }

    wsRef.current.send(
      JSON.stringify({
        type: 'message.delete',
        message_id: messageId,
      })
    );
  }, [onError]);

  const startTyping = useCallback(() => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    wsRef.current.send(
      JSON.stringify({
        type: 'typing.start',
      })
    );
  }, []);

  const stopTyping = useCallback(() => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    wsRef.current.send(
      JSON.stringify({
        type: 'typing.stop',
      })
    );
  }, []);

  useEffect(() => {
    // Disconnect and reconnect when token changes
    if (wsRef.current) {
      disconnect();
    }
    if (token) {
      connect();
    }
    return () => {
      disconnect();
    };
  }, [token, connect, disconnect]);

  return {
    isConnected,
    messages,
    onlineUsers,
    typingUsers: Array.from(typingUsers.values()),
    sendMessage,
    editMessage,
    deleteMessage,
    startTyping,
    stopTyping,
  };
}
