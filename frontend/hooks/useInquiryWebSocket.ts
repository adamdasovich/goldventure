import { useEffect, useRef, useState, useCallback } from 'react';

export interface InquiryMessage {
  id: number;
  inquiry_id: number;
  sender: number;
  sender_name: string;
  sender_email: string;
  message: string;
  is_read: boolean;
  is_from_prospector: boolean;
  created_at: string;
}

interface WebSocketMessage {
  type: string;
  message?: InquiryMessage;
  error?: string;
  inquiry_id?: number;
  user_id?: number;
  is_typing?: boolean;
  read_by?: number;
  message_ids?: number[];
}

interface UseInquiryWebSocketOptions {
  token: string;
  onNewMessage?: (message: InquiryMessage) => void;
  onMessageSent?: (message: InquiryMessage) => void;
  onMessagesRead?: (inquiryId: number, messageIds: number[]) => void;
  onTypingIndicator?: (inquiryId: number, userId: number, isTyping: boolean) => void;
  onError?: (error: string) => void;
}

export function useInquiryWebSocket({
  token,
  onNewMessage,
  onMessageSent,
  onMessagesRead,
  onTypingIndicator,
  onError,
}: UseInquiryWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | undefined>(undefined);

  const connect = useCallback(() => {
    if (!token) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/ws/inbox/?token=${token}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('Inbox WebSocket connected');
      setIsConnected(true);

      // Start heartbeat to maintain connection
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
          case 'connection.established':
            console.log('Inbox WebSocket connection established');
            break;

          case 'message.new':
            if (data.message && onNewMessage) {
              onNewMessage(data.message);
            }
            break;

          case 'message.sent':
            if (data.message && onMessageSent) {
              onMessageSent(data.message);
            }
            break;

          case 'messages.read':
            if (data.inquiry_id && data.message_ids && onMessagesRead) {
              onMessagesRead(data.inquiry_id, data.message_ids);
            }
            break;

          case 'typing.indicator':
            if (data.inquiry_id !== undefined && data.user_id !== undefined && data.is_typing !== undefined && onTypingIndicator) {
              onTypingIndicator(data.inquiry_id, data.user_id, data.is_typing);
            }
            break;

          case 'error':
            console.error('Inbox WebSocket error:', data.error);
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
      console.log('Inbox WebSocket closed:', event.code, event.reason);
      setIsConnected(false);

      // Clear heartbeat
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
      }

      // Attempt to reconnect after 3 seconds (if not a normal closure)
      if (event.code !== 1000) {
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Attempting to reconnect inbox WebSocket...');
          connect();
        }, 3000);
      }
    };

    wsRef.current = ws;
  }, [token, onNewMessage, onMessageSent, onMessagesRead, onTypingIndicator, onError]);

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
    setIsConnected(false);
  }, []);

  const sendMessage = useCallback((inquiryId: number, content: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      onError?.('Not connected to server');
      return false;
    }

    wsRef.current.send(
      JSON.stringify({
        type: 'message.send',
        inquiry_id: inquiryId,
        content,
      })
    );
    return true;
  }, [onError]);

  const markMessagesRead = useCallback((inquiryId: number, messageIds?: number[]) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    wsRef.current.send(
      JSON.stringify({
        type: 'message.read',
        inquiry_id: inquiryId,
        message_ids: messageIds || [],
      })
    );
  }, []);

  const startTyping = useCallback((inquiryId: number) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    wsRef.current.send(
      JSON.stringify({
        type: 'typing.start',
        inquiry_id: inquiryId,
      })
    );
  }, []);

  const stopTyping = useCallback((inquiryId: number) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    wsRef.current.send(
      JSON.stringify({
        type: 'typing.stop',
        inquiry_id: inquiryId,
      })
    );
  }, []);

  useEffect(() => {
    if (token) {
      connect();
    }
    return () => {
      disconnect();
    };
  }, [token, connect, disconnect]);

  return {
    isConnected,
    sendMessage,
    markMessagesRead,
    startTyping,
    stopTyping,
    reconnect: connect,
  };
}
