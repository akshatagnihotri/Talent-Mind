"""
TalentMind AI — Job Match Agent
================================
Compares a candidate's profile against a Job Description and produces a
detailed match report including:
    • Overall fit percentage
    • Matched / missing skills and keywords
    • Experience match assessment
    • Education fit
    • Candidate strengths vs. the role
    • Actionable weaknesses
    • Tailored recommendations

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
class JobMatchReport:
    overall_fit_pct: float              # 0–100
    skill_match_pct: float
    experience_match_pct: float
    education_match_pct: float
    keyword_match_pct: float
    matched_skills: List[str]
    missing_skills: List[str]
    matched_keywords: List[str]
    missing_keywords: List[str]
    required_skills: List[str]
    candidate_skills: List[str]
    experience_years_candidate: float
    experience_years_required: float
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    hiring_signals: List[str]
    fit_label: str                      # Excellent / Good / Partial / Poor


# ---------------------------------------------------------------------------
# Job Match Agent
# ---------------------------------------------------------------------------

class JobMatchAgent:
    """
    Compares a parsed resume against a job description and scores fit.
    """

    name = "Job Match Agent"

    # Common stop-words to exclude from keyword extraction
    STOP_WORDS = {
        "the", "and", "for", "with", "that", "this", "from", "have",
        "will", "your", "you", "are", "not", "but", "all", "any", "our",
        "their", "been", "has", "was", "were", "can", "able", "must",
        "should", "would", "could", "may", "its", "into", "over", "such",
        "who", "what", "how", "they", "them", "use", "used", "using",
        "work", "role", "team", "join", "position", "opportunity", "about",
        "more", "also", "both", "each", "some", "other", "than", "then",
        "good", "great", "strong", "excellent", "ideal", "looking",
    }

    EDUCATION_LEVELS = ["phd", "masters", "mba", "bachelor", "associate", "diploma", "high school"]

    def __init__(self, ollama_client=None) -> None:
        self.ollama = ollama_client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def match(
        self,
        parsed_resume: Dict[str, Any],
        job_description: str,
    ) -> JobMatchReport:
        """
        Compare the candidate against the JD.

        Parameters
        ----------
        parsed_resume : dict
            Output from ResumeParserAgent.
        job_description : str
            Raw JD text.

        Returns
        -------
        JobMatchReport
        """
        logger.info("[%s] Starting job match analysis", self.name)

        jd_lower = job_description.lower()
        jd_skills = self._extract_skills_from_jd(job_description)
        candidate_skills = [s.lower() for s in parsed_resume.get("skills", [])]

        # ---- Skill match ----
        skill_score, matched_skills, missing_skills = self._score_skills(
            candidate_skills, jd_skills
        )

        # ---- Keyword match ----
        kw_score, matched_kw, missing_kw = self._score_keywords(
            parsed_resume, jd_lower
        )

        # ---- Experience match ----
        exp_score, candidate_yoe, required_yoe = self._score_experience(
            parsed_resume, jd_lower
        )

        # ---- Education match ----
        edu_score = self._score_education(parsed_resume, jd_lower)

        # ---- Overall composite ----
        overall = (
            skill_score * 0.40
            + kw_score * 0.25
            + exp_score * 0.20
            + edu_score * 0.15
        )
        overall = round(min(100.0, max(0.0, overall)), 1)

        fit_label = self._fit_label(overall)

        # ---- Narrative insights ----
        strengths = self._build_strengths(
            matched_skills, exp_score, edu_score, candidate_yoe, required_yoe
        )
        weaknesses = self._build_weaknesses(
            missing_skills, exp_score, candidate_yoe, required_yoe
        )
        recommendations = self._build_recommendations(
            missing_skills, missing_kw, exp_score
        )
        hiring_signals = self._build_hiring_signals(
            overall, skill_score, exp_score, edu_score
        )

        report = JobMatchReport(
            overall_fit_pct=overall,
            skill_match_pct=round(skill_score, 1),
            experience_match_pct=round(exp_score, 1),
            education_match_pct=round(edu_score, 1),
            keyword_match_pct=round(kw_score, 1),
            matched_skills=[s.title() for s in matched_skills],
            missing_skills=[s.title() for s in missing_skills],
            matched_keywords=matched_kw[:20],
            missing_keywords=missing_kw[:20],
            required_skills=[s.title() for s in jd_skills],
            candidate_skills=parsed_resume.get("skills", []),
            experience_years_candidate=candidate_yoe,
            experience_years_required=required_yoe,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            hiring_signals=hiring_signals,
            fit_label=fit_label,
        )
        logger.info("[%s] Overall fit: %.1f%% (%s)", self.name, overall, fit_label)
        return report

    # ------------------------------------------------------------------
    # Skill scoring
    # ------------------------------------------------------------------

    def _extract_skills_from_jd(self, jd: str) -> List[str]:
        """Extract skill-like tokens from the job description."""
        # Known tech skills
        tech_patterns = [
            r"\bpython\b", r"\bjava\b", r"\bjavascript\b", r"\btypescript\b",
            r"\breact\b", r"\bangular\b", r"\bvue\b", r"\bnode\.js\b",
            r"\bfastapi\b", r"\bdjango\b", r"\bflask\b", r"\bspring boot\b",
            r"\bsql\b", r"\bpostgresql\b", r"\bmysql\b", r"\bmongodb\b",
            r"\bredis\b", r"\bdocker\b", r"\bkubernetes\b", r"\bterraform\b",
            r"\baws\b", r"\bazure\b", r"\bgcp\b", r"\bci/cd\b",
            r"\bgit\b", r"\brest api\b", r"\bgraphql\b", r"\bmicroservices\b",
            r"\bmachine learning\b", r"\bdeep learning\b", r"\bnlp\b",
            r"\btensorflow\b", r"\bpytorch\b", r"\bscikit[\-\s]learn\b",
            r"\bpandas\b", r"\bnumpy\b", r"\bpower bi\b", r"\btableau\b",
            r"\bscala\b", r"\bgo\b", r"\brust\b", r"\bc\+\+\b", r"\bc#\b",
            r"\bkafka\b", r"\bairflow\b", r"\bspark\b", r"\bhive\b",
            r"\bexcel\b", r"\blinux\b", r"\bagile\b", r"\bscrum\b",
        ]
        jd_lower = jd.lower()
        found = []
        for pattern in tech_patterns:
            if re.search(pattern, jd_lower):
                # Extract the matched skill in normalised form
                match = re.search(pattern, jd_lower)
                if match:
                    found.append(match.group().strip())
        return list(dict.fromkeys(found))  # Preserve order, deduplicate

    def _score_skills(
        self,
        candidate_skills: List[str],
        jd_skills: List[str],
    ) -> Tuple[float, List[str], List[str]]:
        if not jd_skills:
            return 70.0, candidate_skills[:10], []

        candidate_set = set(candidate_skills)
        matched = [s for s in jd_skills if s in candidate_set]
        missing = [s for s in jd_skills if s not in candidate_set]
        score = len(matched) / len(jd_skills) * 100
        return round(score, 1), matched, missing

    # ------------------------------------------------------------------
    # Keyword scoring
    # ------------------------------------------------------------------

    def _score_keywords(
        self,
        parsed_resume: Dict[str, Any],
        jd_lower: str,
    ) -> Tuple[float, List[str], List[str]]:
        # Build full candidate text blob
        resume_text = " ".join([
            parsed_resume.get("summary", ""),
            " ".join(parsed_resume.get("skills", [])),
            " ".join(
                e.get("description", "") for e in parsed_resume.get("work_experience", [])
            ),
            " ".join(
                p.get("description", "") for p in parsed_resume.get("projects", [])
            ),
        ]).lower()

        # Extract meaningful JD tokens
        jd_tokens = {
            w for w in re.findall(r"\b[a-z][a-z0-9+#.]{2,}\b", jd_lower)
            if w not in self.STOP_WORDS
        }
        if not jd_tokens:
            return 70.0, [], []

        matched = [t for t in jd_tokens if re.search(r"\b" + re.escape(t) + r"\b", resume_text)]
        missing = [t for t in jd_tokens if t not in matched]
        score = len(matched) / len(jd_tokens) * 100
        return round(score, 1), matched[:25], missing[:25]

    # ------------------------------------------------------------------
    # Experience scoring
    # ------------------------------------------------------------------

    def _score_experience(
        self,
        parsed_resume: Dict[str, Any],
        jd_lower: str,
    ) -> Tuple[float, float, float]:
        # Years required from JD
        years_match = re.search(
            r"(\d+)\+?\s*(?:to\s*\d+\s*)?years?\s+(?:of\s+)?(?:relevant\s+)?experience",
            jd_lower,
        )
        required_yoe = float(years_match.group(1)) if years_match else 3.0  # Default

        # Candidate years — sum from work_experience entries
        candidate_yoe = self._calculate_candidate_yoe(parsed_resume)

        if candidate_yoe >= required_yoe:
            score = 100.0
        elif candidate_yoe >= required_yoe * 0.75:
            score = 80.0
        elif candidate_yoe >= required_yoe * 0.50:
            score = 60.0
        elif candidate_yoe >= required_yoe * 0.25:
            score = 40.0
        else:
            score = 20.0

        return round(score, 1), round(candidate_yoe, 1), round(required_yoe, 1)

    def _calculate_candidate_yoe(self, parsed_resume: Dict[str, Any]) -> float:
        """Estimate total years of experience from work_experience list."""
        total = 0.0
        for exp in parsed_resume.get("work_experience", []):
            years_str = exp.get("years", "")
            if not years_str:
                continue
            # Pattern: "2019 – 2022" or "Jan 2020 – Present"
            year_nums = re.findall(r"\b(20\d{2}|19\d{2})\b", years_str)
            if "present" in years_str.lower() or "current" in years_str.lower():
                import datetime
                current_year = datetime.datetime.now().year
                if year_nums:
                    total += current_year - int(year_nums[0])
            elif len(year_nums) >= 2:
                total += int(year_nums[1]) - int(year_nums[0])
        # Fallback: count entries × 2 years if no years parsed
        if total == 0 and parsed_resume.get("work_experience"):
            total = len(parsed_resume["work_experience"]) * 2.0
        return max(0.0, total)

    # ------------------------------------------------------------------
    # Education scoring
    # ------------------------------------------------------------------

    def _score_education(self, parsed_resume: Dict[str, Any], jd_lower: str) -> float:
        jd_edu_level = 0
        for i, level in enumerate(self.EDUCATION_LEVELS):
            if level in jd_lower:
                jd_edu_level = len(self.EDUCATION_LEVELS) - i
                break

        if not jd_edu_level:
            return 80.0  # No education requirement specified

        candidate_edu_level = 0
        candidate_edu_text = " ".join(
            str(e.get("degree", "")) for e in parsed_resume.get("education", [])
        ).lower()
        for i, level in enumerate(self.EDUCATION_LEVELS):
            if level in candidate_edu_text:
                candidate_edu_level = len(self.EDUCATION_LEVELS) - i
                break

        if candidate_edu_level >= jd_edu_level:
            return 100.0
        if candidate_edu_level == jd_edu_level - 1:
            return 75.0
        if candidate_edu_level > 0:
            return 50.0
        return 20.0

    # ------------------------------------------------------------------
    # Fit label
    # ------------------------------------------------------------------

    @staticmethod
    def _fit_label(score: float) -> str:
        if score >= 80:
            return "Excellent Fit"
        if score >= 65:
            return "Good Fit"
        if score >= 50:
            return "Partial Fit"
        return "Poor Fit"

    # ------------------------------------------------------------------
    # Narrative builders
    # ------------------------------------------------------------------

    def _build_strengths(
        self,
        matched_skills: List[str],
        exp_score: float,
        edu_score: float,
        candidate_yoe: float,
        required_yoe: float,
    ) -> List[str]:
        strengths = []
        if matched_skills:
            top_skills = ", ".join([s.title() for s in matched_skills[:5]])
            strengths.append(f"Strong skill alignment — proficient in {top_skills}")
        if exp_score >= 80:
            strengths.append(
                f"Meets experience requirement ({candidate_yoe:.0f}+ yrs vs {required_yoe:.0f} required)"
            )
        if edu_score >= 80:
            strengths.append("Education level meets or exceeds role requirements")
        if len(matched_skills) > 8:
            strengths.append("Broad technical skill set covering most JD requirements")
        return strengths or ["Candidate has relevant background for this role"]

    def _build_weaknesses(
        self,
        missing_skills: List[str],
        exp_score: float,
        candidate_yoe: float,
        required_yoe: float,
    ) -> List[str]:
        weaknesses = []
        if missing_skills:
            top_missing = ", ".join([s.title() for s in missing_skills[:4]])
            weaknesses.append(f"Missing key skills: {top_missing}")
        if exp_score < 60:
            gap = max(0.0, required_yoe - candidate_yoe)
            weaknesses.append(
                f"Experience gap — candidate has ~{candidate_yoe:.0f} yrs, "
                f"role requires {required_yoe:.0f} yrs ({gap:.0f} yr gap)"
            )
        return weaknesses or ["No major gaps identified"]

    def _build_recommendations(
        self,
        missing_skills: List[str],
        missing_kw: List[str],
        exp_score: float,
    ) -> List[str]:
        recs = []
        if missing_skills:
            recs.append(
                f"Prioritise learning: {', '.join(s.title() for s in missing_skills[:3])}"
            )
        if missing_kw:
            recs.append(
                f"Include these JD keywords in your resume: {', '.join(missing_kw[:5])}"
            )
        if exp_score < 60:
            recs.append(
                "Consider junior/mid-level roles or build relevant project experience"
            )
        recs.append("Tailor the resume summary to mirror the JD language")
        return recs

    def _build_hiring_signals(
        self,
        overall: float,
        skill_score: float,
        exp_score: float,
        edu_score: float,
    ) -> List[str]:
        signals = []
        if overall >= 80:
            signals.append("✅ High overall fit — recommended for interview")
        elif overall >= 65:
            signals.append("🟡 Good fit — worth reviewing with hiring manager")
        elif overall >= 50:
            signals.append("⚠️  Partial fit — consider for junior or related role")
        else:
            signals.append("❌ Low fit — significant skill/experience gaps")
        if skill_score >= 75:
            signals.append("✅ Core technical skills met")
        if exp_score >= 80:
            signals.append("✅ Experience requirement met")
        return signals


# ---------------------------------------------------------------------------
# Singleton helper
# ---------------------------------------------------------------------------

_job_match_agent: Optional[JobMatchAgent] = None


def get_job_match_agent(ollama_client=None) -> JobMatchAgent:
    global _job_match_agent
    if _job_match_agent is None:
        _job_match_agent = JobMatchAgent(ollama_client)
    return _job_match_agent
