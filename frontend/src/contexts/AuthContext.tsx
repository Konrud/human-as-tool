import { authService, type AuthTokens, type User } from "@/services/auth";
import React, { createContext, useCallback, useEffect, useState } from "react";

interface AuthContextType {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshAuth: () => Promise<void>;
}

// eslint-disable-next-line react-refresh/only-export-components
export const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [tokens, setTokens] = useState<AuthTokens | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize auth state from localStorage
  useEffect(() => {
    const initAuth = () => {
      const storedUser = authService.getUser();
      const storedTokens = authService.getTokens();

      if (storedUser && storedTokens && !authService.isTokenExpired(storedTokens)) {
        setUser(storedUser);
        setTokens(storedTokens);
      }

      setIsLoading(false);
    };

    initAuth();
  }, []);

  // Auto-refresh tokens before expiration
  useEffect(() => {
    if (!tokens) return;

    const timeUntilExpiry = tokens.expiresAt - Date.now();
    const refreshTime = timeUntilExpiry - 5 * 60 * 1000; // Refresh 5 minutes before expiry

    if (refreshTime <= 0) {
      // Token already expired or about to expire, refresh immediately
      refreshAuth();
      return;
    }

    const timeoutId = setTimeout(() => {
      refreshAuth();
    }, refreshTime);

    return () => clearTimeout(timeoutId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tokens]);

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const { user, tokens } = await authService.login(email, password);
      setUser(user);
      setTokens(tokens);
    } catch (error) {
      console.error("Login failed:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    setIsLoading(true);
    try {
      await authService.logout();
      setUser(null);
      setTokens(null);
    } catch (error) {
      console.error("Logout failed:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const refreshAuth = useCallback(async () => {
    if (!tokens?.refreshToken) return;

    try {
      const newTokens = await authService.refreshTokens();
      setTokens(newTokens);
    } catch (error) {
      console.error("Token refresh failed:", error);
      // If refresh fails, logout user
      await logout();
    }
  }, [tokens, logout]);

  const value: AuthContextType = {
    user,
    tokens,
    isAuthenticated: !!user && !!tokens && !authService.isTokenExpired(tokens),
    isLoading,
    login,
    logout,
    refreshAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
