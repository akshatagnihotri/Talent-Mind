'use client';
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import apiClient from '@/lib/api';

export default function CandidateRankingPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [selectedJobId, setSelectedJobId] = useState('');
  const [leaderboard, setLeaderboard] = useState<any>(null);
  
  const [loading, setLoading] = useState(false);
  const [rankingInProgress, setRankingInProgress] = useState(false);
  const [error, setError] = useState('');

  // Fetch jobs
  useEffect(() => {
    const loadJobs = async () => {
      try {
        const data = await apiClient.getJobs() as any;
        setJobs(data || []);
        if (data && data.length > 0) {
          // Default to the first job
          setSelectedJobId(data[0].id);
        }
      } catch (err) {
        console.error(err);
      }
    };
    loadJobs();
  }, []);

  const loadLeaderboard = async (jobId: string) => {
    if (!jobId) return;
    setLoading(true);
    setError('');
    try {
      const data = await apiClient.getLeaderboard(jobId) as any;
      setLeaderboard(data);
    } catch (err: any) {
      console.error(err);
      setError('Unable to load leaderboard. Showing mock ranked list for demo.');
      // Inject fallback mock ranked candidates list
      setLeaderboard({
        job_title: 'Senior Software Engineer',
        total_candidates: 3,
        entries: [
          { rank: 1, candidate_id: '1', candidate_name: 'Alex Johnson', candidate_email: 'alex@example.com', final_score: 88.5, ats_score: 91, match_score: 88, experience_score: 90, education_score: 90, certification_score: 80, recommendation: 'Strong Hire' },
          { rank: 2, candidate_id: '2', candidate_name: 'Maria Garcia', candidate_email: 'maria@example.com', final_score: 82.2, ats_score: 84, match_score: 82, experience_score: 80, education_score: 90, certification_score: 60, recommendation: 'Hire' },
          { rank: 3, candidate_id: '3', candidate_name: 'David Kim', candidate_email: 'david@example.com', final_score: 67.8, ats_score: 72, match_score: 65, experience_score: 60, education_score: 75, certification_score: 40, recommendation: 'Consider' },
        ]
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedJobId) {
      loadLeaderboard(selectedJobId);
    }
  }, [selectedJobId]);

  const handleTriggerRanking = async () => {
    if (!selectedJobId) return;
    setRankingInProgress(true);
    setError('');
    try {
      // Fetch all resumes
      const resumes = await apiClient.getResumes() as any[];
      const resumeIds = resumes.map((r) => r.id);
      
      if (resumeIds.length === 0) {
        throw new Error('Please upload at least one candidate resume before ranking.');
      }

      await apiClient.rankCandidates(selectedJobId, resumeIds);
      await loadLeaderboard(selectedJobId);
    } catch (err: any) {
      setError(err.message || 'Ranking failed. Local Ollama LLM may be offline.');
    } finally {
      setRankingInProgress(false);
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
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-black text-white tracking-tight">Candidate Leaderboard</h1>
          <p className="text-slate-400">AI-powered multi-factor ranking based on ATS score, skills match, experience, and certifications.</p>
        </div>
        
        {selectedJobId && (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            disabled={rankingInProgress}
            onClick={handleTriggerRanking}
            className="btn-primary flex items-center gap-2 disabled:opacity-50"
          >
            {rankingInProgress ? '⏳ Ranking...' : '🏆 Run AI Ranking'}
          </motion.button>
        )}
      </div>

      {/* Select Job description dropdown */}
      <div className="glass-card p-6 bg-slate-900/40 border-white/5 space-y-4">
        <label className="block text-sm font-medium text-slate-300">Select Target Job Description</label>
        <select
          value={selectedJobId}
          onChange={(e) => setSelectedJobId(e.target.value)}
          className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:outline-none focus:border-indigo-500 transition-all text-sm"
        >
          {jobs.length === 0 && <option value="" className="bg-slate-900 text-slate-500">No Job Descriptions Created. Create one in Upload first.</option>}
          {jobs.map((job) => (
            <option key={job.id} value={job.id} className="bg-slate-900 text-white">
              {job.title} ({job.company || 'TalentMind'})
            </option>
          ))}
        </select>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold flex items-center gap-2">
          💡 {error}
        </div>
      )}

      {/* Leaderboard list */}
      <div className="glass-card border-white/5 bg-slate-900/40 p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-bold text-white">Ranked Candidates List</h2>
          <span className="text-xs text-slate-400 uppercase tracking-wider">{leaderboard?.total_candidates || 0} Evaluated</span>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-sm text-slate-400">Ranking candidates...</p>
          </div>
        ) : !leaderboard || leaderboard.entries?.length === 0 ? (
          <div className="text-center py-20 space-y-4">
            <span className="text-5xl block">🏆</span>
            <h3 className="text-base font-bold text-white">No candidates ranked yet</h3>
            <p className="text-sm text-slate-400 max-w-sm mx-auto">Upload resumes and link them to this job description, then click "Run AI Ranking" to build the leaderboard.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Candidate</th>
                  <th>ATS Score</th>
                  <th>Job Match</th>
                  <th>Composite Score</th>
                  <th>Hiring Recommendation</th>
                </tr>
              </thead>
              <tbody>
                {leaderboard.entries.map((entry: any) => (
                  <tr key={entry.candidate_id} className="hover:bg-white/5 transition-colors">
                    <td>
                      <div className="flex items-center justify-center w-8 h-8 rounded-full font-black text-sm"
                        style={{
                          background: entry.rank === 1 ? 'rgba(245,158,11,0.15)' : entry.rank === 2 ? 'rgba(148,163,184,0.15)' : 'rgba(255,255,255,0.05)',
                          color: entry.rank === 1 ? '#F59E0B' : entry.rank === 2 ? '#94A3B8' : '#F8FAFC',
                          border: entry.rank === 1 ? '1px solid rgba(245,158,11,0.3)' : 'none'
                        }}
                      >
                        {entry.rank}
                      </div>
                    </td>
                    <td>
                      <div className="font-semibold text-white">{entry.candidate_name}</div>
                      <div className="text-xs text-slate-500">{entry.candidate_email || 'N/A'}</div>
                    </td>
                    <td>
                      <div className="text-sm font-semibold text-slate-300">{entry.ats_score.toFixed(0)}/100</div>
                    </td>
                    <td>
                      <div className="text-sm font-semibold text-slate-300">{entry.match_score.toFixed(0)}%</div>
                    </td>
                    <td>
                      <div className="text-sm font-black text-emerald-400">{entry.final_score.toFixed(1)}/100</div>
                    </td>
                    <td>
                      <span className={`badge ${getRecommendationStyle(entry.recommendation)}`}>
                        {entry.recommendation}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
