"""
TalentMind AI — ATS (Applicant Tracking System) Analyser Agent
================================================================
Simulates how modern ATS systems evaluate resumes before they reach
a human recruiter.

Checks performed:
    1. Section completeness  — required & recommended sections present
    2. Keyword density       — JD term frequency in the resume
    3. Formatting quality    — bullet points, length, readability
    4. Contact info          — email, phone present
    5. Quantification        — measurable achievements detected
    6. Action verbs          — strong professional language

Returns a structured ATS report with a composite score (0-100).

Author: TalentMind AI
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class SectionCheck:
    name: str
    present: bool
    weight: float
    score: float  # 0.0 – 1.0


@dataclass
class ATSReport:
    overall_score: float               # 0 – 100
    grade: str                         # A / B / C / D / F
    section_score: float               # sub-score 0-100
    keyword_score: float
    formatting_score: float
    contact_score: float
    quantification_score: float
    action_verb_score: float
    sections_found: List[str]
    sections_missing: List[str]
    matched_keywords: List[str]
    missing_keywords: List[str]
    keyword_density: float             # % of JD keywords found
    formatting_issues: List[str]
    strengths: List[str]
    improvements: List[str]
    word_count: int
    estimated_pages: float


# ---------------------------------------------------------------------------
# ATS Analyser Agent
# ---------------------------------------------------------------------------

class ATSAnalyserAgent:
    """
    Analyses a parsed resume dict (plus raw text) against ATS best practices
    and an optional Job Description.
    """

    name = "ATS Analyser Agent"

    # ------------------------------------------------------------------
    # Section definitions
    # ------------------------------------------------------------------
    REQUIRED_SECTIONS: List[Tuple[str, float]] = [
        ("contact",        0.15),
        ("summary",        0.10),
        ("experience",     0.25),
        ("education",      0.20),
        ("skills",         0.30),
    ]
    RECOMMENDED_SECTIONS: List[Tuple[str, float]] = [
        ("certifications", 0.10),
        ("projects",       0.10),
        ("achievements",   0.05),
        ("awards",         0.05),
    ]

    SECTION_KEYWORDS: Dict[str, List[str]] = {
        "contact":        ["email", "phone", "linkedin", "address", "contact"],
        "summary":        ["summary", "objective", "profile", "about", "overview"],
        "experience":     ["experience", "employment", "work history", "career", "positions"],
        "education":      ["education", "academic", "degree", "university", "college"],
        "skills":         ["skills", "technical skills", "competencies", "expertise", "technologies"],
        "certifications": ["certification", "certified", "credentials", "accreditation", "license"],
        "projects":       ["project", "portfolio", "github", "open source"],
        "achievements":   ["achievement", "accomplishment", "award", "recognition", "honor"],
        "awards":         ["award", "honor", "recognition", "prize", "distinction"],
    }

    # ------------------------------------------------------------------
    # Formatting patterns
    # ------------------------------------------------------------------
    BULLET_PATTERNS = re.compile(r"^\s*[•·▸▹►\-–—*]\s+.+", re.MULTILINE)
    NUMBER_PATTERNS = re.compile(r"\b\d[\d,]*%?(?:\s*(?:million|billion|k|m|b))?\b")
    LONG_LINE_PATTERN = re.compile(r".{120,}")

    # Action verbs that impress ATS and recruiters
    ACTION_VERBS: List[str] = [
        "achieved", "accelerated", "architected", "automated", "built",
        "championed", "collaborated", "conducted", "created", "decreased",
        "delivered", "deployed", "designed", "developed", "drove",
        "eliminated", "enabled", "engineered", "enhanced", "established",
        "executed", "expanded", "facilitated", "generated", "implemented",
        "improved", "increased", "initiated", "integrated", "launched",
        "led", "managed", "mentored", "migrated", "modernised",
        "optimised", "orchestrated", "overhauled", "pioneered", "produced",
        "reduced", "refactored", "resolved", "scaled", "spearheaded",
        "streamlined", "trained", "transformed", "upgraded",
    ]

    def __init__(self, ollama_client=None) -> None:
        self.ollama = ollama_client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyse(
        self,
        parsed_resume: Dict[str, Any],
        resume_text: str,
        job_description: str = "",
    ) -> ATSReport:
        """
        Run all ATS checks and return a comprehensive report.

        Parameters
        ----------
        parsed_resume : dict
            Output from ResumeParserAgent.
        resume_text : str
            Original raw text (used for pattern analysis).
        job_description : str, optional
            Job Description text for keyword matching.
        """
        logger.info("[%s] Running ATS analysis", self.name)
        text_lower = resume_text.lower()

        # ---- 1. Section Completeness ----
        section_score, sections_found, sections_missing = self._check_sections(
            parsed_resume, text_lower
        )

        # ---- 2. Keyword Optimisation ----
        kw_score, matched_kw, missing_kw, kw_density = self._check_keywords(
            text_lower, job_description
        )

        # ---- 3. Formatting Quality ----
        fmt_score, fmt_issues = self._check_formatting(resume_text)

        # ---- 4. Contact Completeness ----
        contact_score = self._check_contact(parsed_resume)

        # ---- 5. Quantification ----
        quant_score = self._check_quantification(resume_text)

        # ---- 6. Action Verbs ----
        action_score = self._check_action_verbs(text_lower)

        # ---- Composite Score ----
        overall = (
            section_score * 0.25
            + kw_score * 0.30
            + fmt_score * 0.20
            + contact_score * 0.10
            + quant_score * 0.10
            + action_score * 0.05
        )
        overall = round(min(100.0, max(0.0, overall)), 1)

        # ---- Word Count / Pages ----
        word_count = len(resume_text.split())
        estimated_pages = round(word_count / 450, 1)  # ~450 words per page

        # ---- Grade ----
        grade = self._score_to_grade(overall)

        # ---- Narrative insights ----
        strengths = self._build_strengths(
            section_score, kw_score, fmt_score, contact_score, quant_score, action_score
        )
        improvements = self._build_improvements(
            sections_missing, missing_kw, fmt_issues, quant_score, action_score, word_count
        )

        report = ATSReport(
            overall_score=overall,
            grade=grade,
            section_score=round(section_score, 1),
            keyword_score=round(kw_score, 1),
            formatting_score=round(fmt_score, 1),
            contact_score=round(contact_score, 1),
            quantification_score=round(quant_score, 1),
            action_verb_score=round(action_score, 1),
            sections_found=sections_found,
            sections_missing=sections_missing,
            matched_keywords=matched_kw,
            missing_keywords=missing_kw,
            keyword_density=round(kw_density, 1),
            formatting_issues=fmt_issues,
            strengths=strengths,
            improvements=improvements,
            word_count=word_count,
            estimated_pages=estimated_pages,
        )
        logger.info("[%s] ATS score: %.1f (%s)", self.name, overall, grade)
        return report

    # ------------------------------------------------------------------
    # Section checks
    # ------------------------------------------------------------------

    def _check_sections(
        self,
        parsed: Dict[str, Any],
        text_lower: str,
    ) -> Tuple[float, List[str], List[str]]:
        found: List[str] = []
        missing: List[str] = []
        weighted_score = 0.0
        max_score = 0.0

        all_sections = self.REQUIRED_SECTIONS + [
            (s, w * 0.5) for s, w in self.RECOMMENDED_SECTIONS
        ]

        for section, weight in all_sections:
            max_score += weight * 100
            detected = self._detect_section(section, parsed, text_lower)
            if detected:
                found.append(section)
                weighted_score += weight * 100
            else:
                missing.append(section)

        score = (weighted_score / max_score * 100) if max_score else 0
        return round(score, 1), found, missing

    def _detect_section(
        self, section: str, parsed: Dict[str, Any], text_lower: str
    ) -> bool:
        """Return True if the section appears to be present."""
        keywords = self.SECTION_KEYWORDS.get(section, [section])

        # Check parsed data first
        if section == "contact":
            return bool(parsed.get("email") or parsed.get("phone"))
        if section == "summary":
            return bool(parsed.get("summary"))
        if section == "experience":
            return bool(parsed.get("work_experience"))
        if section == "education":
            return bool(parsed.get("education"))
        if section == "skills":
            return bool(parsed.get("skills"))
        if section == "certifications":
            return bool(parsed.get("certifications"))
        if section == "projects":
            return bool(parsed.get("projects"))

        # Fallback: keyword search in raw text
        return any(kw in text_lower for kw in keywords)

    # ------------------------------------------------------------------
    # Keyword optimisation
    # ------------------------------------------------------------------

    def _check_keywords(
        self,
        text_lower: str,
        job_description: str,
    ) -> Tuple[float, List[str], List[str], float]:
        if not job_description:
            return 70.0, [], [], 70.0  # Neutral score when no JD provided

        jd_lower = job_description.lower()
        # Extract meaningful words from JD (length > 3, not stopwords)
        stop_words = {
            "the", "and", "for", "with", "that", "this", "from", "have",
            "will", "your", "you", "are", "not", "but", "all", "any",
            "our", "their", "been", "has", "was", "were", "can", "able",
        }
        jd_words = {
            w for w in re.findall(r"\b[a-z][a-z0-9+#.]{2,}\b", jd_lower)
            if w not in stop_words
        }
        if not jd_words:
            return 70.0, [], [], 70.0

        matched = [w for w in jd_words if re.search(r"\b" + re.escape(w) + r"\b", text_lower)]
        missing = [w for w in jd_words if w not in matched]
        density = len(matched) / len(jd_words) * 100
        score = min(100.0, density * 1.1)  # Slight boost; cap at 100
        return round(score, 1), matched[:30], missing[:30], round(density, 1)

    # ------------------------------------------------------------------
    # Formatting checks
    # ------------------------------------------------------------------

    def _check_formatting(self, text: str) -> Tuple[float, List[str]]:
        issues: List[str] = []
        score = 100.0

        # Bullet points
        bullet_count = len(self.BULLET_PATTERNS.findall(text))
        if bullet_count < 5:
            issues.append("Too few bullet points — ATS prefers structured bullet lists")
            score -= 20

        # Overly long lines (tables / graphics often cause this)
        long_lines = self.LONG_LINE_PATTERN.findall(text)
        if long_lines:
            issues.append(f"{len(long_lines)} lines are very long — may indicate tables or poor formatting")
            score -= 10

        # Resume length
        word_count = len(text.split())
        if word_count < 200:
            issues.append("Resume appears very short (< 200 words) — add more detail")
            score -= 20
        elif word_count > 1200:
            issues.append("Resume is very long (> 1200 words) — consider condensing to 1-2 pages")
            score -= 10

        # Avoid common ATS-unfriendly content
        if re.search(r"\bheader\b|\bfooter\b|\btable\b|\bcolumn\b", text, re.IGNORECASE):
            issues.append("May contain tables/columns — some ATS cannot parse these correctly")
            score -= 5

        # Check for special characters that could confuse ATS parsers
        special_ratio = len(re.findall(r"[^\x00-\x7F]", text)) / max(len(text), 1)
        if special_ratio > 0.02:
            issues.append("High number of special characters detected — may cause ATS parsing errors")
            score -= 5

        return round(max(0.0, score), 1), issues

    # ------------------------------------------------------------------
    # Contact completeness
    # ------------------------------------------------------------------

    def _check_contact(self, parsed: Dict[str, Any]) -> float:
        score = 0.0
        if parsed.get("email"):
            score += 40
        if parsed.get("phone"):
            score += 30
        if parsed.get("linkedin"):
            score += 20
        if parsed.get("github"):
            score += 10
        return score

    # ------------------------------------------------------------------
    # Quantification
    # ------------------------------------------------------------------

    def _check_quantification(self, text: str) -> float:
        """Check how many measurable achievements are present."""
        numbers_found = len(self.NUMBER_PATTERNS.findall(text))
        # Good resumes have 5-15 quantified achievements
        if numbers_found >= 15:
            return 100.0
        if numbers_found >= 8:
            return 80.0
        if numbers_found >= 4:
            return 60.0
        if numbers_found >= 1:
            return 40.0
        return 10.0

    # ------------------------------------------------------------------
    # Action verbs
    # ------------------------------------------------------------------

    def _check_action_verbs(self, text_lower: str) -> float:
        """Score based on the variety and count of strong action verbs."""
        found = [v for v in self.ACTION_VERBS if v in text_lower]
        count = len(found)
        if count >= 10:
            return 100.0
        if count >= 6:
            return 80.0
        if count >= 3:
            return 60.0
        if count >= 1:
            return 40.0
        return 10.0

    # ------------------------------------------------------------------
    # Grade conversion
    # ------------------------------------------------------------------

    @staticmethod
    def _score_to_grade(score: float) -> str:
        if score >= 90:
            return "A"
        if score >= 80:
            return "B"
        if score >= 70:
            return "C"
        if score >= 60:
            return "D"
        return "F"

    # ------------------------------------------------------------------
    # Narrative builders
    # ------------------------------------------------------------------

    def _build_strengths(self, *scores) -> List[str]:
        section, kw, fmt, contact, quant, action = scores
        strengths = []
        if section >= 80:
            strengths.append("Resume has all major sections, improving ATS readability")
        if kw >= 70:
            strengths.append("Good keyword alignment with the Job Description")
        if fmt >= 80:
            strengths.append("Clean formatting suitable for ATS parsing")
        if contact >= 70:
            strengths.append("Contact information is complete and accessible")
        if quant >= 60:
            strengths.append("Quantified achievements present — adds credibility")
        if action >= 60:
            strengths.append("Strong action verbs used throughout the resume")
        return strengths or ["Resume submitted for review"]

    def _build_improvements(
        self,
        missing_sections: List[str],
        missing_kw: List[str],
        fmt_issues: List[str],
        quant_score: float,
        action_score: float,
        word_count: int,
    ) -> List[str]:
        improvements = []
        if missing_sections:
            improvements.append(
                f"Add missing sections: {', '.join(missing_sections[:4])}"
            )
        if missing_kw:
            improvements.append(
                f"Include JD keywords: {', '.join(missing_kw[:6])}"
            )
        if quant_score < 60:
            improvements.append(
                "Add quantified achievements (%, $, time saved, team size, etc.)"
            )
        if action_score < 60:
            improvements.append(
                "Start bullet points with strong action verbs (led, built, optimised…)"
            )
        improvements.extend(fmt_issues[:3])
        return improvements


# ---------------------------------------------------------------------------
# Singleton helper
# ---------------------------------------------------------------------------

_ats_agent: Optional[ATSAnalyserAgent] = None


def get_ats_agent(ollama_client=None) -> ATSAnalyserAgent:
    global _ats_agent
    if _ats_agent is None:
        _ats_agent = ATSAnalyserAgent(ollama_client)
    return _ats_agent
