"""
TalentMind AI — Analysis Router
Orchestrates all 9 AI agents and returns the full analysis result.

Agent pipeline
──────────────
  Agent 1 — Resume Parser        (Ollama LLM)
  Agent 2 — ATS Scorer           (rule-based ATSEngine)
  Agent 3 — Job Match Scorer     (ATSEngine with JD context)
  Agent 4 — Experience Analyser  (ATSEngine sub-component)
  Agent 5 — Education Evaluator  (ATSEngine sub-component)
  Agent 6 — Skill Gap Detector   (set-diff on JD vs resume skills)
  Agent 7 — Keyword Optimiser    (ATSEngine keyword scorer)
  Agent 8 — LLM Narrative        (Ollama deep analysis)
  Agent 9 — Interview Q-Gen      (Ollama question generator)

Endpoints
─────────
  POST /api/analysis/resume/{resume_id}               – analyse without JD
  POST /api/analysis/resume/{resume_id}/job/{jd_id}   – analyse against a JD
  GET  /api/analysis/{analysis_id}                    – retrieve stored result
  GET  /api/analysis/resume/{resume_id}/latest         – latest result for resume
"""
import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth.jwt_handler import get_current_user
from models.database import (
    AnalysisResult, Candidate, JobDescription, RecruiterNote,
    Resume, SkillGap, User, get_db,
)
from schemas.schemas import AnalysisResultResponse
from services.ats_engine import ats_engine
from services.ollama_client import ollama_client

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _get_resume_or_404(resume_id: str, user_id: str, db: Session) -> Resume:
    r = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user_id).first()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found.")
    return r


def _get_jd_or_404(jd_id: str, user_id: str, db: Session) -> JobDescription:
    jd = (
        db.query(JobDescription)
        .filter(JobDescription.id == jd_id, JobDescription.user_id == user_id)
        .first()
    )
    if not jd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found.")
    return jd


async def _run_full_analysis(
    resume: Resume,
    jd: Optional[JobDescription],
    db: Session,
) -> AnalysisResult:
    """
    Execute all 9 agents and persist the result.
    Returns the newly created AnalysisResult ORM object.
    """
    parsed = resume.parsed_json or {}
    jd_text = jd.description if jd else None
    jd_skills = jd.required_skills if jd else None

    # ── Agent 1: Ensure we have parsed resume data ────────────────────────────
    if not parsed and resume.raw_text:
        parsed = await ollama_client.parse_resume(resume.raw_text)
        resume.parsed_json = parsed
        db.add(resume)

    # ── Agent 2 + 3 + 4 + 5 + 7: ATS Engine ─────────────────────────────────
    ats_result = ats_engine.calculate_score(
        parsed_resume=parsed,
        job_description=jd_text,
        jd_skills=jd_skills,
    )

    # ── Agent 3: Match score (skill overlap with JD) ──────────────────────────
    match_score = ats_result.skills_score if jd else 0.0

    # ── Agent 6: Skill Gap Detection ──────────────────────────────────────────
    candidate_skills = [s.lower() for s in (parsed.get("skills") or [])]
    required_skills = [s.lower() for s in (jd_skills or [])]
    matched_skills = [s for s in required_skills if s in candidate_skills]
    missing_skills = [s for s in required_skills if s not in candidate_skills]
    recommended_paths = _build_learning_paths(missing_skills)

    # ── Agent 8: LLM Narrative Analysis ───────────────────────────────────────
    llm_analysis = await ollama_client.analyze_resume(parsed, jd_text)

    # ── Agent 9: Interview Question Generation ────────────────────────────────
    interview_questions = await ollama_client.generate_interview_questions(parsed, jd_text, count=5)

    # ── Compose full_analysis blob ────────────────────────────────────────────
    full_analysis = {
        "ats_breakdown": {
            "skills_score": ats_result.skills_score,
            "experience_score": ats_result.experience_score,
            "education_score": ats_result.education_score,
            "certification_score": ats_result.certification_score,
            "formatting_score": ats_result.formatting_score,
            "keywords_score": ats_result.keywords_score,
            "details": ats_result.details,
        },
        "suggestions": ats_result.suggestions,
        "keywords_found": ats_result.keywords_found,
        "keywords_missing": ats_result.keywords_missing,
        "skill_gap": {
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "recommended_paths": recommended_paths,
        },
        "llm_analysis": llm_analysis,
        "interview_questions": interview_questions,
        "parsed_resume": parsed,
        "analysed_at": datetime.utcnow().isoformat(),
    }

    # ── Persist AnalysisResult ────────────────────────────────────────────────
    analysis = AnalysisResult(
        resume_id=resume.id,
        job_description_id=jd.id if jd else None,
        ats_score=ats_result.total_score,
        match_score=match_score,
        skills_score=ats_result.skills_score,
        experience_score=ats_result.experience_score,
        education_score=ats_result.education_score,
        certification_score=ats_result.certification_score,
        formatting_score=ats_result.formatting_score,
        keywords_score=ats_result.keywords_score,
        full_analysis=full_analysis,
    )
    db.add(analysis)
    db.flush()

    # ── Persist SkillGap ──────────────────────────────────────────────────────
    skill_gap = SkillGap(
        analysis_result_id=analysis.id,
        missing_skills=missing_skills,
        matched_skills=matched_skills,
        recommended_paths=recommended_paths,
    )
    db.add(skill_gap)

    # ── Persist RecruiterNote ─────────────────────────────────────────────────
    note = RecruiterNote(
        analysis_result_id=analysis.id,
        strengths=llm_analysis.get("strengths", []),
        risks=llm_analysis.get("risks", []),
        interview_questions=interview_questions,
        hiring_recommendation=llm_analysis.get("hiring_recommendation", "Consider"),
        recommendation_justification=llm_analysis.get("recommendation_justification", ""),
        summary=llm_analysis.get("summary", ""),
    )
    db.add(note)

    db.commit()
    db.refresh(analysis)
    return analysis


def _build_learning_paths(missing_skills: List[str]) -> List[dict]:
    """Generate simple curated learning resource suggestions for missing skills."""
    RESOURCES = {
        "kubernetes": [
            {"title": "Kubernetes: Up and Running", "type": "book", "url": "https://www.oreilly.com"},
            {"title": "CKAD Certification", "type": "course", "url": "https://www.udemy.com"},
        ],
        "terraform": [
            {"title": "HashiCorp Terraform Associate", "type": "certification", "url": "https://www.hashicorp.com"},
        ],
        "docker": [
            {"title": "Docker Deep Dive", "type": "course", "url": "https://www.pluralsight.com"},
        ],
        "aws": [
            {"title": "AWS Certified Developer – Associate", "type": "certification", "url": "https://aws.amazon.com/certification"},
        ],
        "python": [
            {"title": "Python for Everybody (Coursera)", "type": "course", "url": "https://www.coursera.org"},
        ],
        "machine learning": [
            {"title": "Machine Learning Specialization (Coursera)", "type": "course", "url": "https://www.coursera.org"},
        ],
        "react": [
            {"title": "React – The Complete Guide (Udemy)", "type": "course", "url": "https://www.udemy.com"},
        ],
        "sql": [
            {"title": "SQL for Data Science (Coursera)", "type": "course", "url": "https://www.coursera.org"},
        ],
    }
    paths = []
    for skill in missing_skills[:5]:
        sk_lower = skill.lower()
        resources = RESOURCES.get(sk_lower, [
            {"title": f"Learn {skill.title()} on LinkedIn Learning", "type": "course", "url": "https://www.linkedin.com/learning"},
        ])
        paths.append({"skill": skill, "resources": resources})
    return paths


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/resume/{resume_id}",
    response_model=AnalysisResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Analyse resume (no JD)",
)
async def analyse_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisResultResponse:
    """Run the full 9-agent pipeline on a resume without a job description."""
    resume = _get_resume_or_404(resume_id, current_user.id, db)
    analysis = await _run_full_analysis(resume, jd=None, db=db)
    return AnalysisResultResponse.model_validate(analysis)


@router.post(
    "/resume/{resume_id}/job/{jd_id}",
    response_model=AnalysisResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Analyse resume against a job description",
)
async def analyse_resume_against_jd(
    resume_id: str,
    jd_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisResultResponse:
    """Run the full 9-agent pipeline comparing a resume to a specific JD."""
    resume = _get_resume_or_404(resume_id, current_user.id, db)
    jd = _get_jd_or_404(jd_id, current_user.id, db)
    analysis = await _run_full_analysis(resume, jd=jd, db=db)
    return AnalysisResultResponse.model_validate(analysis)


@router.get(
    "/{analysis_id}",
    response_model=AnalysisResultResponse,
    summary="Get stored analysis result",
)
async def get_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisResultResponse:
    """Retrieve a previously computed analysis result by its ID."""
    analysis = (
        db.query(AnalysisResult)
        .join(Resume, AnalysisResult.resume_id == Resume.id)
        .filter(
            AnalysisResult.id == analysis_id,
            Resume.user_id == current_user.id,
        )
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis result not found.")
    return AnalysisResultResponse.model_validate(analysis)


@router.get(
    "/resume/{resume_id}/latest",
    response_model=AnalysisResultResponse,
    summary="Get the latest analysis for a resume",
)
async def get_latest_analysis(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisResultResponse:
    """Return the most recent analysis result for the given resume."""
    _get_resume_or_404(resume_id, current_user.id, db)
    analysis = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.resume_id == resume_id)
        .order_by(AnalysisResult.created_at.desc())
        .first()
    )
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No analysis found for this resume. Run an analysis first.",
        )
    return AnalysisResultResponse.model_validate(analysis)


@router.get(
    "/resume/{resume_id}/all",
    response_model=List[AnalysisResultResponse],
    summary="List all analysis results for a resume",
)
async def list_analyses_for_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[AnalysisResultResponse]:
    """Return all stored analysis results for the given resume."""
    _get_resume_or_404(resume_id, current_user.id, db)
    analyses = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.resume_id == resume_id)
        .order_by(AnalysisResult.created_at.desc())
        .all()
    )
    return [AnalysisResultResponse.model_validate(a) for a in analyses]
