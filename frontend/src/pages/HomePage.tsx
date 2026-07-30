import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Compass, Sparkles, Globe, Wallet, CloudSun, 
  Route, Hotel, MapPin, BarChart3, ChevronRight,
  Users, Brain, Shield, Download
} from 'lucide-react';

const fadeInUp = {
  initial: { opacity: 0, y: 30 },
  animate: { opacity: 1, y: 0 }
};

const stagger = {
  animate: {
    transition: { staggerChildren: 0.1 }
  }
};

export default function HomePage() {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden px-4 pt-20 pb-32">
        <div className="max-w-7xl mx-auto">
          <motion.div 
            initial="initial"
            animate="animate"
            variants={stagger}
            className="text-center"
          >
            <motion.div variants={fadeInUp} className="inline-flex items-center px-4 py-2 rounded-full bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300 text-sm font-medium mb-6">
              <Sparkles className="w-4 h-4 mr-2" />
              Powered by Multi-Agent AI
            </motion.div>

            <motion.h1 
              variants={fadeInUp}
              className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6"
            >
              <span className="text-gradient">TravelGenie</span>
              <br />
              <span className="text-slate-900 dark:text-white">Your AI Travel Planner</span>
            </motion.h1>

            <motion.p 
              variants={fadeInUp}
              className="text-xl text-slate-600 dark:text-slate-400 max-w-3xl mx-auto mb-10"
            >
              Experience the power of Agentic AI with 6 intelligent agents collaborating in real time
              to create your perfect personalized travel itinerary.
            </motion.p>

            <motion.div variants={fadeInUp} className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                to="/plan"
                className="group inline-flex items-center px-8 py-4 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold text-lg shadow-lg shadow-indigo-500/25 hover:shadow-xl hover:shadow-indigo-500/30 hover:scale-105 transition-all duration-300"
              >
                Start Planning
                <ChevronRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link
                to="/about"
                className="inline-flex items-center px-8 py-4 rounded-xl bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-semibold text-lg border border-slate-200 dark:border-slate-700 hover:border-indigo-300 dark:hover:border-indigo-600 hover:shadow-lg transition-all duration-300"
              >
                Learn More
              </Link>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="relative z-10 -mt-20 px-4 pb-20">
        <div className="max-w-7xl mx-auto">
          <motion.div 
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="grid grid-cols-2 md:grid-cols-4 gap-4"
          >
            {[
              { icon: Brain, label: 'Intelligent AI Agents', value: '6' },
              { icon: Globe, label: 'Worldwide Destinations', value: '50+' },
              { icon: Users, label: 'Travel Styles', value: '4' },
              { icon: Shield, label: 'Real-Time Planning', value: '100%' },
            ].map((stat, i) => (
              <div key={i} className="glass rounded-2xl p-6 text-center hover-card">
                <stat.icon className="w-8 h-8 text-indigo-600 dark:text-indigo-400 mx-auto mb-3" />
                <div className="text-2xl font-bold text-slate-900 dark:text-white">{stat.value}</div>
                <div className="text-sm text-slate-600 dark:text-slate-400">{stat.label}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* How It Works */}
      <section className="px-4 py-20 bg-white/50 dark:bg-slate-900/50">
        <div className="max-w-7xl mx-auto">
          <motion.div 
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">
              How It Works
            </h2>
            <p className="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
              Six intelligent AI agents collaborate to create your perfect trip
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              { step: '01', title: 'Tell Us Your Preferences', desc: 'Share your budget, destination preferences, interests, and travel style with our AI system.' },
              { step: '02', title: 'AI Agents Collaborate', desc: 'Six specialized agents analyze budget, destination, weather, transport, hotels, and schedule simultaneously.' },
              { step: '03', title: 'Get Your Perfect Plan', desc: 'Receive a comprehensive itinerary with maps, expenses, packing lists, and smart recommendations.' },
            ].map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.2 }}
                className="relative p-8 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover-card"
              >
                <div className="text-5xl font-black text-indigo-100 dark:text-indigo-900/50 mb-4">{item.step}</div>
                <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">{item.title}</h3>
                <p className="text-slate-600 dark:text-slate-400">{item.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="px-4 py-20">
        <div className="max-w-7xl mx-auto">
          <motion.div 
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">
              Everything You Need
            </h2>
            <p className="text-lg text-slate-600 dark:text-slate-400">
              From budget optimization to daily itineraries
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              { icon: Wallet, title: 'Budget Optimization', desc: 'Smart budget allocation across hotels, food, transport, activities, and emergencies.' },
              { icon: Globe, title: 'Smart Destinations', desc: 'AI-powered destination matching based on your interests, budget, and season.' },
              { icon: CloudSun, title: 'Weather Intelligence', desc: 'Real-time weather analysis with indoor/outdoor activity suggestions.' },
              { icon: Route, title: 'Transport Planning', desc: 'Compare flights, trains, buses, and rental cars with cost-time analysis.' },
              { icon: Hotel, title: 'Hotel Recommendations', desc: 'Personalized hotel suggestions based on budget, ratings, and location.' },
              { icon: MapPin, title: 'Attractions Guide', desc: 'Curated list of must-visit places with tips, timing, and cost estimates.' },
              { icon: BarChart3, title: 'Expense Tracking', desc: 'Detailed expense breakdown with pie charts and budget status.' },
              { icon: Download, title: 'PDF Export', desc: 'Download your complete travel plan as a PDF for offline access.' },
              { icon: Sparkles, title: 'AI Reasoning', desc: 'Step-by-step AI reasoning showing how each recommendation was made.' },
            ].map((feature, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.05 }}
                className="p-6 rounded-2xl glass hover-card"
              >
                <div className="w-12 h-12 rounded-xl bg-indigo-100 dark:bg-indigo-900/50 flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">{feature.title}</h3>
                <p className="text-sm text-slate-600 dark:text-slate-400">{feature.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-4 py-20">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="max-w-4xl mx-auto text-center p-12 rounded-3xl gradient-primary"
        >
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Ready to Plan Your Dream Trip?
          </h2>
          <p className="text-lg text-indigo-100 mb-8">
            Let our AI agents create the perfect itinerary for you in seconds.
          </p>
          <Link
            to="/plan"
            className="inline-flex items-center px-8 py-4 rounded-xl bg-white text-indigo-700 font-semibold text-lg shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300"
          >
            Get Started Now
            <ChevronRight className="w-5 h-5 ml-2" />
          </Link>
        </motion.div>
      </section>
    </div>
  );
}

