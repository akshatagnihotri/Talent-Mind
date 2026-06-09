"""
TalentMind AI — Candidate Ranking Agent
=========================================
Compares multiple candidates and produces a ranked leaderboard using the
TalentMind weighted scoring formula:

    Final Score = 0.40×ATS + 0.25×Skill + 0.20×Experience + 0.10×Education + 0.05×Certifications

Each score component must be in the range 0–100.

Returns:
    • Ranked list of candidates with composite scores
    • Tier classification (Top Tier / Strong / Average / Below Average)
    • Comparison table with sub-scores
    • Hiring recommendations per candidate

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
class CandidateScore:
    candidate_id: str
    candidate_name: str
    ats_score: float
    skill_score: float
    experience_score: float
    education_score: float
    certification_score: float
    final_score: float
    rank: int
    tier: str                       # Top Tier / Strong / Average / Below Average
    recommendation: str
    score_breakdown: Dict[str, float] = field(default_factory=dict)
    strengths: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)


@dataclass
class RankingReport:
    ranked_candidates: List[CandidateScore]
    top_candidate: CandidateScore
    total_candidates: int
    average_score: float
    score_distribution: Dict[str, int]   # tier → count
    comparison_table: List[Dict[str, Any]]
    leaderboard_summary: str


# ---------------------------------------------------------------------------
# Ranking Agent
# ---------------------------------------------------------------------------

class RankingAgent:
    """
    Ranks multiple candidates using a weighted composite scoring formula.

    Weights (configurable via constructor):
        ATS           : 0.40
        Skill Match   : 0.25
        Experience    : 0.20
        Education     : 0.10
        Certifications: 0.05
    """

    name = "Ranking Agent"

    DEFAULT_WEIGHTS = {
        "ats":           0.40,
        "skill":         0.25,
        "experience":    0.20,
        "education":     0.10,
        "certification": 0.05,
    }

    TIER_THRESHOLDS = {
        "Top Tier":      80,
        "Strong":        65,
        "Average":       50,
        "Below Average": 0,
    }

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        ollama_client=None,
    ) -> None:
        self.weights = weights or self.DEFAULT_WEIGHTS
        self.ollama = ollama_client
        self._validate_weights()

    def _validate_weights(self) -> None:
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(
                f"Weights must sum to 1.0 (got {total:.3f}). "
                "Adjust weights before initialising the agent."
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def rank(self, candidates: List[Dict[str, Any]]) -> RankingReport:
        """
        Rank a list of candidate analysis results.

        Parameters
        ----------
        candidates : list[dict]
            Each element is the full analysis output for one candidate,
            expected to contain keys:
                candidate_id   (str)
                candidate_name (str)
                ats_score      (float, 0-100)
                skill_score    (float, 0-100)
                experience_score (float, 0-100)
                education_score  (float, 0-100)
                certification_score (float, 0-100)
                strengths      (list[str])
                concerns       (list[str])   optional

        Returns
        -------
        RankingReport
        """
        if not candidates:
            raise ValueError("No candidates provided for ranking")

        logger.info("[%s] Ranking %d candidates", self.name, len(candidates))

        scored: List[CandidateScore] = []
        for candidate in candidates:
            cs = self._score_candidate(candidate)
            scored.append(cs)

        # Sort descending by final score, then by name for tie-breaking
        scored.sort(key=lambda c: (-c.final_score, c.candidate_name))

        # Assign ranks
        for i, cs in enumerate(scored, start=1):
            cs.rank = i

        average = round(sum(c.final_score for c in scored) / len(scored), 1)
        distribution = self._score_distribution(scored)
        comparison = self._build_comparison_table(scored)
        summary = self._build_leaderboard_summary(scored, average)

        report = RankingReport(
            ranked_candidates=scored,
            top_candidate=scored[0],
            total_candidates=len(scored),
            average_score=average,
            score_distribution=distribution,
            comparison_table=comparison,
            leaderboard_summary=summary,
        )
        logger.info(
            "[%s] Ranking complete. #1: %s (%.1f)",
            self.name,
            scored[0].candidate_name,
            scored[0].final_score,
        )
        return report

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def _score_candidate(self, data: Dict[str, Any]) -> CandidateScore:
        ats   = float(data.get("ats_score", 0))
        skill = float(data.get("skill_score", 0))
        exp   = float(data.get("experience_score", 0))
        edu   = float(data.get("education_score", 0))
        cert  = float(data.get("certification_score", 0))

        # Clamp all scores to [0, 100]
        ats, skill, exp, edu, cert = [
            min(100.0, max(0.0, v)) for v in (ats, skill, exp, edu, cert)
        ]

        final = (
            ats   * self.weights["ats"]
            + skill * self.weights["skill"]
            + exp   * self.weights["experience"]
            + edu   * self.weights["education"]
            + cert  * self.weights["certification"]
        )
        final = round(min(100.0, max(0.0, final)), 1)
        tier  = self._classify_tier(final)
        rec   = self._generate_recommendation(final, tier, data)

        return CandidateScore(
            candidate_id=str(data.get("candidate_id", data.get("candidate_name", "unknown"))),
            candidate_name=str(data.get("candidate_name", "Unknown")),
            ats_score=round(ats, 1),
            skill_score=round(skill, 1),
            experience_score=round(exp, 1),
            education_score=round(edu, 1),
            certification_score=round(cert, 1),
            final_score=final,
            rank=0,  # Assigned after sorting
            tier=tier,
            recommendation=rec,
            score_breakdown={
                "ATS (40%)":            round(ats   * self.weights["ats"],   1),
                "Skill (25%)":          round(skill * self.weights["skill"], 1),
                "Experience (20%)":     round(exp   * self.weights["experience"], 1),
                "Education (10%)":      round(edu   * self.weights["education"], 1),
                "Certifications (5%)":  round(cert  * self.weights["certification"], 1),
            },
            strengths=list(data.get("strengths", []))[:5],
            concerns=list(data.get("concerns", []))[:3],
        )

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    def _classify_tier(self, score: float) -> str:
        for tier, threshold in self.TIER_THRESHOLDS.items():
            if score >= threshold:
                return tier
        return "Below Average"

    def _generate_recommendation(
        self,
        score: float,
        tier: str,
        data: Dict[str, Any],
    ) -> str:
        name = data.get("candidate_name", "Candidate")
        if score >= 85:
            return (
                f"🟢 Strong Hire — {name} is an exceptional match. "
                "Fast-track to final round interviews immediately."
            )
        if score >= 70:
            return (
                f"🟡 Hire — {name} meets most requirements. "
                "Proceed to technical interview with minor skill verification."
            )
        if score >= 55:
            return (
                f"🟠 Consider — {name} has potential but gaps exist. "
                "Review with hiring manager; may fit junior or alternate role."
            )
        return (
            f"🔴 Pass — {name} does not meet minimum requirements at this stage. "
            "Keep profile on file for future openings."
        )

    # ------------------------------------------------------------------
    # Report helpers
    # ------------------------------------------------------------------

    def _score_distribution(self, scored: List[CandidateScore]) -> Dict[str, int]:
        distribution: Dict[str, int] = {
            "Top Tier": 0, "Strong": 0, "Average": 0, "Below Average": 0
        }
        for cs in scored:
            distribution[cs.tier] = distribution.get(cs.tier, 0) + 1
        return distribution

    def _build_comparison_table(
        self, scored: List[CandidateScore]
    ) -> List[Dict[str, Any]]:
        table = []
        for cs in scored:
            table.append({
                "rank":               cs.rank,
                "name":               cs.candidate_name,
                "final_score":        cs.final_score,
                "tier":               cs.tier,
                "ats_score":          cs.ats_score,
                "skill_score":        cs.skill_score,
                "experience_score":   cs.experience_score,
                "education_score":    cs.education_score,
                "certification_score": cs.certification_score,
                "recommendation":     cs.recommendation,
            })
        return table

    def _build_leaderboard_summary(
        self, scored: List[CandidateScore], avg: float
    ) -> str:
        n = len(scored)
        top = scored[0]
        top_tier_count = sum(1 for c in scored if c.tier == "Top Tier")
        return (
            f"Evaluated {n} candidate(s). Average composite score: {avg:.1f}/100. "
            f"Top Tier candidates: {top_tier_count}. "
            f"Recommended #1: {top.candidate_name} with a score of {top.final_score:.1f} ({top.tier})."
        )

    # ------------------------------------------------------------------
    # Utility: build input dict from sub-agent outputs
    # ------------------------------------------------------------------

    @staticmethod
    def build_candidate_input(
        candidate_id: str,
        candidate_name: str,
        ats_report: Any,
        job_match_report: Any,
        parsed_resume: Dict[str, Any],
        strengths: Optional[List[str]] = None,
        concerns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Helper to assemble a candidate dict from the outputs of other agents.

        Parameters
        ----------
        ats_report : ATSReport
        job_match_report : JobMatchReport
        parsed_resume : dict
        """
        # Education score (heuristic based on highest degree)
        edu_text = " ".join(
            str(e.get("degree", "")) for e in parsed_resume.get("education", [])
        ).lower()
        edu_score = 100.0
        if "phd" in edu_text or "doctorate" in edu_text:
            edu_score = 100.0
        elif "master" in edu_text or "mba" in edu_text:
            edu_score = 90.0
        elif "bachelor" in edu_text or "b.s" in edu_text or "b.tech" in edu_text:
            edu_score = 75.0
        elif "associate" in edu_text or "diploma" in edu_text:
            edu_score = 55.0
        else:
            edu_score = 40.0

        # Certification score
        certs = parsed_resume.get("certifications", [])
        cert_score = min(100.0, len(certs) * 20)

        # Experience score from job match
        exp_score = getattr(job_match_report, "experience_match_pct", 50.0)

        return {
            "candidate_id":      candidate_id,
            "candidate_name":    candidate_name,
            "ats_score":         getattr(ats_report, "overall_score", 50.0),
            "skill_score":       getattr(job_match_report, "skill_match_pct", 50.0),
            "experience_score":  exp_score,
            "education_score":   edu_score,
            "certification_score": cert_score,
            "strengths":         strengths or [],
            "concerns":          concerns or [],
        }


# ---------------------------------------------------------------------------
# Singleton helper
# ---------------------------------------------------------------------------

_ranking_agent: Optional[RankingAgent] = None


def get_ranking_agent(
    weights: Optional[Dict[str, float]] = None,
    ollama_client=None,
) -> RankingAgent:
    global _ranking_agent
    if _ranking_agent is None:
        _ranking_agent = RankingAgent(weights=weights, ollama_client=ollama_client)
    return _ranking_agent
