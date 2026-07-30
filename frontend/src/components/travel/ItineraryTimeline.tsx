import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { ChevronDown, ChevronUp, Sun, Sunset, Moon, Coffee, Thermometer, MapPin, IndianRupee } from 'lucide-react';
import type { DayPlan } from '@/types/travel';

const fmt = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 });
const INR = (v: number | undefined | null) => { const n = v ?? NaN; return isFinite(n) ? fmt.format(n * 83) : '₹N/A'; };
const toINR = (s: string) => s?.startsWith('$') ? fmt.format(parseFloat(s.replace('$', '')) * 83) : (s || '');

interface ItineraryTimelineProps {
  data: { days: DayPlan[]; summary?: any; travel_tips?: string[] };
}

const slotIcons: Record<string, React.ElementType> = { morning: Coffee, afternoon: Sun, evening: Sunset, night: Moon };
const slotGradients: Record<string, string> = {
  morning:   'from-amber-400 to-orange-400',
  afternoon: 'from-orange-400 to-red-400',
  evening:   'from-indigo-400 to-purple-500',
  night:     'from-purple-600 to-slate-700',
};

export default function ItineraryTimeline({ data }: ItineraryTimelineProps) {
  const days = data?.days ?? [];
  const summary = data?.summary;
  const travel_tips = data?.travel_tips ?? [];
  const [expandedDay, setExpandedDay] = useState<number>(days[0]?.day ?? 1);

  if (days.length === 0) {
    return (
      <Card glass className="p-6">
        <p className="text-slate-500 dark:text-slate-400">Itinerary data not available</p>
      </Card>
    );
  }

  return (
    <Card glass className="p-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
        <h3 className="text-xl font-bold text-slate-900 dark:text-white">Your Itinerary</h3>
        {summary && (
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            {summary.total_days} days • {summary.total_activities} activities
            {summary.estimated_total_cost ? ` • Est. ${INR(summary.estimated_total_cost)}` : ''}
          </p>
        )}
      </motion.div>

      {/* Day cards */}
      <div className="space-y-3">
        {days.map((day, dayIndex) => {
          const isOpen = expandedDay === day.day;
          return (
            <motion.div key={day.day}
              initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}
              transition={{ delay: dayIndex * 0.07 }}>

              {/* Day header */}
              <button onClick={() => setExpandedDay(isOpen ? -1 : day.day)}
                className="w-full flex items-center justify-between p-4 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 text-white hover:shadow-lg hover:scale-[1.01] transition-all">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center font-bold text-lg shrink-0">
                    {day.day}
                  </div>
                  <div className="text-left">
                    <p className="font-semibold">{day.title || `Day ${day.day}`}</p>
                    <div className="flex items-center gap-2 text-xs text-indigo-100 flex-wrap">
                      {day.date && <span>{day.date}</span>}
                      {day.daily_cost_estimate != null && day.daily_cost_estimate > 0 && (
                        <><span>•</span><span>{INR(day.daily_cost_estimate)} est.</span></>
                      )}
                      {day.hotel && <><span>•</span><span>🏨 {day.hotel}</span></>}
                    </div>
                  </div>
                </div>
                {isOpen ? <ChevronUp className="w-5 h-5 shrink-0" /> : <ChevronDown className="w-5 h-5 shrink-0" />}
              </button>

              {/* Expanded content */}
              <AnimatePresence>
                {isOpen && (
                  <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }} className="overflow-hidden">
                    <div className="pt-3 pb-1 px-1 space-y-3">

                      {/* Weather strip */}
                      {day.weather && (
                        <div className="flex items-center gap-3 p-3 rounded-xl bg-sky-50 dark:bg-sky-900/20 border border-sky-100 dark:border-sky-800 text-sm text-sky-700 dark:text-sky-300">
                          <Thermometer className="w-4 h-4 shrink-0" />
                          <span className="font-medium capitalize">{day.weather.condition}</span>
                          <span>{day.weather.temperature_c}°C</span>
                          <span className="text-xs text-sky-500">💧{day.weather.humidity}% 💨{day.weather.wind_speed_kmh}km/h</span>
                        </div>
                      )}

                      {/* Time slots */}
                      {(day.slots ?? []).map((slot, si) => {
                        const SlotIcon = slotIcons[slot.slot] || Sun;
                        const grad = slotGradients[slot.slot] || 'from-indigo-400 to-purple-500';
                        return (
                          <div key={si} className="relative pl-8 border-l-2 border-indigo-200 dark:border-indigo-800 ml-2">
                            {/* Timeline dot */}
                            <div className={`absolute -left-3 top-1 w-6 h-6 rounded-full bg-gradient-to-br ${grad} flex items-center justify-center shadow`}>
                              <SlotIcon className="w-3 h-3 text-white" />
                            </div>

                            <div className="mb-1 flex items-center gap-2">
                              <span className="text-sm font-semibold text-slate-700 dark:text-slate-300 capitalize">{slot.label || slot.slot}</span>
                              {slot.hours && <span className="text-xs text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-full">{slot.hours}</span>}
                            </div>

                            <div className="space-y-2">
                              {(slot.activities ?? []).map((act, ai) => (
                                <motion.div key={ai}
                                  initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}
                                  transition={{ delay: ai * 0.05 }}
                                  className="p-3 rounded-xl bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 shadow-sm hover:shadow-md transition-shadow">
                                  <div className="flex items-start justify-between gap-2">
                                    <div className="flex items-start gap-2 min-w-0">
                                      <span className="text-base shrink-0">{act.icon || '📍'}</span>
                                      <div className="min-w-0">
                                        <p className="text-sm font-medium text-slate-800 dark:text-slate-200 truncate">{act.activity}</p>
                                        {act.description && act.description !== act.activity && (
                                          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{act.description}</p>
                                        )}
                                      </div>
                                    </div>
                                    <div className="text-right shrink-0">
                                      {act.duration && <p className="text-xs text-slate-400">{act.duration}</p>}
                                      {act.cost && act.cost !== '₹0' && act.cost !== '$0' && (
                                        <p className="text-xs font-semibold text-indigo-600 dark:text-indigo-400">{toINR(act.cost)}</p>
                                      )}
                                    </div>
                                  </div>
                                </motion.div>
                              ))}
                            </div>
                          </div>
                        );
                      })}

                      {/* Highlights */}
                      {day.highlights && day.highlights.length > 0 && (
                        <div className="flex flex-wrap gap-2 pt-1">
                          {day.highlights.map((h, i) => (
                            <Badge key={i} variant="success" size="sm">✨ {h}</Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          );
        })}
      </div>

      {/* Travel Tips */}
      {travel_tips.length > 0 && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}
          className="mt-6 p-4 rounded-xl bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-100 dark:border-indigo-800">
          <h4 className="text-sm font-semibold text-indigo-700 dark:text-indigo-300 mb-3">🧳 Travel Tips</h4>
          <div className="grid md:grid-cols-2 gap-2">
            {travel_tips.map((tip, i) => (
              <p key={i} className="text-sm text-indigo-600 dark:text-indigo-400">• {tip}</p>
            ))}
          </div>
        </motion.div>
      )}
    </Card>
  );
}
