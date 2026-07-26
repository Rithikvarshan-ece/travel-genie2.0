import React from 'react';
import { Heart, Github } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="relative z-10 border-t border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center space-x-2 mb-3">
              <span className="text-lg font-bold bg-gradient-to-r from-indigo-600 to-purple-600 dark:from-indigo-400 dark:to-purple-400 bg-clip-text text-transparent">
                TravelGenie
              </span>
            </div>
            <p className="text-sm text-slate-600 dark:text-slate-400 max-w-md">
              Your AI-powered travel companion. Smart budget planning, personalized itineraries, 
              and intelligent recommendations powered by a multi-agent AI system.
            </p>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3">Quick Links</h3>
            <ul className="space-y-2">
              <li><a href="/" className="text-sm text-slate-600 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400">Home</a></li>
              <li><a href="/plan" className="text-sm text-slate-600 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400">Plan Trip</a></li>
              <li><a href="/about" className="text-sm text-slate-600 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400">About</a></li>
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3">Powered By</h3>
            <ul className="space-y-2">
              <li className="text-sm text-slate-600 dark:text-slate-400">React + TypeScript</li>
              <li className="text-sm text-slate-600 dark:text-slate-400">Python FastAPI</li>
              <li className="text-sm text-slate-600 dark:text-slate-400">Multi-Agent AI</li>
            </ul>
          </div>
        </div>
        <div className="mt-8 pt-6 border-t border-slate-200 dark:border-slate-700 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-slate-500 dark:text-slate-500">
            Copyright {new Date().getFullYear()} TravelGenie. Made with <Heart className="inline-block w-3 h-3 text-red-500 fill-red-500" /> for travelers.
          </p>
          <div className="flex items-center space-x-4">
            <a href="#" className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors">
              <Github className="w-4 h-4" />
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
