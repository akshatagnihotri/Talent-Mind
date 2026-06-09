"""
TalentMind AI — Ranking Router
Ranks multiple candidates against a job description and returns a leaderboard.

Endpoints
─────────
  POST /api/ranking/job/{jd_id}/rank          – rank all analysed candidates for a JD
  GET  /api/ranking/job/{jd_id}/leaderboard   – retrieve stored leaderboard
  GET  /api/ranking/job/{jd_id}/top/{n}       – top-N candidates
"""
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from auth.jwt_handler import get_current_user
from models.database import (
    AnalysisResult, Candidate, JobDescription, Ranking, Resume, User, get_db,
)
from schemas.schemas import LeaderboardEntry, LeaderboardResponse, RankingResponse
from services.ranking_engine import ranking_engine

router = APIRouter(prefix="/api/ranking", tags=["Ranking"])


def _get_jd_or_404(jd_id: str, user_id: str, db: Session) -> JobDescription:
    jd = (
        db.query(JobDescription)
        .filter(JobDescription.id == jd_id, JobDescription.user_id == user_id)
        .first()
    )
    if not jd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found.")
    return jd


@router.post(
    "/job/{jd_id}/rank",
    response_model=LeaderboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Rank all candidates for a job description",
)
async def rank_candidates_for_job(
    jd_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LeaderboardResponse:
    """
    Compute or refresh the ranked leaderboard for a job description.

    Collects all ``AnalysisResult`` records linked to this JD,
    runs the ``RankingEngine``, persists ``Ranking`` rows, and
    returns the sorted leaderboard.

    Raises **404** if no analysed candidates exist for the JD.
    """
    jd = _get_jd_or_404(jd_id, current_user.id, db)

    # Gather all analysis results for this JD (scoped to user's own resumes)
    analysis_rows: List[AnalysisResult] = (
        db.query(AnalysisResult)
        .join(Resume, AnalysisResult.resume_id == Resume.id)
        .filter(
            AnalysisResult.job_description_id == jd_id,
            Resume.user_id == current_user.id,
        )
        .all()
    )

    if not analysis_rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No analysed candidates found for this job description. "
                "Run analysis (POST /api/analysis/resume/{id}/job/{jd_id}) first."
            ),
        )

    # Build input for the ranking engine
    candidates_input = []
    for ar in analysis_rows:
        candidate: Candidate = ar.resume.candidate if ar.resume else None
        candidates_input.append(
            {
                "id": candidate.id if candidate else ar.resume_id,
                "name": candidate.name if candidate else "Unknown",
                "email": candidate.email if candidate else None,
                "analysis": {
                    "ats_score": ar.ats_score,
                    "match_score": ar.match_score,
                    "experience_score": ar.experience_score,
                    "education_score": ar.education_score,
                    "certification_score": ar.certification_score,
                },
            }
        )

    ranked = ranking_engine.rank_candidates(candidates_input)

    # Delete old rankings for this JD and persist fresh ones
    db.query(Ranking).filter(Ranking.job_description_id == jd_id).delete()
    for cs in ranked:
        row = Ranking(
            job_description_id=jd_id,
            candidate_id=cs.candidate_id,
            rank=cs.rank,
            final_score=cs.final_score,
            ats_score=cs.ats_score,
            match_score=cs.skill_match,
            experience_score=cs.experience_score,
            education_score=cs.education_score,
            certification_score=cs.certification_score,
            recommendation=cs.recommendation,
        )
        db.add(row)
    db.commit()

    # Build response
    entries = []
    for cs in ranked:
        # Look up email from candidates_input
        candidate_email = next(
            (c.get("email") for c in candidates_input if c["id"] == cs.candidate_id),
            None,
        )
        entries.append(
            LeaderboardEntry(
                rank=cs.rank,
                candidate_id=cs.candidate_id,
                candidate_name=cs.candidate_name,
                candidate_email=candidate_email,
                final_score=cs.final_score,
                ats_score=cs.ats_score,
                match_score=cs.skill_match,
                experience_score=cs.experience_score,
                education_score=cs.education_score,
                certification_score=cs.certification_score,
                recommendation=cs.recommendation,
            )
        )

    return LeaderboardResponse(
        job_description_id=jd_id,
        job_title=jd.title,
        total_candidates=len(entries),
        entries=entries,
        generated_at=datetime.utcnow(),
    )


@router.get(
    "/job/{jd_id}/leaderboard",
    response_model=LeaderboardResponse,
    summary="Retrieve stored leaderboard for a job description",
)
async def get_leaderboard(
    jd_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LeaderboardResponse:
    """
    Return the most recently computed leaderboard from stored ``Ranking`` rows.
    Re-run ``POST /rank`` to refresh results.
    """
    jd = _get_jd_or_404(jd_id, current_user.id, db)

    rankings: List[Ranking] = (
        db.query(Ranking)
        .filter(Ranking.job_description_id == jd_id)
        .order_by(Ranking.rank)
        .all()
    )

    if not rankings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No leaderboard found. Run POST /api/ranking/job/{jd_id}/rank first.",
        )

    entries = []
    for r in rankings:
        candidate = r.candidate
        entries.append(
            LeaderboardEntry(
                rank=r.rank,
                candidate_id=r.candidate_id,
                candidate_name=candidate.name if candidate else "Unknown",
                candidate_email=candidate.email if candidate else None,
                final_score=r.final_score,
                ats_score=r.ats_score,
                match_score=r.match_score,
                experience_score=r.experience_score,
                education_score=r.education_score,
                certification_score=r.certification_score,
                recommendation=r.recommendation,
            )
        )

    return LeaderboardResponse(
        job_description_id=jd_id,
        job_title=jd.title,
        total_candidates=len(entries),
        entries=entries,
        generated_at=rankings[0].created_at if rankings else datetime.utcnow(),
    )


@router.get(
    "/job/{jd_id}/top/{n}",
    response_model=LeaderboardResponse,
    summary="Top-N candidates for a job description",
)
async def get_top_n_candidates(
    jd_id: str,
    n: int = Path(..., ge=1, le=100, description="Number of top candidates to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LeaderboardResponse:
    """Return the top-N ranked candidates for the job description."""
    jd = _get_jd_or_404(jd_id, current_user.id, db)

    rankings: List[Ranking] = (
        db.query(Ranking)
        .filter(Ranking.job_description_id == jd_id)
        .order_by(Ranking.rank)
        .limit(n)
        .all()
    )

    if not rankings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No ranking data found. Run POST /api/ranking/job/{jd_id}/rank first.",
        )

    entries = []
    for r in rankings:
        candidate = r.candidate
        entries.append(
            LeaderboardEntry(
                rank=r.rank,
                candidate_id=r.candidate_id,
                candidate_name=candidate.name if candidate else "Unknown",
                candidate_email=candidate.email if candidate else None,
                final_score=r.final_score,
                ats_score=r.ats_score,
                match_score=r.match_score,
                experience_score=r.experience_score,
                education_score=r.education_score,
                certification_score=r.certification_score,
                recommendation=r.recommendation,
            )
        )

    return LeaderboardResponse(
        job_description_id=jd_id,
        job_title=jd.title,
        total_candidates=len(entries),
        entries=entries,
        generated_at=datetime.utcnow(),
    )
