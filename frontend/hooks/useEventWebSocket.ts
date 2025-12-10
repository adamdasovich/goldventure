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
  enabled?: boolean; // Only connect when enabled (e.g., when event is live)
  onError?: (error: string) => void;
}

export function useEventWebSocket({ eventId, token, enabled = true, onError }: UseEventWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const [event, setEvent] = useState<EventData | null>(null);
  const [questions, setQuestions] = useState<EventQuestion[]>([]);
  const [participants, setParticipants] = useState<EventUser[]>([]);
  const [recentReactions, setRecentReactions] = useState<EventReaction[]>([]);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | undefined>(undefined);
  const onErrorRef = useRef(onError);

  // Keep onError ref updated
  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  // Main connection effect - only depends on eventId, token, and enabled
  useEffect(() => {
    // Don't connect if not enabled or no token
    if (!enabled || !token || !eventId) {
      return;
    }

    const connect = () => {
      // Don't connect if already connected or connecting
      if (wsRef.current?.readyState === WebSocket.OPEN ||
          wsRef.current?.readyState === WebSocket.CONNECTING) {
        return;
      }

      const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/ws/event/${eventId}/?token=${token}`;
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

      ws.onmessage = (messageEvent) => {
        try {
          const data: WebSocketMessage = JSON.parse(messageEvent.data);

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
              setEvent((currentEvent) => {
                if (currentEvent) {
                  return { ...currentEvent, status: data.data?.event.status || currentEvent.status };
                }
                return currentEvent;
              });
              break;

            case 'error':
              console.error('WebSocket error:', data);
              onErrorRef.current?.(data.error || 'An error occurred');
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

      ws.onclose = (closeEvent) => {
        console.log('WebSocket closed:', closeEvent.code, closeEvent.reason);
        setIsConnected(false);

        // Clear heartbeat
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
        }

        // Attempt to reconnect after 3 seconds if not a normal closure
        if (closeEvent.code !== 1000) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect...');
            connect();
          }, 3000);
        }
      };

      wsRef.current = ws;
    };

    // Connect
    connect();

    // Cleanup function
    return () => {
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounted');
        wsRef.current = null;
      }
    };
  }, [eventId, token, enabled]);

  const submitQuestion = useCallback(
    (content: string) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        onErrorRef.current?.('Not connected to server');
        return;
      }

      wsRef.current.send(
        JSON.stringify({
          type: 'question.submit',
          content,
        })
      );
    },
    []
  );

  const upvoteQuestion = useCallback(
    (questionId: number) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        onErrorRef.current?.('Not connected to server');
        return;
      }

      wsRef.current.send(
        JSON.stringify({
          type: 'question.upvote',
          question_id: questionId,
        })
      );
    },
    []
  );

  const sendReaction = useCallback(
    (reactionType: 'applause' | 'thumbs_up' | 'fire' | 'heart') => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        onErrorRef.current?.('Not connected to server');
        return;
      }

      wsRef.current.send(
        JSON.stringify({
          type: 'reaction.send',
          reaction_type: reactionType,
        })
      );
    },
    []
  );

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
