"""
TalentMind AI — SQLAlchemy ORM Models
Defines all database tables and their relationships.
"""
from sqlalchemy import (
    create_engine, Column, String, Integer, Float, Boolean,
    DateTime, Text, JSON, ForeignKey,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import uuid
import enum
from datetime import datetime
from config import settings

# ── Engine & Session ──────────────────────────────────────────────────────────
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,         # detect stale connections
        pool_size=10,
        max_overflow=20,
    )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Enums ─────────────────────────────────────────────────────────────────────
class UserRole(str, enum.Enum):
    admin = "admin"
    recruiter = "recruiter"
    hiring_manager = "hiring_manager"


class HiringRecommendation(str, enum.Enum):
    strong_hire = "Strong Hire"
    hire = "Hire"
    consider = "Consider"
    reject = "Reject"


# ── Models ────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="recruiter")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    job_descriptions = relationship("JobDescription", back_populates="user", cascade="all, delete-orphan")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
    filename = Column(String, nullable=False)
    raw_text = Column(Text)
    parsed_json = Column(JSON)
    file_path = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="resumes")
    candidate = relationship("Candidate", back_populates="resume", uselist=False, cascade="all, delete-orphan")
    analysis_results = relationship("AnalysisResult", back_populates="resume", cascade="all, delete-orphan")


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id = Column(String, ForeignKey("resumes.id", ondelete="CASCADE"), unique=True)
    name = Column(String)
    email = Column(String)
    phone = Column(String)
    linkedin = Column(String)
    education = Column(JSON)
    skills = Column(JSON)
    certifications = Column(JSON)
    projects = Column(JSON)
    work_experience = Column(JSON)
    years_experience = Column(Float, default=0)

    resume = relationship("Resume", back_populates="candidate")
    rankings = relationship("Ranking", back_populates="candidate", cascade="all, delete-orphan")


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
    title = Column(String, nullable=False)
    company = Column(String)
    description = Column(Text, nullable=False)
    required_skills = Column(JSON)
    required_experience = Column(Integer, default=0)
    required_education = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="job_descriptions")
    analysis_results = relationship("AnalysisResult", back_populates="job_description")
    rankings = relationship("Ranking", back_populates="job_description", cascade="all, delete-orphan")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id = Column(String, ForeignKey("resumes.id", ondelete="CASCADE"))
    job_description_id = Column(String, ForeignKey("job_descriptions.id", ondelete="SET NULL"), nullable=True)
    ats_score = Column(Float, default=0)
    match_score = Column(Float, default=0)
    skills_score = Column(Float, default=0)
    experience_score = Column(Float, default=0)
    education_score = Column(Float, default=0)
    certification_score = Column(Float, default=0)
    formatting_score = Column(Float, default=0)
    keywords_score = Column(Float, default=0)
    full_analysis = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    resume = relationship("Resume", back_populates="analysis_results")
    job_description = relationship("JobDescription", back_populates="analysis_results")
    skill_gap = relationship("SkillGap", back_populates="analysis_result", uselist=False, cascade="all, delete-orphan")
    recruiter_notes = relationship("RecruiterNote", back_populates="analysis_result", uselist=False, cascade="all, delete-orphan")


class Ranking(Base):
    __tablename__ = "rankings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_description_id = Column(String, ForeignKey("job_descriptions.id", ondelete="CASCADE"))
    candidate_id = Column(String, ForeignKey("candidates.id", ondelete="CASCADE"))
    rank = Column(Integer)
    final_score = Column(Float)
    ats_score = Column(Float)
    match_score = Column(Float)
    experience_score = Column(Float)
    education_score = Column(Float)
    certification_score = Column(Float)
    recommendation = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    job_description = relationship("JobDescription", back_populates="rankings")
    candidate = relationship("Candidate", back_populates="rankings")


class SkillGap(Base):
    __tablename__ = "skill_gaps"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_result_id = Column(String, ForeignKey("analysis_results.id", ondelete="CASCADE"), unique=True)
    missing_skills = Column(JSON)
    matched_skills = Column(JSON)
    recommended_paths = Column(JSON)

    analysis_result = relationship("AnalysisResult", back_populates="skill_gap")


class RecruiterNote(Base):
    __tablename__ = "recruiter_notes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_result_id = Column(String, ForeignKey("analysis_results.id", ondelete="CASCADE"), unique=True)
    strengths = Column(JSON)
    risks = Column(JSON)
    interview_questions = Column(JSON)
    hiring_recommendation = Column(String)
    recommendation_justification = Column(Text)
    summary = Column(Text)

    analysis_result = relationship("AnalysisResult", back_populates="recruiter_notes")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String, nullable=False)
    action_metadata = Column("metadata", JSON)
    ip_address = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
