import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { CloudSun, CloudRain, Cloud, Sun, Thermometer, Wind, Droplets, Eye, ChevronDown, ChevronUp, AlertTriangle } from 'lucide-react';

interface WeatherForecast {
  day: number; date?: string; day_name?: string;
  condition: string; temperature_c: number; temperature_f?: number;
  humidity: number; wind_speed_kmh: number; precipitation_chance: number;
  icon?: string; recommendation?: string;
}
interface WeatherData {
  forecast?: WeatherForecast[];
  warnings?: string[];
  activity_suggestions?: { indoor?: string[]; outdoor?: string[]; note?: string };
  weather_summary?: string;
}
interface WeatherCardProps { data: WeatherData; }

function WeatherIcon({ condition, className }: { condition: string; className?: string }) {
  const c = (condition || '').toLowerCase();
  if (c.includes('rain') || c.includes('storm') || c.includes('drizzle')) return <CloudRain className={className} />;
  if (c.includes('cloud') || c.includes('overcast') || c.includes('partly')) return <CloudSun className={className} />;
  if (c.includes('sun') || c.includes('clear')) return <Sun className={className} />;
  return <Cloud className={className} />;
}

function tempColor(t: number) {
  if (t >= 35) return 'text-red-500';
  if (t >= 25) return 'text-orange-500';
  if (t >= 15) return 'text-amber-500';
  return 'text-blue-500';
}

function conditionBg(condition: string) {
  const c = (condition || '').toLowerCase();
  if (c.includes('rain') || c.includes('storm')) return 'from-blue-600 to-slate-700';
  if (c.includes('cloud') || c.includes('overcast')) return 'from-slate-500 to-slate-700';
  if (c.includes('sun') || c.includes('clear')) return 'from-amber-400 to-orange-500';
  return 'from-indigo-500 to-blue-600';
}

export default function WeatherCard({ data }: WeatherCardProps) {
  const [showTips, setShowTips] = useState(false);

  // Gracefully handle missing data
  const forecast = data?.forecast ?? [];
  const warnings = data?.warnings ?? [];
  const suggestions = data?.activity_suggestions;
  const summary = data?.weather_summary ?? 'Weather information for your trip';

  if (!data || forecast.length === 0) {
    return (
      <Card glass className="p-6">
        <div className="flex items-center gap-3 mb-4">
          <CloudSun className="w-6 h-6 text-indigo-500" />
          <h3 className="text-xl font-bold text-slate-900 dark:text-white">Weather Forecast</h3>
        </div>
        <div className="p-4 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0" />
          <p className="text-sm text-amber-700 dark:text-amber-300">
            Live weather data unavailable. Add an OpenWeatherMap API key to enable real-time forecasts.
          </p>
        </div>
      </Card>
    );
  }

  const primary = forecast[0];

  return (
    <Card glass className="p-6 overflow-hidden">
      {/* Header with live condition */}
      <motion.div
        initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
        className={`-mx-6 -mt-6 mb-6 p-6 bg-gradient-to-br ${conditionBg(primary.condition)} text-white`}
      >
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-white/70 mb-1">Current Conditions</p>
            <h3 className="text-xl font-bold">Weather Forecast</h3>
            <p className="text-sm text-white/80 mt-1">{summary}</p>
          </div>
          <div className="text-right">
            <motion.div animate={{ rotate: [0, 5, -5, 0] }} transition={{ repeat: Infinity, duration: 4 }}>
              <WeatherIcon condition={primary.condition} className="w-14 h-14 text-white/90 ml-auto" />
            </motion.div>
            <p className={`text-3xl font-bold mt-1`}>{primary.temperature_c}°C</p>
            <p className="text-sm text-white/70 capitalize">{primary.condition}</p>
          </div>
        </div>

        {/* Quick stats */}
        <div className="grid grid-cols-3 gap-3 mt-4">
          {[
            { icon: Droplets, label: 'Humidity', value: `${primary.humidity}%` },
            { icon: Wind, label: 'Wind', value: `${primary.wind_speed_kmh} km/h` },
            { icon: Eye, label: 'Rain', value: `${primary.precipitation_chance}%` },
          ].map(({ icon: Icon, label, value }) => (
            <div key={label} className="bg-white/10 rounded-xl p-2 text-center">
              <Icon className="w-4 h-4 mx-auto mb-1 text-white/80" />
              <p className="text-xs text-white/60">{label}</p>
              <p className="text-sm font-semibold">{value}</p>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Warnings */}
      <AnimatePresence>
        {warnings.length > 0 && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}
            className="mb-4 p-3 rounded-xl bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800">
            <p className="text-sm font-semibold text-yellow-700 dark:text-yellow-300 mb-1">⚠️ Weather Alerts</p>
            {warnings.map((w, i) => <p key={i} className="text-sm text-yellow-600 dark:text-yellow-400">• {w}</p>)}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Multi-day forecast */}
      {forecast.length > 1 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2 mb-6">
          {forecast.map((day, i) => (
            <motion.div key={i}
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08 }}
              className="p-3 rounded-xl text-center bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 hover:border-indigo-300 dark:hover:border-indigo-600 transition-colors"
            >
              <p className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                {day.day_name || `Day ${day.day}`}
              </p>
              <WeatherIcon condition={day.condition} className="w-7 h-7 mx-auto mb-1 text-indigo-500" />
              <p className={`text-lg font-bold ${tempColor(day.temperature_c)}`}>{day.temperature_c}°C</p>
              <p className="text-xs text-slate-500 dark:text-slate-400 capitalize truncate">{day.condition}</p>
              <div className="flex justify-center gap-1 mt-1">
                <span className="text-xs text-blue-400 flex items-center"><Droplets className="w-2.5 h-2.5 mr-0.5" />{day.humidity}%</span>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Activity suggestions toggle */}
      {suggestions && (
        <div>
          <button onClick={() => setShowTips(p => !p)}
            className="w-full flex items-center justify-between p-3 rounded-xl bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-100 dark:border-indigo-800 text-sm font-semibold text-indigo-700 dark:text-indigo-300 hover:bg-indigo-100 dark:hover:bg-indigo-900/40 transition-colors">
            <span>🌤️ Activity Suggestions</span>
            {showTips ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
          <AnimatePresence>
            {showTips && (
              <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden">
                <div className="grid md:grid-cols-2 gap-3 mt-3">
                  <div className="p-3 rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-100 dark:border-green-800">
                    <p className="text-sm font-semibold text-green-700 dark:text-green-300 mb-2">🌿 Outdoor</p>
                    {suggestions.outdoor?.map((a, i) => <p key={i} className="text-sm text-green-600 dark:text-green-400">• {a}</p>)}
                  </div>
                  <div className="p-3 rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800">
                    <p className="text-sm font-semibold text-blue-700 dark:text-blue-300 mb-2">🏠 Indoor</p>
                    {suggestions.indoor?.map((a, i) => <p key={i} className="text-sm text-blue-600 dark:text-blue-400">• {a}</p>)}
                  </div>
                </div>
                {suggestions.note && <p className="mt-2 text-xs text-slate-500 dark:text-slate-400 italic">{suggestions.note}</p>}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* Per-day recommendations */}
      {forecast.some(d => d.recommendation) && (
        <div className="mt-4 space-y-2">
          {forecast.filter(d => d.recommendation).map((day, i) => (
            <motion.div key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.1 }}
              className="p-2 rounded-lg bg-slate-50 dark:bg-slate-800/50 flex items-start gap-2">
              <Badge variant="info" size="sm">Day {day.day}</Badge>
              <p className="text-xs text-slate-600 dark:text-slate-400">{day.recommendation}</p>
            </motion.div>
          ))}
        </div>
      )}
    </Card>
  );
}
