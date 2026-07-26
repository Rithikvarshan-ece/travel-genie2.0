import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { 
  Brain, Wallet, Globe, CloudSun, Route, 
  Hotel, MapPin, Calendar, BarChart3, 
  CheckCircle2, AlertCircle, Clock
} from 'lucide-react';

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
  budget: Wallet,
  destination: Globe,
  weather: CloudSun,
  transport: Route,
  hotel: Hotel,
  attraction: MapPin,
  itinerary: Calendar,
  expense: BarChart3,
};

const statusConfig = {
  success: { icon: CheckCircle2, color: 'text-green-500', bg: 'bg-green-50 dark:bg-green-900/20', border: 'border-green-200 dark:border-green-800' },
  warning: { icon: AlertCircle, color: 'text-yellow-500', bg: 'bg-yellow-50 dark:bg-yellow-900/20', border: 'border-yellow-200 dark:border-yellow-800' },
  error: { icon: AlertCircle, color: 'text-red-500', bg: 'bg-red-50 dark:bg-red-900/20', border: 'border-red-200 dark:border-red-800' },
};

export default function AgentCard({ name, description, data, index }: AgentCardProps) {
  const Icon = agentIcons[index] || Brain;
  const status = data?.status || 'success';
  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.success;
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
    case 'Budget Agent':
      return (
        <div className="space-y-1">
          <p className="text-xs text-slate-600 dark:text-slate-400">
            Total: <span className="font-semibold">${data.total_budget?.toLocaleString() || 'N/A'}</span>
          </p>
          <p className="text-xs text-slate-600 dark:text-slate-400">
            Level: <Badge variant="info" size="sm">{data.budget_level || 'N/A'}</Badge>
          </p>
          <p className="text-xs text-slate-600 dark:text-slate-400">
            Daily budget: <span className="font-semibold">${data.daily_budget?.per_day_total || 'N/A'}/day</span>
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
              • {d.name}, {d.country} (${d.estimated_total_cost || d.avg_daily_cost}/day)
            </p>
          ))}
        </div>
      );

    case 'Weather Agent':
      return (
        <div className="space-y-1">
          <p className="text-xs text-slate-600 dark:text-slate-400">
            Forecast: <span className="font-semibold">{data.forecast?.length || 0} days</span>
          </p>
          {data.weather_summary && (
            <p className="text-xs text-slate-500">{data.weather_summary}</p>
          )}
        </div>
      );

    case 'Transport Agent':
      return (
        <div className="space-y-1">
          <p className="text-xs text-slate-600 dark:text-slate-400">
            Options: <span className="font-semibold">{data.options?.length || 0}</span>
          </p>
          {data.best_option && (
            <p className="text-xs text-indigo-600 dark:text-indigo-400">
              Best: {data.best_option.mode} (${data.best_option.total_cost})
            </p>
          )}
        </div>
      );

    case 'Hotel Agent':
      return (
        <div className="space-y-1">
          <p className="text-xs text-slate-600 dark:text-slate-400">
            Hotels: <span className="font-semibold">{data.hotels?.length || 0} options</span>
          </p>
          {data.top_pick && (
            <p className="text-xs text-indigo-600 dark:text-indigo-400">
              Top: {data.top_pick.name} (${data.top_pick.price_per_night}/night)
            </p>
          )}
        </div>
      );

    case 'Attraction Agent':
      return (
        <p className="text-xs text-slate-600 dark:text-slate-400">
          Attractions: <span className="font-semibold">{data.attractions?.length || 0} places</span>
        </p>
      );

    case 'Itinerary Agent':
      return (
        <div className="space-y-1">
          <p className="text-xs text-slate-600 dark:text-slate-400">
            Days: <span className="font-semibold">{data.days?.length || 0}</span>
          </p>
          {data.summary && (
            <p className="text-xs text-slate-500">
              ~{data.summary.total_activities || 0} activities • ${data.summary.estimated_total_cost || 0}
            </p>
          )}
        </div>
      );

    case 'Expense Agent':
      return (
        <div className="space-y-1">
          <p className="text-xs text-slate-600 dark:text-slate-400">
            Total: <span className="font-semibold">${data.total_cost?.toLocaleString() || 'N/A'}</span>
          </p>
          <p className="text-xs text-green-600 dark:text-green-400">
            Remaining: ${data.remaining_budget?.toFixed(0) || 'N/A'}
          </p>
        </div>
      );

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

    default:
      return <p className="text-xs text-slate-400">Data available</p>;
  }
}

