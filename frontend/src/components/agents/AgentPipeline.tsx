import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent } from '@/components/ui/Card';
import { 
  Brain, Wallet, Globe, Route, 
  Calendar, BarChart3, 
  ArrowRight, CheckCircle2, Timer
} from 'lucide-react';

interface AgentPerformance {
  [key: string]: number | { duration_s?: number; confidence_pct?: number; apis_used?: string[] };
}

interface AgentPipelineProps {
  agentPerformance?: AgentPerformance;
  generationTime?: number;
}

const pipelineSteps = [
  { key: 'trip_feasibility', name: 'Feasibility', icon: Wallet, color: 'text-emerald-500', bg: 'bg-emerald-50 dark:bg-emerald-900/20' },
  { key: 'destination', name: 'Destination', icon: Globe, color: 'text-blue-500', bg: 'bg-blue-50 dark:bg-blue-900/20' },
  { key: 'route_logistics', name: 'Route & Logistics', icon: Route, color: 'text-cyan-500', bg: 'bg-cyan-50 dark:bg-cyan-900/20' },
  { key: 'schedule', name: 'Schedule', icon: Calendar, color: 'text-orange-500', bg: 'bg-orange-50 dark:bg-orange-900/20' },
  { key: 'validation', name: 'Validation', icon: BarChart3, color: 'text-red-500', bg: 'bg-red-50 dark:bg-red-900/20' },
];

export default function AgentPipeline({ agentPerformance, generationTime }: AgentPipelineProps) {
  return (
    <Card glass className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-slate-900 dark:text-white">🤖 AI Agent Pipeline</h3>
        {generationTime && (
          <div className="flex items-center gap-1 text-sm text-slate-500 dark:text-slate-400">
            <Timer className="w-4 h-4" />
            <span>{generationTime}s</span>
          </div>
        )}
      </div>

      {/* Pipeline Flow */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {pipelineSteps.map((step, i) => {
          const Icon = step.icon;
          const perf = agentPerformance?.[step.key];
          const time = typeof perf === 'object' ? perf?.duration_s : perf;
          const isLast = i === pipelineSteps.length - 1;

          return (
            <motion.div
              key={step.key}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.1 }}
              className="relative"
            >
              <div className={`p-3 rounded-xl ${step.bg} border border-slate-200 dark:border-slate-700 text-center`}>
                <Icon className={`w-6 h-6 ${step.color} mx-auto mb-1`} />
                <p className="text-xs font-medium text-slate-700 dark:text-slate-300">{step.name}</p>
                {time !== undefined && (
                  <p className="text-xs text-slate-400 mt-0.5">{time.toFixed(1)}s</p>
                )}
              </div>
              {!isLast && (
                <div className="hidden sm:block absolute -right-2.5 top-1/2 -translate-y-1/2 z-10">
                  <ArrowRight className="w-5 h-5 text-slate-300 dark:text-slate-600" />
                </div>
              )}
            </motion.div>
          );
        })}
      </div>

      {/* Planner Agent Highlight */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="mt-4 p-3 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 text-white flex items-center gap-3"
      >
        <Brain className="w-6 h-6 text-white/80" />
        <div>
          <p className="text-sm font-semibold">Planner Agent</p>
          <p className="text-xs text-indigo-100">Coordinates all 6 agents to generate your perfect travel plan</p>
        </div>
        <CheckCircle2 className="w-5 h-5 text-white/80 ml-auto" />
      </motion.div>
    </Card>
  );
}

