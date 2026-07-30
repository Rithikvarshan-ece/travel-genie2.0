import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import { TravelFormData, TravelPlan } from '@/types/travel';

interface AppState {
  isDarkMode: boolean;
  isLoading: boolean;
  isStreaming: boolean;
  isFollowingUp: boolean;
  pendingRequest: TravelFormData | null;
  currentPlan: TravelPlan | null;
  error: string | null;
  tripHistory: TravelPlan[];
}

interface AppContextType extends AppState {
  toggleDarkMode: () => void;
  setLoading: (loading: boolean) => void;
  generatePlan: (data: TravelFormData) => Promise<void>;
  followUp: (instruction: string) => Promise<void>;
  clearPlan: () => void;
  setError: (error: string | null) => void;
  setPlan: (plan: TravelPlan) => void;
  loadHistoryPlan: (plan: TravelPlan) => void;
  deleteHistory: (planId: number) => void;
}

const HISTORY_KEY = 'travelgenie_history';

function loadHistory(): TravelPlan[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveHistory(history: TravelPlan[]) {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, 10)));
  } catch {}
}

const initialState: AppState = {
  isDarkMode: true,
  isLoading: false,
  isStreaming: false,
  isFollowingUp: false,
  pendingRequest: null,
  currentPlan: null,
  error: null,
  tripHistory: loadHistory(),
};

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AppState>(initialState);

  // Persist history whenever it changes
  useEffect(() => {
    saveHistory(state.tripHistory);
  }, [state.tripHistory]);

  const toggleDarkMode = useCallback(() => {
    setState(prev => {
      const newMode = !prev.isDarkMode;
      document.documentElement.classList.toggle('dark', newMode);
      return { ...prev, isDarkMode: newMode };
    });
  }, []);

  const setLoading = useCallback((loading: boolean) => {
    setState(prev => ({ ...prev, isLoading: loading }));
  }, []);

  const setError = useCallback((error: string | null) => {
    setState(prev => ({ ...prev, error, isLoading: false, isStreaming: false, isFollowingUp: false, pendingRequest: null }));
  }, []);

  const clearPlan = useCallback(() => {
    setState(prev => ({ ...prev, currentPlan: null, error: null, pendingRequest: null }));
  }, []);

  const setPlan = useCallback((plan: TravelPlan) => {
    setState(prev => {
      const history = [plan, ...prev.tripHistory.filter(p => p.plan_id !== plan.plan_id)].slice(0, 10);
      return {
        ...prev,
        currentPlan: plan,
        isLoading: false,
        isStreaming: false,
        isFollowingUp: false,
        pendingRequest: null,
        tripHistory: history,
      };
    });
  }, []);

  const loadHistoryPlan = useCallback((plan: TravelPlan) => {
    setState(prev => ({ ...prev, currentPlan: plan, error: null }));
  }, []);

  const deleteHistory = useCallback((planId: number) => {
    setState(prev => {
      const history = prev.tripHistory.filter(p => p.plan_id !== planId);
      saveHistory(history);
      return { ...prev, tripHistory: history };
    });
  }, []);

  const generatePlan = useCallback(async (data: TravelFormData) => {
    setState(prev => ({
      ...prev,
      isLoading: false,
      isStreaming: true,
      pendingRequest: data,
      error: null,
      currentPlan: null,
    }));
  }, []);

  const followUp = useCallback(async (instruction: string) => {
    setState(prev => {
      if (!prev.currentPlan) return { ...prev, error: 'No current plan to follow up on' };
      return { ...prev, isFollowingUp: true, error: null };
    });
    // Read current plan from state snapshot via functional update
    let planSnapshot: TravelPlan | null = null;
    setState(prev => { planSnapshot = prev.currentPlan; return prev; });
    try {
      if (!planSnapshot) throw new Error('No current plan to follow up on');
      const res = await fetch('/api/plan/followup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          original_request: (planSnapshot as TravelPlan).user_input,
          instruction,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Follow-up failed');
      const plan: TravelPlan = data.plan ?? data;
      setState(prev => {
        const history = [plan, ...prev.tripHistory.filter(p => p.plan_id !== plan.plan_id)].slice(0, 10);
        return { ...prev, currentPlan: plan, isFollowingUp: false, tripHistory: history };
      });
    } catch (e: any) {
      setState(prev => ({ ...prev, isFollowingUp: false, error: e.message }));
    }
  }, []);

  return (
    <AppContext.Provider value={{
      ...state,
      toggleDarkMode, setLoading, generatePlan, followUp,
      clearPlan, setError, setPlan, loadHistoryPlan, deleteHistory,
    }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp(): AppContextType {
  const context = useContext(AppContext);
  if (!context) throw new Error('useApp must be used within an AppProvider');
  return context;
}
