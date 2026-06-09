'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import UploadZone from '@/components/UploadZone';
import AgentStatus from '@/components/AgentStatus';
import apiClient from '@/lib/api';
import Navbar from '@/components/Navbar';

interface JobDescription {
  id: string;
  title: string;
  company: string;
}

export default function UploadPage() {
  const router = useRouter();
  const [files, setFiles] = useState<File[]>([]);
  const [jobs, setJobs] = useState<JobDescription[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>('');
  const [newJobTitle, setNewJobTitle] = useState('');
  const [newJobDesc, setNewJobDesc] = useState('');
  const [showNewJobForm, setShowNewJobForm] = useState(false);
  
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [error, setError] = useState('');
  const [analysisId, setAnalysisId] = useState('');

  useEffect(() => {
    // Ensure user is authenticated
    const token = typeof window !== 'undefined' ? localStorage.getItem('talentmind_token') : null;
    if (!token) {
      router.push('/auth');
      return;
    }

    const fetchJobs = async () => {
      try {
        const response = await apiClient.getJobs() as any;
        setJobs(response || []);
      } catch (err) {
        console.error('Failed to load jobs:', err);
      }
    };
    fetchJobs();
  }, [router]);

  const handleFilesChange = (newFiles: File[]) => {
    setFiles(newFiles);
  };

  const handleStartAnalysis = async () => {
    if (files.length === 0) {
      setError('Please select a resume file to upload.');
      return;
    }
    
    setError('');
    setIsUploading(true);
    setUploadProgress(15);
    
    try {
      let jobId = selectedJobId;
      
      if (showNewJobForm) {
        if (!newJobTitle || !newJobDesc) {
          throw new Error('Please fill in both Job Title and Description.');
        }
        setUploadProgress(30);
        const newJob = await apiClient.createJob({
          title: newJobTitle,
          company: 'TalentMind Org',
          description: newJobDesc,
          required_skills: [],
        }) as any;
        jobId = newJob.id;
      }
      
      setUploadProgress(50);
      // Upload file
      const uploadRes = await apiClient.uploadResume(files[0], jobId || undefined) as any;
      setUploadProgress(75);
      
      // Trigger multi-agent pipeline
      const analysisRes = await apiClient.analyzeResume(uploadRes.id, jobId || undefined) as any;
      setUploadProgress(100);
      setIsUploading(false);
      
      // Store current context in localStorage for easy dashboard access
      localStorage.setItem('talentmind_latest_resume_id', uploadRes.id);
      localStorage.setItem('talentmind_latest_analysis_id', analysisRes.id);
      if (jobId) {
        localStorage.setItem('talentmind_latest_job_id', jobId);
      } else {
        localStorage.removeItem('talentmind_latest_job_id');
      }
      
      setAnalysisId(analysisRes.id);
      setPipelineRunning(true);
    } catch (err: any) {
      setError(err.message || 'Analysis pipeline failed. Please check backend connection.');
      setIsUploading(false);
    }
  };

  const handlePipelineComplete = () => {
    router.push(`/dashboard/ats?id=${analysisId}`);
  };

  return (
    <div className="animated-bg min-h-screen text-slate-100 pb-16">
      <Navbar />

      <div className="max-w-4xl mx-auto px-6 pt-28">
        <div className="mb-8">
          <h1 className="text-3xl font-black tracking-tight text-white mb-2">Upload Candidate Resume</h1>
          <p className="text-slate-400">Upload a PDF or Word document to run the multi-agent AI screening pipeline.</p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 items-start">
          {/* Left: Upload controls & Form */}
          <div className="md:col-span-2 space-y-6">
            <AnimatePresence mode="wait">
              {!pipelineRunning ? (
                <motion.div
                  initial={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="space-y-6"
                >
                  {/* Step 1: Upload */}
                  <div className="glass-card p-6 bg-slate-900/40 border-white/5 space-y-4">
                    <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Step 1: Select Resume</h2>
                    <UploadZone onFilesChange={handleFilesChange} multiple={false} />
                  </div>

                  {/* Step 2: Job Description */}
                  <div className="glass-card p-6 bg-slate-900/40 border-white/5 space-y-4">
                    <div className="flex justify-between items-center">
                      <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Step 2: Job Target</h2>
                      <button
                        onClick={() => setShowNewJobForm(!showNewJobForm)}
                        className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold"
                      >
                        {showNewJobForm ? 'Select Existing Job' : 'Create Custom Job'}
                      </button>
                    </div>

                    {!showNewJobForm ? (
                      <div className="space-y-2">
                        <label className="block text-sm font-medium text-slate-300">Target Job Role</label>
                        <select
                          value={selectedJobId}
                          onChange={(e) => setSelectedJobId(e.target.value)}
                          className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:outline-none focus:border-indigo-500 transition-all text-sm"
                        >
                          <option value="" className="bg-slate-900 text-slate-400">General Resume Check (No job match)</option>
                          {jobs.map((job) => (
                            <option key={job.id} value={job.id} className="bg-slate-900 text-white">
                              {job.title} ({job.company || 'TalentMind'})
                            </option>
                          ))}
                        </select>
                      </div>
                    ) : (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        className="space-y-4"
                      >
                        <div className="space-y-2">
                          <label className="block text-sm font-medium text-slate-300">Job Title</label>
                          <input
                            type="text"
                            value={newJobTitle}
                            onChange={(e) => setNewJobTitle(e.target.value)}
                            placeholder="e.g. Senior Software Engineer"
                            className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 text-sm"
                          />
                        </div>
                        <div className="space-y-2">
                          <label className="block text-sm font-medium text-slate-300">Job Description</label>
                          <textarea
                            value={newJobDesc}
                            onChange={(e) => setNewJobDesc(e.target.value)}
                            placeholder="Paste the requirements, role description and key qualifications here..."
                            rows={6}
                            className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 text-sm"
                          />
                        </div>
                      </motion.div>
                    )}
                  </div>

                  {error && (
                    <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-semibold">
                      ⚠️ {error}
                    </div>
                  )}

                  {/* Trigger Button */}
                  <button
                    onClick={handleStartAnalysis}
                    disabled={isUploading}
                    className="w-full btn-primary py-4 rounded-xl flex items-center justify-center gap-2 font-bold text-base shadow-lg shadow-indigo-500/20 transition-all"
                  >
                    {isUploading ? (
                      <>
                        <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        Uploading Resume ({uploadProgress}%)...
                      </>
                    ) : (
                      '▶ Upload & Run AI Agents'
                    )}
                  </button>
                </motion.div>
              ) : (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="glass-card p-6 bg-slate-900/40 border-white/5"
                >
                  <AgentStatus autoRun={true} onComplete={handlePipelineComplete} />
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Right: Info Panels */}
          <div className="space-y-6">
            <div className="glass-card p-6 bg-slate-900/40 border-white/5 space-y-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <span>🛡️</span> Privacy Guarantee
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                TalentMind AI runs fully locally. Your resumes, job descriptions, and candidates are analyzed on your machine using Docker, Postgres, and local LLMs. No external data sharing.
              </p>
            </div>

            <div className="glass-card p-6 bg-slate-900/40 border-white/5 space-y-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <span>🤖</span> Pipeline Summary
              </h3>
              <ul className="text-xs text-slate-400 space-y-2.5">
                <li className="flex items-center gap-2">
                  <span className="text-emerald-400">✓</span> Parser extracts text content
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-emerald-400">✓</span> Skills normalized and classified
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-emerald-400">✓</span> ATS scoring calculated (6 dimensions)
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-emerald-400">✓</span> Job matching against target JD
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-emerald-400">✓</span> recruiter brief, strengths, risks, Qs
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-emerald-400">✓</span> Skill gap and learning paths identified
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
