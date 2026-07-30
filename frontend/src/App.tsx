import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { AppProvider } from '@/context/AppContext';
import { AuthProvider, useAuth } from '@/context/AuthContext';
import Layout from '@/components/layout/Layout';
import HomePage from '@/pages/HomePage';
import PlannerPage from '@/pages/PlannerPage';
import ResultsPage from '@/pages/ResultsPage';
import HistoryPage from '@/pages/HistoryPage';
import AboutPage from '@/pages/AboutPage';
import AuthPage from '@/pages/AuthPage';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <>{children}</> : <Navigate to="/auth" replace />;
}

function App() {
  return (
    <AuthProvider>
      <AppProvider>
        <Router>
          <AnimatePresence mode="wait">
            <Routes>
              <Route path="/auth" element={<AuthPage />} />
              <Route path="/" element={<Layout><HomePage /></Layout>} />
              <Route path="/plan" element={<ProtectedRoute><Layout><PlannerPage /></Layout></ProtectedRoute>} />
              <Route path="/results" element={<ProtectedRoute><Layout><ResultsPage /></Layout></ProtectedRoute>} />
              <Route path="/history" element={<ProtectedRoute><Layout><HistoryPage /></Layout></ProtectedRoute>} />
              <Route path="/about" element={<Layout><AboutPage /></Layout>} />
            </Routes>
          </AnimatePresence>
        </Router>
      </AppProvider>
    </AuthProvider>
  );
}

export default App;
