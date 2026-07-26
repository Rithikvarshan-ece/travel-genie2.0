import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { TravelFormData, TravelPlan } from '@/types/travel';

interface AppState {
  isDarkMode: boolean;
  isLoading: boolean;
  currentPlan: TravelPlan | null;
  error: string | null;
  tripHistory: TravelPlan[];
}

interface AppContextType extends AppState {
  toggleDarkMode: () => void;
  setLoading: (loading: boolean) => void;
  generatePlan: (data: TravelFormData) => Promise<void>;
  clearPlan: () => void;
  setError: (error: string | null) => void;
}

const API_BASE_URL = '/api';

const initialState: AppState = {
  isDarkMode: true,
  isLoading: false,
  currentPlan: null,
  error: null,
  tripHistory: [],
};

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AppState>(initialState);

  const toggleDarkMode = useCallback(() => {
    setState(prev => {
      const newMode = !prev.isDarkMode;
      if (newMode) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
      return { ...prev, isDarkMode: newMode };
    });
  }, []);

  const setLoading = useCallback((loading: boolean) => {
    setState(prev => ({ ...prev, isLoading: loading }));
  }, []);

  const setError = useCallback((error: string | null) => {
    setState(prev => ({ ...prev, error }));
  }, []);

  const clearPlan = useCallback(() => {
    setState(prev => ({ ...prev, currentPlan: null, error: null }));
  }, []);

  const generatePlan = useCallback(async (data: TravelFormData) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const response = await fetch(`${API_BASE_URL}/plan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      const responseData = await response.json();
      if (!response.ok) {
        throw new Error(responseData.detail || responseData.error || 'Failed to generate travel plan');
      }

      const plan: TravelPlan = responseData.plan ?? responseData;
      
      setState(prev => ({
        ...prev,
        currentPlan: plan,
        isLoading: false,
        tripHistory: [plan, ...prev.tripHistory].slice(0, 10),
      }));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An unexpected error occurred';
      setState(prev => ({ ...prev, isLoading: false, error: message }));
      throw err;
    }
  }, []);

  return (
    <AppContext.Provider
      value={{
        ...state,
        toggleDarkMode,
        setLoading,
        generatePlan,
        clearPlan,
        setError,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp(): AppContextType {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}
