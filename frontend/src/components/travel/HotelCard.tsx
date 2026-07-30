import React from 'react';
import { motion } from 'framer-motion';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Star, MapPin, Wifi, Coffee, Car, Dumbbell, Waves, Shield } from 'lucide-react';
import type { Hotel } from '@/types/travel';

const INR = (v: number | string | undefined | null): string => {
  const n = typeof v === 'string' ? parseFloat(v) : (v ?? NaN);
  if (!isFinite(n)) return '₹N/A';
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n * 83);
};

interface HotelCardProps {
  data: { hotels: Hotel[]; top_pick: Hotel };
}

const amenityIcons: Record<string, React.ElementType> = {
  wifi: Wifi,
  breakfast: Coffee,
  parking: Car,
  gym: Dumbbell,
  pool: Waves,
  '24/7': Shield,
};

export default function HotelCard({ data }: HotelCardProps) {
  const { hotels, top_pick } = data;

  if (!hotels || hotels.length === 0) {
    return (
      <Card glass className="p-6">
        <p className="text-slate-500 dark:text-slate-400">Hotel data not available</p>
      </Card>
    );
  }

  return (
    <Card glass className="p-6">
      <div className="mb-6">
        <h3 className="text-xl font-bold text-slate-900 dark:text-white">Hotel Recommendations</h3>
        <p className="text-sm text-slate-500 dark:text-slate-400">{hotels.length} options found</p>
      </div>

      {/* Top Pick */}
      {top_pick && Object.keys(top_pick).length > 0 && (
        <div className="mb-6 p-4 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 text-white">
          <div className="flex items-center gap-2 mb-2">
            <Badge variant="purple" size="md">⭐ Top Pick</Badge>
          </div>
          <h4 className="text-lg font-bold mb-1">{top_pick.name}</h4>
          <p className="text-sm text-indigo-100 mb-2">
            <MapPin className="w-3 h-3 inline mr-1" />
            {top_pick.destination} • {top_pick.distance_from_center}km from center
          </p>
          <div className="flex items-center gap-4">
            <div className="flex items-center">
              <Star className="w-4 h-4 text-yellow-300 fill-yellow-300 mr-1" />
              <span className="font-semibold">{top_pick.rating}</span>
            </div>
            <span className="text-2xl font-bold">{INR(top_pick.price_per_night)}/night</span>
          </div>
        </div>
      )}

      {/* Hotel List */}
      <div className="space-y-4">
        {hotels.map((hotel, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700"
          >
            <div className="flex items-start justify-between mb-2">
              <div>
                <h4 className="font-semibold text-slate-900 dark:text-white">{hotel.name}</h4>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {hotel.destination} • {hotel.distance_from_center}km from center
                </p>
              </div>
              <div className="text-right">
                <p className="text-lg font-bold text-indigo-600 dark:text-indigo-400">
                  {INR(hotel.price_per_night)}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">per night</p>
              </div>
            </div>

            <div className="flex items-center gap-3 mb-2">
              <div className="flex items-center">
                <Star className="w-3 h-3 text-yellow-500 fill-yellow-500 mr-1" />
                <span className="text-sm text-slate-600 dark:text-slate-400">{hotel.rating}</span>
              </div>
              <Badge variant="default" size="sm">{hotel.category}</Badge>
              {hotel.value_rating && (
                <Badge variant="success" size="sm">{hotel.value_rating}</Badge>
              )}
            </div>

            {hotel.amenities && hotel.amenities.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {hotel.amenities.slice(0, 4).map((amenity, j) => {
                  const Icon = amenityIcons[amenity.toLowerCase()] || Shield;
                  return (
                    <span key={j} className="inline-flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
                      <Icon className="w-3 h-3" />
                      {amenity}
                    </span>
                  );
                })}
                {hotel.amenities.length > 4 && (
                  <span className="text-xs text-indigo-500">+{hotel.amenities.length - 4} more</span>
                )}
              </div>
            )}

            {hotel.description && (
              <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">{hotel.description}</p>
            )}
          </motion.div>
        ))}
      </div>
    </Card>
  );
}

