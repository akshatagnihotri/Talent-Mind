'use client';
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell, PieChart, Pie, Legend } from 'recharts';
import apiClient from '@/lib/api';

const getStageColor = (stage: string) => {
  switch (stage) {
    case 'Strong Hire': return '#10B981';
    case 'Hire': return '#6366F1';
    case 'Consider': return '#F59E0B';
    case 'Reject': return '#F43F5E';
    default: return '#94A3B8';
  }
};

export default function AnalyticsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true);
        const res = await apiClient.getDashboardAnalytics() as any;
        setData(res);
      } catch (err) {
        console.error(err);
        setError('Failed to fetch analytics from backend. Displaying sandbox demo metrics.');
        // Inject fallback mock data so the charts render beautifully
        setData({
          total_resumes: 24,
          avg_ats_score: 76.4,
          total_jobs: 4,
          total_candidates: 24,
          strong_hire_count: 3,
          score_trend: [
            { date: 'Jun 01', avg_ats_score: 72 },
            { date: 'Jun 03', avg_ats_score: 75 },
            { date: 'Jun 05', avg_ats_score: 73 },
            { date: 'Jun 07', avg_ats_score: 78 },
            { date: 'Jun 09', avg_ats_score: 76.4 }
          ],
          top_skills_demand: [
            { skill: 'Python', count: 18, percentage: 80 },
            { skill: 'React', count: 14, percentage: 70 },
            { skill: 'PostgreSQL', count: 12, percentage: 65 },
            { skill: 'Docker', count: 10, percentage: 45 },
            { skill: 'AWS', count: 8, percentage: 55 },
            { skill: 'Kubernetes', count: 6, percentage: 30 }
          ],
          hiring_funnel: [
            { stage: 'Strong Hire', count: 3, percentage: 12.5 },
            { stage: 'Hire', count: 11, percentage: 45.8 },
            { stage: 'Consider', count: 7, percentage: 29.2 },
            { stage: 'Reject', count: 3, percentage: 12.5 }
          ]
        });
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-40 gap-3">
        <div className="w-10 h-10 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm text-slate-400">Loading analytics dashboards...</p>
      </div>
    );
  }

  const totalCandidates = data?.total_candidates || 0;
  const strongHireCount = data?.strong_hire_count || 0;
  const strongHirePercentage = totalCandidates > 0 ? (strongHireCount / totalCandidates) * 100 : 0;

  return (
    <div className="space-y-8 animate-slide-up">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-black text-white tracking-tight">Recruitment Analytics</h1>
        <p className="text-slate-400">Aggregate statistics, quality-of-hire trends, and skill demand distributions.</p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold flex items-center gap-2">
          💡 {error}
        </div>
      )}

      {/* Analytics Summary Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { label: 'Total Resumes', value: data?.total_resumes || 0, icon: '📄', color: 'text-indigo-400', bg: 'rgba(99,102,241,0.1)' },
          { label: 'Avg ATS Score', value: `${(data?.avg_ats_score || 0).toFixed(1)}/100`, icon: '🎯', color: 'text-emerald-400', bg: 'rgba(16,185,129,0.1)' },
          { label: 'Top Tier Ratio', value: `${strongHirePercentage.toFixed(1)}%`, icon: '🥇', color: 'text-violet-400', bg: 'rgba(139,92,246,0.1)' },
          { label: 'Active Jobs', value: data?.total_jobs || 0, icon: '💼', color: 'text-cyan-400', bg: 'rgba(6,182,212,0.1)' },
        ].map((stat) => (
          <div key={stat.label} className="glass-card p-6 flex items-center gap-5 border-white/5 bg-slate-900/40">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl" style={{ background: stat.bg }}>
              {stat.icon}
            </div>
            <div>
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">{stat.label}</p>
              <h3 className="text-2xl font-black mt-1 text-white">{stat.value}</h3>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Grid */}
      <div className="grid md:grid-cols-2 gap-8">
        {/* Chart 1: Average Score Trend */}
        <div className="glass-card p-6 bg-slate-900/40 border-white/5 space-y-4">
          <h3 className="text-base font-bold text-white">Quality-of-Hire Score Trend</h3>
          <div className="h-[280px] w-full pt-4">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data?.score_trend || []}>
                <defs>
                  <linearGradient id="scoreColor" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366F1" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#6366F1" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="date" stroke="#94A3B8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94A3B8" fontSize={11} domain={[0, 100]} tickLine={false} />
                <Tooltip contentStyle={{ background: '#0F172A', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12, color: 'white', fontSize: 12 }} />
                <Area type="monotone" dataKey="avg_ats_score" stroke="#6366F1" strokeWidth={2.5} fillOpacity={1} fill="url(#scoreColor)" name="Avg ATS Score" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Hiring Funnel / Distribution */}
        <div className="glass-card p-6 bg-slate-900/40 border-white/5 space-y-4">
          <h3 className="text-base font-bold text-white">Hiring Recommendation Distribution</h3>
          <div className="h-[280px] w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data?.hiring_funnel || []}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={85}
                  paddingAngle={5}
                  dataKey="count"
                  nameKey="stage"
                >
                  {(data?.hiring_funnel || []).map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={getStageColor(entry.stage)} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: '#0F172A', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12, color: 'white', fontSize: 12 }} />
                <Legend iconType="circle" wrapperStyle={{ fontSize: 12, color: '#94A3B8' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 3: Skills in Demand */}
        <div className="glass-card md:col-span-2 p-6 bg-slate-900/40 border-white/5 space-y-4">
          <h3 className="text-base font-bold text-white">Skills Demand & Candidate Match Rate</h3>
          <div className="h-[300px] w-full pt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data?.top_skills_demand || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="skill" stroke="#94A3B8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94A3B8" fontSize={11} tickLine={false} />
                <Tooltip contentStyle={{ background: '#0F172A', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12, color: 'white', fontSize: 12 }} />
                <Bar dataKey="count" fill="#6366F1" radius={[6, 6, 0, 0]} name="Mentions Count">
                  {(data?.top_skills_demand || []).map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={index % 2 === 0 ? '#6366F1' : '#10B981'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
