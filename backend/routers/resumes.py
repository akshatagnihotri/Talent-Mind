"""
TalentMind AI — Resumes Router
Endpoints:
  POST   /api/resumes/upload          – upload and process a PDF/DOCX
  GET    /api/resumes                 – list current user's resumes
  GET    /api/resumes/{id}            – get resume detail + candidate info
  DELETE /api/resumes/{id}            – delete resume and all associated data
  GET    /api/resumes/{id}/candidate  – get parsed candidate profile
"""
import os
import shutil
import uuid
from pathlib import Path
from typing import List

import aiofiles
from fastapi import (
    APIRouter, Depends, File, HTTPException, UploadFile, status
)
from sqlalchemy.orm import Session

from auth.jwt_handler import get_current_user
from config import settings
from models.database import Candidate, Resume, User, get_db
from schemas.schemas import CandidateDetail, ResumeResponse, ResumeUploadResponse, CandidateResponse
from services.ollama_client import ollama_client
from services.pdf_extractor import extract_text_from_file

router = APIRouter(prefix="/api/resumes", tags=["Resumes"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def _get_upload_dir() -> Path:
    upload_path = Path(settings.UPLOAD_DIR)
    upload_path.mkdir(parents=True, exist_ok=True)
    return upload_path


@router.post("/upload", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeUploadResponse:
    """
    Upload a PDF or DOCX resume.

    Processing pipeline:
    1. Validate extension and file size.
    2. Save to ``UPLOAD_DIR``.
    3. Extract raw text via pdfminer / python-docx.
    4. Parse structured fields via Ollama (or demo mode).
    5. Persist ``Resume`` and ``Candidate`` ORM records.
    """
    # ── Validate extension ────────────────────────────────────────────────────
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{suffix}'. Allowed: PDF, DOCX, DOC.",
        )

    # ── Read & size-check ─────────────────────────────────────────────────────
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_MB} MB.",
        )

    # ── Save to disk ──────────────────────────────────────────────────────────
    upload_dir = _get_upload_dir()
    unique_name = f"{uuid.uuid4()}{suffix}"
    file_path = upload_dir / unique_name

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(file_bytes)

    # ── Extract text ──────────────────────────────────────────────────────────
    try:
        raw_text = await extract_text_from_file(str(file_path))
    except Exception as exc:
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not extract text from the file: {exc}",
        )

    # ── Parse via LLM ─────────────────────────────────────────────────────────
    parsed = await ollama_client.parse_resume(raw_text)

    # ── Persist Resume ────────────────────────────────────────────────────────
    resume = Resume(
        user_id=current_user.id,
        filename=file.filename,
        raw_text=raw_text[:50000],   # cap stored raw text at 50k chars
        parsed_json=parsed,
        file_path=str(file_path),
    )
    db.add(resume)
    db.flush()  # get resume.id before inserting candidate

    # ── Persist Candidate ─────────────────────────────────────────────────────
    years_exp = _estimate_years(parsed.get("work_experience", []))
    candidate = Candidate(
        resume_id=resume.id,
        name=parsed.get("name"),
        email=parsed.get("email"),
        phone=parsed.get("phone"),
        linkedin=parsed.get("linkedin"),
        education=parsed.get("education", []),
        skills=parsed.get("skills", []),
        certifications=parsed.get("certifications", []),
        projects=parsed.get("projects", []),
        work_experience=parsed.get("work_experience", []),
        years_experience=years_exp,
    )
    db.add(candidate)
    db.commit()
    db.refresh(resume)

    return ResumeUploadResponse(
        id=resume.id,
        filename=resume.filename,
        uploaded_at=resume.uploaded_at,
        message="Resume uploaded and processed successfully.",
    )


@router.get("", response_model=List[ResumeResponse])
async def list_resumes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
) -> List[ResumeResponse]:
    """Return a paginated list of resumes belonging to the current user."""
    resumes = (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.uploaded_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    result = []
    for r in resumes:
        resp = ResumeResponse(
            id=r.id,
            filename=r.filename,
            uploaded_at=r.uploaded_at,
            user_id=r.user_id,
            has_candidate=r.candidate is not None,
            candidate=CandidateResponse.model_validate(r.candidate) if r.candidate else None,
        )
        result.append(resp)
    return result


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeResponse:
    """Retrieve a single resume by ID (must belong to current user)."""
    resume = _get_resume_or_404(resume_id, current_user.id, db)
    return ResumeResponse(
        id=resume.id,
        filename=resume.filename,
        uploaded_at=resume.uploaded_at,
        user_id=resume.user_id,
        has_candidate=resume.candidate is not None,
        candidate=CandidateResponse.model_validate(resume.candidate) if resume.candidate else None,
    )


@router.get("/{resume_id}/candidate", response_model=CandidateDetail)
async def get_resume_candidate(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CandidateDetail:
    """Return the structured candidate profile extracted from a resume."""
    resume = _get_resume_or_404(resume_id, current_user.id, db)
    if not resume.candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No candidate profile found for this resume.",
        )
    return CandidateDetail.model_validate(resume.candidate)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a resume and all associated data (candidate, analysis results, skill gaps, etc.).
    Also removes the uploaded file from disk.
    """
    resume = _get_resume_or_404(resume_id, current_user.id, db)

    # Remove file from disk
    if resume.file_path:
        file_path = Path(resume.file_path)
        if file_path.exists():
            file_path.unlink(missing_ok=True)

    db.delete(resume)
    db.commit()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_resume_or_404(resume_id: str, user_id: str, db: Session) -> Resume:
    """Fetch a resume by ID, scoped to the current user; raise 404 otherwise."""
    resume = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == user_id)
        .first()
    )
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found.",
        )
    return resume


def _estimate_years(work_experience: list) -> float:
    """Estimate total years of experience from work_experience list."""
    import re
    total = 0.0
    for exp in work_experience:
        years_str = str(exp.get("years", "") or exp.get("duration", "")) if isinstance(exp, dict) else ""
        matches = re.findall(r"\d{4}", years_str)
        if len(matches) >= 2:
            total += abs(int(matches[-1]) - int(matches[0]))
        elif len(matches) == 1:
            total += 1.0
    return round(total, 1)
