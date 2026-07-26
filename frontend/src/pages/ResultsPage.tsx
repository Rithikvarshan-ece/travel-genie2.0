import React, { useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useApp } from '@/context/AppContext';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import AgentPipeline from '@/components/agents/AgentPipeline';
import AgentCard from '@/components/agents/AgentCard';
import BudgetChart from '@/components/travel/BudgetChart';
import WeatherCard from '@/components/travel/WeatherCard';
import TransportCard from '@/components/travel/TransportCard';
import HotelCard from '@/components/travel/HotelCard';
import AttractionCard from '@/components/travel/AttractionCard';
import ItineraryTimeline from '@/components/travel/ItineraryTimeline';
import ExpenseSummary from '@/components/travel/ExpenseSummary';
import { 
  ArrowLeft, Download, Sparkles, Loader2, 
  AlertCircle, Brain, CheckCircle2, Timer,
  Share2, Printer
} from 'lucide-react';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';

export default function ResultsPage() {
  const navigate = useNavigate();
  const { currentPlan, isLoading, error, clearPlan } = useApp();
  const resultsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!currentPlan && !isLoading && !error) {
      navigate('/plan');
    }
  }, [currentPlan, isLoading, error, navigate]);

  const handleDownloadPDF = async () => {
    if (!resultsRef.current) return;
    try {
      const canvas = await html2canvas(resultsRef.current, {
        backgroundColor: '#ffffff',
        scale: 2,
        useCORS: true,
      });
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'mm', 'a4');
      const imgWidth = 210;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      let heightLeft = imgHeight;
      let position = 0;
      
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
      heightLeft -= pdf.internal.pageSize.height;
      
      while (heightLeft > 0) {
        position = heightLeft - imgHeight;
        pdf.addPage();
        pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
        heightLeft -= pdf.internal.pageSize.height;
      }
      
      pdf.save('travel-plan.pdf');
    } catch (err) {
      console.error('PDF generation failed:', err);
    }
  };

  const handleNewPlan = () => {
    clearPlan();
    navigate('/plan');
  };

  // Loading State
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center max-w-md"
        >
          <div className="w-20 h-20 rounded-full bg-indigo-100 dark:bg-indigo-900/50 flex items-center justify-center mx-auto mb-6">
            <Loader2 className="w-10 h-10 text-indigo-600 dark:text-indigo-400 animate-spin" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-3">
            AI Agents are Planning Your Trip
          </h2>
          <p className="text-slate-600 dark:text-slate-400 mb-6">
            Nine specialized AI agents are working together to create the perfect itinerary...
          </p>
          <div className="space-y-3">
            {['Analyzing budget & preferences...', 'Finding best destinations...', 'Checking weather conditions...', 'Planning daily activities...', 'Calculating expenses...'].map((step, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.5 }}
                className="flex items-center gap-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50"
              >
                <div className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse" />
                <span className="text-sm text-slate-600 dark:text-slate-400">{step}</span>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    );
  }

  // Error State
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center max-w-md"
        >
          <div className="w-20 h-20 rounded-full bg-red-100 dark:bg-red-900/50 flex items-center justify-center mx-auto mb-6">
            <AlertCircle className="w-10 h-10 text-red-600 dark:text-red-400" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-3">
            Oops! Something went wrong
          </h2>
          <p className="text-slate-600 dark:text-slate-400 mb-6">{error}</p>
          <div className="flex gap-3 justify-center">
            <button onClick={handleNewPlan}
              className="px-6 py-3 rounded-xl bg-indigo-600 text-white font-semibold hover:bg-indigo-700 transition-colors">
              Try Again
            </button>
            <Link to="/"
              className="px-6 py-3 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-semibold hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors">
              Go Home
            </Link>
          </div>
        </motion.div>
      </div>
    );
  }

  // No plan state
  if (!currentPlan) return null;

  const { plan_id, generation_time_seconds, user_input, agents, agent_performance } = currentPlan;
  const { planner, budget, destination, weather, transport, hotel, attraction, itinerary, expense } = agents;

  const agentInfo = [
    { name: 'Planner Agent', description: 'Main coordinator that orchestrates the entire travel planning process', data: planner, key: 'planner' },
    { name: 'Budget Agent', description: 'Calculates budget allocation across all travel categories', data: budget, key: 'budget' },
    { name: 'Destination Agent', description: 'Suggests destinations based on preferences and budget', data: destination, key: 'destination' },
    { name: 'Weather Agent', description: 'Checks weather conditions for trip duration', data: weather, key: 'weather' },
    { name: 'Transport Agent', description: 'Recommends transport options with cost comparison', data: transport, key: 'transport' },
    { name: 'Hotel Agent', description: 'Suggests hotels based on budget and preferences', data: hotel, key: 'hotel' },
    { name: 'Attraction Agent', description: 'Generates must-visit attractions and activities', data: attraction, key: 'attraction' },
    { name: 'Itinerary Agent', description: 'Creates detailed day-by-day travel plan', data: itinerary, key: 'itinerary' },
    { name: 'Expense Agent', description: 'Calculates total trip expenses and budget analysis', data: expense, key: 'expense' },
  ];

  return (
    <div className="min-h-screen px-4 py-8">
      <motion.div
        ref={resultsRef}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-6xl mx-auto"
      >
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Badge variant="success" size="md">
                <CheckCircle2 className="w-3 h-3 mr-1" /> Plan Generated
              </Badge>
              {generation_time_seconds && (
                <Badge variant="info" size="sm">
                  <Timer className="w-3 h-3 mr-1" /> {generation_time_seconds}s
                </Badge>
              )}
            </div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Your Travel Plan</h1>
            <p className="text-slate-500 dark:text-slate-400">
              {planner?.final_recommendation?.summary?.destination || 'Personalized'} • {user_input.trip_days} days • ${user_input.budget?.toLocaleString()} budget
            </p>
          </div>
          <div className="flex gap-2">
            <button onClick={handleNewPlan}
              className="px-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium text-sm hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors flex items-center gap-1">
              <ArrowLeft className="w-4 h-4" /> New Plan
            </button>
            <button onClick={handleDownloadPDF}
              className="px-4 py-2 rounded-xl bg-indigo-600 text-white font-medium text-sm hover:bg-indigo-700 transition-colors flex items-center gap-1">
              <Download className="w-4 h-4" /> PDF
            </button>
          </div>
        </div>

        {/* Agent Pipeline */}
        <div className="mb-8">
          <AgentPipeline agentPerformance={agent_performance} generationTime={generation_time_seconds} />
        </div>

        {/* Summary Section */}
        {planner?.final_recommendation?.summary && (
          <Card glass className="p-6 mb-8">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">Trip Summary</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: 'Destination', value: planner.final_recommendation.summary.destination || 'AI Selected' },
                { label: 'Duration', value: planner.final_recommendation.summary.duration || `${user_input.trip_days} days` },
                { label: 'Budget', value: `$${planner.final_recommendation.summary.total_budget?.toLocaleString() || user_input.budget?.toLocaleString()}` },
                { label: 'Status', value: planner.final_recommendation.summary.within_budget ? '✅ Within Budget' : '⚠️ Over Budget' },
              ].map((item, i) => (
                <div key={i} className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50">
                  <p className="text-xs text-slate-500 dark:text-slate-400">{item.label}</p>
                  <p className="text-lg font-bold text-slate-900 dark:text-white">{item.value}</p>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Budget Section */}
        {budget && budget.breakdown && (
          <div className="mb-8">
            <BudgetChart data={budget} />
          </div>
        )}

        {/* Weather Section */}
        {weather && weather.forecast && (
          <div className="mb-8">
            <WeatherCard data={weather} />
          </div>
        )}

        {/* Transport Section */}
        {transport && transport.options && (
          <div className="mb-8">
            <TransportCard data={transport} />
          </div>
        )}

        {/* Hotel Section */}
        {hotel && hotel.hotels && (
          <div className="mb-8">
            <HotelCard data={hotel} />
          </div>
        )}

        {/* Attractions Section */}
        {attraction && attraction.attractions && (
          <div className="mb-8">
            <AttractionCard data={attraction} />
          </div>
        )}

        {/* Itinerary Section */}
        {itinerary && itinerary.days && (
          <div className="mb-8">
            <ItineraryTimeline data={itinerary} />
          </div>
        )}

        {/* Expense Summary */}
        {expense && expense.expense_breakdown && (
          <div className="mb-8">
            <ExpenseSummary data={expense} />
          </div>
        )}

        {/* Agent Reasoning Section */}
        {planner?.reasoning_steps && (
          <Card glass className="p-6 mb-8">
            <div className="flex items-center gap-2 mb-4">
              <Brain className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              <h2 className="text-xl font-bold text-slate-900 dark:text-white">AI Reasoning</h2>
            </div>
            <div className="space-y-3">
              {planner.reasoning_steps.map((step: any, i: number) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className="w-6 h-6 rounded-full bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300 text-xs font-bold flex items-center justify-center">
                      {step.step}
                    </span>
                    <span className="text-sm font-semibold text-slate-700 dark:text-slate-300">{step.name}</span>
                    <Badge variant={step.status === 'success' ? 'success' : 'warning'} size="sm">
                      {step.status}
                    </Badge>
                  </div>
                  <p className="text-sm text-slate-600 dark:text-slate-400 ml-8">{step.details}</p>
                </motion.div>
              ))}
            </div>
          </Card>
        )}

        {/* Agent Details */}
        <Card glass className="p-6 mb-8">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">Agent Contributions</h2>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agentInfo.map((agent, i) => (
              <AgentCard key={agent.key} name={agent.name} description={agent.description} data={agent.data} index={i} />
            ))}
          </div>
        </Card>

        {/* Footer */}
        <div className="text-center py-8">
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Generated by TravelGenie Multi-Agent AI System • Plan ID: {plan_id}
          </p>
        </div>
      </motion.div>
    </div>
  );
}
