"""
TalentMind AI — Analytics Router
Provides dashboard metrics, hiring-funnel stats, skill-demand heatmap, and score trends.

Endpoints
─────────
  GET /api/analytics/dashboard   – full analytics payload for the dashboard
  GET /api/analytics/funnel      – hiring funnel breakdown
  GET /api/analytics/skills      – top skill demand across all analysed resumes
  GET /api/analytics/trends      – ATS score trend over time
"""
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth.jwt_handler import get_current_user
from models.database import (
    AnalysisResult, Candidate, JobDescription, RecruiterNote, Resume, User, get_db,
)
from schemas.schemas import (
    AnalyticsResponse,
    HiringFunnelStage,
    ScoreTrend,
    SkillDemandItem,
)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


def _collect_analytics(user_id: str, db: Session) -> AnalyticsResponse:
    """
    Compute all analytics metrics for the current user's data.
    Everything is scoped to the authenticated user for data isolation.
    """
    # ── Basic counts ──────────────────────────────────────────────────────────
    total_resumes = db.query(Resume).filter(Resume.user_id == user_id).count()
    total_candidates = (
        db.query(Candidate)
        .join(Resume, Candidate.resume_id == Resume.id)
        .filter(Resume.user_id == user_id)
        .count()
    )
    total_jobs = db.query(JobDescription).filter(JobDescription.user_id == user_id).count()

    # ── Score averages ────────────────────────────────────────────────────────
    analyses: List[AnalysisResult] = (
        db.query(AnalysisResult)
        .join(Resume, AnalysisResult.resume_id == Resume.id)
        .filter(Resume.user_id == user_id)
        .all()
    )

    avg_ats = round(sum(a.ats_score for a in analyses) / len(analyses), 1) if analyses else 0.0
    avg_match = round(sum(a.match_score for a in analyses) / len(analyses), 1) if analyses else 0.0

    # ── Hiring funnel ─────────────────────────────────────────────────────────
    recommendation_counts: Dict[str, int] = {
        "Strong Hire": 0,
        "Hire": 0,
        "Consider": 0,
        "Reject": 0,
    }
    notes: List[RecruiterNote] = (
        db.query(RecruiterNote)
        .join(AnalysisResult, RecruiterNote.analysis_result_id == AnalysisResult.id)
        .join(Resume, AnalysisResult.resume_id == Resume.id)
        .filter(Resume.user_id == user_id)
        .all()
    )
    for note in notes:
        rec = note.hiring_recommendation or "Reject"
        recommendation_counts[rec] = recommendation_counts.get(rec, 0) + 1

    total_with_notes = sum(recommendation_counts.values())
    hiring_funnel = [
        HiringFunnelStage(
            stage=stage,
            count=count,
            percentage=round(count / total_with_notes * 100, 1) if total_with_notes else 0.0,
        )
        for stage, count in recommendation_counts.items()
    ]

    strong_hire = recommendation_counts["Strong Hire"]
    hire = recommendation_counts["Hire"]
    consider = recommendation_counts["Consider"]
    reject = recommendation_counts["Reject"]

    # ── Skill demand ──────────────────────────────────────────────────────────
    all_skills: List[str] = []
    candidates: List[Candidate] = (
        db.query(Candidate)
        .join(Resume, Candidate.resume_id == Resume.id)
        .filter(Resume.user_id == user_id)
        .all()
    )
    for cand in candidates:
        if cand.skills:
            all_skills.extend([s.lower().strip() for s in cand.skills if s])

    skill_counter = Counter(all_skills)
    total_skill_mentions = sum(skill_counter.values()) or 1
    top_skills: List[SkillDemandItem] = [
        SkillDemandItem(
            skill=skill.title(),
            count=count,
            percentage=round(count / total_skill_mentions * 100, 1),
        )
        for skill, count in skill_counter.most_common(15)
    ]

    # ── Score trend (last 30 days, grouped by day) ────────────────────────────
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_analyses: List[AnalysisResult] = (
        db.query(AnalysisResult)
        .join(Resume, AnalysisResult.resume_id == Resume.id)
        .filter(
            Resume.user_id == user_id,
            AnalysisResult.created_at >= thirty_days_ago,
        )
        .order_by(AnalysisResult.created_at)
        .all()
    )

    daily_data: Dict[str, List[float]] = {}
    for ar in recent_analyses:
        day_key = ar.created_at.strftime("%Y-%m-%d")
        daily_data.setdefault(day_key, []).append(ar.ats_score)

    score_trend: List[ScoreTrend] = [
        ScoreTrend(
            date=day,
            avg_ats_score=round(sum(scores) / len(scores), 1),
            candidate_count=len(scores),
        )
        for day, scores in sorted(daily_data.items())
    ]

    # ── Candidates this month ─────────────────────────────────────────────────
    first_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    candidates_this_month = (
        db.query(Resume)
        .filter(Resume.user_id == user_id, Resume.uploaded_at >= first_of_month)
        .count()
    )

    return AnalyticsResponse(
        total_candidates=total_candidates,
        total_resumes=total_resumes,
        total_jobs=total_jobs,
        avg_ats_score=avg_ats,
        avg_match_score=avg_match,
        hiring_funnel=hiring_funnel,
        top_skills_demand=top_skills,
        score_trend=score_trend,
        candidates_this_month=candidates_this_month,
        strong_hire_count=strong_hire,
        hire_count=hire,
        consider_count=consider,
        reject_count=reject,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/dashboard",
    response_model=AnalyticsResponse,
    summary="Full analytics dashboard payload",
)
async def get_dashboard_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalyticsResponse:
    """
    Returns all analytics metrics in a single call:
    - Total candidates, resumes, and jobs
    - Average ATS and match scores
    - Hiring funnel breakdown
    - Top 15 in-demand skills
    - 30-day ATS score trend
    - Month-to-date candidate count
    """
    return _collect_analytics(current_user.id, db)


@router.get(
    "/funnel",
    response_model=List[HiringFunnelStage],
    summary="Hiring funnel stage breakdown",
)
async def get_hiring_funnel(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[HiringFunnelStage]:
    """Return the count and percentage for each hiring recommendation category."""
    analytics = _collect_analytics(current_user.id, db)
    return analytics.hiring_funnel


@router.get(
    "/skills",
    response_model=List[SkillDemandItem],
    summary="Top skill demand across all analysed resumes",
)
async def get_skill_demand(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[SkillDemandItem]:
    """Return the 15 most frequently appearing skills across all candidate profiles."""
    analytics = _collect_analytics(current_user.id, db)
    return analytics.top_skills_demand


@router.get(
    "/trends",
    response_model=List[ScoreTrend],
    summary="ATS score trend over the last 30 days",
)
async def get_score_trends(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[ScoreTrend]:
    """Return daily average ATS scores for the past 30 days."""
    analytics = _collect_analytics(current_user.id, db)
    return analytics.score_trend


@router.get(
    "/summary",
    response_model=Dict[str, Any],
    summary="Quick summary card metrics",
)
async def get_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Return a lightweight summary suitable for dashboard header cards."""
    a = _collect_analytics(current_user.id, db)
    return {
        "total_candidates": a.total_candidates,
        "total_jobs": a.total_jobs,
        "avg_ats_score": a.avg_ats_score,
        "avg_match_score": a.avg_match_score,
        "strong_hire_count": a.strong_hire_count,
        "candidates_this_month": a.candidates_this_month,
    }
