import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { 
  Brain, Wallet, Globe, Route, 
  Calendar, BarChart3, 
  CheckCircle2, AlertCircle
} from 'lucide-react';

const INR = (v: number | string | undefined | null): string => {
  const n = typeof v === 'string' ? parseFloat(v) : (v ?? NaN);
  if (!isFinite(n)) return '₹N/A';
  const inr = n * 83;
  const snapped = Math.abs(inr) < 5 ? 0 : inr;
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(snapped);
};

interface AgentStep {
  step: number;
  name: string;
  description: string;
  status: string;
  details?: string;
  [key: string]: any;
}

interface AgentCardProps {
  name: string;
  description: string;
  data: any;
  index: number;
}

const agentIcons: Record<string, React.ElementType> = {
  planner: Brain,
  trip_feasibility: Wallet,
  destination: Globe,
  route_logistics: Route,
  schedule: Calendar,
  validation: BarChart3,
};

const statusConfig = {
  success: { icon: CheckCircle2, color: 'text-green-500', bg: 'bg-green-50 dark:bg-green-900/20', border: 'border-green-200 dark:border-green-800' },
  warning: { icon: AlertCircle, color: 'text-yellow-500', bg: 'bg-yellow-50 dark:bg-yellow-900/20', border: 'border-yellow-200 dark:border-yellow-800' },
  error: { icon: AlertCircle, color: 'text-red-500', bg: 'bg-red-50 dark:bg-red-900/20', border: 'border-red-200 dark:border-red-800' },
};

// Derive status purely from data content — never from agent name/type
function deriveStatus(data: any): keyof typeof statusConfig {
  if (!data) return 'success';
  // Explicit error flag
  if (data.status === 'error' || data.error) return 'error';
  // Validation agent: use is_valid
  if (typeof data.is_valid === 'boolean') return data.is_valid ? 'success' : 'warning';
  // Feasibility agent: use is_feasible
  if (typeof data.is_feasible === 'boolean') return data.is_feasible ? 'success' : 'warning';
  // Budget agent: within_budget
  if (typeof data.budget_within_limit === 'boolean') return data.budget_within_limit ? 'success' : 'warning';
  return 'success';
}

export default function AgentCard({ name, description, data, index }: AgentCardProps) {
  const Icon = agentIcons[name.toLowerCase().replace(/ /g, '_').replace('&_', '')] || Brain;
  const status = deriveStatus(data);
  const config = statusConfig[status];
  const StatusIcon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
    >
      <Card className={`p-4 ${config.bg} ${config.border}`}>
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-xl bg-white dark:bg-slate-800 shadow-sm flex items-center justify-center">
            <Icon className={`w-5 h-5 ${config.color}`} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h4 className="font-semibold text-slate-900 dark:text-white text-sm">{name}</h4>
              <StatusIcon className={`w-4 h-4 ${config.color}`} />
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-2">{description}</p>

            {/* Data-specific display */}
            {renderAgentData(name, data)}
          </div>
        </div>
      </Card>
    </motion.div>
  );
}

function renderAgentData(agentName: string, data: any) {
  if (!data) return <p className="text-xs text-slate-400">No data available</p>;

  switch (agentName) {
    case 'Planner Agent':
      return (
        <div className="space-y-1">
          <p className="text-xs text-slate-600 dark:text-slate-400">
            Steps: <span className="font-semibold">{data.reasoning_steps?.length || 0}</span>
          </p>
          {data.final_recommendation?.summary && (
            <p className="text-xs text-indigo-600 dark:text-indigo-400">
              {data.final_recommendation.summary.destination} • {data.final_recommendation.summary.duration}
            </p>
          )}
        </div>
      );

    case 'Trip Feasibility Agent':
      return (
        <div className="space-y-1">
          <p className="text-xs text-slate-600 dark:text-slate-400">
            Feasible: <span className="font-semibold">{data.is_feasible ? '✅ Yes' : '❌ No'}</span>
          </p>
          <p className="text-xs text-slate-600 dark:text-slate-400">
            Daily budget: <span className="font-semibold">{INR(
              typeof data.daily_budget === 'object'
                ? data.daily_budget?.per_day_total
                : data.daily_budget
            )}/day</span>
          </p>
          <p className="text-xs text-slate-600 dark:text-slate-400">
            Level: <Badge variant="info" size="sm">{data.budget_level || 'N/A'}</Badge>
          </p>
        </div>
      );

    case 'Destination Agent':
      return (
        <div className="space-y-1">
          <p className="text-xs text-slate-600 dark:text-slate-400">
            Suggestions: <span className="font-semibold">{data.suggestions?.length || 0} destinations</span>
          </p>
          {data.suggestions?.slice(0, 2).map((d: any, i: number) => (
            <p key={i} className="text-xs text-indigo-600 dark:text-indigo-400">
              • {d.name}, {d.country} ({INR(d.avg_daily_cost)}/day)
            </p>
          ))}
        </div>
      );

    case 'Route & Logistics Agent':
      return (
        <div className="space-y-1">
          <p className="text-xs text-slate-600 dark:text-slate-400">
            Distance: <span className="font-semibold">{data.travel_distance_km} km</span>
          </p>
          <p className="text-xs text-slate-600 dark:text-slate-400">
            Travel time: <span className="font-semibold">{data.travel_time_hours} hrs</span>
          </p>
          {data.best_option && (
            <p className="text-xs text-indigo-600 dark:text-indigo-400">
              Best: {data.best_option.mode} ({INR(data.best_option.total_cost)})
            </p>
          )}
        </div>
      );

    case 'Schedule Agent':
      return (
        <div className="space-y-1">
          <p className="text-xs text-slate-600 dark:text-slate-400">
            Days: <span className="font-semibold">{data.days?.length || 0}</span>
          </p>
          {data.summary && (
            <p className="text-xs text-slate-500">
              ~{data.summary.total_activities || 0} activities • {INR(data.summary.estimated_total_cost || 0)}
            </p>
          )}
        </div>
      );

    case 'Validation Agent':
      return (
        <div className="space-y-1">
          <p className="text-xs text-slate-600 dark:text-slate-400">
            Valid: <span className="font-semibold">{data.is_valid ? '✅ Yes' : '⚠️ Issues found'}</span>
          </p>
          <p className="text-xs text-green-600 dark:text-green-400">
            Remaining: {INR(data.remaining_budget) ?? '₹N/A'}
          </p>
        </div>
      );

    default:
      return <p className="text-xs text-slate-400">Data available</p>;
  }
}

