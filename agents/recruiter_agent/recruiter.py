"""
TalentMind AI — Recruiter Agent
=================================
Uses Ollama (with structured-fallback) to generate a human-readable recruiter
brief for any candidate.  Output includes:

    • 5 candidate strengths (bullet points)
    • 3 risks / concerns (bullet points)
    • 5-7 tailored interview questions
    • Professional summary paragraph
    • Hiring recommendation rationale

The recruiter brief is designed to save the recruiter 20-30 minutes of
resume review time per candidate.

Author: TalentMind AI
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class RecruiterBrief:
    candidate_name: str
    professional_summary: str
    strengths: List[str]               # 5 bullets
    risks: List[str]                   # 3 bullets
    interview_questions: List[str]     # 5-7 questions
    hiring_recommendation: str
    recommendation_rationale: str
    culture_fit_notes: str
    salary_range_suggestion: str


# ---------------------------------------------------------------------------
# Recruiter Agent
# ---------------------------------------------------------------------------

class RecruiterAgent:
    """
    Generates a structured recruiter brief using Ollama.
    Falls back to rule-based generation when Ollama is unavailable.
    """

    name = "Recruiter Agent"

    # Default interview question banks per category
    BEHAVIORAL_QUESTIONS = [
        "Tell me about a time you delivered a project under a tight deadline. What was your approach?",
        "Describe a situation where you had to persuade a sceptical stakeholder. What was the outcome?",
        "Give an example of when you identified and resolved a critical production issue.",
        "How have you handled disagreements with your manager or team lead?",
        "Tell me about the most complex technical challenge you faced and how you solved it.",
        "Describe your experience mentoring junior developers. What impact did it have?",
        "Walk me through a time you introduced a new technology or process at work.",
    ]

    TECHNICAL_QUESTION_TEMPLATES = [
        "Can you walk us through a recent {skill} project you built from scratch?",
        "How would you optimise a slow {skill} query / pipeline for a production system?",
        "Explain the trade-offs between {skill} and its main alternatives.",
        "What design patterns do you use when working with {skill}?",
        "How do you ensure code quality and testing coverage in a {skill} project?",
    ]

    def __init__(self, ollama_client=None) -> None:
        self.ollama = ollama_client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_brief(
        self,
        parsed_resume: Dict[str, Any],
        ats_report: Any,
        job_match_report: Any,
        job_description: str = "",
    ) -> RecruiterBrief:
        """
        Generate a complete recruiter brief for the candidate.

        Parameters
        ----------
        parsed_resume : dict
            Output from ResumeParserAgent.
        ats_report : ATSReport
            Output from ATSAnalyserAgent.
        job_match_report : JobMatchReport
            Output from JobMatchAgent.
        job_description : str
            Raw JD text for context.
        """
        candidate_name = parsed_resume.get("name", "Unknown Candidate")
        logger.info("[%s] Generating recruiter brief for: %s", self.name, candidate_name)

        # Try Ollama first
        brief = None
        if self.ollama:
            brief = await self._llm_generate_brief(
                parsed_resume, ats_report, job_match_report, job_description
            )

        # Fallback to rule-based
        if brief is None:
            brief = self._rule_based_brief(
                parsed_resume, ats_report, job_match_report
            )

        logger.info("[%s] Brief generated for: %s", self.name, candidate_name)
        return brief

    # ------------------------------------------------------------------
    # LLM-based generation
    # ------------------------------------------------------------------

    async def _llm_generate_brief(
        self,
        parsed_resume: Dict[str, Any],
        ats_report: Any,
        job_match_report: Any,
        job_description: str,
    ) -> Optional[RecruiterBrief]:
        """Ask Ollama to generate a structured recruiter brief."""
        candidate_name = parsed_resume.get("name", "Candidate")
        skills_str = ", ".join(parsed_resume.get("skills", [])[:15])
        experience_count = len(parsed_resume.get("work_experience", []))
        ats_score = getattr(ats_report, "overall_score", "N/A")
        fit_pct = getattr(job_match_report, "overall_fit_pct", "N/A")
        matched_skills = getattr(job_match_report, "matched_skills", [])[:8]
        missing_skills = getattr(job_match_report, "missing_skills", [])[:5]

        system_prompt = """You are a senior HR recruiter writing a concise candidate brief.
Return ONLY a valid JSON object with these exact keys:
  professional_summary (string, 3-4 sentences),
  strengths (list of exactly 5 strings, each a complete sentence starting with a strong adjective),
  risks (list of exactly 3 strings, each a complete sentence describing a concern),
  interview_questions (list of 6 strings, each a complete interview question),
  hiring_recommendation (string: one of "Strong Hire", "Hire", "Consider", "Reject"),
  recommendation_rationale (string, 2-3 sentences justifying the recommendation),
  culture_fit_notes (string, 1-2 sentences about culture fit),
  salary_range_suggestion (string, e.g. "$90,000 – $110,000 based on experience")
Return ONLY the JSON, no explanation, no markdown."""

        prompt = f"""Generate a recruiter brief for:

Name: {candidate_name}
Skills: {skills_str}
Work Experience Entries: {experience_count}
ATS Score: {ats_score}/100
Job Fit %: {fit_pct}%
Matched Skills: {', '.join(matched_skills)}
Missing Skills: {', '.join(missing_skills)}

Job Description Summary:
{job_description[:1000]}"""

        try:
            response = await self.ollama.generate(prompt, system_prompt)
            cleaned = re.sub(r"```(?:json)?\n?|```", "", response).strip()
            first_brace = cleaned.find("{")
            last_brace = cleaned.rfind("}")
            if first_brace == -1 or last_brace == -1:
                raise ValueError("No JSON object in response")
            data = json.loads(cleaned[first_brace: last_brace + 1])

            return RecruiterBrief(
                candidate_name=candidate_name,
                professional_summary=str(data.get("professional_summary", "")),
                strengths=[str(s) for s in data.get("strengths", [])[:5]],
                risks=[str(r) for r in data.get("risks", [])[:3]],
                interview_questions=[str(q) for q in data.get("interview_questions", [])[:7]],
                hiring_recommendation=str(data.get("hiring_recommendation", "Consider")),
                recommendation_rationale=str(data.get("recommendation_rationale", "")),
                culture_fit_notes=str(data.get("culture_fit_notes", "")),
                salary_range_suggestion=str(data.get("salary_range_suggestion", "Market rate")),
            )
        except Exception as exc:
            logger.warning("[%s] LLM brief generation failed: %s", self.name, exc)
            return None

    # ------------------------------------------------------------------
    # Rule-based fallback
    # ------------------------------------------------------------------

    def _rule_based_brief(
        self,
        parsed_resume: Dict[str, Any],
        ats_report: Any,
        job_match_report: Any,
    ) -> RecruiterBrief:
        candidate_name = parsed_resume.get("name", "The Candidate")
        skills = parsed_resume.get("skills", [])
        top_skills = skills[:5]
        experience_entries = parsed_resume.get("work_experience", [])
        certifications = parsed_resume.get("certifications", [])
        ats_score = getattr(ats_report, "overall_score", 50.0)
        fit_pct = getattr(job_match_report, "overall_fit_pct", 50.0)
        matched = getattr(job_match_report, "matched_skills", [])
        missing = getattr(job_match_report, "missing_skills", [])
        years_exp = getattr(job_match_report, "experience_years_candidate", 0)

        # Professional summary
        summary = (
            f"{candidate_name} is a {self._seniority_label(years_exp)} professional "
            f"with expertise in {', '.join(top_skills[:3]) if top_skills else 'various technologies'}. "
            f"They have {len(experience_entries)} documented work experience position(s) "
            f"and scored {ats_score:.0f}/100 on ATS evaluation with a {fit_pct:.0f}% job fit. "
            f"{'Certifications include: ' + ', '.join(certifications[:3]) + '.' if certifications else ''}"
        ).strip()

        # Strengths
        strengths = []
        if matched:
            strengths.append(
                f"Demonstrated proficiency in key required skills: {', '.join(matched[:4])}"
            )
        if ats_score >= 70:
            strengths.append(
                f"Well-structured resume with strong ATS score of {ats_score:.0f}/100 "
                "indicating good formatting and keyword optimisation"
            )
        if years_exp >= 3:
            strengths.append(
                f"Solid {years_exp:.0f}+ years of relevant industry experience "
                "across multiple roles"
            )
        if certifications:
            strengths.append(
                f"Holds {len(certifications)} professional certification(s) "
                f"({', '.join(certifications[:2])}), demonstrating commitment to learning"
            )
        if len(skills) >= 8:
            strengths.append(
                f"Broad technical skill set with {len(skills)} documented competencies "
                "covering multiple domains"
            )
        while len(strengths) < 5:
            strengths.append("Shows initiative and capability based on overall profile")

        # Risks
        risks = []
        if missing:
            risks.append(
                f"Missing {len(missing)} JD-required skills ({', '.join(missing[:3])}); "
                "may require ramp-up time"
            )
        if ats_score < 60:
            risks.append(
                f"Below-average ATS score ({ats_score:.0f}/100) suggests potential "
                "resume formatting or keyword gaps"
            )
        if years_exp < getattr(job_match_report, "experience_years_required", 3):
            req = getattr(job_match_report, "experience_years_required", 3)
            risks.append(
                f"Experience ({years_exp:.0f} yrs) is below the {req:.0f}-year requirement; "
                "may need closer supervision initially"
            )
        while len(risks) < 3:
            risks.append("No additional significant concerns identified at this stage")

        # Interview questions
        questions = list(self.BEHAVIORAL_QUESTIONS[:3])
        for skill in top_skills[:2]:
            q = self.TECHNICAL_QUESTION_TEMPLATES[0].format(skill=skill)
            questions.append(q)
        q2 = self.TECHNICAL_QUESTION_TEMPLATES[2].format(skill=top_skills[0] if top_skills else "your primary technology")
        questions.append(q2)
        questions = questions[:7]

        # Recommendation
        if fit_pct >= 80:
            rec = "Strong Hire"
            rationale = (
                f"{candidate_name} demonstrates strong alignment with the role requirements "
                f"({fit_pct:.0f}% fit). Their technical background and ATS performance "
                "make them a top-tier candidate. Recommend immediate interview scheduling."
            )
        elif fit_pct >= 65:
            rec = "Hire"
            rationale = (
                f"{candidate_name} is a solid candidate with {fit_pct:.0f}% job fit. "
                "Minor skill gaps can be addressed with onboarding support. "
                "Proceed to technical interview to validate core competencies."
            )
        elif fit_pct >= 50:
            rec = "Consider"
            rationale = (
                f"{candidate_name} shows potential ({fit_pct:.0f}% fit) but has notable gaps. "
                "May be suitable for a junior variant of the role or a related position. "
                "Recommend a pre-screening call before committing to a full interview."
            )
        else:
            rec = "Reject"
            rationale = (
                f"{candidate_name} does not meet minimum requirements ({fit_pct:.0f}% fit). "
                "Significant skill and experience gaps would require extensive investment. "
                "Recommend keeping profile on file for future junior openings."
            )

        salary = self._estimate_salary(skills, years_exp, certifications)

        return RecruiterBrief(
            candidate_name=candidate_name,
            professional_summary=summary,
            strengths=strengths[:5],
            risks=risks[:3],
            interview_questions=questions,
            hiring_recommendation=rec,
            recommendation_rationale=rationale,
            culture_fit_notes=(
                "Based on the diversity of projects and collaborative roles listed, "
                "the candidate appears to have experience in cross-functional team environments."
            ),
            salary_range_suggestion=salary,
        )

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _seniority_label(years: float) -> str:
        if years >= 10:
            return "Principal/Staff-level"
        if years >= 7:
            return "Senior"
        if years >= 4:
            return "Mid-level"
        if years >= 1:
            return "Junior to Mid-level"
        return "Entry-level"

    @staticmethod
    def _estimate_salary(
        skills: List[str],
        years: float,
        certifications: List[str],
    ) -> str:
        base = 55_000
        base += min(years, 12) * 5_000

        premium_skills = {
            "Machine Learning", "Deep Learning", "Kubernetes", "AWS", "GCP",
            "Azure", "Terraform", "Spark", "Kafka", "TensorFlow", "PyTorch",
        }
        premium_count = sum(1 for s in skills if s in premium_skills)
        base += premium_count * 3_000
        base += len(certifications) * 2_000

        high = base + 20_000
        return f"${base:,.0f} – ${high:,.0f} (estimated, market-dependent)"


# ---------------------------------------------------------------------------
# Singleton helper
# ---------------------------------------------------------------------------

_recruiter_agent: Optional[RecruiterAgent] = None


def get_recruiter_agent(ollama_client=None) -> RecruiterAgent:
    global _recruiter_agent
    if _recruiter_agent is None:
        _recruiter_agent = RecruiterAgent(ollama_client)
    return _recruiter_agent
