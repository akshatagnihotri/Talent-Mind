'use client';
import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import apiClient from '@/lib/api';

export default function RecruiterNotesPage() {
  const searchParams = useSearchParams();
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  const [activeTab, setActiveTab] = useState<'summary' | 'questions'>('summary');
  const [activeQuestionIdx, setActiveQuestionIdx] = useState<number | null>(null);

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
      setError('Unable to load recruiter notes. Displaying sandbox fallback notes.');
      setAnalysis({
        ats_score: 84.0,
        match_score: 82.0,
        recruiter_notes: {
          summary: 'A highly qualified software engineer with solid credentials. Strong proficiency in core stack including Python, FastAPI, React, and TypeScript. Has proven capability leading development tasks. Lacks minor DevOps tooling like Docker and Kubernetes but represents a strong match. We recommend fast-tracking this candidate to technical rounds.',
          strengths: [
            'Highly proficient in core stack (Python, React, FastAPI)',
            'Strong academic background with BS in Computer Science from top institution',
            'Quantified achievements including increasing product performance by 30%',
            'AWS Developer certification indicates solid cloud capabilities',
            'Strong soft skills - experience mentoring junior engineers'
          ],
          risks: [
            'Gaps in containerization skills (Docker, Kubernetes)',
            'Slightly shorter tenure (1 year) in the previous technical developer role',
            'No direct experience managing enterprise data pipelines'
          ],
          interview_questions: [
            'Can you walk us through a recent FastAPI project you built from scratch?',
            'How would you optimize a slow database query / connection pool in PostgreSQL?',
            'Describe a situation where you had to lead a project under a tight deadline.',
            'What is your experience deploying software on AWS using CI/CD pipelines?',
            'How do you approach code reviews and mentoring junior team members?'
          ],
          hiring_recommendation: 'Strong Hire',
          recommendation_justification: 'The candidate satisfies 80%+ of the key technical criteria. Strong programming foundations, direct familiarity with our stack, and cloud skills outweigh the minor Docker upskilling gap. Immediate tech interview is recommended.',
          culture_fit_notes: 'Demonstrates strong collaborative spirit, mentor experience, and clear communication skills.',
          salary_range_suggestion: '$110,000 – $130,000 based on experience'
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
        <p className="text-sm text-slate-400">Loading recruiter briefing...</p>
      </div>
    );
  }

  const notes = analysis?.recruiter_notes || {};
  const strengths = notes.strengths || [];
  const risks = notes.risks || [];
  const questions = notes.interview_questions || [];

  const getRecommendationStyle = (rec: string) => {
    const r = rec?.toLowerCase() || '';
    if (r.includes('strong')) return 'badge-strong-hire';
    if (r.includes('reject')) return 'badge-reject';
    if (r.includes('consider')) return 'badge-consider';
    return 'badge-hire';
  };

  return (
    <div className="space-y-8 animate-slide-up">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-black text-white tracking-tight">Recruiter Copilot Briefing</h1>
          <p className="text-slate-400">AI-generated candidate brief, interview questions, strengths & concerns analysis.</p>
        </div>
        
        <button
          onClick={() => window.print()}
          className="btn-secondary flex items-center gap-2 text-sm py-2.5 px-5"
        >
          🖨️ Export PDF Brief
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold flex items-center gap-2">
          💡 {error}
        </div>
      )}

      {/* Decision Summary Card */}
      <div className="glass-card p-8 bg-slate-900/40 border-white/5 grid md:grid-cols-4 gap-8 items-center">
        {/* Recommendation badge */}
        <div className="text-center md:border-r border-white/5 md:pr-8 py-2">
          <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider mb-2">Recommendation</p>
          <span className={`badge ${getRecommendationStyle(notes.hiring_recommendation)} text-sm py-2 px-5 rounded-full`}>
            {notes.hiring_recommendation || 'Consider'}
          </span>
          <p className="text-xs text-slate-400 mt-3">{notes.salary_range_suggestion || 'Market rate'}</p>
        </div>

        {/* Justification details */}
        <div className="md:col-span-3 space-y-2">
          <h2 className="text-lg font-bold text-white">Hiring Justification</h2>
          <p className="text-sm text-slate-300 leading-relaxed">
            {notes.recommendation_justification || 'Candidate matches requirements. Proceed to screen.'}
          </p>
          <p className="text-xs text-slate-500 font-semibold italic">Culture Fit: {notes.culture_fit_notes || 'Satisfactory'}</p>
        </div>
      </div>

      {/* Tabs Menu */}
      <div className="flex border-b border-white/5">
        <button
          onClick={() => setActiveTab('summary')}
          className="px-6 py-3 font-semibold text-sm transition-all relative"
          style={{ color: activeTab === 'summary' ? '#6366F1' : '#94A3B8' }}
        >
          📋 Brief Summary & Gaps
          {activeTab === 'summary' && (
            <motion.div layoutId="tabIndicator" className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#6366F1]" />
          )}
        </button>
        <button
          onClick={() => setActiveTab('questions')}
          className="px-6 py-3 font-semibold text-sm transition-all relative"
          style={{ color: activeTab === 'questions' ? '#6366F1' : '#94A3B8' }}
        >
          ❓ Guided Interview Questions ({questions.length})
          {activeTab === 'questions' && (
            <motion.div layoutId="tabIndicator" className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#6366F1]" />
          )}
        </button>
      </div>

      {/* Tab Panels */}
      <div className="space-y-8">
        {activeTab === 'summary' ? (
          <>
            {/* Summary paragraph */}
            <div className="glass-card p-6 bg-slate-900/40 border-white/5 space-y-3">
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Professional Summary</h3>
              <p className="text-sm text-slate-300 leading-relaxed">
                {notes.summary || 'Summary not generated yet.'}
              </p>
            </div>

            {/* Strengths & Risks columns */}
            <div className="grid md:grid-cols-2 gap-8">
              {/* Strengths */}
              <div className="glass-card p-6 bg-slate-900/40 border-white/5 space-y-4">
                <h3 className="text-base font-bold text-emerald-400 flex items-center gap-2">
                  <span>🟢</span> Candidate Strengths
                </h3>
                <ul className="space-y-3">
                  {strengths.map((str: string, i: number) => (
                    <li key={i} className="flex gap-3 text-sm text-slate-300 leading-relaxed">
                      <span className="text-emerald-400 font-bold">✓</span>
                      <span>{str}</span>
                    </li>
                  ))}
                  {strengths.length === 0 && <li className="text-sm text-slate-500">None identified</li>}
                </ul>
              </div>

              {/* Risks */}
              <div className="glass-card p-6 bg-slate-900/40 border-white/5 space-y-4">
                <h3 className="text-base font-bold text-rose-400 flex items-center gap-2">
                  <span>🔴</span> Identified Concerns / Risks
                </h3>
                <ul className="space-y-3">
                  {risks.map((risk: string, i: number) => (
                    <li key={i} className="flex gap-3 text-sm text-slate-300 leading-relaxed">
                      <span className="text-rose-400 font-bold">⚠</span>
                      <span>{risk}</span>
                    </li>
                  ))}
                  {risks.length === 0 && <li className="text-sm text-slate-500">None identified</li>}
                </ul>
              </div>
            </div>
          </>
        ) : (
          /* Guided Interview Questions Accordion */
          <div className="glass-card p-6 bg-slate-900/40 border-white/5 space-y-4">
            <h3 className="text-base font-bold text-white mb-2">Tailored Interview Questions</h3>
            <p className="text-xs text-slate-400">Ollama generated behavior and skill verification questions based on gaps.</p>
            
            <div className="space-y-3 pt-2">
              {questions.map((q: string, idx: number) => (
                <div
                  key={idx}
                  className="rounded-xl border border-white/5 bg-white/2 cursor-pointer overflow-hidden transition-all"
                  onClick={() => setActiveQuestionIdx(activeQuestionIdx === idx ? null : idx)}
                >
                  <div className="p-4 flex items-center justify-between gap-4">
                    <span className="text-sm font-semibold text-slate-200">{q}</span>
                    <span className="text-slate-500 text-xs">{activeQuestionIdx === idx ? '▲' : '▼'}</span>
                  </div>
                  <AnimatePresence>
                    {activeQuestionIdx === idx && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="px-4 pb-4 border-t border-white/5 pt-3"
                      >
                        <p className="text-xs text-indigo-400 font-bold uppercase tracking-wider mb-1">Recruiter Note / Evaluation Guide</p>
                        <p className="text-xs text-slate-400 leading-relaxed">
                          Listen for candidate details on project scale, specific API implementations, and how they handle conflicts or design trade-offs. The candidate should demonstrate clear reasoning and specify libraries or framework components used (e.g. async/await loops, SQL indexing, connection limits).
                        </p>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
