import { useEffect, useRef, useState, useCallback } from 'react';

export interface EventUser {
  id: number;
  username: string;
  full_name: string;
  user_type: string;
}

export interface EventQuestion {
  id: number;
  user: EventUser;
  content: string;
  status: string;
  upvotes: number;
  is_featured: boolean;
  created_at: string;
}

export interface EventReaction {
  user: EventUser;
  reaction_type: 'applause' | 'thumbs_up' | 'fire' | 'heart';
  timestamp: string;
}

export interface EventData {
  id: number;
  title: string;
  description: string;
  status: string;
  format: 'video' | 'text';
  video_url: string | null;
  scheduled_start: string;
  scheduled_end: string;
}

interface WebSocketMessage {
  type: string;
  question?: EventQuestion;
  reaction?: EventReaction;
  user?: EventUser;
  user_id?: number;
  error?: string;
  data?: {
    event: EventData;
    questions: EventQuestion[];
    participants: EventUser[];
  };
}

interface UseEventWebSocketOptions {
  eventId: number;
  token: string;
  onError?: (error: string) => void;
}

export function useEventWebSocket({ eventId, token, onError }: UseEventWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const [event, setEvent] = useState<EventData | null>(null);
  const [questions, setQuestions] = useState<EventQuestion[]>([]);
  const [participants, setParticipants] = useState<EventUser[]>([]);
  const [recentReactions, setRecentReactions] = useState<EventReaction[]>([]);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const heartbeatIntervalRef = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const wsUrl = `ws://localhost:8002/ws/event/${eventId}/?token=${token}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('Event WebSocket connected');
      setIsConnected(true);

      // Start heartbeat
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
              setEvent(data.data.event);
              setQuestions(data.data.questions);
              setParticipants(data.data.participants);
            }
            break;

          case 'question.new':
            if (data.question) {
              setQuestions((prev) => [data.question!, ...prev]);
            }
            break;

          case 'question.upvoted':
            if (data.question) {
              setQuestions((prev) =>
                prev
                  .map((q) => (q.id === data.question!.id ? data.question! : q))
                  .sort((a, b) => b.upvotes - a.upvotes)
              );
            }
            break;

          case 'reaction.received':
            if (data.reaction) {
              setRecentReactions((prev) => {
                const updated = [data.reaction!, ...prev];
                // Keep only last 50 reactions
                return updated.slice(0, 50);
              });

              // Auto-remove reaction after 3 seconds
              setTimeout(() => {
                setRecentReactions((prev) =>
                  prev.filter((r) => r.timestamp !== data.reaction!.timestamp)
                );
              }, 3000);
            }
            break;

          case 'user.joined':
            if (data.user) {
              setParticipants((prev) => {
                if (prev.some((u) => u.id === data.user!.id)) {
                  return prev;
                }
                return [...prev, data.user!];
              });
            }
            break;

          case 'user.left':
            if (data.user_id) {
              setParticipants((prev) => prev.filter((user) => user.id !== data.user_id));
            }
            break;

          case 'event.status_changed':
            if (event) {
              setEvent({ ...event, status: data.data?.event.status || event.status });
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
      if (event.code !== 1000) {
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Attempting to reconnect...');
          connect();
        }, 3000);
      }
    };

    wsRef.current = ws;
  }, [eventId, token, onError, event]);

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

  const submitQuestion = useCallback(
    (content: string) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        onError?.('Not connected to server');
        return;
      }

      wsRef.current.send(
        JSON.stringify({
          type: 'question.submit',
          content,
        })
      );
    },
    [onError]
  );

  const upvoteQuestion = useCallback(
    (questionId: number) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        onError?.('Not connected to server');
        return;
      }

      wsRef.current.send(
        JSON.stringify({
          type: 'question.upvote',
          question_id: questionId,
        })
      );
    },
    [onError]
  );

  const sendReaction = useCallback(
    (reactionType: 'applause' | 'thumbs_up' | 'fire' | 'heart') => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        onError?.('Not connected to server');
        return;
      }

      wsRef.current.send(
        JSON.stringify({
          type: 'reaction.send',
          reaction_type: reactionType,
        })
      );
    },
    [onError]
  );

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
    event,
    questions,
    participants,
    recentReactions,
    submitQuestion,
    upvoteQuestion,
    sendReaction,
  };
}
