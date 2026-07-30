// TravelGenie TypeScript Types

export interface TravelFormData {
  budget: number;
  source_city: string;
  destination_city?: string;
  trip_days: number;
  travel_type: 'solo' | 'family' | 'couple' | 'friends';
  transportation: 'flight' | 'train' | 'bus' | 'car';
  interests: string[];
  hotel_preference: 'budget' | 'luxury' | 'hostel' | 'resort';
  travel_month: string;
}

export interface Destination {
  name: string;
  country: string;
  continent: string;
  season: string[];
  popularity: number;
  avg_daily_cost: number;
  interests: string[];
  description: string;
  latitude: number;
  longitude: number;
  currency: string;
  language: string;
  best_months: string;
  image?: string;
  score?: number;
  estimated_total_cost?: number;
  budget_fit?: string;
  match_reason?: string;
}

export interface BudgetBreakdown {
  hotel: { amount: number; percentage: number; description: string; per_night: number };
  food: { amount: number; percentage: number; description: string; per_day: number };
  activities: { amount: number; percentage: number; description: string; per_day: number };
  transport: { amount: number; percentage: number; description: string; per_trip: number };
  emergency: { amount: number; percentage: number; description: string; per_day: number };
}

export interface WeatherForecast {
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

export interface TransportOption {
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

export interface Hotel {
  name: string;
  destination: string;
  category: string;
  price_per_night: number;
  rating: number;
  reviews: number;
  amenities: string[];
  latitude: number;
  longitude: number;
  distance_from_center: number;
  description: string;
  score?: number;
  value_rating?: string;
  recommended_for?: string;
}

export interface Attraction {
  name: string;
  type: string;
  duration: string;
  cost: string;
  description: string;
  best_time: string;
  tips: string;
  time?: string;
}

export interface DayPlan {
  day: number;
  title: string;
  date: string;
  weather?: WeatherForecast;
  hotel: string;
  slots: TimeSlot[];
  daily_cost_estimate: number;
  highlights: string[];
}

export interface TimeSlot {
  slot: string;
  icon: string;
  label: string;
  hours: string;
  activities: Activity[];
  weather_note?: string;
}

export interface Activity {
  activity: string;
  icon: string;
  description: string;
  duration: string;
  cost: string;
}

export interface ExpenseData {
  total_budget: number;
  total_cost: number;
  remaining_budget: number;
  budget_utilization_percentage: number;
  expense_breakdown: Record<string, ExpenseCategory>;
  chart_data: ChartData;
  budget_status: BudgetStatus;
  saving_tips?: string[];
}

export interface ExpenseCategory {
  amount: number;
  percentage: number;
  color: string;
  label: string;
}

export interface ChartData {
  type: string;
  labels: string[];
  datasets: ChartDataset[];
}

export interface ChartDataset {
  data: number[];
  backgroundColor: string[];
  borderColor: string[];
  borderWidth: number;
}

export interface BudgetStatus {
  status: string;
  message: string;
  color: string;
}

export interface TravelPlan {
  plan_id: number;
  generation_time_seconds: number;
  agent_performance?: Record<string, { duration_s: number; confidence_pct: number; apis_used: string[] }>;
  why_reasons?: string[];
  user_input: TravelFormData;
  agents: {
    planner: any;
    trip_feasibility: {
      is_feasible: boolean;
      daily_budget: number;
      budget_allocation: Record<string, number>;
      budget_level: string;
      total_budget: number;
      breakdown: BudgetBreakdown;
      optimization_tips: string[];
      warnings: string[];
      reasoning: string;
      confidence_score: number;
    };
    destination: {
      suggestions: Destination[];
      weather: {
        forecast: WeatherForecast[];
        warnings: string[];
        activity_suggestions: { indoor: string[]; outdoor: string[]; note: string };
        weather_summary: string;
      };
      hotels: Hotel[];
      top_pick: Hotel;
      attractions: Attraction[];
      daily_breakdown: any[];
    };
    route_logistics: {
      source: string;
      destination: string;
      travel_distance_km: number;
      travel_time_hours: number;
      transport_options: TransportOption[];
      best_option: TransportOption;
      recommended_mode: string;
    };
    schedule: {
      days: DayPlan[];
      summary: any;
      travel_tips: string[];
      packing_recommendations: string[];
    };
    validation: {
      is_valid: boolean;
      budget_within_limit: boolean;
      total_cost: number;
      remaining_budget: number;
      budget_utilization_percentage: number;
      confidence_score: number;
      issues: any[];
      recommendations: string[];
      expense_breakdown: Record<string, any>;
      chart_data: ChartData;
      budget_status: BudgetStatus;
      saving_tips: string[];
    };
  };
  status: string;
}

export interface AgentInfo {
  name: string;
  description: string;
  key: string;
}
