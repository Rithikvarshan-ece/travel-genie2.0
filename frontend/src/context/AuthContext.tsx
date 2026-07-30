import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

interface User {
  id: string;
  name: string;
  email: string;
  avatar: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isAuthLoading: boolean;
  authError: string | null;
}

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  clearAuthError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);
const API = '/api/auth';

const stored = (): AuthState => {
  try {
    const token = localStorage.getItem('tg_token');
    const user = localStorage.getItem('tg_user');
    if (token && user) return { user: JSON.parse(user), token, isAuthenticated: true, isAuthLoading: false, authError: null };
  } catch {}
  return { user: null, token: null, isAuthenticated: false, isAuthLoading: false, authError: null };
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(stored);

  const clearAuthError = useCallback(() => setState(p => ({ ...p, authError: null })), []);

  const login = useCallback(async (email: string, password: string) => {
    setState(p => ({ ...p, isAuthLoading: true, authError: null }));
    try {
      const res = await fetch(`${API}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Login failed');
      localStorage.setItem('tg_token', data.token);
      localStorage.setItem('tg_user', JSON.stringify(data.user));
      setState({ user: data.user, token: data.token, isAuthenticated: true, isAuthLoading: false, authError: null });
    } catch (e: any) {
      setState(p => ({ ...p, isAuthLoading: false, authError: e.message }));
      throw e;
    }
  }, []);

  const signup = useCallback(async (name: string, email: string, password: string) => {
    setState(p => ({ ...p, isAuthLoading: true, authError: null }));
    try {
      const res = await fetch(`${API}/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Signup failed');
      localStorage.setItem('tg_token', data.token);
      localStorage.setItem('tg_user', JSON.stringify(data.user));
      setState({ user: data.user, token: data.token, isAuthenticated: true, isAuthLoading: false, authError: null });
    } catch (e: any) {
      setState(p => ({ ...p, isAuthLoading: false, authError: e.message }));
      throw e;
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('tg_token');
    localStorage.removeItem('tg_user');
    setState({ user: null, token: null, isAuthenticated: false, isAuthLoading: false, authError: null });
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, login, signup, logout, clearAuthError }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
