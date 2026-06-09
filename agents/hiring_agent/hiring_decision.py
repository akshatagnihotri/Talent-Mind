"""
TalentMind AI — Hiring Decision Agent
=======================================
Produces a final hiring recommendation for a candidate by synthesising
all sub-agent outputs into a clear, defensible decision.

Decision outcomes:
    🟢 Strong Hire   — Candidate clearly exceeds requirements
    🟡 Hire          — Candidate meets requirements with minor gaps
    🟠 Consider      — Candidate is borderline; conditional recommendation
    🔴 Reject        — Candidate does not meet minimum requirements

The agent also surfaces the key decision factors, risk flags,
and a hiring panel briefing note.

Author: TalentMind AI
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class HiringDecision:
    candidate_name: str
    decision: str                   # Strong Hire / Hire / Consider / Reject
    decision_emoji: str             # 🟢 / 🟡 / 🟠 / 🔴
    confidence: str                 # High / Medium / Low
    composite_score: float          # 0–100
    key_factors: List[str]          # Most important reasons for the decision
    positive_signals: List[str]     # Green flags
    risk_flags: List[str]           # Red / amber flags
    conditions: List[str]           # Conditions for a conditional hire
    panel_briefing: str             # Short paragraph for the hiring panel
    next_steps: List[str]           # Recommended next actions
    alternative_roles: List[str]    # Other roles this candidate might fit


# ---------------------------------------------------------------------------
# Hiring Decision Agent
# ---------------------------------------------------------------------------

class HiringDecisionAgent:
    """
    Synthesises all agent outputs into a final hiring decision.
    """

    name = "Hiring Decision Agent"

    # Minimum score thresholds
    THRESHOLDS = {
        "strong_hire": 80,
        "hire":        65,
        "consider":    50,
        # Below 50 → Reject
    }

    # Skills considered deal-breakers if missing (role-category specific)
    DEAL_BREAKER_SIGNALS = [
        "experience_score < 30",   # Evaluated programmatically
        "ats_score < 30",
        "skill_score < 25",
    ]

    def __init__(self, ollama_client=None) -> None:
        self.ollama = ollama_client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def decide(
        self,
        parsed_resume: Dict[str, Any],
        ats_report: Any,
        job_match_report: Any,
        ranking_score: Optional[float] = None,
        recruiter_brief: Any = None,
    ) -> HiringDecision:
        """
        Produce a final hiring decision.

        Parameters
        ----------
        parsed_resume : dict
            Output from ResumeParserAgent.
        ats_report : ATSReport
        job_match_report : JobMatchReport
        ranking_score : float, optional
            Composite score from RankingAgent (0-100).
        recruiter_brief : RecruiterBrief, optional
        """
        candidate_name = parsed_resume.get("name", "Unknown Candidate")
        logger.info("[%s] Generating hiring decision for: %s", self.name, candidate_name)

        # Extract key metrics
        ats_score      = float(getattr(ats_report, "overall_score", 50.0))
        skill_score    = float(getattr(job_match_report, "skill_match_pct", 50.0))
        fit_pct        = float(getattr(job_match_report, "overall_fit_pct", 50.0))
        exp_score      = float(getattr(job_match_report, "experience_match_pct", 50.0))
        edu_score      = float(getattr(job_match_report, "education_match_pct", 50.0))
        matched_skills = getattr(job_match_report, "matched_skills", [])
        missing_skills = getattr(job_match_report, "missing_skills", [])
        candidate_yoe  = float(getattr(job_match_report, "experience_years_candidate", 0))
        required_yoe   = float(getattr(job_match_report, "experience_years_required", 3))

        # Composite score
        composite = ranking_score if ranking_score is not None else self._compute_composite(
            ats_score, skill_score, exp_score, edu_score,
            len(parsed_resume.get("certifications", []))
        )

        # Check for deal-breakers
        deal_breakers = self._check_deal_breakers(ats_score, skill_score, exp_score)

        # Primary decision
        if deal_breakers:
            decision = "Reject"
        elif composite >= self.THRESHOLDS["strong_hire"]:
            decision = "Strong Hire"
        elif composite >= self.THRESHOLDS["hire"]:
            decision = "Hire"
        elif composite >= self.THRESHOLDS["consider"]:
            decision = "Consider"
        else:
            decision = "Reject"

        emoji_map = {
            "Strong Hire": "🟢",
            "Hire":        "🟡",
            "Consider":    "🟠",
            "Reject":      "🔴",
        }

        # Confidence level
        confidence = self._assess_confidence(composite, decision)

        # Build structured outputs
        key_factors    = self._build_key_factors(decision, composite, ats_score, skill_score, exp_score)
        positive       = self._build_positive_signals(matched_skills, ats_score, exp_score, edu_score, candidate_yoe, required_yoe, parsed_resume)
        risks          = self._build_risk_flags(missing_skills, ats_score, exp_score, candidate_yoe, required_yoe, deal_breakers)
        conditions     = self._build_conditions(decision, missing_skills, exp_score)
        briefing       = self._build_panel_briefing(candidate_name, decision, composite, fit_pct, parsed_resume, matched_skills, missing_skills)
        next_steps     = self._build_next_steps(decision, missing_skills)
        alt_roles      = self._suggest_alternative_roles(parsed_resume, decision)

        hiring_decision = HiringDecision(
            candidate_name=candidate_name,
            decision=decision,
            decision_emoji=emoji_map.get(decision, ""),
            confidence=confidence,
            composite_score=round(composite, 1),
            key_factors=key_factors,
            positive_signals=positive,
            risk_flags=risks,
            conditions=conditions,
            panel_briefing=briefing,
            next_steps=next_steps,
            alternative_roles=alt_roles,
        )
        logger.info(
            "[%s] Decision: %s (%.1f, confidence: %s)",
            self.name, decision, composite, confidence
        )
        return hiring_decision

    # ------------------------------------------------------------------
    # Score computation
    # ------------------------------------------------------------------

    def _compute_composite(
        self,
        ats: float,
        skill: float,
        exp: float,
        edu: float,
        cert_count: int,
    ) -> float:
        cert_score = min(100.0, cert_count * 20)
        return round(
            ats   * 0.40
            + skill * 0.25
            + exp   * 0.20
            + edu   * 0.10
            + cert_score * 0.05,
            1,
        )

    # ------------------------------------------------------------------
    # Deal-breaker detection
    # ------------------------------------------------------------------

    def _check_deal_breakers(
        self, ats: float, skill: float, exp: float
    ) -> List[str]:
        breakers = []
        if ats < 30:
            breakers.append(f"Critically low ATS score ({ats:.0f}/100)")
        if skill < 25:
            breakers.append(f"Critical skill shortage — only {skill:.0f}% of required skills met")
        if exp < 25:
            breakers.append(f"Severely under-experienced for the role ({exp:.0f}% experience match)")
        return breakers

    # ------------------------------------------------------------------
    # Confidence assessment
    # ------------------------------------------------------------------

    @staticmethod
    def _assess_confidence(composite: float, decision: str) -> str:
        if decision == "Strong Hire" and composite >= 85:
            return "High"
        if decision == "Reject" and composite <= 35:
            return "High"
        if 60 <= composite <= 75:
            return "Medium"
        return "Medium"

    # ------------------------------------------------------------------
    # Narrative builders
    # ------------------------------------------------------------------

    def _build_key_factors(
        self,
        decision: str,
        composite: float,
        ats: float,
        skill: float,
        exp: float,
    ) -> List[str]:
        factors = [
            f"Composite hiring score: {composite:.1f}/100 → {decision}",
            f"ATS readiness: {ats:.0f}/100 (weight: 40%)",
            f"Skill match: {skill:.0f}/100 (weight: 25%)",
            f"Experience match: {exp:.0f}/100 (weight: 20%)",
        ]
        return factors

    def _build_positive_signals(
        self,
        matched_skills: List[str],
        ats: float,
        exp: float,
        edu: float,
        cand_yoe: float,
        req_yoe: float,
        parsed: Dict[str, Any],
    ) -> List[str]:
        signals = []
        if matched_skills:
            signals.append(f"Strong skill alignment — {len(matched_skills)} required skills matched")
        if ats >= 70:
            signals.append(f"Good ATS readiness ({ats:.0f}/100)")
        if exp >= 80:
            signals.append(f"Experience meets requirement ({cand_yoe:.0f}/{req_yoe:.0f} years)")
        if edu >= 80:
            signals.append("Education level meets or exceeds role requirements")
        if parsed.get("certifications"):
            signals.append(f"Holds {len(parsed['certifications'])} professional certification(s)")
        if parsed.get("projects"):
            signals.append(f"Demonstrated project portfolio ({len(parsed['projects'])} projects)")
        return signals or ["Candidate shows potential for the role"]

    def _build_risk_flags(
        self,
        missing_skills: List[str],
        ats: float,
        exp: float,
        cand_yoe: float,
        req_yoe: float,
        deal_breakers: List[str],
    ) -> List[str]:
        flags = list(deal_breakers)
        if missing_skills:
            flags.append(f"{len(missing_skills)} JD-required skill(s) not found on resume")
        if ats < 60:
            flags.append(f"Below-average ATS score ({ats:.0f}) — may not pass automated screening")
        if cand_yoe < req_yoe:
            gap = req_yoe - cand_yoe
            flags.append(f"Experience gap: {gap:.0f} year(s) below requirement")
        return flags or ["No major risk flags identified"]

    def _build_conditions(
        self,
        decision: str,
        missing_skills: List[str],
        exp: float,
    ) -> List[str]:
        if decision == "Strong Hire":
            return []
        if decision in ("Hire", "Consider"):
            conds = []
            if missing_skills:
                conds.append(
                    f"Candidate commits to upskilling in: {', '.join(missing_skills[:3])}"
                )
            if exp < 70:
                conds.append("Satisfactory performance in technical screening round")
            conds.append("Reference checks clear")
            return conds
        return []

    def _build_panel_briefing(
        self,
        name: str,
        decision: str,
        composite: float,
        fit_pct: float,
        parsed: Dict[str, Any],
        matched: List[str],
        missing: List[str],
    ) -> str:
        skills_str = ", ".join(matched[:5]) if matched else "various technologies"
        edu_str = parsed.get("education", [{}])[0].get("degree", "Not specified") if parsed.get("education") else "Not specified"
        missing_str = ", ".join(missing[:3]) if missing else "none significant"
        briefing = (
            f"{name} is recommended as a '{decision}' with a composite score of {composite:.1f}/100 "
            f"and {fit_pct:.0f}% job fit. "
            f"Core competencies include {skills_str}. "
            f"Education: {edu_str}. "
            f"Notable gaps: {missing_str}. "
        )
        if decision == "Strong Hire":
            briefing += "Fast-track to final round is recommended."
        elif decision == "Hire":
            briefing += "Proceed to technical interview to confirm core competencies."
        elif decision == "Consider":
            briefing += "A pre-screening call is advised before committing to a full interview cycle."
        else:
            briefing += "Candidate does not meet minimum requirements at this stage; archive profile."
        return briefing

    def _build_next_steps(
        self, decision: str, missing_skills: List[str]
    ) -> List[str]:
        steps_map = {
            "Strong Hire": [
                "Schedule final-round technical interview immediately",
                "Prepare compensation and offer discussion",
                "Complete background and reference check in parallel",
                "Assign a hiring buddy / onboarding mentor",
            ],
            "Hire": [
                "Schedule technical interview within 5 business days",
                "Verify key skills during the interview",
                "Request 2 professional references",
                "Prepare conditional offer letter",
            ],
            "Consider": [
                "Schedule 30-minute pre-screening call with recruiter",
                "Share the role requirements document and ask for candidate's self-assessment",
                "Evaluate for junior or alternate role if main role doesn't fit",
                "Re-assess in 3 months if candidate upskills",
            ],
            "Reject": [
                "Send a professional, timely rejection email",
                f"Archive profile — flag for future openings in {', '.join(missing_skills[:2]) or 'relevant areas'}",
                "Provide general feedback if requested by candidate",
            ],
        }
        return steps_map.get(decision, ["Proceed as per standard recruitment policy"])

    def _suggest_alternative_roles(
        self, parsed: Dict[str, Any], decision: str
    ) -> List[str]:
        if decision in ("Strong Hire", "Hire"):
            return []
        skills = [s.lower() for s in parsed.get("skills", [])]
        alternatives = []
        if any(s in skills for s in ["python", "pandas", "sql", "machine learning"]):
            alternatives.append("Junior Data Analyst / Data Engineer")
        if any(s in skills for s in ["react", "javascript", "html", "css"]):
            alternatives.append("Junior Frontend Developer")
        if any(s in skills for s in ["java", "spring", "node.js", "fastapi"]):
            alternatives.append("Junior Backend Developer")
        if any(s in skills for s in ["aws", "docker", "linux", "terraform"]):
            alternatives.append("Cloud Support Engineer / DevOps Associate")
        if any(s in skills for s in ["agile", "scrum", "jira", "project management"]):
            alternatives.append("Technical Project Coordinator")
        return alternatives[:3] or ["Explore entry-level roles in the relevant domain"]


# ---------------------------------------------------------------------------
# Singleton helper
# ---------------------------------------------------------------------------

_hiring_agent: Optional[HiringDecisionAgent] = None


def get_hiring_agent(ollama_client=None) -> HiringDecisionAgent:
    global _hiring_agent
    if _hiring_agent is None:
        _hiring_agent = HiringDecisionAgent(ollama_client)
    return _hiring_agent
