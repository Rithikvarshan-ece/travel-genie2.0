import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { 
  Brain, Sparkles, Globe, Wallet,
  Route, Calendar, BarChart3,
  Shield, ChevronRight,
  Users, Code, Zap, CheckCircle2
} from 'lucide-react';

const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 }
};

const agents = [
  { icon: Brain,    name: 'Planner Agent',           desc: 'Main coordinator that orchestrates the entire 6-agent travel planning pipeline',          color: 'text-indigo-500',  bg: 'bg-indigo-50 dark:bg-indigo-900/20'  },
  { icon: Wallet,   name: 'Trip Feasibility Agent',  desc: 'Validates trip feasibility and calculates optimal budget allocation across all categories', color: 'text-emerald-500', bg: 'bg-emerald-50 dark:bg-emerald-900/20' },
  { icon: Globe,    name: 'Destination Agent',       desc: 'Selects best destination using real-time weather, hotels, and attractions data',           color: 'text-blue-500',    bg: 'bg-blue-50 dark:bg-blue-900/20'      },
  { icon: Route,    name: 'Route & Logistics Agent', desc: 'Calculates travel distance, time, and compares all transport modes with cost analysis',    color: 'text-cyan-500',    bg: 'bg-cyan-50 dark:bg-cyan-900/20'      },
  { icon: Calendar, name: 'Schedule Agent',          desc: 'Creates detailed day-by-day itinerary with time-slot activities and meal recommendations',  color: 'text-orange-500',  bg: 'bg-orange-50 dark:bg-orange-900/20'  },
  { icon: BarChart3,name: 'Validation Agent',        desc: 'Validates the complete plan, checks budget compliance, and triggers self-correction if needed', color: 'text-red-500',  bg: 'bg-red-50 dark:bg-red-900/20'        },
];

const features = [
  { icon: Zap, title: 'Instant Planning', desc: 'Get a complete travel plan in seconds, not hours' },
  { icon: Shield, title: 'Budget Smart', desc: 'Optimized budget allocation ensuring you get the best value' },
  { icon: Users, title: 'Personalized', desc: 'Tailored recommendations based on your unique preferences' },
  { icon: Code, title: 'Multi-Agent AI', desc: '6 specialized AI agents collaborate for comprehensive planning' },
];

export default function AboutPage() {
  return (
    <div className="min-h-screen px-4 py-12">
      <motion.div initial="initial" animate="animate" className="max-w-5xl mx-auto">
        {/* Hero */}
        <div className="text-center mb-16">
          <motion.div variants={fadeInUp} className="inline-flex items-center px-4 py-2 rounded-full bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300 text-sm font-medium mb-4">
            <Sparkles className="w-4 h-4 mr-2" />
            Multi-Agent AI Travel Planner
          </motion.div>
          <motion.h1 variants={fadeInUp} className="text-4xl md:text-5xl font-extrabold text-slate-900 dark:text-white mb-4">
            About <span className="text-gradient">TravelGenie</span>
          </motion.h1>
          <motion.p variants={fadeInUp} className="text-lg text-slate-600 dark:text-slate-400 max-w-3xl mx-auto">
            TravelGenie is an intelligent travel planning platform powered by a multi-agent AI system.
            Six specialized agents work together to create personalized, budget-friendly travel itineraries
            that adapt to your unique preferences.
          </motion.p>
        </div>

        {/* How It Works */}
        <motion.div variants={fadeInUp} className="mb-16">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white text-center mb-8">How It Works</h2>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { step: '1', title: 'Share Preferences', desc: 'Tell us your budget, destination preferences, interests, and travel style.' },
              { step: '2', title: 'AI Agents Collaborate', desc: 'Six specialized agents analyze budget, destination, weather, transport, hotels, and schedule.' },
              { step: '3', title: 'Get Your Plan', desc: 'Receive a comprehensive itinerary with daily schedules, expenses, and tips.' },
            ].map((item, i) => (
              <Card key={i} glass className="p-6 text-center">
                <div className="w-12 h-12 rounded-full bg-indigo-100 dark:bg-indigo-900/50 flex items-center justify-center mx-auto mb-4">
                  <span className="text-xl font-bold text-indigo-600 dark:text-indigo-400">{item.step}</span>
                </div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">{item.title}</h3>
                <p className="text-sm text-slate-600 dark:text-slate-400">{item.desc}</p>
              </Card>
            ))}
          </div>
        </motion.div>

        {/* Agent System */}
        <motion.div variants={fadeInUp} className="mb-16">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">The Multi-Agent System</h2>
            <p className="text-slate-600 dark:text-slate-400">Six specialized AI agents working in harmony</p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agents.map((agent, i) => {
              const Icon = agent.icon;
              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.05 }}
                  className={`p-4 rounded-xl ${agent.bg} border border-slate-200 dark:border-slate-700`}
                >
                  <div className="flex items-start gap-3">
                    <Icon className={`w-5 h-5 ${agent.color} mt-1`} />
                    <div>
                      <h4 className="font-semibold text-slate-900 dark:text-white text-sm">{agent.name}</h4>
                      <p className="text-xs text-slate-600 dark:text-slate-400">{agent.desc}</p>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </motion.div>

        {/* Features */}
        <motion.div variants={fadeInUp} className="mb-16">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white text-center mb-8">Key Features</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {features.map((feature, i) => {
              const Icon = feature.icon;
              return (
                <Card key={i} glass className="p-5 text-center">
                  <div className="w-12 h-12 rounded-xl bg-indigo-100 dark:bg-indigo-900/50 flex items-center justify-center mx-auto mb-3">
                    <Icon className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
                  </div>
                  <h3 className="font-semibold text-slate-900 dark:text-white mb-1">{feature.title}</h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400">{feature.desc}</p>
                </Card>
              );
            })}
          </div>
        </motion.div>

        {/* Tech Stack */}
        <motion.div variants={fadeInUp} className="mb-16">
          <Card glass className="p-8 text-center">
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">Built With</h2>
            <div className="flex flex-wrap justify-center gap-3">
              {[
                { name: 'React', color: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' },
                { name: 'TypeScript', color: 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300' },
                { name: 'Tailwind CSS', color: 'bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300' },
                { name: 'Framer Motion', color: 'bg-pink-100 dark:bg-pink-900/30 text-pink-700 dark:text-pink-300' },
                { name: 'Python', color: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300' },
                { name: 'FastAPI', color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' },
                { name: 'SQLite', color: 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300' },
                { name: 'Recharts', color: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300' },
              ].map((tech, i) => (
                <Badge key={i} variant="default" size="md" className={tech.color}>
                  {tech.name}
                </Badge>
              ))}
            </div>
          </Card>
        </motion.div>

        {/* CTA */}
        <motion.div variants={fadeInUp} className="text-center">
          <Card glass className="p-8 gradient-primary">
            <h2 className="text-2xl font-bold text-white mb-2">Ready to Plan Your Trip?</h2>
            <p className="text-indigo-100 mb-6">Let our AI agents create the perfect itinerary for you.</p>
            <Link
              to="/plan"
              className="inline-flex items-center px-8 py-4 rounded-xl bg-white text-indigo-700 font-semibold text-lg shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300"
            >
              Get Started <ChevronRight className="w-5 h-5 ml-2" />
            </Link>
          </Card>
        </motion.div>
      </motion.div>
    </div>
  );
}
