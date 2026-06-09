"""
TalentMind AI — Pydantic Schemas
All request/response models used across the API.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


# ═══════════════════════════════════════════════════════════════════════════════
# Auth / User
# ═══════════════════════════════════════════════════════════════════════════════
class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=120)
    password: str = Field(..., min_length=6)
    role: str = Field(default="recruiter", pattern="^(admin|recruiter|hiring_manager)$")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    email: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Resume
# ═══════════════════════════════════════════════════════════════════════════════
class ResumeUploadResponse(BaseModel):
    id: str
    filename: str
    uploaded_at: datetime
    message: str = "Resume uploaded and processed successfully"

    model_config = {"from_attributes": True}


class ResumeResponse(BaseModel):
    id: str
    filename: str
    uploaded_at: datetime
    user_id: str
    has_candidate: bool = False
    candidate: Optional[CandidateResponse] = None

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════════════════
# Candidate
# ═══════════════════════════════════════════════════════════════════════════════
class CandidateResponse(BaseModel):
    id: str
    resume_id: str
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    linkedin: Optional[str]
    skills: Optional[List[str]] = []
    years_experience: float = 0

    model_config = {"from_attributes": True}


class CandidateDetail(BaseModel):
    id: str
    resume_id: str
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    linkedin: Optional[str]
    education: Optional[List[Any]] = []
    skills: Optional[List[str]] = []
    certifications: Optional[List[str]] = []
    projects: Optional[List[Any]] = []
    work_experience: Optional[List[Any]] = []
    years_experience: float = 0

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════════════════
# Job Description
# ═══════════════════════════════════════════════════════════════════════════════
class JobDescriptionCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    company: Optional[str] = None
    description: str = Field(..., min_length=50)
    required_skills: Optional[List[str]] = []
    required_experience: int = Field(default=0, ge=0)
    required_education: Optional[str] = None


class JobDescriptionUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    description: Optional[str] = None
    required_skills: Optional[List[str]] = None
    required_experience: Optional[int] = None
    required_education: Optional[str] = None


class JobDescriptionResponse(BaseModel):
    id: str
    title: str
    company: Optional[str]
    description: str
    required_skills: Optional[List[str]] = []
    required_experience: int = 0
    required_education: Optional[str]
    created_at: datetime
    user_id: str

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════════════════
# Skill Gap
# ═══════════════════════════════════════════════════════════════════════════════
class SkillGapResponse(BaseModel):
    id: str
    analysis_result_id: str
    missing_skills: Optional[List[str]] = []
    matched_skills: Optional[List[str]] = []
    recommended_paths: Optional[List[Dict[str, Any]]] = []

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════════════════
# Recruiter Notes
# ═══════════════════════════════════════════════════════════════════════════════
class RecruiterNoteResponse(BaseModel):
    id: str
    analysis_result_id: str
    strengths: Optional[List[str]] = []
    risks: Optional[List[str]] = []
    interview_questions: Optional[List[str]] = []
    hiring_recommendation: Optional[str]
    recommendation_justification: Optional[str]
    summary: Optional[str]

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════════════════
# Analysis Result
# ═══════════════════════════════════════════════════════════════════════════════
class AnalysisResultResponse(BaseModel):
    id: str
    resume_id: str
    job_description_id: Optional[str]
    ats_score: float
    match_score: float
    skills_score: float
    experience_score: float
    education_score: float
    certification_score: float
    formatting_score: float
    keywords_score: float
    full_analysis: Optional[Dict[str, Any]]
    created_at: datetime
    skill_gap: Optional[SkillGapResponse] = None
    recruiter_notes: Optional[RecruiterNoteResponse] = None

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════════════════
# Ranking / Leaderboard
# ═══════════════════════════════════════════════════════════════════════════════
class RankingResponse(BaseModel):
    id: str
    job_description_id: str
    candidate_id: str
    rank: int
    final_score: float
    ats_score: float
    match_score: float
    experience_score: float
    education_score: float
    certification_score: float
    recommendation: str
    created_at: datetime
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None

    model_config = {"from_attributes": True}


class LeaderboardEntry(BaseModel):
    rank: int
    candidate_id: str
    candidate_name: str
    candidate_email: Optional[str]
    final_score: float
    ats_score: float
    match_score: float
    experience_score: float
    education_score: float
    certification_score: float
    recommendation: str


class LeaderboardResponse(BaseModel):
    job_description_id: str
    job_title: str
    total_candidates: int
    entries: List[LeaderboardEntry]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ═══════════════════════════════════════════════════════════════════════════════
# Analytics
# ═══════════════════════════════════════════════════════════════════════════════
class HiringFunnelStage(BaseModel):
    stage: str
    count: int
    percentage: float


class SkillDemandItem(BaseModel):
    skill: str
    count: int
    percentage: float


class ScoreTrend(BaseModel):
    date: str
    avg_ats_score: float
    candidate_count: int


class AnalyticsResponse(BaseModel):
    total_candidates: int
    total_resumes: int
    total_jobs: int
    avg_ats_score: float
    avg_match_score: float
    hiring_funnel: List[HiringFunnelStage]
    top_skills_demand: List[SkillDemandItem]
    score_trend: List[ScoreTrend]
    candidates_this_month: int
    strong_hire_count: int
    hire_count: int
    consider_count: int
    reject_count: int

class ChatRequest(BaseModel):
    message: str
