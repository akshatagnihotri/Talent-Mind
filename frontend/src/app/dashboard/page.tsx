'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import Link from 'next/link';
import apiClient from '@/lib/api';

interface Candidate {
  id: string;
  name: string;
  email: string;
  resume_id: string;
  years_experience: number;
  skills: string[];
}

interface Resume {
  id: string;
  filename: string;
  uploaded_at: string;
  candidate?: Candidate;
}

export default function DashboardMain() {
  const router = useRouter();
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [stats, setStats] = useState({
    total: 0,
    avgAts: 0.0,
    strongHire: 0,
    hiringRate: 0,
  });

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const fetchedResumes = await apiClient.getResumes() as any;
      setResumes(fetchedResumes || []);
      
      const dashboardStats = await apiClient.getDashboardAnalytics() as any;
      if (dashboardStats) {
        setStats({
          total: dashboardStats.total_resumes || fetchedResumes.length,
          avgAts: dashboardStats.avg_ats_score || 0,
          strongHire: dashboardStats.strong_hire_count || 0,
          hiringRate: Math.round(((dashboardStats.strong_hire_count + dashboardStats.hire_count) / Math.max(dashboardStats.total_candidates, 1)) * 100) || 0,
        });
      }
    } catch (err: any) {
      console.error(err);
      setError('Failed to load dashboard metrics. Ensure Ollama/Database is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    if (!confirm('Are you sure you want to delete this candidate?')) return;
    try {
      await apiClient.deleteResume(id);
      loadDashboardData();
    } catch (err: any) {
      alert(err.message || 'Failed to delete resume.');
    }
  };

  const getRecommendationStyle = (rec: string) => {
    const r = rec?.toLowerCase() || '';
    if (r.includes('strong')) return 'badge-strong-hire';
    if (r.includes('reject')) return 'badge-reject';
    if (r.includes('consider')) return 'badge-consider';
    return 'badge-hire';
  };

  return (
    <div className="space-y-8 animate-slide-up">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-black text-white tracking-tight">Recruiter Dashboard</h1>
          <p className="text-slate-400">Welcome to TalentMind AI. Screen, rank, and track candidates.</p>
        </div>
        <Link href="/upload">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="btn-primary flex items-center gap-2"
          >
            ➕ Screen New Resume
          </motion.button>
        </Link>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold flex items-center gap-2">
          💡 {error} (Demo fallback mode active)
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { label: 'Total Resumes', value: stats.total, icon: '📄', color: 'text-indigo-400', bg: 'rgba(99,102,241,0.1)' },
          { label: 'Average ATS Score', value: `${stats.avgAts.toFixed(1)}/100`, icon: '🎯', color: 'text-emerald-400', bg: 'rgba(16,185,129,0.1)' },
          { label: 'Strong Hires', value: stats.strongHire, icon: '🟢', color: 'text-green-400', bg: 'rgba(52,211,153,0.1)' },
          { label: 'Acceptance Rate', value: `${stats.hiringRate}%`, icon: '📈', color: 'text-violet-400', bg: 'rgba(139,92,246,0.1)' },
        ].map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="glass-card p-6 flex items-center gap-5 border-white/5 bg-slate-900/40"
          >
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-2xl`} style={{ background: stat.bg }}>
              {stat.icon}
            </div>
            <div>
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">{stat.label}</p>
              <h3 className={`text-2xl font-black mt-1 text-white`}>{stat.value}</h3>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Main Content Area: Candidate Table */}
      <div className="glass-card border-white/5 bg-slate-900/40 p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-bold text-white">Analyzed Candidates</h2>
          <button
            onClick={loadDashboardData}
            className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold"
          >
            🔄 Refresh List
          </button>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <div className="w-8 h-8 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            <p className="text-sm text-slate-400">Loading candidate records...</p>
          </div>
        ) : resumes.length === 0 ? (
          <div className="text-center py-20 space-y-4">
            <span className="text-5xl block">📥</span>
            <h3 className="text-base font-bold text-white">No candidates analyzed yet</h3>
            <p className="text-sm text-slate-400 max-w-sm mx-auto">Upload a resume to kick off the multi-agent AI pipeline and view results here.</p>
            <Link href="/upload" className="inline-block mt-2">
              <button className="btn-primary text-sm">Upload Resume</button>
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Candidate</th>
                  <th>Job Title / File</th>
                  <th>Experience</th>
                  <th>Date Analyzed</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {resumes.map((resume) => {
                  const candidate = resume.candidate;
                  const candidateId = candidate?.id || 'unknown';
                  return (
                    <tr
                      key={resume.id}
                      className="cursor-pointer hover:bg-white/5 transition-colors group"
                      onClick={() => router.push(`/dashboard/ats?id=${resume.id}`)}
                    >
                      <td>
                        <div className="font-semibold text-white group-hover:text-indigo-400 transition-colors">
                          {candidate?.name || 'Processing...'}
                        </div>
                        <div className="text-xs text-slate-500">{candidate?.email || 'N/A'}</div>
                      </td>
                      <td>
                        <div className="text-sm font-medium text-slate-300">{resume.filename}</div>
                      </td>
                      <td>
                        <span className="text-sm text-slate-300 font-medium">
                          {candidate?.years_experience !== undefined ? `${candidate.years_experience.toFixed(1)} yrs` : 'N/A'}
                        </span>
                      </td>
                      <td>
                        <div className="text-sm text-slate-400">
                          {new Date(resume.uploaded_at).toLocaleDateString(undefined, {
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric',
                          })}
                        </div>
                      </td>
                      <td>
                        <div className="flex items-center gap-3">
                          <button
                            onClick={(e) => handleDelete(resume.id, e)}
                            className="w-8 h-8 rounded-lg flex items-center justify-center bg-rose-500/10 border border-rose-500/20 text-rose-400 hover:bg-rose-500 hover:text-white transition-all text-xs"
                            title="Delete candidate"
                          >
                            🗑️
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
