import React, { useEffect, useRef, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useApp } from '@/context/AppContext';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import AgentPipeline from '@/components/agents/AgentPipeline';
import AgentCard from '@/components/agents/AgentCard';
import AgentProgressScreen from '@/components/agents/AgentProgressScreen';
import BudgetChart from '@/components/travel/BudgetChart';
import WeatherCard from '@/components/travel/WeatherCard';
import TransportCard from '@/components/travel/TransportCard';
import HotelCard from '@/components/travel/HotelCard';
import AttractionCard from '@/components/travel/AttractionCard';
import ItineraryTimeline from '@/components/travel/ItineraryTimeline';
import ExpenseSummary from '@/components/travel/ExpenseSummary';
import {
  ArrowLeft, Download, Sparkles, AlertCircle,
  Brain, CheckCircle2, Timer, BookmarkCheck, Loader2,
} from 'lucide-react';
import jsPDF from 'jspdf';

const INR = (v: number | string | undefined | null): string => {
  const n = typeof v === 'string' ? parseFloat(v) : (v ?? NaN);
  if (!isFinite(n)) return '₹N/A';
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n * 83);
};

// Extract numeric days from "3 days" or "3" or 3 safely
const parseDays = (v: string | number | undefined): number => {
  if (typeof v === 'number') return isFinite(v) && v > 0 ? v : 1;
  if (typeof v === 'string') {
    const n = parseFloat(v);
    return isFinite(n) && n > 0 ? n : 1;
  }
  return 1;
};

// Staggered section reveal — each section fades in with a delay
function RevealSection({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay, ease: 'easeOut' }}
    >
      {children}
    </motion.div>
  );
}

export default function ResultsPage() {
  const navigate = useNavigate();
  const { currentPlan, isStreaming, pendingRequest, error, clearPlan, setError, setPlan } = useApp();
  const resultsRef = useRef<HTMLDivElement>(null);
  const [confirming, setConfirming] = useState(false);
  const [confirmResult, setConfirmResult] = useState<{ trip_id: number; message: string } | null>(null);

  useEffect(() => {
    if (!currentPlan && !isStreaming && !error) {
      navigate('/plan');
    }
  }, [currentPlan, isStreaming, error, navigate]);

  const handleDownloadPDF = () => {
    if (!currentPlan) return;
    const { agents, user_input } = currentPlan;
    const { planner, trip_feasibility, destination, route_logistics, schedule, validation } = agents;
    const dest = planner?.final_recommendation?.summary?.destination || 'Trip';
    const fmt = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 });
    const inr = (v: number) => fmt.format((v ?? 0) * 83);

    const doc = new jsPDF({ unit: 'mm', format: 'a4' });
    const W = 210; const margin = 16; const col = W - margin * 2;
    let y = 0;

    const addPage = () => { doc.addPage(); y = 20; };
    const checkY = (need = 12) => { if (y + need > 280) addPage(); };

    const h1 = (text: string) => { checkY(14); doc.setFontSize(18).setFont('helvetica', 'bold'); doc.text(text, margin, y); y += 10; };
    const h2 = (text: string) => { checkY(10); doc.setFontSize(13).setFont('helvetica', 'bold'); doc.text(text, margin, y); y += 8; };
    const row = (label: string, value: string) => {
      checkY(7);
      doc.setFontSize(10).setFont('helvetica', 'bold').text(label, margin, y);
      doc.setFont('helvetica', 'normal').text(value, margin + 50, y);
      y += 6;
    };
    const line = (text: string, indent = 0) => {
      checkY(6);
      doc.setFontSize(10).setFont('helvetica', 'normal');
      const lines = doc.splitTextToSize(text, col - indent);
      doc.text(lines, margin + indent, y);
      y += lines.length * 5.5;
    };
    const divider = () => { checkY(5); doc.setDrawColor(200).line(margin, y, W - margin, y); y += 4; };

    // ── Cover page ──────────────────────────────────────────────────
    doc.setFillColor(63, 70, 229).rect(0, 0, W, 60, 'F');
    doc.setTextColor(255, 255, 255).setFontSize(26).setFont('helvetica', 'bold');
    doc.text('TravelGenie', margin, 28);
    doc.setFontSize(14).setFont('helvetica', 'normal');
    doc.text('AI-Powered Travel Plan', margin, 38);
    doc.setFontSize(11).text(`Destination: ${dest}`, margin, 50);
    doc.setTextColor(0, 0, 0);
    y = 72;

    // ── Trip Summary ────────────────────────────────────────────────
    h1('Trip Summary');
    divider();
    row('Destination:', dest);
    row('Duration:', planner?.final_recommendation?.summary?.duration || `${user_input.trip_days} days`);
    row('Total Budget:', inr(user_input.budget));
    row('Travel Type:', user_input.travel_type);
    row('Transport:', user_input.transportation);
    row('Hotel:', user_input.hotel_preference);
    row('Month:', user_input.travel_month);
    row('Status:', planner?.final_recommendation?.summary?.within_budget ? 'Within Budget ✓' : 'Over Budget ⚠');
    if (confirmResult) row('Trip ID:', `#${confirmResult.trip_id}`);
    y += 4;

    // ── Budget ──────────────────────────────────────────────────────
    h2('Budget Breakdown');
    divider();
    const bd = trip_feasibility?.breakdown;
    if (bd) {
      Object.entries(bd).forEach(([k, v]: [string, any]) => {
        row(`${k.charAt(0).toUpperCase() + k.slice(1)}:`, `${inr(v.amount)} (${v.percentage}%)`);
      });
      const db = trip_feasibility?.daily_budget;
      const perDay = typeof db === 'object' ? db?.per_day_total : db;
      row('Per Day:', inr(perDay));
    }
    y += 4;

    // ── Hotels ──────────────────────────────────────────────────────
    addPage();
    h1('Hotel Recommendations');
    divider();
    const hotels = destination?.hotels || [];
    hotels.slice(0, 5).forEach((h: any) => {
      h2(h.name);
      row('Category:', h.category);
      row('Price/Night:', inr(h.price_per_night));
      row('Rating:', `${h.rating} / 5`);
      row('Amenities:', (h.amenities || []).join(', '));
      y += 3;
    });

    // ── Attractions ─────────────────────────────────────────────────
    h1('Top Attractions');
    divider();
    const attractions = destination?.attractions || [];
    attractions.slice(0, 8).forEach((a: any) => {
      checkY(20);
      h2(a.name);
      row('Type:', a.type || a.category);
      row('Duration:', a.duration);
      row('Entry Fee:', a.cost ? inr(parseFloat(a.cost)) : 'Free');
      if (a.description) line(a.description, 4);
      y += 2;
    });

    // ── Route ───────────────────────────────────────────────────────
    addPage();
    h1('Route & Transport');
    divider();
    if (route_logistics) {
      row('From:', route_logistics.source);
      row('To:', route_logistics.destination);
      row('Distance:', `${route_logistics.travel_distance_km} km`);
      row('Travel Time:', `${route_logistics.travel_time_hours} hrs`);
      row('Recommended:', route_logistics.recommended_mode);
    }
    y += 4;

    // ── Day-by-day itinerary ─────────────────────────────────────────
    h1('Day-by-Day Itinerary');
    divider();
    const days = schedule?.days || [];
    days.forEach((day: any) => {
      checkY(16);
      h2(`Day ${day.day}: ${day.title}`);
      (day.slots || []).forEach((slot: any) => {
        (slot.activities || []).forEach((act: any) => {
          line(`• [${slot.hours}] ${act.activity}${act.cost && act.cost !== '0' ? ` — ${inr(parseFloat(act.cost))}` : ''}`, 4);
        });
      });
      y += 2;
    });

    // ── Expense Summary ──────────────────────────────────────────────
    addPage();
    h1('Expense Summary');
    divider();
    if (validation) {
      row('Total Cost:', inr(validation.total_cost));
      row('Remaining:', inr(Math.max(validation.remaining_budget, 0)));
      row('Budget Used:', `${validation.budget_utilization_percentage}%`);
      const eb = validation.expense_breakdown;
      if (eb) {
        y += 3;
        h2('Breakdown');
        Object.entries(eb).forEach(([k, v]: [string, any]) => {
          row(`${k.charAt(0).toUpperCase() + k.slice(1)}:`, `${inr(v.amount)} (${v.percentage}%)`);
        });
      }
    }
    y += 6;

    // ── Footer ───────────────────────────────────────────────────────
    checkY(12);
    divider();
    doc.setFontSize(9).setTextColor(120).setFont('helvetica', 'italic');
    doc.text('Generated by TravelGenie Multi-Agent AI System', margin, y);
    if (confirmResult) { y += 5; doc.text(`Confirmed Trip ID: #${confirmResult.trip_id}`, margin, y); }

    doc.save(`TravelGenie-${dest.replace(/\s+/g, '-')}.pdf`);
  };

  const handleConfirmTrip = async () => {
    if (!currentPlan || confirming) return;
    setConfirming(true);
    try {
      const res = await fetch('/api/plan/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plan: currentPlan, user_input: currentPlan.user_input }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Confirm failed');
      setConfirmResult({ trip_id: data.trip_id, message: data.message });
      setPlan({ ...currentPlan, plan_id: data.trip_id });
    } catch (e: any) {
      setError(e.message);
    } finally {
      setConfirming(false);
    }
  };

  const handleNewPlan = () => {
    clearPlan();
    navigate('/plan');
  };

  // ── Streaming / loading state ──────────────────────────────────────
  if (isStreaming && pendingRequest) {
    return (
      <AgentProgressScreen
        requestData={pendingRequest}
        onComplete={(plan, generationTime) => {
          setPlan({ ...plan, generation_time_seconds: generationTime });
        }}
        onError={(msg) => setError(msg)}
      />
    );
  }

  // ── Error state ────────────────────────────────────────────────────
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center max-w-md">
          <div className="w-20 h-20 rounded-full bg-red-100 dark:bg-red-900/50 flex items-center justify-center mx-auto mb-6">
            <AlertCircle className="w-10 h-10 text-red-600 dark:text-red-400" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-3">Oops! Something went wrong</h2>
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

  if (!currentPlan) return null;

  const { plan_id, generation_time_seconds, user_input, agents, agent_performance } = currentPlan;
  const { planner, trip_feasibility, destination, route_logistics, schedule, validation } = agents;

  const agentInfo = [
    { name: 'Planner Agent',           description: 'Main coordinator that orchestrates the entire travel planning process', data: planner,          key: 'planner'          },
    { name: 'Trip Feasibility Agent',  description: 'Validates trip feasibility and calculates budget allocation',           data: trip_feasibility, key: 'trip_feasibility' },
    { name: 'Destination Agent',       description: 'Suggests destinations based on preferences and budget',                 data: destination,      key: 'destination'      },
    { name: 'Route & Logistics Agent', description: 'Calculates travel distance, time, and transport options',               data: route_logistics,  key: 'route_logistics'  },
    { name: 'Schedule Agent',          description: 'Creates detailed day-by-day travel plan',                               data: schedule,         key: 'schedule'         },
    { name: 'Validation Agent',        description: 'Validates the plan and calculates final expenses',                      data: validation,       key: 'validation'       },
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
        <RevealSection delay={0}>
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
                {planner?.final_recommendation?.summary?.destination || 'Personalized'} • {user_input.trip_days} days • {INR(user_input.budget)} budget
              </p>
            </div>
            <div className="flex gap-2 flex-wrap">
              <button onClick={handleNewPlan}
                className="px-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium text-sm hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors flex items-center gap-1">
                <ArrowLeft className="w-4 h-4" /> New Plan
              </button>
              {!confirmResult && (
                <button onClick={handleConfirmTrip} disabled={confirming}
                  className="px-4 py-2 rounded-xl bg-green-600 text-white font-medium text-sm hover:bg-green-700 transition-colors flex items-center gap-1 disabled:opacity-60">
                  {confirming ? <Loader2 className="w-4 h-4 animate-spin" /> : <BookmarkCheck className="w-4 h-4" />}
                  {confirming ? 'Saving...' : 'Confirm Trip'}
                </button>
              )}
              <button onClick={handleDownloadPDF}
                className="px-4 py-2 rounded-xl bg-indigo-600 text-white font-medium text-sm hover:bg-indigo-700 transition-colors flex items-center gap-1">
                <Download className="w-4 h-4" /> PDF
              </button>
            </div>
          </div>
        </RevealSection>

        {/* Confirm success banner */}
        {confirmResult && (
          <RevealSection delay={0}>
            <div className="mb-6 p-4 rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0" />
              <div>
                <p className="text-sm font-semibold text-green-800 dark:text-green-300">{confirmResult.message}</p>
                <p className="text-xs text-green-600 dark:text-green-400">Trip ID #{confirmResult.trip_id} saved to history.</p>
              </div>
            </div>
          </RevealSection>
        )}

        {/* Agent Pipeline */}
        <RevealSection delay={0.1}>
          <div className="mb-8">
            <AgentPipeline agentPerformance={agent_performance} generationTime={generation_time_seconds} />
          </div>
        </RevealSection>

        {/* Trip Summary */}
        {planner?.final_recommendation?.summary && (
          <RevealSection delay={0.2}>
            <Card glass className="p-6 mb-8">
              <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">Trip Summary</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { label: 'Destination', value: planner.final_recommendation.summary.destination || 'AI Selected' },
                  { label: 'Duration',    value: planner.final_recommendation.summary.duration || `${user_input.trip_days} days` },
                  { label: 'Budget',      value: INR(planner.final_recommendation.summary.total_budget || user_input.budget) },
                  { label: 'Status',      value: planner.final_recommendation.summary.within_budget ? '✅ Within Budget' : '⚠️ Over Budget' },
                ].map((item, i) => (
                  <div key={i} className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50">
                    <p className="text-xs text-slate-500 dark:text-slate-400">{item.label}</p>
                    <p className="text-lg font-bold text-slate-900 dark:text-white">{item.value}</p>
                  </div>
                ))}
              </div>
            </Card>
          </RevealSection>
        )}

        {/* Budget */}
        {trip_feasibility?.breakdown && (
          <RevealSection delay={0.3}>
            <div className="mb-8"><BudgetChart data={trip_feasibility} /></div>
          </RevealSection>
        )}

        {/* Weather */}
        <RevealSection delay={0.4}>
          <div className="mb-8"><WeatherCard data={destination?.weather ?? {}} /></div>
        </RevealSection>

        {/* Transport */}
        {route_logistics?.transport_options && (
          <RevealSection delay={0.5}>
            <div className="mb-8">
              <TransportCard data={{ options: route_logistics.transport_options, best_option: route_logistics.best_option }} />
            </div>
          </RevealSection>
        )}

        {/* Hotels */}
        {destination?.hotels && (
          <RevealSection delay={0.6}>
            <div className="mb-8">
              <HotelCard data={{ hotels: destination.hotels, top_pick: destination.top_pick }} />
            </div>
          </RevealSection>
        )}

        {/* Attractions */}
        {destination?.attractions && (
          <RevealSection delay={0.7}>
            <div className="mb-8">
              <AttractionCard data={{ attractions: destination.attractions, daily_breakdown: destination.daily_breakdown }} />
            </div>
          </RevealSection>
        )}

        {/* Itinerary */}
        {schedule?.days && (
          <RevealSection delay={0.8}>
            <div className="mb-8"><ItineraryTimeline data={schedule} /></div>
          </RevealSection>
        )}

        {/* Expense Summary */}
        {validation?.expense_breakdown && (
          <RevealSection delay={0.9}>
            <div className="mb-8">
              <ExpenseSummary data={{
                total_budget: user_input.budget,
                total_cost: validation.total_cost,
                remaining_budget: validation.remaining_budget,
                budget_utilization_percentage: validation.budget_utilization_percentage,
                expense_breakdown: validation.expense_breakdown,
                chart_data: validation.chart_data,
                budget_status: validation.budget_status,
                saving_tips: validation.saving_tips,
              }} />
            </div>
          </RevealSection>
        )}

        {/* AI Reasoning */}
        {planner?.reasoning_steps && (
          <RevealSection delay={1.0}>
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
                    transition={{ delay: 1.0 + i * 0.1 }}
                    className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700"
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="w-6 h-6 rounded-full bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300 text-xs font-bold flex items-center justify-center">
                        {step.step}
                      </span>
                      <span className="text-sm font-semibold text-slate-700 dark:text-slate-300">{step.name}</span>
                      <Badge variant={step.status === 'success' ? 'success' : 'warning'} size="sm">{step.status}</Badge>
                    </div>
                    <p className="text-sm text-slate-600 dark:text-slate-400 ml-8">{step.details}</p>
                  </motion.div>
                ))}
              </div>
            </Card>
          </RevealSection>
        )}

        {/* Agent Contributions */}
        <RevealSection delay={1.1}>
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
        </RevealSection>

        {/* Footer */}
        <RevealSection delay={1.2}>
          <div className="text-center py-8">
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Generated by TravelGenie Multi-Agent AI System{plan_id ? ` • Plan ID: ${plan_id}` : ''}
            </p>
          </div>
        </RevealSection>
      </motion.div>
    </div>
  );
}
