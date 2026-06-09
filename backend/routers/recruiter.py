"""
TalentMind AI — Recruiter Dashboard Router
Surfaces AI-generated recruiter notes, hiring recommendations, interview questions,
and skill-gap analysis per candidate / per analysis result.

Endpoints
─────────
  GET /api/recruiter/notes/{analysis_id}           – recruiter note for one analysis
  GET /api/recruiter/candidates                    – all candidates with latest notes
  GET /api/recruiter/candidate/{candidate_id}      – full profile with latest analysis
  GET /api/recruiter/skill-gap/{analysis_id}       – skill gap for one analysis
  GET /api/recruiter/questions/{analysis_id}       – interview questions
  POST /api/recruiter/notes/{analysis_id}/update   – manually update recruiter note
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from auth.jwt_handler import get_current_user
from models.database import (
    AnalysisResult, Candidate, RecruiterNote, Resume, SkillGap, User, get_db,
)
from schemas.schemas import CandidateDetail, RecruiterNoteResponse, SkillGapResponse, ChatRequest
from services.ollama_client import ollama_client

router = APIRouter(prefix="/api/recruiter", tags=["Recruiter"])


def _get_analysis_or_404(analysis_id: str, user_id: str, db: Session) -> AnalysisResult:
    ar = (
        db.query(AnalysisResult)
        .join(Resume, AnalysisResult.resume_id == Resume.id)
        .filter(AnalysisResult.id == analysis_id, Resume.user_id == user_id)
        .first()
    )
    if not ar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis result not found.")
    return ar


@router.get(
    "/notes/{analysis_id}",
    response_model=RecruiterNoteResponse,
    summary="Get AI-generated recruiter notes for an analysis",
)
async def get_recruiter_notes(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecruiterNoteResponse:
    """Return the recruiter notes (strengths, risks, recommendation, summary) for an analysis."""
    ar = _get_analysis_or_404(analysis_id, current_user.id, db)
    if not ar.recruiter_notes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No recruiter notes found for this analysis. Run analysis first.",
        )
    return RecruiterNoteResponse.model_validate(ar.recruiter_notes)


@router.post(
    "/notes/{analysis_id}/update",
    response_model=RecruiterNoteResponse,
    summary="Manually override recruiter notes",
)
async def update_recruiter_notes(
    analysis_id: str,
    hiring_recommendation: Optional[str] = Body(default=None),
    recommendation_justification: Optional[str] = Body(default=None),
    summary: Optional[str] = Body(default=None),
    strengths: Optional[List[str]] = Body(default=None),
    risks: Optional[List[str]] = Body(default=None),
    interview_questions: Optional[List[str]] = Body(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecruiterNoteResponse:
    """Allow a recruiter to manually override the AI-generated notes."""
    ar = _get_analysis_or_404(analysis_id, current_user.id, db)
    if not ar.recruiter_notes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No recruiter notes to update. Run analysis first.",
        )
    note: RecruiterNote = ar.recruiter_notes
    if hiring_recommendation is not None:
        note.hiring_recommendation = hiring_recommendation
    if recommendation_justification is not None:
        note.recommendation_justification = recommendation_justification
    if summary is not None:
        note.summary = summary
    if strengths is not None:
        note.strengths = strengths
    if risks is not None:
        note.risks = risks
    if interview_questions is not None:
        note.interview_questions = interview_questions
    db.commit()
    db.refresh(note)
    return RecruiterNoteResponse.model_validate(note)


@router.get(
    "/candidates",
    response_model=List[Dict[str, Any]],
    summary="List all candidates with their latest recruiter notes",
)
async def list_candidates_with_notes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    recommendation: Optional[str] = Query(default=None, description="Filter by hiring recommendation"),
) -> List[Dict[str, Any]]:
    """
    Return a list of all candidates belonging to the current user's resumes,
    enriched with the latest analysis scores and recruiter recommendation.
    """
    resumes = (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    for resume in resumes:
        if not resume.candidate:
            continue

        candidate: Candidate = resume.candidate

        # Get the latest analysis
        latest_analysis: Optional[AnalysisResult] = (
            db.query(AnalysisResult)
            .filter(AnalysisResult.resume_id == resume.id)
            .order_by(AnalysisResult.created_at.desc())
            .first()
        )

        rec_note = latest_analysis.recruiter_notes if latest_analysis else None

        # Filter by recommendation if requested
        if recommendation and rec_note and rec_note.hiring_recommendation != recommendation:
            continue
        if recommendation and not rec_note:
            continue

        result.append(
            {
                "candidate_id": candidate.id,
                "name": candidate.name,
                "email": candidate.email,
                "phone": candidate.phone,
                "skills": candidate.skills or [],
                "years_experience": candidate.years_experience,
                "resume_id": resume.id,
                "filename": resume.filename,
                "uploaded_at": resume.uploaded_at.isoformat() if resume.uploaded_at else None,
                "has_analysis": latest_analysis is not None,
                "ats_score": latest_analysis.ats_score if latest_analysis else None,
                "match_score": latest_analysis.match_score if latest_analysis else None,
                "hiring_recommendation": rec_note.hiring_recommendation if rec_note else None,
                "summary": rec_note.summary if rec_note else None,
                "analysis_id": latest_analysis.id if latest_analysis else None,
            }
        )

    return result


@router.get(
    "/candidate/{candidate_id}",
    response_model=Dict[str, Any],
    summary="Full candidate profile with latest analysis",
)
async def get_candidate_full_profile(
    candidate_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Return the complete candidate profile including education, experience, skills,
    all analysis results, and recruiter notes.
    """
    candidate = (
        db.query(Candidate)
        .join(Resume, Candidate.resume_id == Resume.id)
        .filter(Candidate.id == candidate_id, Resume.user_id == current_user.id)
        .first()
    )
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")

    resume = candidate.resume
    analyses = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.resume_id == resume.id)
        .order_by(AnalysisResult.created_at.desc())
        .all()
    )

    latest = analyses[0] if analyses else None
    note = latest.recruiter_notes if latest else None
    skill_gap = latest.skill_gap if latest else None

    return {
        "candidate": CandidateDetail.model_validate(candidate).model_dump(),
        "resume": {
            "id": resume.id,
            "filename": resume.filename,
            "uploaded_at": resume.uploaded_at.isoformat() if resume.uploaded_at else None,
        },
        "latest_analysis": {
            "id": latest.id if latest else None,
            "ats_score": latest.ats_score if latest else None,
            "match_score": latest.match_score if latest else None,
            "experience_score": latest.experience_score if latest else None,
            "education_score": latest.education_score if latest else None,
            "certification_score": latest.certification_score if latest else None,
            "formatting_score": latest.formatting_score if latest else None,
            "keywords_score": latest.keywords_score if latest else None,
            "suggestions": (latest.full_analysis or {}).get("suggestions", []) if latest else [],
            "created_at": latest.created_at.isoformat() if latest else None,
        },
        "recruiter_notes": {
            "strengths": note.strengths if note else [],
            "risks": note.risks if note else [],
            "hiring_recommendation": note.hiring_recommendation if note else None,
            "recommendation_justification": note.recommendation_justification if note else None,
            "summary": note.summary if note else None,
        },
        "interview_questions": note.interview_questions if note else [],
        "skill_gap": {
            "matched_skills": skill_gap.matched_skills if skill_gap else [],
            "missing_skills": skill_gap.missing_skills if skill_gap else [],
            "recommended_paths": skill_gap.recommended_paths if skill_gap else [],
        },
        "analysis_history_count": len(analyses),
    }


@router.get(
    "/skill-gap/{analysis_id}",
    response_model=SkillGapResponse,
    summary="Get skill gap analysis for a specific analysis",
)
async def get_skill_gap(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SkillGapResponse:
    """Return the skill gap (matched vs missing skills and learning paths) for an analysis."""
    ar = _get_analysis_or_404(analysis_id, current_user.id, db)
    if not ar.skill_gap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No skill gap data found for this analysis.",
        )
    return SkillGapResponse.model_validate(ar.skill_gap)


@router.get(
    "/questions/{analysis_id}",
    response_model=List[str],
    summary="Get AI-generated interview questions for a candidate",
)
async def get_interview_questions(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[str]:
    """Return the list of tailored interview questions generated during analysis."""
    ar = _get_analysis_or_404(analysis_id, current_user.id, db)
    if ar.recruiter_notes and ar.recruiter_notes.interview_questions:
        return ar.recruiter_notes.interview_questions
    # Fallback: extract from full_analysis blob
    full = ar.full_analysis or {}
    return full.get("interview_questions", [])


@router.post(
    "/{resume_id}/chat",
    response_model=Dict[str, str],
    summary="Chat dynamically with the AI Recruiter Copilot about a candidate",
)
async def chat_with_copilot(
    resume_id: str,
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """
    Given a user message, fetches the candidate's parsed data and analysis results,
    constructs a context-rich prompt, and asks Ollama to respond.
    """
    resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")
    
    candidate = resume.candidate
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate data not yet available for this resume.")

    latest_analysis = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.resume_id == resume.id)
        .order_by(AnalysisResult.created_at.desc())
        .first()
    )

    system_prompt = f"You are the TalentMind AI Recruiter Copilot. You assist human recruiters by answering questions about candidates based ONLY on the provided context."
    
    context = f"Candidate Name: {candidate.name}\n"
    context += f"Email: {candidate.email}\n"
    context += f"Experience: {candidate.years_experience} years\n"
    context += f"Skills: {', '.join(candidate.skills) if candidate.skills else 'None'}\n\n"
    
    if latest_analysis:
        context += f"ATS Score: {latest_analysis.ats_score}\n"
        context += f"Match Score: {latest_analysis.match_score}\n"
        if latest_analysis.recruiter_notes:
            note = latest_analysis.recruiter_notes
            context += f"Hiring Recommendation: {note.hiring_recommendation}\n"
            context += f"Recommendation Justification: {note.recommendation_justification}\n"
            context += f"Summary: {note.summary}\n"
            context += f"Strengths: {', '.join(note.strengths) if note.strengths else 'None'}\n"
            context += f"Risks: {', '.join(note.risks) if note.risks else 'None'}\n"

    full_prompt = f"Context:\n{context}\n\nRecruiter asks: {payload.message}\nAnswer concisely and professionally."
    
    response_text = await ollama_client.generate(prompt=full_prompt, system=system_prompt)
    
    return {"response": response_text}
