"""
TalentMind AI — ATS Scoring Engine
Calculates a weighted Applicant Tracking System score across 6 dimensions.

Score breakdown
───────────────
  Skills         30 %
  Experience     25 %
  Education      10 %
  Certifications 10 %
  Formatting     10 %
  Keywords       15 %
  ──────────────────
  Total         100 %
"""
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ATSScoreBreakdown:
    total_score: float
    skills_score: float
    experience_score: float
    education_score: float
    certification_score: float
    formatting_score: float
    keywords_score: float
    details: Dict[str, Any]
    suggestions: List[str]
    keywords_found: List[str]
    keywords_missing: List[str]


class ATSEngine:
    """Rule-based ATS scorer that does not require an LLM."""

    # Dimension weights (must sum to 1.0)
    WEIGHTS: Dict[str, float] = {
        "skills": 0.30,
        "experience": 0.25,
        "education": 0.10,
        "certifications": 0.10,
        "formatting": 0.10,
        "keywords": 0.15,
    }

    # Ordered from highest to lowest so the first match wins
    EDUCATION_LEVELS: Dict[str, float] = {
        "phd": 100,
        "ph.d": 100,
        "doctorate": 100,
        "master": 90,
        "mba": 90,
        "m.s": 90,
        "m.sc": 90,
        "bachelor": 70,
        "b.s": 70,
        "b.sc": 70,
        "b.e": 70,
        "b.tech": 70,
        "associate": 50,
        "diploma": 40,
        "certificate": 30,
        "high school": 20,
        "secondary": 20,
    }

    STOPWORDS: frozenset = frozenset(
        {
            "the", "and", "for", "this", "that", "with", "will", "have",
            "from", "are", "you", "your", "our", "we", "be", "in", "to",
            "a", "of", "is", "it", "as", "an", "on", "at", "by", "or",
            "but", "not", "can", "all", "was", "they", "has", "had",
            "its", "than", "then", "when", "who", "which", "also", "been",
            "their", "would", "about", "into", "more", "over", "such",
            "these", "those", "them", "what", "well", "any", "may",
        }
    )

    def calculate_score(
        self,
        parsed_resume: Dict[str, Any],
        job_description: Optional[str] = None,
        jd_skills: Optional[List[str]] = None,
    ) -> ATSScoreBreakdown:
        """
        Compute the ATS score for a parsed resume.

        Parameters
        ----------
        parsed_resume:
            Dictionary produced by the Ollama resume parser.
        job_description:
            Full JD text used for keyword matching (optional).
        jd_skills:
            List of required skills from the JD (optional).
        """
        suggestions: List[str] = []

        skills_score, skill_details = self._score_skills(
            parsed_resume.get("skills", []), jd_skills, suggestions
        )
        experience_score, exp_details = self._score_experience(
            parsed_resume.get("work_experience", []), suggestions
        )
        education_score, edu_details = self._score_education(
            parsed_resume.get("education", []), suggestions
        )
        cert_score, cert_details = self._score_certifications(
            parsed_resume.get("certifications", []), suggestions
        )
        formatting_score, fmt_details = self._score_formatting(parsed_resume, suggestions)
        keywords_score, kw_found, kw_missing = self._score_keywords(
            parsed_resume, job_description, suggestions
        )

        total = (
            skills_score * self.WEIGHTS["skills"]
            + experience_score * self.WEIGHTS["experience"]
            + education_score * self.WEIGHTS["education"]
            + cert_score * self.WEIGHTS["certifications"]
            + formatting_score * self.WEIGHTS["formatting"]
            + keywords_score * self.WEIGHTS["keywords"]
        )

        return ATSScoreBreakdown(
            total_score=round(min(total, 100.0), 1),
            skills_score=round(skills_score, 1),
            experience_score=round(experience_score, 1),
            education_score=round(education_score, 1),
            certification_score=round(cert_score, 1),
            formatting_score=round(formatting_score, 1),
            keywords_score=round(keywords_score, 1),
            details={
                "skills": skill_details,
                "experience": exp_details,
                "education": edu_details,
                "certifications": cert_details,
                "formatting": fmt_details,
            },
            suggestions=list(dict.fromkeys(suggestions))[:10],  # deduplicate, cap at 10
            keywords_found=kw_found,
            keywords_missing=kw_missing,
        )

    # ── Private scoring helpers ───────────────────────────────────────────────

    def _score_skills(
        self,
        candidate_skills: List[str],
        jd_skills: Optional[List[str]],
        suggestions: List[str],
    ) -> Tuple[float, Dict[str, Any]]:
        if not candidate_skills:
            suggestions.append(
                "Add a dedicated Skills section with relevant technical and soft skills."
            )
            return 20.0, {"count": 0, "matched": 0, "total_required": len(jd_skills or [])}

        matched = 0
        if jd_skills:
            candidate_lower = {s.lower() for s in candidate_skills}
            for skill in jd_skills:
                if skill.lower() in candidate_lower:
                    matched += 1
            match_rate = matched / len(jd_skills) if jd_skills else 0
            score = match_rate * 100
            if score < 60:
                missing_sample = [s for s in jd_skills if s.lower() not in {c.lower() for c in candidate_skills}][:4]
                suggestions.append(
                    f"Add these required skills to your resume: {', '.join(missing_sample)}."
                )
        else:
            # No JD provided — score based on quantity (8 pts per skill, cap 100)
            score = min(100.0, len(candidate_skills) * 8.0)
            if score < 60:
                suggestions.append("Expand your Skills section with more relevant technologies.")

        return score, {
            "count": len(candidate_skills),
            "matched": matched,
            "total_required": len(jd_skills or []),
        }

    def _score_experience(
        self,
        work_experience: List[Any],
        suggestions: List[str],
    ) -> Tuple[float, Dict[str, Any]]:
        if not work_experience:
            suggestions.append(
                "Add detailed work experience with job titles, companies, and quantified achievements."
            )
            return 20.0, {"positions": 0, "estimated_years": 0}

        positions = len(work_experience)
        estimated_years = 0

        for exp in work_experience:
            if isinstance(exp, dict):
                years_str = str(exp.get("years", "") or exp.get("duration", ""))
                year_matches = re.findall(r"\d{4}", years_str)
                if len(year_matches) >= 2:
                    estimated_years += abs(int(year_matches[-1]) - int(year_matches[0]))
                elif len(year_matches) == 1:
                    estimated_years += 1  # treat single year as 1 year tenure

        # Base score on position count
        if positions == 1:
            score = 50.0
        elif positions == 2:
            score = 65.0
        elif positions <= 4:
            score = 80.0
        else:
            score = 90.0

        # Bonus: quantified achievements
        has_quantified = any(
            re.search(
                r"\d+\s*%|\$\s*\d+|\d+\s*(people|engineers|users|clients|projects|million|k\b)",
                str(exp),
                re.IGNORECASE,
            )
            for exp in work_experience
        )
        if has_quantified:
            score = min(100.0, score + 10.0)
        else:
            suggestions.append(
                "Quantify your achievements (e.g., 'Reduced latency by 30%' or 'Managed 8-person team')."
            )

        # Bonus: recent experience (position mentioned 202x)
        current_year_exp = any(
            re.search(r"202[0-9]", str(exp)) for exp in work_experience
        )
        if not current_year_exp:
            suggestions.append("Ensure work experience includes recent (2020+) positions.")

        return min(100.0, score), {
            "positions": positions,
            "estimated_years": estimated_years,
        }

    def _score_education(
        self,
        education: List[Any],
        suggestions: List[str],
    ) -> Tuple[float, Dict[str, Any]]:
        if not education:
            suggestions.append("Include your educational background with institution and graduation year.")
            return 30.0, {"level": "None", "score": 30}

        best_score = 30.0
        best_level = "Unknown"
        for edu in education:
            edu_str = str(edu).lower()
            for level, lvl_score in self.EDUCATION_LEVELS.items():
                if level in edu_str:
                    if lvl_score > best_score:
                        best_score = float(lvl_score)
                        best_level = level.title()
                    break

        return best_score, {"level": best_level, "score": best_score}

    def _score_certifications(
        self,
        certifications: List[Any],
        suggestions: List[str],
    ) -> Tuple[float, Dict[str, Any]]:
        if not certifications:
            suggestions.append(
                "Add relevant professional certifications (AWS, Google Cloud, PMP, etc.)."
            )
            return 30.0, {"count": 0}

        # 30 base + 20 per cert, cap at 100
        score = min(100.0, 30.0 + len(certifications) * 20.0)
        return score, {"count": len(certifications), "certs": certifications}

    def _score_formatting(
        self,
        parsed_resume: Dict[str, Any],
        suggestions: List[str],
    ) -> Tuple[float, Dict[str, Any]]:
        score = 0.0
        detail: Dict[str, bool] = {}

        checks = [
            ("name", 20, "Include your full name prominently at the top of the resume."),
            ("email", 20, "Include a professional email address."),
            ("phone", 15, "Add a phone number for recruiters to contact you."),
            ("linkedin", 15, "Add your LinkedIn profile URL."),
            ("skills", 15, "Add a Skills section."),
            ("work_experience", 15, "Add a Work Experience section."),
        ]

        for key, pts, suggestion in checks:
            has_value = bool(parsed_resume.get(key))
            detail[f"has_{key}"] = has_value
            if has_value:
                score += pts
            else:
                suggestions.append(suggestion)

        return min(100.0, score), detail

    def _score_keywords(
        self,
        parsed_resume: Dict[str, Any],
        job_description: Optional[str],
        suggestions: List[str],
    ) -> Tuple[float, List[str], List[str]]:
        if not job_description:
            return 50.0, [], []

        # Build keyword set from JD (alpha tokens ≥3 chars, not stopwords)
        raw_words = re.findall(r"\b[a-zA-Z][a-zA-Z+#.\-]{2,}\b", job_description.lower())
        jd_keywords = {w for w in raw_words if w not in self.STOPWORDS}

        # Build resume corpus
        corpus_parts: List[str] = []
        corpus_parts += [s.lower() for s in (parsed_resume.get("skills") or [])]
        corpus_parts.append(str(parsed_resume.get("name", "")).lower())
        for section in ("work_experience", "education", "certifications", "projects"):
            for item in (parsed_resume.get(section) or []):
                corpus_parts.append(str(item).lower())
        resume_corpus = " ".join(corpus_parts)

        # Score top 40 JD keywords
        top_keywords = list(jd_keywords)[:40]
        found: List[str] = []
        missing: List[str] = []
        for kw in top_keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", resume_corpus):
                found.append(kw)
            else:
                missing.append(kw)

        total = len(found) + len(missing)
        score = (len(found) / total * 100) if total else 50.0

        if len(missing) > 5:
            suggestions.append(
                f"Include these job-description keywords: {', '.join(missing[:5])}."
            )

        return round(score, 1), found[:20], missing[:20]


# Shared singleton
ats_engine = ATSEngine()
