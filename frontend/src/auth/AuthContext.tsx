import { createContext, useContext } from 'react';
import type { ReactNode } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import type { User, LoginResponse } from '../types/api';
import { apiClient, ACCESS_TOKEN_KEY, REFRESH_TOKEN_KEY } from '../api/client';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const CURRENT_USER_QUERY_KEY = ['auth', 'me'] as const;

async function fetchCurrentUser(): Promise<User> {
  const { data } = await apiClient.get<User>('/auth/me');
  return data;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const hasStoredToken = Boolean(localStorage.getItem(ACCESS_TOKEN_KEY));

  // Session restore on mount: GET /auth/me only if a token is present. Using
  // react-query here (instead of a useEffect + setState) means there's no
  // "setState synchronously in an effect" pattern to trip react-hooks/set-state-in-effect —
  // the query owns its own async/loading/error state, and `login`/`logout` below
  // just write directly into the query cache.
  const { data: user, isLoading } = useQuery<User>({
    queryKey: CURRENT_USER_QUERY_KEY,
    queryFn: fetchCurrentUser,
    enabled: hasStoredToken,
    retry: false,
    staleTime: Infinity,
  });

  const login = async (email: string, password: string) => {
    const { data } = await apiClient.post<LoginResponse>('/auth/login', { email, password });

    localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token);

    queryClient.setQueryData(CURRENT_USER_QUERY_KEY, data.user);
  };

  const logout = () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    queryClient.removeQueries({ queryKey: CURRENT_USER_QUERY_KEY });
  };

  const value: AuthContextType = {
    user: user ?? null,
    isAuthenticated: Boolean(user),
    isLoading,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
