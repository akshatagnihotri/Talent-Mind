"""
TalentMind AI — Candidate Ranking Engine
Combines multiple score dimensions into a single final score and assigns
hiring recommendations.

Weighting formula
─────────────────
  ATS Score        40 %
  Skill Match      25 %
  Experience       20 %
  Education        10 %
  Certifications    5 %
  ────────────────────
  Final Score     100 %
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class CandidateScore:
    candidate_id: str
    candidate_name: str
    final_score: float
    ats_score: float
    skill_match: float
    experience_score: float
    education_score: float
    certification_score: float
    rank: int
    recommendation: str


class RankingEngine:
    """
    Ranks a pool of candidates for a single job description.

    Each candidate dict is expected to have:
        id                 – candidate database id
        name               – display name
        analysis:          – dict of scored dimensions
            ats_score
            match_score    (skill match %)
            experience_score
            education_score
            certification_score
    """

    WEIGHTS: Dict[str, float] = {
        "ats_score": 0.40,
        "skill_match": 0.25,
        "experience": 0.20,
        "education": 0.10,
        "certifications": 0.05,
    }

    RECOMMENDATION_THRESHOLDS = [
        (80.0, "Strong Hire"),
        (65.0, "Hire"),
        (50.0, "Consider"),
        (0.0, "Reject"),
    ]

    def rank_candidates(self, candidates: List[Dict[str, Any]]) -> List[CandidateScore]:
        """
        Score and rank a list of candidates.

        Parameters
        ----------
        candidates:
            List of dicts, each with ``id``, ``name``, and ``analysis`` sub-dict.

        Returns
        -------
        List[CandidateScore]
            Sorted descending by ``final_score`` with ``rank`` assigned (1-indexed).
        """
        scored: List[CandidateScore] = []

        for candidate in candidates:
            analysis = candidate.get("analysis") or {}
            final = (
                float(analysis.get("ats_score", 0)) * self.WEIGHTS["ats_score"]
                + float(analysis.get("match_score", 0)) * self.WEIGHTS["skill_match"]
                + float(analysis.get("experience_score", 0)) * self.WEIGHTS["experience"]
                + float(analysis.get("education_score", 0)) * self.WEIGHTS["education"]
                + float(analysis.get("certification_score", 0)) * self.WEIGHTS["certifications"]
            )
            final = min(round(final, 1), 100.0)

            scored.append(
                CandidateScore(
                    candidate_id=candidate.get("id", ""),
                    candidate_name=candidate.get("name") or "Unknown Candidate",
                    final_score=final,
                    ats_score=float(analysis.get("ats_score", 0)),
                    skill_match=float(analysis.get("match_score", 0)),
                    experience_score=float(analysis.get("experience_score", 0)),
                    education_score=float(analysis.get("education_score", 0)),
                    certification_score=float(analysis.get("certification_score", 0)),
                    rank=0,  # assigned below
                    recommendation=self._get_recommendation(final),
                )
            )

        # Sort descending by final score; use candidate_name as a tiebreaker
        scored.sort(key=lambda x: (-x.final_score, x.candidate_name))

        # Assign 1-based ranks
        for idx, cs in enumerate(scored):
            cs.rank = idx + 1

        return scored

    def _get_recommendation(self, score: float) -> str:
        for threshold, label in self.RECOMMENDATION_THRESHOLDS:
            if score >= threshold:
                return label
        return "Reject"

    def generate_leaderboard_summary(
        self, ranked: List[CandidateScore]
    ) -> Dict[str, Any]:
        """Return aggregate stats for the leaderboard header."""
        if not ranked:
            return {
                "total": 0,
                "strong_hire": 0,
                "hire": 0,
                "consider": 0,
                "reject": 0,
                "avg_score": 0.0,
            }
        recommendation_counts: Dict[str, int] = {
            "Strong Hire": 0,
            "Hire": 0,
            "Consider": 0,
            "Reject": 0,
        }
        for cs in ranked:
            recommendation_counts[cs.recommendation] = (
                recommendation_counts.get(cs.recommendation, 0) + 1
            )
        avg_score = round(sum(c.final_score for c in ranked) / len(ranked), 1)
        return {
            "total": len(ranked),
            "strong_hire": recommendation_counts["Strong Hire"],
            "hire": recommendation_counts["Hire"],
            "consider": recommendation_counts["Consider"],
            "reject": recommendation_counts["Reject"],
            "avg_score": avg_score,
        }


# Shared singleton
ranking_engine = RankingEngine()
