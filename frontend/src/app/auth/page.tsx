'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import apiClient from '@/lib/api';

export default function AuthPage() {
  const router = useRouter();
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (isLogin) {
        await apiClient.login(email, password);
        router.push('/upload');
      } else {
        await apiClient.register(name, email, password);
        // Auto-login after successful registration
        await apiClient.login(email, password);
        router.push('/upload');
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const fillDemoCredentials = () => {
    setEmail('admin@talentmind.ai');
    setPassword('admin123');
  };

  return (
    <div className="animated-bg min-h-screen flex items-center justify-center px-4 py-12">
      {/* Background glow orbs */}
      <div className="absolute w-[400px] h-[400px] rounded-full blur-3xl opacity-10 bg-indigo-600 top-1/4 left-1/4 pointer-events-none" />
      <div className="absolute w-[400px] h-[400px] rounded-full blur-3xl opacity-10 bg-emerald-600 bottom-1/4 right-1/4 pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        {/* Logo and Header */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-3 mb-4">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center text-2xl shadow-lg"
              style={{ background: 'linear-gradient(135deg, #6366F1, #8B5CF6)' }}
            >
              🧠
            </div>
            <span className="text-2xl font-black text-white tracking-tight">
              TalentMind <span style={{ color: '#6366F1' }}>AI</span>
            </span>
          </Link>
          <h2 className="text-xl font-bold text-slate-300">
            {isLogin ? 'Welcome back Recruiter' : 'Create your account'}
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            {isLogin ? 'Sign in to access your dashboard' : 'Join 500+ hiring teams screening with AI'}
          </p>
        </div>

        {/* Card Container */}
        <div className="glass-card p-8 shadow-2xl relative border-white/5 bg-slate-900/40">
          <form onSubmit={handleSubmit} className="space-y-6">
            <AnimatePresence mode="wait">
              {!isLogin && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.2 }}
                  className="space-y-2"
                >
                  <label className="block text-sm font-medium text-slate-300">Full Name</label>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Jane Doe"
                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all text-sm"
                  />
                </motion.div>
              )}
            </AnimatePresence>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-300">Email Address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all text-sm"
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <label className="block text-sm font-medium text-slate-300">Password</label>
                {isLogin && (
                  <a href="#" className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors">
                    Forgot password?
                  </a>
                )}
              </div>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all text-sm"
              />
            </div>

            {error && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-medium"
              >
                ⚠️ {error}
              </motion.div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary py-3 rounded-xl flex items-center justify-center gap-2 font-semibold text-sm transition-all"
            >
              {loading ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Processing...
                </>
              ) : (
                isLogin ? 'Sign In' : 'Create Account'
              )}
            </button>
          </form>

          {/* Demo Sandbox Button */}
          {isLogin && (
            <div className="mt-6 pt-6 border-t border-white/5 text-center">
              <button
                type="button"
                onClick={fillDemoCredentials}
                className="text-xs text-emerald-400 hover:text-emerald-300 bg-emerald-500/10 border border-emerald-500/20 px-4 py-2 rounded-xl transition-all font-semibold"
              >
                🔑 Quick Fill Demo Admin Credentials
              </button>
            </div>
          )}

          {/* Toggle Tab */}
          <div className="mt-6 text-center text-sm text-slate-400">
            {isLogin ? "Don't have an account? " : "Already have an account? "}
            <button
              onClick={() => {
                setIsLogin(!isLogin);
                setError('');
              }}
              className="text-indigo-400 font-semibold hover:text-indigo-300 transition-colors"
            >
              {isLogin ? 'Sign up' : 'Sign in'}
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
