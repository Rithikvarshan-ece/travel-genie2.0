import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { AppProvider } from '@/context/AppContext';
import Layout from '@/components/layout/Layout';
import HomePage from '@/pages/HomePage';
import PlannerPage from '@/pages/PlannerPage';
import ResultsPage from '@/pages/ResultsPage';
import HistoryPage from '@/pages/HistoryPage';
import AboutPage from '@/pages/AboutPage';

function App() {
  return (
    <AppProvider>
      <Router>
        <Layout>
          <AnimatePresence mode="wait">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/plan" element={<PlannerPage />} />
              <Route path="/results" element={<ResultsPage />} />
              <Route path="/history" element={<HistoryPage />} />
              <Route path="/about" element={<AboutPage />} />
            </Routes>
          </AnimatePresence>
        </Layout>
      </Router>
    </AppProvider>
  );
}

export default App;
