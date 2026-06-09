"""
TalentMind AI — Job Descriptions Router
Full CRUD for job descriptions.

Endpoints
─────────
  POST   /api/jobs           – create a new job description
  GET    /api/jobs           – list all JDs for current user
  GET    /api/jobs/{id}      – retrieve single JD
  PUT    /api/jobs/{id}      – update JD
  DELETE /api/jobs/{id}      – delete JD
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from auth.jwt_handler import get_current_user
from models.database import JobDescription, User, get_db
from schemas.schemas import (
    JobDescriptionCreate,
    JobDescriptionResponse,
    JobDescriptionUpdate,
)

router = APIRouter(prefix="/api/jobs", tags=["Job Descriptions"])


def _get_jd_or_404(jd_id: str, user_id: str, db: Session) -> JobDescription:
    jd = (
        db.query(JobDescription)
        .filter(JobDescription.id == jd_id, JobDescription.user_id == user_id)
        .first()
    )
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description not found.",
        )
    return jd


@router.post("", response_model=JobDescriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_job_description(
    payload: JobDescriptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobDescriptionResponse:
    """Create a new job description owned by the authenticated user."""
    jd = JobDescription(
        user_id=current_user.id,
        title=payload.title,
        company=payload.company,
        description=payload.description,
        required_skills=payload.required_skills or [],
        required_experience=payload.required_experience,
        required_education=payload.required_education,
    )
    db.add(jd)
    db.commit()
    db.refresh(jd)
    return JobDescriptionResponse.model_validate(jd)


@router.get("", response_model=List[JobDescriptionResponse])
async def list_job_descriptions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    search: Optional[str] = Query(default=None, description="Filter by title or company name"),
) -> List[JobDescriptionResponse]:
    """
    List all job descriptions for the current user.
    Supports optional ``search`` filter on title and company.
    """
    query = db.query(JobDescription).filter(JobDescription.user_id == current_user.id)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            JobDescription.title.ilike(pattern) | JobDescription.company.ilike(pattern)
        )

    jds = query.order_by(JobDescription.created_at.desc()).offset(skip).limit(limit).all()
    return [JobDescriptionResponse.model_validate(jd) for jd in jds]


@router.get("/{jd_id}", response_model=JobDescriptionResponse)
async def get_job_description(
    jd_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobDescriptionResponse:
    """Retrieve a single job description by ID."""
    jd = _get_jd_or_404(jd_id, current_user.id, db)
    return JobDescriptionResponse.model_validate(jd)


@router.put("/{jd_id}", response_model=JobDescriptionResponse)
async def update_job_description(
    jd_id: str,
    payload: JobDescriptionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobDescriptionResponse:
    """
    Partially update a job description.
    Only provided fields are changed (all fields are optional in the request body).
    """
    jd = _get_jd_or_404(jd_id, current_user.id, db)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(jd, field, value)

    db.commit()
    db.refresh(jd)
    return JobDescriptionResponse.model_validate(jd)


@router.delete("/{jd_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_description(
    jd_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete a job description and all its associated rankings."""
    jd = _get_jd_or_404(jd_id, current_user.id, db)
    db.delete(jd)
    db.commit()
