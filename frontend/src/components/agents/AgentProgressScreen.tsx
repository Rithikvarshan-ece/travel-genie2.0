import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain, Wallet, Globe, Route, Calendar, BarChart3,
  CheckCircle2, Loader2, Clock, Zap,
} from 'lucide-react';

interface AgentState {
  status: 'waiting' | 'running' | 'completed' | 'error';
  logs: string[];
  startedAt?: number;
  duration?: number;
  confidence_pct?: number;
  why_reasons?: string[];
}

const AGENTS = [
  { key: 'planner',          label: 'Planner Agent',           icon: Brain,    color: 'indigo'  },
  { key: 'trip_feasibility', label: 'Trip Feasibility Agent',  icon: Wallet,   color: 'emerald' },
  { key: 'destination',      label: 'Destination Agent',       icon: Globe,    color: 'blue'    },
  { key: 'route_logistics',  label: 'Route & Logistics Agent', icon: Route,    color: 'cyan'    },
  { key: 'schedule',         label: 'Schedule Agent',          icon: Calendar, color: 'orange'  },
  { key: 'validation',       label: 'Validation Agent',        icon: BarChart3,color: 'violet'  },
];

const C: Record<string, { ring: string; bg: string; text: string; badge: string }> = {
  indigo:  { ring: 'ring-indigo-400',  bg: 'bg-indigo-50 dark:bg-indigo-900/20',  text: 'text-indigo-600 dark:text-indigo-400',  badge: 'bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300'  },
  emerald: { ring: 'ring-emerald-400', bg: 'bg-emerald-50 dark:bg-emerald-900/20',text: 'text-emerald-600 dark:text-emerald-400',badge: 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300' },
  blue:    { ring: 'ring-blue-400',    bg: 'bg-blue-50 dark:bg-blue-900/20',      text: 'text-blue-600 dark:text-blue-400',      badge: 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300'           },
  cyan:    { ring: 'ring-cyan-400',    bg: 'bg-cyan-50 dark:bg-cyan-900/20',      text: 'text-cyan-600 dark:text-cyan-400',      badge: 'bg-cyan-100 dark:bg-cyan-900/40 text-cyan-700 dark:text-cyan-300'           },
  orange:  { ring: 'ring-orange-400',  bg: 'bg-orange-50 dark:bg-orange-900/20',  text: 'text-orange-600 dark:text-orange-400',  badge: 'bg-orange-100 dark:bg-orange-900/40 text-orange-700 dark:text-orange-300'   },
  violet:  { ring: 'ring-violet-400',  bg: 'bg-violet-50 dark:bg-violet-900/20',  text: 'text-violet-600 dark:text-violet-400',  badge: 'bg-violet-100 dark:bg-violet-900/40 text-violet-700 dark:text-violet-300'   },
};

interface Props {
  requestData: object;
  onComplete: (plan: any, generationTime: number) => void;
  onError: (msg: string) => void;
}

export default function AgentProgressScreen({ requestData, onComplete, onError }: Props) {
  const [agentStates, setAgentStates] = useState<Record<string, AgentState>>(() =>
    Object.fromEntries(AGENTS.map(a => [a.key, { status: 'waiting', logs: [] }]))
  );
  const [overallProgress, setOverallProgress] = useState(0);
  const [etaSeconds, setEtaSeconds] = useState<number | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;

    const run = async () => {
      try {
        const res = await fetch('/api/plan/stream', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestData),
        });

        if (!res.ok || !res.body) {
          const err = await res.json().catch(() => ({ message: 'Stream failed' }));
          onError(err.detail || err.message || 'Failed to start plan generation');
          return;
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (!cancelled) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() ?? '';

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            const raw = line.slice(6).trim();
            if (!raw) continue;
            try {
              const event = JSON.parse(raw);
              if (cancelled) break;

              if (event.type === 'complete') {
                setOverallProgress(100);
                onComplete(event.plan, event.generation_time_seconds);
                return;
              }
              if (event.type === 'error') {
                onError(event.message || 'Unknown error');
                return;
              }

              const { agent, status, log, progress, eta_seconds, confidence_pct, why_reasons } = event;
              if (progress !== undefined) setOverallProgress(progress);
              if (eta_seconds !== undefined) setEtaSeconds(eta_seconds);

              setAgentStates(prev => {
                const existing = prev[agent] ?? { status: 'waiting', logs: [] };
                return {
                  ...prev,
                  [agent]: {
                    status,
                    logs: log ? [...existing.logs, log] : existing.logs,
                    startedAt: existing.startedAt ?? (status === 'running' ? Date.now() : undefined),
                    duration: status === 'completed' && existing.startedAt
                      ? (Date.now() - existing.startedAt) / 1000
                      : existing.duration,
                    confidence_pct: confidence_pct ?? existing.confidence_pct,
                    why_reasons: why_reasons ?? existing.why_reasons,
                  },
                };
              });
            } catch { /* ignore malformed */ }
          }
        }
      } catch (e: any) {
        if (!cancelled) onError(e.message || 'Connection failed');
      }
    };

    run();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [agentStates]);

  const completedCount = AGENTS.filter(a => agentStates[a.key]?.status === 'completed').length;

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-2xl">

        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-6">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mx-auto mb-4 shadow-lg">
            <Brain className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">AI Agents Planning Your Trip</h2>
          <p className="text-slate-500 dark:text-slate-400 mt-1 text-sm">
            {completedCount} of {AGENTS.length} agents completed
          </p>
        </motion.div>

        {/* Progress bar + ETA */}
        <div className="mb-5">
          <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
            <span>Overall Progress</span>
            <span className="flex items-center gap-2">
              {etaSeconds !== null && etaSeconds > 0 && (
                <span className="flex items-center gap-1 text-indigo-500">
                  <Clock className="w-3 h-3" />~{etaSeconds}s remaining
                </span>
              )}
              <span>{overallProgress}%</span>
            </span>
          </div>
          <div className="h-2.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
              animate={{ width: `${overallProgress}%` }}
              transition={{ duration: 0.5, ease: 'easeOut' }}
            />
          </div>
        </div>

        {/* Agent cards */}
        <div className="space-y-2">
          {AGENTS.map((agent, idx) => {
            const state = agentStates[agent.key] ?? { status: 'waiting', logs: [] };
            const colors = C[agent.color];
            const Icon = agent.icon;
            const isActive = state.status === 'running';
            const isDone = state.status === 'completed';
            const isWaiting = state.status === 'waiting';

            return (
              <motion.div
                key={agent.key}
                initial={{ opacity: 0, x: -16 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.04 }}
                className={`rounded-xl border transition-all duration-300 overflow-hidden
                  ${isDone ? `${colors.bg} border-transparent` : ''}
                  ${isActive ? `${colors.bg} ring-2 ${colors.ring} border-transparent` : ''}
                  ${isWaiting ? 'bg-slate-50 dark:bg-slate-800/40 border-slate-200 dark:border-slate-700' : ''}
                `}
              >
                <div className="flex items-start gap-3 p-3">
                  {/* Status icon */}
                  <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5
                    ${isDone || isActive ? colors.bg : 'bg-slate-100 dark:bg-slate-700'}`}>
                    {isDone
                      ? <CheckCircle2 className={`w-5 h-5 ${colors.text}`} />
                      : isActive
                        ? <Loader2 className={`w-5 h-5 ${colors.text} animate-spin`} />
                        : <Icon className="w-5 h-5 text-slate-400 dark:text-slate-500" />
                    }
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <span className={`text-sm font-semibold
                        ${isDone || isActive ? 'text-slate-900 dark:text-white' : 'text-slate-400 dark:text-slate-500'}`}>
                        {agent.label}
                      </span>
                      <div className="flex items-center gap-1.5 flex-shrink-0">
                        {isDone && state.confidence_pct !== undefined && (
                          <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${colors.badge}`}>
                            <Zap className="w-2.5 h-2.5 inline mr-0.5" />{state.confidence_pct}%
                          </span>
                        )}
                        {isDone && state.duration && (
                          <span className="text-xs text-slate-400 flex items-center gap-0.5">
                            <Clock className="w-3 h-3" />{state.duration.toFixed(1)}s
                          </span>
                        )}
                        {isWaiting && <span className="text-xs text-slate-400">Waiting</span>}
                      </div>
                    </div>

                    {/* Logs — always show all, highlight last active */}
                    <AnimatePresence>
                      {state.logs.length > 0 && (
                        <div className="mt-1 space-y-0.5">
                          {state.logs.map((log, li) => {
                            const isLast = li === state.logs.length - 1;
                            return (
                              <motion.p
                                key={li}
                                initial={{ opacity: 0, y: 3 }}
                                animate={{ opacity: 1, y: 0 }}
                                className={`text-xs leading-relaxed
                                  ${isLast && isActive ? colors.text + ' font-medium' : 'text-slate-500 dark:text-slate-400'}`}
                              >
                                {isDone && isLast ? '✓ ' : isActive && isLast ? '● ' : '  '}
                                {log}
                              </motion.p>
                            );
                          })}
                        </div>
                      )}
                    </AnimatePresence>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>

        <div ref={logsEndRef} />
      </div>
    </div>
  );
}
