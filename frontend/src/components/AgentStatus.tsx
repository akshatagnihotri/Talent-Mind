'use client';
import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export interface AgentStepData {
  id: string;
  name: string;
  description: string;
  icon: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  duration?: number;
}

const DEFAULT_AGENTS: AgentStepData[] = [
  { id: '1', name: 'Document Parser', description: 'Extracting text and structure from resume', icon: '📄', status: 'pending' },
  { id: '2', name: 'Entity Extractor', description: 'Identifying skills, experience, education', icon: '🔍', status: 'pending' },
  { id: '3', name: 'ATS Scorer', description: 'Calculating ATS compatibility score', icon: '🎯', status: 'pending' },
  { id: '4', name: 'Skill Analyzer', description: 'Comparing skills vs job requirements', icon: '⚡', status: 'pending' },
  { id: '5', name: 'Job Matcher', description: 'Computing match percentage', icon: '🔗', status: 'pending' },
  { id: '6', name: 'Experience Validator', description: 'Validating years and seniority level', icon: '📅', status: 'pending' },
  { id: '7', name: 'Keyword Optimizer', description: 'Scanning for industry keywords', icon: '🔑', status: 'pending' },
  { id: '8', name: 'Candidate Ranker', description: 'Generating comparative ranking', icon: '🏆', status: 'pending' },
  { id: '9', name: 'Copilot Summarizer', description: 'Generating recruiter insights', icon: '🤖', status: 'pending' },
];

interface AgentStatusProps {
  agents?: AgentStepData[];
  autoRun?: boolean;
  onComplete?: () => void;
}

export default function AgentStatus({ agents = DEFAULT_AGENTS, autoRun = false, onComplete }: AgentStatusProps) {
  const [steps, setSteps] = useState<AgentStepData[]>(agents);
  const [running, setRunning] = useState(autoRun);
  const [currentIndex, setCurrentIndex] = useState(-1);

  const runPipeline = async () => {
    setRunning(true);
    setSteps(agents.map((a) => ({ ...a, status: 'pending' })));

    for (let i = 0; i < agents.length; i++) {
      setCurrentIndex(i);
      setSteps((prev) =>
        prev.map((s, idx) =>
          idx === i ? { ...s, status: 'running' } : s,
        ),
      );
      const delay = 800 + Math.random() * 600;
      await new Promise((r) => setTimeout(r, delay));
      setSteps((prev) =>
        prev.map((s, idx) =>
          idx === i ? { ...s, status: 'completed', duration: Math.round(delay) } : s,
        ),
      );
    }
    setRunning(false);
    setCurrentIndex(-1);
    onComplete?.();
  };

  useEffect(() => {
    if (autoRun) runPipeline();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoRun]);

  const completedCount = steps.filter((s) => s.status === 'completed').length;
  const progress = (completedCount / steps.length) * 100;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-white">AI Agent Pipeline</h3>
          <p className="text-sm text-slate-400">{completedCount}/{steps.length} agents completed</p>
        </div>
        {!autoRun && (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={runPipeline}
            disabled={running}
            className="btn-primary text-sm px-4 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {running ? '⏳ Running...' : '▶ Run Agents'}
          </motion.button>
        )}
      </div>

      {/* Overall progress bar */}
      <div className="progress-bar">
        <motion.div
          className="progress-fill"
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5 }}
          style={{ background: 'linear-gradient(90deg, #6366F1, #10B981)' }}
        />
      </div>

      {/* Agent steps */}
      <div className="space-y-2">
        {steps.map((step, i) => (
          <motion.div
            key={step.id}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
            className="flex items-center gap-3 px-4 py-3 rounded-xl transition-all"
            style={{
              background:
                step.status === 'running'
                  ? 'rgba(99,102,241,0.12)'
                  : step.status === 'completed'
                    ? 'rgba(16,185,129,0.06)'
                    : 'rgba(255,255,255,0.03)',
              border:
                step.status === 'running'
                  ? '1px solid rgba(99,102,241,0.3)'
                  : step.status === 'completed'
                    ? '1px solid rgba(16,185,129,0.15)'
                    : '1px solid rgba(255,255,255,0.04)',
              boxShadow: step.status === 'running' ? '0 0 20px rgba(99,102,241,0.15)' : 'none',
            }}
          >
            {/* Icon */}
            <div
              className="w-9 h-9 rounded-lg flex items-center justify-center text-lg flex-shrink-0"
              style={{
                background:
                  step.status === 'running'
                    ? 'rgba(99,102,241,0.2)'
                    : step.status === 'completed'
                      ? 'rgba(16,185,129,0.15)'
                      : 'rgba(255,255,255,0.05)',
              }}
            >
              {step.icon}
            </div>

            {/* Info */}
            <div className="flex-1 min-w-0">
              <p
                className="text-sm font-semibold truncate"
                style={{
                  color:
                    step.status === 'running'
                      ? '#818CF8'
                      : step.status === 'completed'
                        ? '#34D399'
                        : '#94A3B8',
                }}
              >
                {step.name}
              </p>
              <p className="text-xs text-slate-500 truncate">{step.description}</p>
            </div>

            {/* Duration */}
            {step.duration && step.status === 'completed' && (
              <span className="text-xs text-slate-500 flex-shrink-0">{step.duration}ms</span>
            )}

            {/* Status indicator */}
            <div className="flex-shrink-0">
              <AnimatePresence mode="wait">
                {step.status === 'running' && (
                  <motion.div
                    key="running"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    exit={{ scale: 0 }}
                    className="w-6 h-6 rounded-full border-2 animate-spin"
                    style={{ borderColor: '#6366F1', borderTopColor: 'transparent' }}
                  />
                )}
                {step.status === 'completed' && (
                  <motion.div
                    key="done"
                    initial={{ scale: 0, rotate: -90 }}
                    animate={{ scale: 1, rotate: 0 }}
                    exit={{ scale: 0 }}
                    transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                    className="w-6 h-6 rounded-full flex items-center justify-center"
                    style={{ background: 'rgba(16,185,129,0.2)', border: '1px solid rgba(16,185,129,0.4)' }}
                  >
                    <span className="text-xs text-emerald-400">✓</span>
                  </motion.div>
                )}
                {step.status === 'pending' && (
                  <motion.div
                    key="pending"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="w-6 h-6 rounded-full"
                    style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}
                  />
                )}
                {step.status === 'error' && (
                  <motion.div
                    key="error"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="w-6 h-6 rounded-full flex items-center justify-center"
                    style={{ background: 'rgba(244,63,94,0.15)', border: '1px solid rgba(244,63,94,0.3)' }}
                  >
                    <span className="text-xs text-rose-400">✕</span>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Completion banner */}
      <AnimatePresence>
        {completedCount === steps.length && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            className="flex items-center gap-3 px-4 py-3 rounded-xl"
            style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.25)' }}
          >
            <span className="text-2xl">🎉</span>
            <div>
              <p className="text-sm font-semibold text-emerald-400">Analysis Complete!</p>
              <p className="text-xs text-slate-400">All 9 AI agents finished processing the resume.</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
