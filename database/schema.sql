-- TalentMind AI Database Schema
-- PostgreSQL 15+

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'recruiter' CHECK (role IN ('admin', 'recruiter', 'hiring_manager')),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Job Descriptions table
CREATE TABLE IF NOT EXISTS job_descriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255),
    description TEXT NOT NULL,
    required_skills JSONB DEFAULT '[]',
    required_experience INTEGER DEFAULT 0,
    required_education VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Resumes table
CREATE TABLE IF NOT EXISTS resumes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    filename VARCHAR(255) NOT NULL,
    raw_text TEXT,
    parsed_json JSONB,
    file_path VARCHAR(500),
    file_size INTEGER,
    file_type VARCHAR(20),
    uploaded_at TIMESTAMP DEFAULT NOW()
);

-- Candidates table
CREATE TABLE IF NOT EXISTS candidates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resume_id UUID REFERENCES resumes(id) ON DELETE CASCADE UNIQUE,
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    linkedin VARCHAR(500),
    education JSONB DEFAULT '[]',
    skills JSONB DEFAULT '[]',
    certifications JSONB DEFAULT '[]',
    projects JSONB DEFAULT '[]',
    work_experience JSONB DEFAULT '[]',
    years_experience FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Analysis Results table
CREATE TABLE IF NOT EXISTS analysis_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resume_id UUID REFERENCES resumes(id) ON DELETE CASCADE,
    job_description_id UUID REFERENCES job_descriptions(id) ON DELETE SET NULL,
    ats_score FLOAT DEFAULT 0,
    match_score FLOAT DEFAULT 0,
    skills_score FLOAT DEFAULT 0,
    experience_score FLOAT DEFAULT 0,
    education_score FLOAT DEFAULT 0,
    certification_score FLOAT DEFAULT 0,
    formatting_score FLOAT DEFAULT 0,
    keywords_score FLOAT DEFAULT 0,
    full_analysis JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Rankings table
CREATE TABLE IF NOT EXISTS rankings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_description_id UUID REFERENCES job_descriptions(id) ON DELETE CASCADE,
    candidate_id UUID REFERENCES candidates(id) ON DELETE CASCADE,
    rank INTEGER,
    final_score FLOAT,
    ats_score FLOAT,
    match_score FLOAT,
    experience_score FLOAT,
    education_score FLOAT,
    certification_score FLOAT,
    recommendation VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Skill Gaps table
CREATE TABLE IF NOT EXISTS skill_gaps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_result_id UUID REFERENCES analysis_results(id) ON DELETE CASCADE UNIQUE,
    missing_skills JSONB DEFAULT '[]',
    matched_skills JSONB DEFAULT '[]',
    recommended_paths JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Recruiter Notes table
CREATE TABLE IF NOT EXISTS recruiter_notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_result_id UUID REFERENCES analysis_results(id) ON DELETE CASCADE UNIQUE,
    strengths JSONB DEFAULT '[]',
    risks JSONB DEFAULT '[]',
    interview_questions JSONB DEFAULT '[]',
    hiring_recommendation VARCHAR(50),
    recommendation_justification TEXT,
    summary TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Audit Logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    metadata JSONB,
    ip_address VARCHAR(45),
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON resumes(user_id);
CREATE INDEX IF NOT EXISTS idx_candidates_resume_id ON candidates(resume_id);
CREATE INDEX IF NOT EXISTS idx_analysis_resume_id ON analysis_results(resume_id);
CREATE INDEX IF NOT EXISTS idx_analysis_jd_id ON analysis_results(job_description_id);
CREATE INDEX IF NOT EXISTS idx_rankings_jd_id ON rankings(job_description_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);

-- Seed admin user (password: Admin@123)
INSERT INTO users (email, name, password_hash, role) 
VALUES (
    'admin@talentmind.ai',
    'TalentMind Admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMqJqhN3TLpJqX9mzFG0a5GYSK',
    'admin'
) ON CONFLICT (email) DO NOTHING;
