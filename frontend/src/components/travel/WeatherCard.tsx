import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { CloudSun, CloudRain, Cloud, Sun, Thermometer, Wind, Droplets } from 'lucide-react';

interface WeatherForecast {
  day: number;
  date: string;
  day_name: string;
  condition: string;
  temperature_c: number;
  temperature_f: number;
  humidity: number;
  wind_speed_kmh: number;
  precipitation_chance: number;
  icon: string;
  recommendation: string;
}

interface WeatherData {
  forecast: WeatherForecast[];
  warnings: string[];
  activity_suggestions: { indoor: string[]; outdoor: string[]; note: string };
  weather_summary: string;
}

interface WeatherCardProps {
  data: WeatherData;
}

function getWeatherIcon(condition: string) {
  const c = condition.toLowerCase();
  if (c.includes('rain') || c.includes('storm') || c.includes('drizzle')) return CloudRain;
  if (c.includes('cloud') || c.includes('overcast')) return Cloud;
  if (c.includes('sun') || c.includes('clear')) return Sun;
  return CloudSun;
}

function getWeatherColor(condition: string) {
  const c = condition.toLowerCase();
  if (c.includes('rain') || c.includes('storm')) return 'blue';
  if (c.includes('cloud') || c.includes('overcast')) return 'slate';
  if (c.includes('sun') || c.includes('clear')) return 'amber';
  return 'indigo';
}

export default function WeatherCard({ data }: WeatherCardProps) {
  const { forecast, warnings, activity_suggestions, weather_summary } = data;

  if (!forecast || forecast.length === 0) {
    return (
      <Card glass className="p-6">
        <p className="text-slate-500 dark:text-slate-400">Weather data not available</p>
      </Card>
    );
  }

  return (
    <Card glass className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-slate-900 dark:text-white">Weather Forecast</h3>
          <p className="text-sm text-slate-500 dark:text-slate-400">{weather_summary}</p>
        </div>
        {warnings && warnings.length > 0 && (
          <Badge variant="warning" size="md">
            ⚠️ {warnings.length} warning{warnings.length > 1 ? 's' : ''}
          </Badge>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
        {forecast.map((day, i) => {
          const WeatherIcon = getWeatherIcon(day.condition);
          const color = getWeatherColor(day.condition);
          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className={`p-3 rounded-xl text-center bg-${color}-50 dark:bg-${color}-900/20 border border-${color}-100 dark:border-${color}-800`}
            >
              <p className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                {day.day_name || `Day ${day.day}`}
              </p>
              <WeatherIcon className={`w-8 h-8 mx-auto mb-1 text-${color}-500`} />
              <p className="text-lg font-bold text-slate-900 dark:text-white">
                {day.temperature_c}°C
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400 capitalize">{day.condition}</p>
              <div className="flex items-center justify-center gap-2 mt-1 text-xs text-slate-400">
                <span className="flex items-center"><Droplets className="w-3 h-3 mr-0.5" />{day.humidity}%</span>
                <span className="flex items-center"><Wind className="w-3 h-3 mr-0.5" />{day.wind_speed_kmh}km/h</span>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Weather Warnings */}
      {warnings && warnings.length > 0 && (
        <div className="mb-4 p-3 rounded-xl bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800">
          <p className="text-sm font-semibold text-yellow-700 dark:text-yellow-300 mb-1">⚠️ Weather Alerts</p>
          {warnings.map((w, i) => (
            <p key={i} className="text-sm text-yellow-600 dark:text-yellow-400">• {w}</p>
          ))}
        </div>
      )}

      {/* Activity Suggestions */}
      {activity_suggestions && (
        <div className="grid md:grid-cols-2 gap-4">
          <div className="p-3 rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-100 dark:border-green-800">
            <p className="text-sm font-semibold text-green-700 dark:text-green-300 mb-2">🌿 Outdoor Activities</p>
            <ul className="space-y-1">
              {activity_suggestions.outdoor?.map((a, i) => (
                <li key={i} className="text-sm text-green-600 dark:text-green-400">• {a}</li>
              ))}
            </ul>
          </div>
          <div className="p-3 rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800">
            <p className="text-sm font-semibold text-blue-700 dark:text-blue-300 mb-2">🏠 Indoor Activities</p>
            <ul className="space-y-1">
              {activity_suggestions.indoor?.map((a, i) => (
                <li key={i} className="text-sm text-blue-600 dark:text-blue-400">• {a}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Per-day recommendation */}
      {forecast.map((day, i) => day.recommendation && (
        <div key={i} className="mt-3 p-2 rounded-lg bg-slate-50 dark:bg-slate-800/50">
          <p className="text-xs text-slate-500 dark:text-slate-400">
            <span className="font-medium">Day {day.day}:</span> {day.recommendation}
          </p>
        </div>
      ))}
    </Card>
  );
}

