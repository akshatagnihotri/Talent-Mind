'use client';
import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';
import apiClient from '@/lib/api';

export default function JobMatchPage() {
  const searchParams = useSearchParams();
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadAnalysis = async () => {
    try {
      setLoading(true);
      setError('');
      
      let id = searchParams.get('id');
      if (!id && typeof window !== 'undefined') {
        id = localStorage.getItem('talentmind_latest_analysis_id') || 
             localStorage.getItem('talentmind_latest_resume_id');
      }

      if (!id) {
        setError('No candidate analysis found. Please upload a resume first.');
        setLoading(false);
        return;
      }

      let data;
      try {
        data = await apiClient.getAnalysis(id);
      } catch (err) {
        try {
          data = await apiClient.getAnalysisByResume(id);
        } catch (innerErr) {
          throw err;
        }
      }
      
      setAnalysis(data);
    } catch (err: any) {
      console.error(err);
      setError('Unable to load matching metrics. Displaying sandbox demo metrics.');
      setAnalysis({
        match_score: 82.0,
        ats_score: 84.0,
        experience_score: 80.0,
        education_score: 90.0,
        full_analysis: {
          skill_gap: {
            matched_skills: ['python', 'fastapi', 'postgresql', 'react', 'typescript', 'aws', 'agile'],
            missing_skills: ['docker', 'kubernetes', 'terraform'],
            recommended_paths: [
              {
                skill: 'docker',
                resources: [
                  { title: 'Docker Deep Dive (Pluralsight)', type: 'course', url: 'https://www.pluralsight.com' },
                  { title: 'Docker Official Get Started Guide', type: 'guide', url: 'https://docs.docker.com' }
                ]
              },
              {
                skill: 'kubernetes',
                resources: [
                  { title: 'CKAD Certification Prep (Udemy)', type: 'certification', url: 'https://www.udemy.com' }
                ]
              }
            ]
          }
        },
        recruiter_notes: {
          strengths: ['Highly proficient in core stack (Python, React)', 'Strong academic background', 'Proven tech lead experience'],
          risks: ['DevOps skill gaps (Docker, Terraform)', 'Short tenure at second position']
        }
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalysis();
  }, [searchParams]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-40 gap-3">
        <div className="w-10 h-10 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm text-slate-400">Loading Job Match results...</p>
      </div>
    );
  }

  const skillGap = analysis?.full_analysis?.skill_gap || {};
  const matched = skillGap.matched_skills || [];
  const missing = skillGap.missing_skills || [];
  const paths = skillGap.recommended_paths || [];
  
  const matchScore = analysis?.match_score || 0;
  const expScore = analysis?.experience_score || 0;
  const eduScore = analysis?.education_score || 0;

  const getFitLabel = (score: number) => {
    if (score >= 80) return { label: 'Excellent Match', color: 'text-emerald-400', border: 'border-emerald-500/20', bg: 'bg-emerald-500/5' };
    if (score >= 65) return { label: 'Good Match', color: 'text-indigo-400', border: 'border-indigo-500/20', bg: 'bg-indigo-500/5' };
    if (score >= 50) return { label: 'Borderline Match', color: 'text-amber-400', border: 'border-amber-500/20', bg: 'bg-amber-500/5' };
    return { label: 'Low Match', color: 'text-rose-400', border: 'border-rose-500/20', bg: 'bg-rose-500/5' };
  };

  const fit = getFitLabel(matchScore);

  return (
    <div className="space-y-8 animate-slide-up">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-black text-white tracking-tight">Job Match Assessment</h1>
        <p className="text-slate-400">Semantic comparison of candidate skills and experience against job description requirements.</p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold flex items-center gap-2">
          💡 {error}
        </div>
      )}

      {/* Top Section: Match summary card */}
      <div className={`glass-card p-8 bg-slate-900/40 border-white/5 flex flex-col md:flex-row items-center gap-8`}>
        {/* Animated Match Gauge */}
        <div className="relative w-36 h-36 flex-shrink-0 flex items-center justify-center">
          <svg className="absolute w-full h-full -rotate-90">
            <circle cx="72" cy="72" r="62" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
            <motion.circle
              cx="72"
              cy="72"
              r="62"
              fill="none"
              stroke={matchScore >= 80 ? '#10B981' : matchScore >= 65 ? '#6366F1' : '#F59E0B'}
              strokeWidth="8"
              strokeDasharray={2 * Math.PI * 62}
              initial={{ strokeDashoffset: 2 * Math.PI * 62 }}
              animate={{ strokeDashoffset: 2 * Math.PI * 62 * (1 - matchScore / 100) }}
              transition={{ duration: 1.2, ease: 'easeOut' }}
              strokeLinecap="round"
            />
          </svg>
          <div className="text-center z-10">
            <span className="text-3xl font-black text-white">{matchScore.toFixed(0)}%</span>
            <p className="text-xs text-slate-500 font-medium mt-0.5">Overlap</p>
          </div>
        </div>

        {/* Narrative info */}
        <div className="space-y-4 flex-1">
          <div>
            <span className={`badge ${fit.color} ${fit.bg} ${fit.border} mb-2`}>{fit.label}</span>
            <h2 className="text-xl font-bold text-white">Semantic Profile Fit</h2>
            <p className="text-sm text-slate-400 leading-relaxed mt-1">
              Candidate shows {matchScore.toFixed(0)}% direct compatibility with the role criteria. Technical match is strong, with core qualifications satisfied.
            </p>
          </div>

          {/* Sub-fit parameters */}
          <div className="grid grid-cols-2 gap-4 pt-2 border-t border-white/5">
            <div>
              <p className="text-xs text-slate-500 font-medium uppercase tracking-wider">Experience Match</p>
              <p className="text-sm font-bold text-slate-200 mt-1">{expScore.toFixed(0)}% match rate</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 font-medium uppercase tracking-wider">Education Match</p>
              <p className="text-sm font-bold text-slate-200 mt-1">{eduScore.toFixed(0)}% match rate</p>
            </div>
          </div>
        </div>
      </div>

      {/* Skill Gaps: Matched vs Missing */}
      <div className="grid md:grid-cols-2 gap-8">
        <div className="glass-card p-6 bg-slate-900/40 border-white/5 space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <span className="text-emerald-400">✓</span> Matched Skills ({matched.length})
          </h3>
          <div className="flex flex-wrap gap-2">
            {matched.map((s: string) => (
              <span key={s} className="skill-chip skill-chip-matched">
                {s}
              </span>
            ))}
            {matched.length === 0 && <span className="text-sm text-slate-500">None matched</span>}
          </div>
        </div>

        <div className="glass-card p-6 bg-slate-900/40 border-white/5 space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <span className="text-rose-400">✕</span> Missing Required Skills ({missing.length})
          </h3>
          <div className="flex flex-wrap gap-2">
            {missing.map((s: string) => (
              <span key={s} className="skill-chip skill-chip-missing">
                {s}
              </span>
            ))}
            {missing.length === 0 && <span className="text-sm text-slate-500">No missing skills detected</span>}
          </div>
        </div>
      </div>

      {/* Actionable Upskilling Learning Paths */}
      {paths.length > 0 && (
        <div className="glass-card p-6 bg-slate-900/40 border-white/5 space-y-6">
          <div>
            <h3 className="text-base font-bold text-white">Recommended Learning Paths</h3>
            <p className="text-xs text-slate-400 mt-1">Suggested courses and certifications to help the candidate close technical gaps.</p>
          </div>

          <div className="space-y-4">
            {paths.map((path: any) => (
              <div key={path.skill} className="p-4 rounded-xl bg-white/5 border border-white/5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <span className="text-xs font-semibold text-rose-400 uppercase tracking-wider">Skill Gap</span>
                  <h4 className="text-sm font-bold text-white mt-0.5 capitalize">{path.skill}</h4>
                </div>
                <div className="flex flex-wrap gap-3">
                  {path.resources?.map((res: any, idx: number) => (
                    <a
                      key={idx}
                      href={res.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3.5 py-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold hover:bg-indigo-500 hover:text-white transition-all"
                    >
                      📖 {res.title} ({res.type || 'Course'})
                    </a>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
