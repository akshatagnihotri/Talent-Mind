'use client';
import { useEffect, useRef, useState } from 'react';
import { motion, useInView, useScroll, useTransform } from 'framer-motion';
import Link from 'next/link';
import Navbar from '@/components/Navbar';

// ─── Counter animation hook ───────────────────────────────────────────────────
function useCounter(target: number, duration = 2000) {
  const [count, setCount] = useState(0);
  const ref = useRef(null);
  const inView = useInView(ref, { once: true });

  useEffect(() => {
    if (!inView) return;
    let start = 0;
    const step = target / (duration / 16);
    const timer = setInterval(() => {
      start += step;
      if (start >= target) { setCount(target); clearInterval(timer); }
      else setCount(Math.floor(start));
    }, 16);
    return () => clearInterval(timer);
  }, [inView, target, duration]);

  return { count, ref };
}

// ─── Fade-in section ─────────────────────────────────────────────────────────
function FadeInSection({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: '-80px' });
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 40 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.6, delay, ease: 'easeOut' }}
    >
      {children}
    </motion.div>
  );
}

// ─── Floating particle dot ────────────────────────────────────────────────────
function Particle({ x, y, size, color, delay }: { x: number; y: number; size: number; color: string; delay: number }) {
  return (
    <motion.div
      className="absolute rounded-full opacity-30 pointer-events-none"
      style={{ left: `${x}%`, top: `${y}%`, width: size, height: size, background: color }}
      animate={{ y: [0, -20, 0], opacity: [0.2, 0.5, 0.2] }}
      transition={{ duration: 3 + delay, repeat: Infinity, ease: 'easeInOut', delay }}
    />
  );
}

function StatItem({ stat }: { stat: { value: number; suffix: string; label: string } }) {
  const { count, ref } = useCounter(stat.value);
  return (
    <div ref={ref} className="text-center">
      <div className="text-4xl font-black gradient-text mb-1">
        {count}{stat.suffix}
      </div>
      <p className="text-sm text-slate-400">{stat.label}</p>
    </div>
  );
}

// ─── Features ────────────────────────────────────────────────────────────────
const features = [
  { icon: '🤖', title: 'Resume Parser AI', desc: 'Extracts structured candidate data from PDF/DOCX with 99%+ accuracy. Name, skills, experience, education — all parsed in seconds.', color: '#6366F1' },
  { icon: '🎯', title: 'ATS Scoring Engine', desc: 'Intelligent 0-100 ATS compatibility score across 6 dimensions: skills, experience, education, formatting, certifications and keywords.', color: '#10B981' },
  { icon: '🔗', title: 'Job Match Analysis', desc: 'Deep semantic matching against job descriptions. Calculates fit percentage and identifies missing qualifications.', color: '#8B5CF6' },
  { icon: '🏆', title: 'Candidate Ranking', desc: 'AI-powered leaderboard with multi-factor scoring. Instantly surface your top 3 candidates from any pool.', color: '#F59E0B' },
  { icon: '📋', title: 'Recruiter Copilot', desc: 'AI-generated recruiter summaries, interview questions, strengths & risks analysis — ready to share in one click.', color: '#06B6D4' },
  { icon: '📈', title: 'Skill Gap Analysis', desc: 'Identifies exact missing skills, experience gaps, and provides actionable learning path recommendations for each candidate.', color: '#F43F5E' },
];

// ─── Stats ───────────────────────────────────────────────────────────────────
const stats = [
  { value: 500, suffix: 'K+', label: 'Resumes Analyzed' },
  { value: 9, suffix: '', label: 'AI Agents' },
  { value: 99, suffix: '.2%', label: 'ATS Accuracy' },
  { value: 10, suffix: 'x', label: 'Faster Hiring' },
];

// ─── Pricing ─────────────────────────────────────────────────────────────────
const pricing = [
  {
    name: 'Starter', price: 'Free', period: '', highlight: false,
    features: ['10 resumes/month', '3 AI agents', 'ATS scoring', 'Basic ranking', 'Email support'],
    cta: 'Get Started',
  },
  {
    name: 'Pro', price: '$49', period: '/month', highlight: true,
    features: ['500 resumes/month', 'All 9 AI agents', 'Full ATS analysis', 'Candidate ranking', 'Recruiter Copilot', 'Skill gap analysis', 'Priority support'],
    cta: 'Start Free Trial',
  },
  {
    name: 'Enterprise', price: 'Custom', period: '', highlight: false,
    features: ['Unlimited resumes', 'All 9 AI agents', 'Custom AI tuning', 'API access', 'SSO & SAML', 'Dedicated support', 'SLA guarantee'],
    cta: 'Contact Sales',
  },
];

// ─── Testimonials ────────────────────────────────────────────────────────────
const testimonials = [
  {
    name: 'Sarah Chen', role: 'Head of Talent, Stripe', avatar: 'SC',
    text: 'TalentMind AI cut our screening time by 80%. The ATS scoring is incredibly accurate and the Recruiter Copilot summaries save hours of manual work.',
    rating: 5,
  },
  {
    name: 'Marcus Rodriguez', role: 'HR Director, Shopify', avatar: 'MR',
    text: "We screen 200+ resumes a week. TalentMind's ranking system ensures we never miss a great candidate. The 9-agent pipeline is game-changing.",
    rating: 5,
  },
  {
    name: 'Priya Patel', role: 'Recruiting Manager, Zoom', avatar: 'PP',
    text: 'The job match analysis is frighteningly good. It finds skill gaps I would have missed. Our quality-of-hire improved significantly in 3 months.',
    rating: 5,
  },
];

// ─── Main Landing Page ────────────────────────────────────────────────────────
export default function LandingPage() {
  const { count: atsScore, ref: atsRef } = useCounter(87);
  const heroRef = useRef(null);
  const { scrollYProgress } = useScroll({ target: heroRef });
  const heroY = useTransform(scrollYProgress, [0, 1], [0, -100]);

  const particles = [
    { x: 10, y: 20, size: 4, color: '#6366F1', delay: 0 },
    { x: 85, y: 15, size: 6, color: '#8B5CF6', delay: 0.5 },
    { x: 70, y: 70, size: 3, color: '#10B981', delay: 1 },
    { x: 25, y: 80, size: 5, color: '#6366F1', delay: 1.5 },
    { x: 90, y: 50, size: 4, color: '#06B6D4', delay: 0.8 },
    { x: 50, y: 10, size: 3, color: '#F59E0B', delay: 0.3 },
    { x: 15, y: 60, size: 5, color: '#8B5CF6', delay: 1.2 },
    { x: 60, y: 90, size: 4, color: '#10B981', delay: 0.7 },
  ];

  return (
    <div className="animated-bg min-h-screen">
      <Navbar />

      {/* ─── Hero ─── */}
      <section ref={heroRef} className="relative min-h-screen flex items-center overflow-hidden pt-16">
        {/* Particles */}
        {particles.map((p, i) => <Particle key={i} {...p} />)}

        {/* Grid pattern */}
        <div
          className="absolute inset-0 opacity-5"
          style={{
            backgroundImage: 'linear-gradient(rgba(99,102,241,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(99,102,241,0.5) 1px, transparent 1px)',
            backgroundSize: '50px 50px',
          }}
        />

        <motion.div style={{ y: heroY }} className="max-w-7xl mx-auto px-6 py-24 grid lg:grid-cols-2 gap-16 items-center w-full">
          {/* Left: Text */}
          <div>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full mb-6 text-sm font-medium"
              style={{ background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.25)', color: '#818CF8' }}
            >
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              9 AI Agents • Powered by Ollama LLM
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.1 }}
              className="text-6xl xl:text-7xl font-black leading-tight mb-6"
            >
              <span className="text-white">Screen</span>{' '}
              <span className="gradient-text">Smarter.</span>
              <br />
              <span className="text-white">Hire </span>
              <span className="gradient-text-emerald">Better.</span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.2 }}
              className="text-lg text-slate-400 leading-relaxed mb-10 max-w-xl"
            >
              TalentMind AI uses{' '}
              <span className="text-violet-400 font-semibold">9 specialized AI agents</span> to analyze
              resumes, rank candidates, and generate recruiter insights — all running locally with Ollama.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="flex flex-wrap gap-4"
            >
              <Link href="/upload">
                <motion.button
                  whileHover={{ scale: 1.05, y: -2 }}
                  whileTap={{ scale: 0.97 }}
                  className="btn-primary text-base px-8 py-4 flex items-center gap-2"
                >
                  🚀 Start Screening
                </motion.button>
              </Link>
              <Link href="/dashboard/analytics">
                <motion.button
                  whileHover={{ scale: 1.03 }}
                  whileTap={{ scale: 0.97 }}
                  className="btn-secondary text-base px-8 py-4 flex items-center gap-2"
                >
                  ▶ Watch Demo
                </motion.button>
              </Link>
            </motion.div>

            {/* Trust badges */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6 }}
              className="flex items-center gap-6 mt-10"
            >
              {['No cloud needed', 'Privacy first', 'Open source'].map((badge) => (
                <div key={badge} className="flex items-center gap-1.5 text-sm text-slate-400">
                  <span className="text-emerald-400">✓</span> {badge}
                </div>
              ))}
            </motion.div>
          </div>

          {/* Right: Floating UI Mockups */}
          <div className="relative hidden lg:flex items-center justify-center h-[520px]">
            {/* Main score card */}
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{
                opacity: 1,
                scale: 1,
                y: [0, -15, 0],
              }}
              transition={{
                opacity: { duration: 0.7, delay: 0.4 },
                scale: { duration: 0.7, delay: 0.4 },
                y: {
                  duration: 6,
                  repeat: Infinity,
                  ease: 'easeInOut',
                }
              }}
              className="glass-card p-8 absolute shadow-2xl border-white/5"
              style={{ top: '8%', right: '8%', width: 220 }}
            >
              <p className="text-xs text-slate-400 mb-4 font-semibold uppercase tracking-wider">ATS Score</p>
              <div ref={atsRef} className="text-6xl font-black mb-2" style={{ color: '#10B981' }}>
                {atsScore}
              </div>
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${atsScore}%`, background: 'linear-gradient(90deg,#6366F1,#10B981)' }} />
              </div>
              <p className="text-xs text-emerald-400 mt-2 font-semibold">Excellent Match ✓</p>
            </motion.div>

            {/* Ranking card */}
            <motion.div
              initial={{ opacity: 0, x: 40 }}
              animate={{
                opacity: 1,
                x: 0,
                y: [0, 15, 0],
              }}
              transition={{
                opacity: { duration: 0.7, delay: 0.6 },
                x: { duration: 0.7, delay: 0.6 },
                y: {
                  duration: 7,
                  repeat: Infinity,
                  ease: 'easeInOut',
                  delay: 0.5,
                }
              }}
              className="glass-card p-6 absolute shadow-2xl border-white/5"
              style={{ bottom: '10%', right: '14%', width: 240 }}
            >
              <p className="text-xs text-slate-400 mb-3 font-semibold uppercase tracking-wider">Top Candidates</p>
              {[
                { name: 'Alex Johnson', score: 94, emoji: '🥇' },
                { name: 'Maria Garcia', score: 87, emoji: '🥈' },
                { name: 'David Kim', score: 81, emoji: '🥉' },
              ].map((c) => (
                <div key={c.name} className="flex items-center gap-2 mb-2">
                  <span>{c.emoji}</span>
                  <span className="text-sm text-slate-300 flex-1">{c.name}</span>
                  <span className="text-sm font-bold" style={{ color: '#10B981' }}>{c.score}</span>
                </div>
              ))}
            </motion.div>

            {/* Agents pill */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{
                opacity: 1,
                y: [0, -12, 0],
                x: [0, 6, 0],
              }}
              transition={{
                opacity: { duration: 0.7, delay: 0.8 },
                y: {
                  duration: 5,
                  repeat: Infinity,
                  ease: 'easeInOut',
                  delay: 0.2,
                },
                x: {
                  duration: 6,
                  repeat: Infinity,
                  ease: 'easeInOut',
                  delay: 0.2,
                }
              }}
              className="glass-card px-5 py-4 absolute shadow-2xl border-white/5"
              style={{ top: '22%', left: '4%', width: 220 }}
            >
              <div className="flex items-center gap-2 mb-3">
                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <p className="text-xs text-emerald-400 font-semibold">Agents Running</p>
              </div>
              {['📄 Parser', '🎯 ATS Scorer', '🔗 Job Matcher'].map((a) => (
                <div key={a} className="text-xs text-slate-400 mb-1 flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-violet-400" />
                  {a}
                </div>
              ))}
            </motion.div>

            {/* Glow orb */}
            <div
              className="absolute w-80 h-80 rounded-full blur-3xl opacity-15"
              style={{ background: 'radial-gradient(circle, #6366F1, #8B5CF6)', top: '20%', left: '15%' }}
            />
          </div>
        </motion.div>
      </section>

      {/* ─── Stats Bar ─── */}
      <FadeInSection>
        <section className="py-12 border-y" style={{ borderColor: 'rgba(255,255,255,0.06)', background: 'rgba(255,255,255,0.02)' }}>
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat) => (
              <StatItem key={stat.label} stat={stat} />
            ))}
          </div>
        </section>
      </FadeInSection>

      {/* ─── Features ─── */}
      <FadeInSection>
        <section className="py-24 max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <span className="text-sm font-semibold text-violet-400 uppercase tracking-wider mb-3 block">Features</span>
            <h2 className="text-4xl font-bold text-white mb-4">Everything you need to hire smarter</h2>
            <p className="text-slate-400 max-w-xl mx-auto">9 specialized AI agents working in concert to give you unprecedented hiring intelligence.</p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.5 }}
                whileHover={{ y: -4, scale: 1.02 }}
                className="glass-card glass-card-hover p-7"
              >
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl mb-5"
                  style={{ background: `${f.color}18`, border: `1px solid ${f.color}30` }}
                >
                  {f.icon}
                </div>
                <h3 className="text-lg font-bold text-white mb-2">{f.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </section>
      </FadeInSection>

      {/* ─── How It Works ─── */}
      <FadeInSection>
        <section className="py-24" style={{ background: 'rgba(255,255,255,0.02)' }}>
          <div className="max-w-5xl mx-auto px-6">
            <div className="text-center mb-16">
              <span className="text-sm font-semibold text-violet-400 uppercase tracking-wider mb-3 block">How It Works</span>
              <h2 className="text-4xl font-bold text-white mb-4">From resume to insight in 3 steps</h2>
            </div>
            <div className="grid md:grid-cols-3 gap-8 relative">
              {/* Connector line */}
              <div className="hidden md:block absolute top-12 left-1/6 right-1/6 h-px" style={{ background: 'linear-gradient(90deg, transparent, #6366F1, transparent)' }} />
              {[
                { step: '01', icon: '📤', title: 'Upload Resume(s)', desc: 'Drag & drop one or multiple PDF/DOCX files. Batch processing supported.' },
                { step: '02', icon: '🤖', title: 'AI Agents Analyze', desc: '9 specialized agents process the resume in parallel — parsing, scoring, matching.' },
                { step: '03', icon: '💡', title: 'Get Actionable Insights', desc: 'ATS score, ranking, skill gaps, interview questions, and recruiter summary.' },
              ].map((step, i) => (
                <motion.div
                  key={step.step}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.15 }}
                  className="text-center relative"
                >
                  <div
                    className="w-24 h-24 rounded-2xl flex items-center justify-center text-4xl mx-auto mb-6 relative"
                    style={{ background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.2)' }}
                  >
                    {step.icon}
                    <span
                      className="absolute -top-3 -right-3 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold"
                      style={{ background: 'linear-gradient(135deg,#6366F1,#8B5CF6)', color: 'white' }}
                    >
                      {step.step}
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-white mb-3">{step.title}</h3>
                  <p className="text-sm text-slate-400 leading-relaxed">{step.desc}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>
      </FadeInSection>

      {/* ─── Pricing ─── */}
      <FadeInSection>
        <section className="py-24 max-w-6xl mx-auto px-6">
          <div className="text-center mb-16">
            <span className="text-sm font-semibold text-violet-400 uppercase tracking-wider mb-3 block">Pricing</span>
            <h2 className="text-4xl font-bold text-white mb-4">Simple, transparent pricing</h2>
            <p className="text-slate-400">Start free, scale when ready.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {pricing.map((plan, i) => (
              <motion.div
                key={plan.name}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                whileHover={{ y: -4 }}
                className="glass-card p-8 relative flex flex-col"
                style={
                  plan.highlight
                    ? { border: '1px solid rgba(99,102,241,0.4)', background: 'rgba(99,102,241,0.07)', boxShadow: '0 0 40px rgba(99,102,241,0.15)' }
                    : {}
                }
              >
                {plan.highlight && (
                  <div
                    className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full text-xs font-bold text-white"
                    style={{ background: 'linear-gradient(135deg,#6366F1,#8B5CF6)' }}
                  >
                    ⭐ Most Popular
                  </div>
                )}
                <h3 className="text-xl font-bold text-white mb-2">{plan.name}</h3>
                <div className="flex items-end gap-1 mb-6">
                  <span className="text-4xl font-black text-white">{plan.price}</span>
                  <span className="text-slate-400 mb-1">{plan.period}</span>
                </div>
                <ul className="space-y-3 flex-1 mb-8">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-center gap-2 text-sm text-slate-300">
                      <span className="text-emerald-400">✓</span> {f}
                    </li>
                  ))}
                </ul>
                <Link href="/auth">
                  <motion.button
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.97 }}
                    className="w-full py-3 rounded-xl font-semibold text-sm transition-all"
                    style={
                      plan.highlight
                        ? { background: 'linear-gradient(135deg,#6366F1,#8B5CF6)', color: 'white', boxShadow: '0 4px 15px rgba(99,102,241,0.4)' }
                        : { background: 'rgba(255,255,255,0.05)', color: 'white', border: '1px solid rgba(255,255,255,0.1)' }
                    }
                  >
                    {plan.cta}
                  </motion.button>
                </Link>
              </motion.div>
            ))}
          </div>
        </section>
      </FadeInSection>

      {/* ─── Testimonials ─── */}
      <FadeInSection>
        <section className="py-24" style={{ background: 'rgba(255,255,255,0.02)' }}>
          <div className="max-w-6xl mx-auto px-6">
            <div className="text-center mb-16">
              <span className="text-sm font-semibold text-violet-400 uppercase tracking-wider mb-3 block">Testimonials</span>
              <h2 className="text-4xl font-bold text-white mb-4">Loved by HR teams worldwide</h2>
            </div>
            <div className="grid md:grid-cols-3 gap-6">
              {testimonials.map((t, i) => (
                <motion.div
                  key={t.name}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                  className="glass-card glass-card-hover p-7"
                >
                  <div className="flex gap-1 mb-4">
                    {Array.from({ length: t.rating }).map((_, j) => (
                      <span key={j} className="text-amber-400">⭐</span>
                    ))}
                  </div>
                  <p className="text-sm text-slate-300 leading-relaxed mb-6 italic">"{t.text}"</p>
                  <div className="flex items-center gap-3">
                    <div
                      className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold"
                      style={{ background: 'linear-gradient(135deg,#6366F1,#8B5CF6)', color: 'white' }}
                    >
                      {t.avatar}
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-white">{t.name}</p>
                      <p className="text-xs text-slate-400">{t.role}</p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>
      </FadeInSection>

      {/* ─── CTA Banner ─── */}
      <FadeInSection>
        <section className="py-24 max-w-4xl mx-auto px-6 text-center">
          <motion.div
            whileHover={{ scale: 1.01 }}
            className="glass-card p-16 relative overflow-hidden"
            style={{ border: '1px solid rgba(99,102,241,0.2)' }}
          >
            <div className="absolute inset-0 opacity-20" style={{ background: 'radial-gradient(circle at 50% 50%, #6366F1, transparent 70%)' }} />
            <div className="relative z-10">
              <h2 className="text-4xl font-bold text-white mb-4">Ready to transform your hiring?</h2>
              <p className="text-slate-400 mb-8 text-lg">Join 500+ companies using TalentMind AI to find top talent faster.</p>
              <div className="flex flex-wrap gap-4 justify-center">
                <Link href="/upload">
                  <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.97 }} className="btn-primary text-base px-10 py-4">
                    🚀 Start for Free
                  </motion.button>
                </Link>
                <Link href="/auth">
                  <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }} className="btn-secondary text-base px-10 py-4">
                    Sign In
                  </motion.button>
                </Link>
              </div>
            </div>
          </motion.div>
        </section>
      </FadeInSection>

      {/* ─── Footer ─── */}
      <footer className="border-t py-12" style={{ borderColor: 'rgba(255,255,255,0.06)', background: 'rgba(0,0,0,0.2)' }}>
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid md:grid-cols-4 gap-8 mb-10">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center text-lg" style={{ background: 'linear-gradient(135deg,#6366F1,#8B5CF6)' }}>🧠</div>
                <span className="font-bold text-white">TalentMind AI</span>
              </div>
              <p className="text-sm text-slate-400">AI-powered resume screening for modern HR teams.</p>
            </div>
            {[
              { title: 'Product', links: ['Features', 'Pricing', 'Changelog', 'Roadmap'] },
              { title: 'Resources', links: ['Documentation', 'API Reference', 'Blog', 'Support'] },
              { title: 'Company', links: ['About', 'Careers', 'Privacy', 'Terms'] },
            ].map((col) => (
              <div key={col.title}>
                <h4 className="text-sm font-semibold text-white mb-3">{col.title}</h4>
                <ul className="space-y-2">
                  {col.links.map((link) => (
                    <li key={link}>
                      <a 
                        href="#" 
                        onClick={(e) => { e.preventDefault(); alert(link + ' page coming soon!'); }} 
                        className="text-sm text-slate-400 hover:text-white transition-colors"
                      >
                        {link}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
          <div className="border-t pt-8 flex flex-col md:flex-row items-center justify-between gap-4" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
            <p className="text-sm text-slate-500">© 2025 TalentMind AI. All rights reserved.</p>
            <p className="text-sm text-slate-500">Built with ❤️ using Next.js & Ollama</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
