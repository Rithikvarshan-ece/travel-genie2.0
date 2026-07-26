import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Clock, DollarSign, MapPin, Lightbulb } from 'lucide-react';
import type { Attraction } from '@/types/travel';

interface AttractionCardProps {
  data: { attractions: Attraction[]; daily_breakdown: any[] };
}

export default function AttractionCard({ data }: AttractionCardProps) {
  const { attractions, daily_breakdown } = data;

  if (!attractions || attractions.length === 0) {
    return (
      <Card glass className="p-6">
        <p className="text-slate-500 dark:text-slate-400">Attractions data not available</p>
      </Card>
    );
  }

  return (
    <Card glass className="p-6">
      <div className="mb-6">
        <h3 className="text-xl font-bold text-slate-900 dark:text-white">Top Attractions</h3>
        <p className="text-sm text-slate-500 dark:text-slate-400">{attractions.length} attractions to explore</p>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        {attractions.map((attr, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.05 }}
            className="p-4 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover-card"
          >
            <div className="flex items-start justify-between mb-2">
              <div>
                <h4 className="font-semibold text-slate-900 dark:text-white">{attr.name}</h4>
                <Badge variant="info" size="sm">{attr.type}</Badge>
              </div>
              {attr.cost && (
                <span className="text-sm font-medium text-indigo-600 dark:text-indigo-400">
                  {attr.cost}
                </span>
              )}
            </div>

            <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">{attr.description}</p>

            <div className="flex flex-wrap gap-3 text-xs text-slate-500 dark:text-slate-400">
              {attr.duration && (
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {attr.duration}
                </span>
              )}
              {attr.best_time && (
                <span className="flex items-center gap-1">
                  <MapPin className="w-3 h-3" />
                  Best: {attr.best_time}
                </span>
              )}
              {attr.time && (
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {attr.time}
                </span>
              )}
            </div>

            {attr.tips && (
              <div className="mt-2 p-2 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-100 dark:border-amber-800">
                <p className="text-xs text-amber-700 dark:text-amber-300 flex items-start gap-1">
                  <Lightbulb className="w-3 h-3 mt-0.5 flex-shrink-0" />
                  {attr.tips}
                </p>
              </div>
            )}
          </motion.div>
        ))}
      </div>

      {/* Daily Breakdown */}
      {daily_breakdown && daily_breakdown.length > 0 && (
        <div className="mt-6">
          <h4 className="text-lg font-semibold text-slate-900 dark:text-white mb-3">Daily Schedule</h4>
          <div className="space-y-3">
            {daily_breakdown.map((day: any, i: number) => (
              <div key={i} className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
                <p className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                  Day {day.day || i + 1} — {day.theme || 'Exploration'}
                </p>
                <div className="flex flex-wrap gap-2">
                  {day.attractions?.map((a: any, j: number) => (
                    <Badge key={j} variant="default" size="sm">{a.name || a}</Badge>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}

