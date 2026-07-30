import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { motion } from 'framer-motion';
import { Card, CardContent } from '@/components/ui/Card';

interface BudgetCategory {
  amount: number;
  percentage: number;
  description: string;
  per_night?: number;
  per_day?: number;
  per_trip?: number;
}

interface BudgetBreakdown {
  hotel: BudgetCategory;
  food: BudgetCategory;
  activities: BudgetCategory;
  transport: BudgetCategory;
  emergency: BudgetCategory;
}

interface BudgetData {
  total_budget: number;
  breakdown: BudgetBreakdown;
  daily_budget: { per_day_total: number; per_person_per_day: number };
  budget_level: string;
  optimization_tips: string[];
}

interface BudgetChartProps {
  data: BudgetData;
}

const COLORS = {
  hotel: '#4F46E5',
  food: '#F59E0B',
  activities: '#EF4444',
  transport: '#10B981',
  emergency: '#8B5CF6',
};

// INR formatter — multiplies backend values by 83
const INR = (v: number | string | undefined | null): string => {
  const n = typeof v === 'string' ? parseFloat(v) : (v ?? NaN);
  if (!isFinite(n)) return '₹N/A';
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n * 83);
};

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const d = payload[0].payload;
    return (
      <div className="bg-white dark:bg-slate-800 p-3 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700">
        <p className="font-semibold text-slate-900 dark:text-white">{d.label}</p>
        <p className="text-sm text-slate-600 dark:text-slate-400">{INR(d.amount)}</p>
        <p className="text-sm text-slate-500">{d.percentage}%</p>
      </div>
    );
  }
  return null;
};

export default function BudgetChart({ data }: BudgetChartProps) {
  const { breakdown, total_budget, daily_budget, budget_level, optimization_tips } = data;

  // daily_budget may be a number (from backend) or an object — handle both safely
  const perDayTotal: number = typeof daily_budget === 'number'
    ? daily_budget
    : (daily_budget as any)?.per_day_total ?? (daily_budget as any)?.per_person_per_day ?? 0;

  const chartData = Object.entries(breakdown).map(([key, val]) => ({
    name: key,
    label: key.charAt(0).toUpperCase() + key.slice(1),
    amount: val.amount,
    percentage: val.percentage,
    color: COLORS[key as keyof typeof COLORS],
  }));

  return (
    <Card glass className="p-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-slate-900 dark:text-white">Budget Breakdown</h3>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Total: {INR(total_budget)} • {budget_level}
          </p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
            {INR(perDayTotal)}
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400">per day</p>
        </div>
      </motion.div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Pie Chart */}
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={3}
                dataKey="amount"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              <Legend
                formatter={(value: string) => (
                  <span className="text-sm text-slate-600 dark:text-slate-400">{value}</span>
                )}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Breakdown List */}
        <div className="space-y-3">
          {chartData.map((item, i) => (
            <motion.div
              key={item.name}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.1 }}
              className="flex items-center justify-between p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50"
            >
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                <div>
                  <p className="text-sm font-medium text-slate-700 dark:text-slate-300">{item.label}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">{breakdown[item.name as keyof BudgetBreakdown].description}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-semibold text-slate-900 dark:text-white">{INR(item.amount)}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400">{item.percentage}%</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Optimization Tips */}
      {optimization_tips && optimization_tips.length > 0 && (
        <div className="mt-6 p-4 rounded-xl bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-100 dark:border-indigo-800">
          <h4 className="text-sm font-semibold text-indigo-700 dark:text-indigo-300 mb-2">💡 Optimization Tips</h4>
          <ul className="space-y-1">
            {optimization_tips.map((tip, i) => (
              <li key={i} className="text-sm text-indigo-600 dark:text-indigo-400">• {tip}</li>
            ))}
          </ul>
        </div>
      )}
    </Card>
  );
}

