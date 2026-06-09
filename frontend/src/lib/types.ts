// ─── Auth ───────────────────────────────────────────────────────────────────
export interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'recruiter' | 'viewer';
  avatar?: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// ─── Resume ──────────────────────────────────────────────────────────────────
export interface Resume {
  id: string;
  filename: string;
  candidate_name: string;
  candidate_email: string;
  candidate_phone?: string;
  candidate_linkedin?: string;
  file_url: string;
  status: 'pending' | 'processing' | 'analyzed' | 'error';
  job_description_id?: string;
  uploaded_at: string;
  analysis_id?: string;
}

export interface ParsedResume {
  name: string;
  email: string;
  phone?: string;
  linkedin?: string;
  summary?: string;
  skills: string[];
  experience: WorkExperience[];
  education: Education[];
  certifications: string[];
  languages: string[];
}

export interface WorkExperience {
  company: string;
  title: string;
  start_date: string;
  end_date?: string;
  description: string;
  technologies: string[];
}

export interface Education {
  institution: string;
  degree: string;
  field: string;
  graduation_year: number;
  gpa?: number;
}

// ─── Job Description ─────────────────────────────────────────────────────────
export interface JobDescription {
  id: string;
  title: string;
  company: string;
  description: string;
  required_skills: string[];
  preferred_skills: string[];
  experience_years: number;
  created_at: string;
  resume_count?: number;
}

// ─── Analysis ────────────────────────────────────────────────────────────────
export type RecommendationType = 'Strong Hire' | 'Hire' | 'Consider' | 'Reject';

export interface ATSScore {
  total: number;
  skills: number;
  experience: number;
  education: number;
  certifications: number;
  formatting: number;
  keywords: number;
}

export interface SkillAnalysis {
  matched: string[];
  missing: string[];
  additional: string[];
  match_percentage: number;
}

export interface Analysis {
  id: string;
  resume_id: string;
  job_description_id?: string;
  ats_score: ATSScore;
  job_match_percentage: number;
  skill_analysis: SkillAnalysis;
  recommendation: RecommendationType;
  strengths: string[];
  risks: string[];
  suggestions: string[];
  interview_questions: string[];
  recruiter_summary: string;
  recommendation_justification: string;
  experience_years: number;
  created_at: string;
  candidate?: ParsedResume;
}

// ─── Ranking ─────────────────────────────────────────────────────────────────
export interface RankedCandidate {
  rank: number;
  resume_id: string;
  candidate_name: string;
  candidate_email: string;
  ats_score: number;
  match_percentage: number;
  experience_years: number;
  recommendation: RecommendationType;
  analysis_id: string;
  key_skills: string[];
}

export interface RankingResult {
  job_description_id: string;
  job_title: string;
  company: string;
  total_candidates: number;
  strong_hire_count: number;
  hire_count: number;
  consider_count: number;
  reject_count: number;
  average_score: number;
  candidates: RankedCandidate[];
  created_at: string;
}

// ─── Analytics ───────────────────────────────────────────────────────────────
export interface DashboardAnalytics {
  total_resumes: number;
  avg_ats_score: number;
  strong_hire_percentage: number;
  avg_processing_time_seconds: number;
  score_trend: ScoreTrend[];
  skill_demand: SkillDemand[];
  recommendation_distribution: RecommendationDist[];
  candidate_volume: CandidateVolume[];
}

export interface ScoreTrend {
  date: string;
  avg_score: number;
  count: number;
}

export interface SkillDemand {
  skill: string;
  count: number;
  match_rate: number;
}

export interface RecommendationDist {
  recommendation: RecommendationType;
  count: number;
  percentage: number;
}

export interface CandidateVolume {
  date: string;
  count: number;
}

// ─── Agent Pipeline ───────────────────────────────────────────────────────────
export interface AgentStep {
  id: string;
  name: string;
  description: string;
  icon: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  duration?: number;
}

// ─── Chat ─────────────────────────────────────────────────────────────────────
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  candidate_id?: string;
}

// ─── UI State ─────────────────────────────────────────────────────────────────
export interface UploadState {
  files: File[];
  uploading: boolean;
  progress: number;
  error?: string;
  success?: boolean;
}
