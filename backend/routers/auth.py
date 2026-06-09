"""
TalentMind AI — Authentication Router
Endpoints: POST /register, POST /login, GET /me, PUT /me
"""
from datetime import timedelta, datetime

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import uuid

from auth.jwt_handler import create_access_token, get_current_user
from auth.password import hash_password, verify_password
from config import settings
from models.database import AuditLog, User, JobDescription, Resume, Candidate, AnalysisResult, Ranking, SkillGap, RecruiterNote, get_db
from schemas.schemas import Token, UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def _log_action(db: Session, user_id: str | None, action: str, meta: dict, ip: str) -> None:
    """Helper to persist an audit log entry."""
    entry = AuditLog(user_id=user_id, action=action, action_metadata=meta, ip_address=ip)
    db.add(entry)
    db.commit()


def _seed_user_data(db: Session, user_id: str):
    """Seed the database with sample data for a new user."""
    # 1. Job Descriptions
    jd_frontend = JobDescription(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title="Senior Frontend Developer",
        company="TechCorp AI",
        description="Looking for an experienced React developer with strong TypeScript skills.",
        required_skills=["React", "TypeScript", "Next.js", "Tailwind CSS"],
        required_experience=5,
        required_education="Bachelor's in Computer Science",
        created_at=datetime.utcnow()
    )
    jd_backend = JobDescription(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title="Backend Engineer",
        company="TechCorp AI",
        description="Python backend engineer with FastAPI and PostgreSQL experience.",
        required_skills=["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
        required_experience=3,
        required_education="Bachelor's in Computer Science",
        created_at=datetime.utcnow()
    )
    db.add_all([jd_frontend, jd_backend])
    db.commit()

    # 2. Resumes and Candidates
    cands = [
        {"name": "Alex Johnson", "email": "alex.j@example.com", "phone": "+1 (555) 019-2834", "skills": ["React", "TypeScript", "Next.js", "Node.js", "GraphQL"], "exp": 6, "rank": 1, "final_score": 94, "score_f": 94, "score_b": 60, "rec_f": "Strong Hire", "rec_b": "Consider"},
        {"name": "Maria Garcia", "email": "maria.g@example.com", "phone": "+1 (555) 832-9102", "skills": ["Python", "FastAPI", "Docker", "PostgreSQL", "AWS"], "exp": 4, "rank": 2, "final_score": 87, "score_f": 45, "score_b": 92, "rec_f": "Reject", "rec_b": "Strong Hire"},
        {"name": "David Kim", "email": "david.k@example.com", "phone": "+1 (555) 748-3921", "skills": ["JavaScript", "React", "Python", "SQL"], "exp": 3, "rank": 3, "final_score": 81, "score_f": 81, "score_b": 75, "rec_f": "Hire", "rec_b": "Hire"},
    ]

    for c in cands:
        res = Resume(
            id=str(uuid.uuid4()),
            user_id=user_id,
            filename=f"{c['name'].replace(' ', '_')}_Resume.pdf",
            uploaded_at=datetime.utcnow(),
            raw_text="Sample resume text...",
            parsed_json={"skills": c['skills'], "experience": c['exp']}
        )
        db.add(res)
        db.commit()
        
        cand = Candidate(
            id=str(uuid.uuid4()),
            resume_id=res.id,
            name=c['name'],
            email=c['email'],
            phone=c['phone'],
            skills=c['skills'],
            years_experience=c['exp']
        )
        db.add(cand)
        db.commit()

        # Add Analysis Results and Rankings for Frontend JD
        ar_f = AnalysisResult(
            id=str(uuid.uuid4()),
            resume_id=res.id,
            job_description_id=jd_frontend.id,
            ats_score=c['score_f'],
            match_score=c['score_f'],
            skills_score=c['score_f'],
            experience_score=90,
            full_analysis={"summary": f"Analysis for {c['name']} against Frontend role."}
        )
        rk_f = Ranking(
            id=str(uuid.uuid4()),
            job_description_id=jd_frontend.id,
            candidate_id=cand.id,
            final_score=c['score_f'],
            ats_score=c['score_f'],
            recommendation=c['rec_f']
        )
        db.add_all([ar_f, rk_f])

        # Add Analysis Results and Rankings for Backend JD
        ar_b = AnalysisResult(
            id=str(uuid.uuid4()),
            resume_id=res.id,
            job_description_id=jd_backend.id,
            ats_score=c['score_b'],
            match_score=c['score_b'],
            skills_score=c['score_b'],
            experience_score=85,
            full_analysis={"summary": f"Analysis for {c['name']} against Backend role."}
        )
        rk_b = Ranking(
            id=str(uuid.uuid4()),
            job_description_id=jd_backend.id,
            candidate_id=cand.id,
            final_score=c['score_b'],
            ats_score=c['score_b'],
            recommendation=c['rec_b']
        )
        db.add_all([ar_b, rk_b])
    
    db.commit()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> Token:
    """
    Register a new user account.

    - Raises **409** if the email is already in use.
    - Returns a JWT token so the client is immediately authenticated.
    """
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        email=payload.email,
        name=payload.name,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    _seed_user_data(db, user.id)

    _log_action(
        db,
        user.id,
        "user_registered",
        {"email": user.email, "role": user.role},
        request.client.host if request.client else "unknown",
    )

    token = create_access_token(
        {"sub": user.email, "role": user.role},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=Token)
async def login(
    payload: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
) -> Token:
    """
    Authenticate with email + password and receive a JWT access token.

    - Raises **401** for invalid credentials.
    - Raises **403** if the account is disabled.
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        _log_action(
            db,
            None,
            "login_failed",
            {"email": payload.email},
            request.client.host if request.client else "unknown",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Contact your administrator.",
        )

    _log_action(
        db,
        user.id,
        "login_success",
        {"email": user.email},
        request.client.host if request.client else "unknown",
    )

    token = create_access_token(
        {"sub": user.email, "role": user.role},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Return the currently authenticated user's profile."""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_me(
    name: str | None = None,
    current_password: str | None = None,
    new_password: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Update the authenticated user's name and/or password."""
    if name:
        current_user.name = name

    if new_password:
        if not current_password or not verify_password(current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect.",
            )
        if len(new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="New password must be at least 6 characters.",
            )
        current_user.password_hash = hash_password(new_password)

    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)
