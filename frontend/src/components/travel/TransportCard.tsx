import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Plane, Train, Bus, Car, Check, X, Leaf } from 'lucide-react';

interface TransportOption {
  mode: string;
  mode_emoji: string;
  travel_time_hours: number;
  travel_time_display: string;
  total_cost: number;
  cost_per_person: number;
  overall_score: number;
  co2_emissions_kg: number;
  pros: string[];
  cons: string[];
}

interface TransportData {
  options: TransportOption[];
  best_option: TransportOption;
  comparison: any;
}

interface TransportCardProps {
  data: TransportData;
}

function getTransportIcon(mode: string) {
  const m = mode.toLowerCase();
  if (m.includes('flight') || m.includes('plane')) return Plane;
  if (m.includes('train') || m.includes('rail')) return Train;
  if (m.includes('bus')) return Bus;
  if (m.includes('car') || m.includes('rental')) return Car;
  return Car;
}

function getScoreColor(score: number) {
  if (score >= 8) return 'text-green-600 dark:text-green-400';
  if (score >= 6) return 'text-yellow-600 dark:text-yellow-400';
  return 'text-red-600 dark:text-red-400';
}

function getScoreBg(score: number) {
  if (score >= 8) return 'bg-green-100 dark:bg-green-900/30';
  if (score >= 6) return 'bg-yellow-100 dark:bg-yellow-900/30';
  return 'bg-red-100 dark:bg-red-900/30';
}

export default function TransportCard({ data }: TransportCardProps) {
  const { options, best_option } = data;

  if (!options || options.length === 0) {
    return (
      <Card glass className="p-6">
        <p className="text-slate-500 dark:text-slate-400">Transport options not available</p>
      </Card>
    );
  }

  return (
    <Card glass className="p-6">
      <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-6">Transport Options</h3>

      <div className="space-y-4">
        {options.map((option, i) => {
          const Icon = getTransportIcon(option.mode);
          const isBest = best_option && option.mode === best_option.mode;
          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className={`relative p-4 rounded-xl border-2 transition-all ${
                isBest
                  ? 'border-green-400 dark:border-green-500 bg-green-50 dark:bg-green-900/20'
                  : 'border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800'
              }`}
            >
              {isBest && (
                <Badge variant="success" size="sm" className="absolute -top-2 -right-2">
                  Best Choice
                </Badge>
              )}

              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-indigo-100 dark:bg-indigo-900/50 flex items-center justify-center">
                    <Icon className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-900 dark:text-white capitalize">
                      {option.mode.replace('_', ' ')}
                    </h4>
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                      {option.travel_time_display}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-slate-900 dark:text-white">
                    ${option.total_cost.toFixed(0)}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    ${option.cost_per_person.toFixed(0)}/person
                  </p>
                </div>
              </div>

              {/* Score bar */}
              <div className="flex items-center gap-2 mb-3">
                <div className="flex-1 h-2 rounded-full bg-slate-200 dark:bg-slate-700">
                  <div
                    className={`h-2 rounded-full transition-all ${
                      option.overall_score >= 8 ? 'bg-green-500' :
                      option.overall_score >= 6 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${(option.overall_score / 10) * 100}%` }}
                  />
                </div>
                <span className={`text-sm font-bold ${getScoreColor(option.overall_score)}`}>
                  {option.overall_score}/10
                </span>
              </div>

              {/* CO2 Emissions */}
              <div className="flex items-center gap-2 mb-3 text-sm text-slate-500 dark:text-slate-400">
                <Leaf className="w-4 h-4" />
                <span>{option.co2_emissions_kg} kg CO₂</span>
              </div>

              {/* Pros & Cons */}
              <div className="grid md:grid-cols-2 gap-3">
                <div>
                  <p className="text-xs font-semibold text-green-600 dark:text-green-400 mb-1">Pros</p>
                  <ul className="space-y-0.5">
                    {option.pros?.map((pro, j) => (
                      <li key={j} className="text-xs text-slate-600 dark:text-slate-400 flex items-start gap-1">
                        <Check className="w-3 h-3 text-green-500 mt-0.5 flex-shrink-0" />
                        {pro}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="text-xs font-semibold text-red-600 dark:text-red-400 mb-1">Cons</p>
                  <ul className="space-y-0.5">
                    {option.cons?.map((con, j) => (
                      <li key={j} className="text-xs text-slate-600 dark:text-slate-400 flex items-start gap-1">
                        <X className="w-3 h-3 text-red-500 mt-0.5 flex-shrink-0" />
                        {con}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </Card>
  );
}

