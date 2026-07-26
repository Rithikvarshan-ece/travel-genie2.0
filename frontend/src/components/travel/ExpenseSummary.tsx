import React from 'react';
import { motion } from 'framer-motion';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { DollarSign, TrendingUp, PiggyBank, AlertTriangle } from 'lucide-react';
import type { ExpenseData } from '@/types/travel';

interface ExpenseSummaryProps {
  data: ExpenseData;
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white dark:bg-slate-800 p-3 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700">
        <p className="font-semibold text-slate-900 dark:text-white">{data.label}</p>
        <p className="text-sm text-slate-600 dark:text-slate-400">${data.amount.toFixed(2)}</p>
        <p className="text-sm text-slate-500 dark:text-slate-500">{data.percentage}%</p>
      </div>
    );
  }
  return null;
};

export default function ExpenseSummary({ data }: ExpenseSummaryProps) {
  const { 
    total_budget, total_cost, remaining_budget, 
    budget_utilization_percentage, expense_breakdown, 
    chart_data, budget_status, saving_tips 
  } = data;

  if (!expense_breakdown) {
    return (
      <Card glass className="p-6">
        <p className="text-slate-500 dark:text-slate-400">Expense data not available</p>
      </Card>
    );
  }

  const chartItems = chart_data?.labels?.map((label, i) => ({
    label,
    amount: chart_data.datasets[0].data[i],
    color: chart_data.datasets[0].backgroundColor[i],
    percentage: ((chart_data.datasets[0].data[i] / total_cost) * 100).toFixed(1),
  })) || [];

  const statusColors: Record<string, string> = {
    green: 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800',
    blue: 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800',
    yellow: 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800',
    red: 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800',
  };

  return (
    <Card glass className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-slate-900 dark:text-white">Expense Summary</h3>
          <p className="text-sm text-slate-500 dark:text-slate-400">Budget utilization: {budget_utilization_percentage}%</p>
        </div>
        {budget_status && (
          <div className={`px-3 py-1.5 rounded-lg border text-sm font-medium ${statusColors[budget_status.color] || statusColors.green}`}>
            {budget_status.message}
          </div>
        )}
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 text-center">
          <DollarSign className="w-5 h-5 text-indigo-500 mx-auto mb-1" />
          <p className="text-2xl font-bold text-slate-900 dark:text-white">${total_cost.toFixed(0)}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400">Total Cost</p>
        </div>
        <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 text-center">
          <PiggyBank className="w-5 h-5 text-green-500 mx-auto mb-1" />
          <p className="text-2xl font-bold text-green-600 dark:text-green-400">${remaining_budget.toFixed(0)}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400">Remaining</p>
        </div>
        <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 text-center">
          <TrendingUp className="w-5 h-5 text-blue-500 mx-auto mb-1" />
          <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{budget_utilization_percentage}%</p>
          <p className="text-xs text-slate-500 dark:text-slate-400">Used</p>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Pie Chart */}
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartItems}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={3}
                dataKey="amount"
              >
                {chartItems.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Breakdown List */}
        <div className="space-y-2">
          {chartItems.map((item, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.1 }}
              className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/50"
            >
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                <span className="text-sm text-slate-700 dark:text-slate-300">{item.label}</span>
              </div>
              <div className="text-right">
                <span className="text-sm font-semibold text-slate-900 dark:text-white">${item.amount.toFixed(0)}</span>
                <span className="text-xs text-slate-400 ml-1">({item.percentage}%)</span>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Saving Tips */}
      {saving_tips && saving_tips.length > 0 && (
        <div className="mt-6 p-4 rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-100 dark:border-green-800">
          <h4 className="text-sm font-semibold text-green-700 dark:text-green-300 mb-2">💰 Money Saving Tips</h4>
          <div className="grid md:grid-cols-2 gap-1">
            {saving_tips.map((tip, i) => (
              <p key={i} className="text-sm text-green-600 dark:text-green-400">• {tip}</p>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}

