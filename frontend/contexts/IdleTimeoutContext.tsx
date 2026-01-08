'use client';

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { useAuth } from './AuthContext';

interface IdleTimeoutContextType {
  isIdle: boolean;
  showWarning: boolean;
  remainingTime: number;
  resetTimer: () => void;
}

const IdleTimeoutContext = createContext<IdleTimeoutContextType | undefined>(undefined);

// Configuration
const IDLE_TIMEOUT = 30 * 60 * 1000; // 30 minutes in ms
const WARNING_BEFORE = 5 * 60 * 1000; // Show warning 5 minutes before logout
const WARNING_TIME = IDLE_TIMEOUT - WARNING_BEFORE; // 25 minutes

interface IdleTimeoutProviderProps {
  children: ReactNode;
}

export function IdleTimeoutProvider({ children }: IdleTimeoutProviderProps) {
  const { isAuthenticated, logout } = useAuth();
  const [lastActivity, setLastActivity] = useState<number>(Date.now());
  const [showWarning, setShowWarning] = useState(false);
  const [remainingTime, setRemainingTime] = useState(WARNING_BEFORE);
  const [isIdle, setIsIdle] = useState(false);

  // Reset the timer on user activity
  const resetTimer = useCallback(() => {
    setLastActivity(Date.now());
    setShowWarning(false);
    setIsIdle(false);
    setRemainingTime(WARNING_BEFORE);
  }, []);

  // Track user activity
  useEffect(() => {
    if (!isAuthenticated) return;

    const events = ['mousedown', 'mousemove', 'keydown', 'scroll', 'touchstart', 'click'];

    const handleActivity = () => {
      // Only reset if not showing warning (user must explicitly dismiss)
      if (!showWarning) {
        setLastActivity(Date.now());
      }
    };

    // Throttle the activity handler to avoid too many updates
    let throttleTimeout: NodeJS.Timeout | null = null;
    const throttledHandler = () => {
      if (!throttleTimeout) {
        handleActivity();
        throttleTimeout = setTimeout(() => {
          throttleTimeout = null;
        }, 1000); // Only update once per second
      }
    };

    events.forEach(event => {
      window.addEventListener(event, throttledHandler, { passive: true });
    });

    return () => {
      events.forEach(event => {
        window.removeEventListener(event, throttledHandler);
      });
      if (throttleTimeout) {
        clearTimeout(throttleTimeout);
      }
    };
  }, [isAuthenticated, showWarning]);

  // Check for idle state
  useEffect(() => {
    if (!isAuthenticated) {
      setShowWarning(false);
      setIsIdle(false);
      return;
    }

    const checkIdle = () => {
      const now = Date.now();
      const timeSinceActivity = now - lastActivity;

      if (timeSinceActivity >= IDLE_TIMEOUT) {
        // Time's up - logout
        setIsIdle(true);
        setShowWarning(false);
        logout();
      } else if (timeSinceActivity >= WARNING_TIME) {
        // Show warning
        setShowWarning(true);
        setRemainingTime(IDLE_TIMEOUT - timeSinceActivity);
      } else {
        setShowWarning(false);
        setIsIdle(false);
      }
    };

    // Check every second when warning is shown, every 10 seconds otherwise
    const interval = setInterval(checkIdle, showWarning ? 1000 : 10000);
    checkIdle(); // Check immediately

    return () => clearInterval(interval);
  }, [isAuthenticated, lastActivity, showWarning, logout]);

  return (
    <IdleTimeoutContext.Provider
      value={{
        isIdle,
        showWarning,
        remainingTime,
        resetTimer,
      }}
    >
      {children}
    </IdleTimeoutContext.Provider>
  );
}

export function useIdleTimeout() {
  const context = useContext(IdleTimeoutContext);
  if (context === undefined) {
    throw new Error('useIdleTimeout must be used within an IdleTimeoutProvider');
  }
  return context;
}
