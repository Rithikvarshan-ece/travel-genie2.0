import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { 
  ChevronDown, ChevronUp, Sun, Sunset, Moon, Coffee,
  DollarSign, Thermometer, MapPin
} from 'lucide-react';
import type { DayPlan, TimeSlot, Activity } from '@/types/travel';

interface ItineraryTimelineProps {
  data: { days: DayPlan[]; summary: any; travel_tips: string[] };
}

const slotIcons: Record<string, React.ElementType> = {
  morning: Coffee,
  afternoon: Sun,
  evening: Sunset,
  night: Moon,
};

const slotColors: Record<string, string> = {
  morning: 'amber',
  afternoon: 'orange',
  evening: 'indigo',
  night: 'purple',
};

export default function ItineraryTimeline({ data }: ItineraryTimelineProps) {
  const { days, summary, travel_tips } = data;
  const [expandedDay, setExpandedDay] = useState<number>(1);

  if (!days || days.length === 0) {
    return (
      <Card glass className="p-6">
        <p className="text-slate-500 dark:text-slate-400">Itinerary data not available</p>
      </Card>
    );
  }

  return (
    <Card glass className="p-6">
      <div className="mb-6">
        <h3 className="text-xl font-bold text-slate-900 dark:text-white">Your Itinerary</h3>
        {summary && (
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {summary.total_days} days • {summary.total_activities} activities • Est. ${summary.estimated_total_cost}
          </p>
        )}
      </div>

      {/* Timeline */}
      <div className="relative">
        {days.map((day, dayIndex) => (
          <motion.div
            key={dayIndex}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: dayIndex * 0.1 }}
            className="mb-4 last:mb-0"
          >
            <div
              onClick={() => setExpandedDay(expandedDay === day.day ? -1 : day.day)}
              className="flex items-center justify-between p-4 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 text-white cursor-pointer hover:shadow-lg transition-shadow"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center font-bold text-lg">
                  {day.day}
                </div>
                <div>
                  <h4 className="font-semibold">{day.title || `Day ${day.day}`}</h4>
                  <div className="flex items-center gap-2 text-xs text-indigo-100">
                    <span>{day.date}</span>
                    {day.daily_cost_estimate && (
                      <>
                        <span>•</span>
                        <span>${day.daily_cost_estimate} est.</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
              {expandedDay === day.day ? (
                <ChevronUp className="w-5 h-5" />
              ) : (
                <ChevronDown className="w-5 h-5" />
              )}
            </div>

            <AnimatePresence>
              {expandedDay === day.day && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="overflow-hidden"
                >
                  <div className="p-4 space-y-3">
                    {/* Weather note */}
                    {day.weather && (
                      <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400 mb-2">
                        <Thermometer className="w-4 h-4" />
                        <span>
                          {day.weather.condition} • {day.weather.temperature_c}°C
                        </span>
                        <span className="text-xs">
                          (Humidity: {day.weather.humidity}% • Wind: {day.weather.wind_speed_kmh}km/h)
                        </span>
                      </div>
                    )}

                    {/* Hotel info */}
                    <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
                      <MapPin className="w-4 h-4" />
                      <span>Stay at: {day.hotel}</span>
                    </div>

                    {/* Time slots */}
                    {day.slots?.map((slot, slotIndex) => {
                      const SlotIcon = slotIcons[slot.slot] || Sun;
                      const color = slotColors[slot.slot] || 'indigo';
                      return (
                        <div key={slotIndex} className="relative pl-6 border-l-2 border-indigo-200 dark:border-indigo-800">
                          <div className={`absolute -left-2.5 top-0 w-5 h-5 rounded-full bg-${color}-100 dark:bg-${color}-900/50 flex items-center justify-center`}>
                            <SlotIcon className={`w-3 h-3 text-${color}-600 dark:text-${color}-400`} />
                          </div>
                          <div className="mb-1">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                                {slot.label}
                              </span>
                              <span className="text-xs text-slate-400">{slot.hours}</span>
                            </div>
                            {slot.weather_note && (
                              <p className="text-xs text-slate-500 dark:text-slate-400">{slot.weather_note}</p>
                            )}
                          </div>
                          <div className="space-y-2">
                            {slot.activities?.map((activity, actIndex) => (
                              <div key={actIndex} className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50">
                                <div className="flex items-start justify-between">
                                  <div className="flex items-center gap-2">
                                    <span className="text-lg">{activity.icon}</span>
                                    <div>
                                      <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                                        {activity.activity}
                                      </p>
                                      <p className="text-xs text-slate-500 dark:text-slate-400">
                                        {activity.description}
                                      </p>
                                    </div>
                                  </div>
                                  <div className="text-right text-xs text-slate-500 dark:text-slate-400">
                                    <p>{activity.duration}</p>
                                    <p className="text-indigo-600 dark:text-indigo-400 font-medium">{activity.cost}</p>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    })}

                    {/* Highlights */}
                    {day.highlights && day.highlights.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-2">
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
        ))}
      </div>

      {/* Travel Tips */}
      {travel_tips && travel_tips.length > 0 && (
        <div className="mt-6 p-4 rounded-xl bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-100 dark:border-indigo-800">
          <h4 className="text-sm font-semibold text-indigo-700 dark:text-indigo-300 mb-2">🧳 Travel Tips</h4>
          <div className="grid md:grid-cols-2 gap-2">
            {travel_tips.map((tip, i) => (
              <p key={i} className="text-sm text-indigo-600 dark:text-indigo-400">• {tip}</p>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}

