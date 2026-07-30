import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useApp } from '@/context/AppContext';
import { 
  Plane, Train, Bus, Car, Users, MapPin, 
  Calendar, IndianRupee, Sparkles, Loader2,
  Heart, TreePine, Utensils, ShoppingBag, 
  Landmark, Palmtree, Music, Building2,
  ChevronRight, AlertCircle
} from 'lucide-react';
import type { TravelFormData } from '@/types/travel';

const interestsList = [
  { value: 'nature', label: 'Nature', icon: TreePine },
  { value: 'adventure', label: 'Adventure', icon: Sparkles },
  { value: 'food', label: 'Food', icon: Utensils },
  { value: 'shopping', label: 'Shopping', icon: ShoppingBag },
  { value: 'historical', label: 'Historical', icon: Landmark },
  { value: 'beach', label: 'Beach', icon: Palmtree },
  { value: 'nightlife', label: 'Nightlife', icon: Music },
  { value: 'culture', label: 'Culture', icon: Building2 },
];

const travelTypes = [
  { value: 'solo', label: 'Solo', icon: Users },
  { value: 'couple', label: 'Couple', icon: Heart },
  { value: 'family', label: 'Family', icon: Users },
  { value: 'friends', label: 'Friends', icon: Users },
];

const transportOptions = [
  { value: 'flight', label: 'Flight', icon: Plane },
  { value: 'train', label: 'Train', icon: Train },
  { value: 'bus', label: 'Bus', icon: Bus },
  { value: 'car', label: 'Car', icon: Car },
];

const hotelOptions = [
  { value: 'budget', label: 'Budget' },
  { value: 'luxury', label: 'Luxury' },
  { value: 'hostel', label: 'Hostel' },
  { value: 'resort', label: 'Resort' },
];

const months = ['January','February','March','April','May','June',
  'July','August','September','October','November','December'];

export default function PlannerPage() {
  const navigate = useNavigate();
  const { isLoading, generatePlan, setError, error } = useApp();
  
  const [formData, setFormData] = useState<TravelFormData>({
    budget: 50000,
    source_city: '',
    trip_days: 3,
    travel_type: 'solo',
    transportation: 'flight',
    interests: [],
    hotel_preference: 'budget',
    travel_month: '',
  });

  const handleInterestToggle = (interest: string) => {
    setFormData(prev => ({
      ...prev,
      interests: prev.interests.includes(interest)
        ? prev.interests.filter(i => i !== interest)
        : [...prev.interests, interest]
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await generatePlan(formData);
      navigate('/results');
    } catch {
      // Error handled by context
    }
  };

  const updateField = <K extends keyof TravelFormData>(key: K, value: TravelFormData[K]) => {
    setFormData(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="min-h-screen px-4 py-12">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">Plan Your Dream Trip</h1>
          <p className="text-lg text-slate-600 dark:text-slate-400">
            Fill in your preferences and let our AI agents create the perfect itinerary
          </p>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 flex items-start">
            <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-8">
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                <IndianRupee className="w-4 h-4 inline mr-1" />Total Budget (INR)
              </label>
              <input type="number" value={formData.budget}
                onChange={e => updateField('budget', Number(e.target.value))}
                className="w-full px-4 py-3 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                min={1000} required />
            </div>
            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                <MapPin className="w-4 h-4 inline mr-1" />Source City
              </label>
              <input type="text" value={formData.source_city}
                onChange={e => updateField('source_city', e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                placeholder="e.g., New York, London, Mumbai" required />
            </div>
            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                <MapPin className="w-4 h-4 inline mr-1" />Destination City <span className="text-slate-400 font-normal">(optional)</span>
              </label>
              <input type="text" value={formData.destination_city ?? ''}
                onChange={e => updateField('destination_city', e.target.value || undefined)}
                className="w-full px-4 py-3 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                placeholder="e.g., Paris, Bali, Mumbai" />
            </div>
            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                <Calendar className="w-4 h-4 inline mr-1" />Number of Days
              </label>
              <input type="number" value={formData.trip_days}
                onChange={e => updateField('trip_days', Number(e.target.value))}
                className="w-full px-4 py-3 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                min={1} max={30} required />
            </div>
            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                <Calendar className="w-4 h-4 inline mr-1" />Travel Month
              </label>
              <select value={formData.travel_month}
                onChange={e => updateField('travel_month', e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all" required>
                <option value="">Select month</option>
                {months.map(m => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="space-y-3">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              <Users className="w-4 h-4 inline mr-1" />Travel Type
            </label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {travelTypes.map(type => (
                <button key={type.value} type="button"
                  onClick={() => updateField('travel_type', type.value as TravelFormData['travel_type'])}
                  className={"p-4 rounded-xl border-2 transition-all " + (
                    formData.travel_type === type.value 
                      ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300' 
                      : 'border-slate-200 dark:border-slate-700 hover:border-indigo-300 dark:hover:border-indigo-600'
                  )}>
                  <type.icon className="w-5 h-5 mx-auto mb-1" />
                  <div className="text-sm font-medium">{type.label}</div>
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Transportation</label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {transportOptions.map(t => (
                <button key={t.value} type="button"
                  onClick={() => updateField('transportation', t.value as TravelFormData['transportation'])}
                  className={"p-4 rounded-xl border-2 transition-all " + (
                    formData.transportation === t.value 
                      ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300' 
                      : 'border-slate-200 dark:border-slate-700 hover:border-indigo-300 dark:hover:border-indigo-600'
                  )}>
                  <t.icon className="w-5 h-5 mx-auto mb-1" />
                  <div className="text-sm font-medium">{t.label}</div>
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Interests</label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {interestsList.map(interest => {
                const Icon = interest.icon;
                const isSelected = formData.interests.includes(interest.value);
                return (
                  <button key={interest.value} type="button"
                    onClick={() => handleInterestToggle(interest.value)}
                    className={"p-4 rounded-xl border-2 transition-all " + (
                      isSelected 
                        ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300' 
                        : 'border-slate-200 dark:border-slate-700 hover:border-indigo-300 dark:hover:border-indigo-600'
                    )}>
                    <Icon className="w-5 h-5 mx-auto mb-1" />
                    <div className="text-sm font-medium">{interest.label}</div>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="space-y-3">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Hotel Preference</label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {hotelOptions.map(h => (
                <button key={h.value} type="button"
                  onClick={() => updateField('hotel_preference', h.value as TravelFormData['hotel_preference'])}
                  className={"p-4 rounded-xl border-2 transition-all " + (
                    formData.hotel_preference === h.value 
                      ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300' 
                      : 'border-slate-200 dark:border-slate-700 hover:border-indigo-300 dark:hover:border-indigo-600'
                  )}>
                  <div className="text-sm font-medium">{h.label}</div>
                </button>
              ))}
            </div>
          </div>

          <button type="submit" disabled={isLoading}
            className="w-full py-4 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold text-lg shadow-lg hover:shadow-xl hover:scale-[1.02] transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center">
            {isLoading ? (
              <><Loader2 className="w-5 h-5 mr-2 animate-spin" />AI Agents are planning your trip...</>
            ) : (
              <><Sparkles className="w-5 h-5 mr-2" />Generate My Travel Plan <ChevronRight className="w-5 h-5 ml-2" /></>
            )}
          </button>
        </form>
      </motion.div>
    </div>
  );
}
