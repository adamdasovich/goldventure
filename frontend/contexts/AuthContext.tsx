'use client';

import { createContext, useContext, useState, useEffect, useRef, useCallback, ReactNode } from 'react';

interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  user_type: string;
  is_staff?: boolean;
  is_superuser?: boolean;
  company_id?: number | null;
  company_name?: string | null;
}

interface AuthContextType {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string, fullName: string, userType: string) => Promise<void>;
  logout: () => void;
  refreshAccessToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Token refresh interval: 50 minutes (tokens expire in 1 hour)
const TOKEN_REFRESH_INTERVAL = 50 * 60 * 1000;

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const isRefreshingRef = useRef(false);

  // Refresh the access token using the refresh token
  const refreshAccessToken = useCallback(async (): Promise<string | null> => {
    // Prevent multiple simultaneous refresh requests
    if (isRefreshingRef.current) {
      return accessToken;
    }

    const refreshToken = localStorage.getItem('refreshToken');
    if (!refreshToken) {
      return null;
    }

    isRefreshingRef.current = true;

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/auth/token/refresh/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh: refreshToken }),
      });

      if (!response.ok) {
        // Refresh token is invalid, log out
        throw new Error('Refresh token expired');
      }

      const data = await response.json();
      const newAccessToken = data.access;

      setAccessToken(newAccessToken);
      localStorage.setItem('accessToken', newAccessToken);

      // If a new refresh token was returned (token rotation), store it
      if (data.refresh) {
        localStorage.setItem('refreshToken', data.refresh);
      }

      return newAccessToken;
    } catch {
      // Refresh failed, log out the user
      logout();
      return null;
    } finally {
      isRefreshingRef.current = false;
    }
  }, [accessToken]);

  // Set up automatic token refresh
  const setupTokenRefresh = useCallback(() => {
    // Clear any existing interval
    if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current);
    }

    // Set up new refresh interval
    refreshIntervalRef.current = setInterval(() => {
      refreshAccessToken();
    }, TOKEN_REFRESH_INTERVAL);
  }, [refreshAccessToken]);

  // Load user from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('accessToken');
    const storedUser = localStorage.getItem('user');

    if (storedToken && storedUser) {
      setAccessToken(storedToken);
      // Safely parse user data with error handling
      try {
        setUser(JSON.parse(storedUser));
      } catch {
        // Corrupted user data, clear storage
        localStorage.removeItem('user');
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        setIsLoading(false);
        return;
      }

      // Verify token is still valid, or try to refresh it
      fetchCurrentUser(storedToken).catch(async () => {
        // Token might be expired, try to refresh
        const newToken = await refreshAccessToken();
        if (newToken) {
          // Refresh succeeded, fetch user with new token
          fetchCurrentUser(newToken).catch(() => {
            logout();
          });
        } else {
          logout();
        }
      });

      // Set up automatic token refresh
      setupTokenRefresh();
    }
    setIsLoading(false);

    // Cleanup on unmount
    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, []);

  const fetchCurrentUser = async (token: string) => {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/auth/me/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch user');
    }

    const userData = await response.json();
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
  };

  const login = async (username: string, password: string) => {
    // Clear any existing auth data first
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
    setUser(null);
    setAccessToken(null);

    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/auth/login/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Login failed');
    }

    const data = await response.json();

    setUser(data.user);
    setAccessToken(data.access);

    localStorage.setItem('accessToken', data.access);
    localStorage.setItem('refreshToken', data.refresh);
    localStorage.setItem('user', JSON.stringify(data.user));

    // Set up automatic token refresh
    setupTokenRefresh();

    // Force reload to ensure fresh state
    window.location.reload();
  };

  const register = async (
    username: string,
    email: string,
    password: string,
    fullName: string,
    userType: string
  ) => {
    // Clear any existing auth data first
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
    setUser(null);
    setAccessToken(null);

    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/auth/register/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username,
        email,
        password,
        full_name: fullName,
        user_type: userType,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Registration failed');
    }

    const data = await response.json();

    setUser(data.user);
    setAccessToken(data.access);

    localStorage.setItem('accessToken', data.access);
    localStorage.setItem('refreshToken', data.refresh);
    localStorage.setItem('user', JSON.stringify(data.user));

    // Set up automatic token refresh
    setupTokenRefresh();

    // Force reload to ensure fresh state
    window.location.reload();
  };

  const logout = () => {
    // Clear the token refresh interval
    if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current);
      refreshIntervalRef.current = null;
    }

    setUser(null);
    setAccessToken(null);
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
    // Force reload to clear all state
    window.location.href = '/';
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        refreshAccessToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
