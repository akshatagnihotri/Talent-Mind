"""
TalentMind AI — Coordinator Agent
====================================
The central orchestrator of the TalentMind AI multi-agent pipeline.

Pipeline (sequential with error isolation):
    1.  ResumeParserAgent   → Structured candidate profile
    2.  SkillExtractorAgent → Normalised & grouped skills
    3.  ATSAnalyserAgent    → ATS score + formatting report
    4.  JobMatchAgent       → Fit percentage vs. JD
    5.  RecruiterAgent      → Human-readable recruiter brief
    6.  SkillGapAgent       → Gap analysis + learning paths
    7.  HiringDecisionAgent → Final hiring recommendation
    8.  RankingAgent        → Multi-candidate leaderboard (optional)

Design principles:
    • Each agent runs in isolation; failures are caught and logged
    • Fallback values are injected so the pipeline never crashes
    • All results are unified into a single AgentResult object
    • Timing metadata is collected for performance monitoring

Author: TalentMind AI
"""

import asyncio
import logging
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Agent imports
from agents.parser_agent.parser         import ResumeParserAgent, get_parser_agent
from agents.skill_agent.skill_extractor import SkillExtractorAgent, get_skill_agent
from agents.ats_agent.ats_analyzer      import ATSAnalyserAgent, get_ats_agent
from agents.job_match_agent.job_matcher import JobMatchAgent, get_job_match_agent
from agents.recruiter_agent.recruiter   import RecruiterAgent, get_recruiter_agent
from agents.skill_gap_agent.skill_gap   import SkillGapAgent, get_skill_gap_agent
from agents.hiring_agent.hiring_decision import HiringDecisionAgent, get_hiring_agent
from agents.ranking_agent.ranker        import RankingAgent, get_ranking_agent, RankingReport

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result data structures
# ---------------------------------------------------------------------------

@dataclass
class AgentError:
    agent_name: str
    error_type: str
    error_message: str
    traceback_snippet: str


@dataclass
class AgentResult:
    """
    Unified result object containing all sub-agent outputs.
    Every field has a fallback default so partial failures are recoverable.
    """
    # === Core parsed profile ===
    candidate_id: str = ""
    candidate_name: str = "Unknown Candidate"
    parsed_resume: Dict[str, Any] = field(default_factory=dict)

    # === Sub-agent reports ===
    skill_analysis: Any = None          # SkillAnalysis
    ats_report: Any = None              # ATSReport
    job_match_report: Any = None        # JobMatchReport
    recruiter_brief: Any = None         # RecruiterBrief
    skill_gap_report: Any = None        # SkillGapReport
    hiring_decision: Any = None         # HiringDecision

    # === Summary metrics (for quick access) ===
    ats_score: float = 0.0
    skill_match_pct: float = 0.0
    job_fit_pct: float = 0.0
    experience_years: float = 0.0
    total_skills: int = 0
    total_skill_gaps: int = 0
    composite_score: float = 0.0
    final_decision: str = "Pending"
    final_decision_emoji: str = "⏳"

    # === Pipeline metadata ===
    pipeline_duration_ms: float = 0.0
    agent_timings: Dict[str, float] = field(default_factory=dict)
    errors: List[AgentError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    pipeline_status: str = "success"    # success / partial / failed


@dataclass
class BatchRankingResult:
    """Result when multiple candidates are processed and ranked."""
    individual_results: List[AgentResult]
    ranking_report: Optional[RankingReport]
    batch_duration_ms: float
    total_candidates: int
    pipeline_errors: List[str]


# ---------------------------------------------------------------------------
# Coordinator Agent
# ---------------------------------------------------------------------------

class CoordinatorAgent:
    """
    Orchestrates the complete TalentMind AI analysis pipeline.

    Usage
    -----
    Single candidate:
        result = await coordinator.analyse(resume_text, job_description)

    Multiple candidates (with ranking):
        batch = await coordinator.analyse_batch(resumes, job_description)
    """

    name = "Coordinator Agent"

    def __init__(
        self,
        ollama_client: Any,
        ranking_weights: Optional[Dict[str, float]] = None,
    ) -> None:
        self.ollama = ollama_client
        self.ranking_weights = ranking_weights

        # Instantiate all agents
        self.parser_agent   : ResumeParserAgent   = get_parser_agent(ollama_client)
        self.skill_agent    : SkillExtractorAgent  = get_skill_agent(ollama_client)
        self.ats_agent      : ATSAnalyserAgent     = get_ats_agent(ollama_client)
        self.job_match_agent: JobMatchAgent        = get_job_match_agent(ollama_client)
        self.recruiter_agent: RecruiterAgent       = get_recruiter_agent(ollama_client)
        self.skill_gap_agent: SkillGapAgent        = get_skill_gap_agent(ollama_client)
        self.hiring_agent   : HiringDecisionAgent  = get_hiring_agent(ollama_client)
        self.ranking_agent  : RankingAgent         = get_ranking_agent(
            weights=ranking_weights, ollama_client=ollama_client
        )

        logger.info("[%s] All 8 agents initialised successfully", self.name)

    # ------------------------------------------------------------------
    # Single candidate pipeline
    # ------------------------------------------------------------------

    async def analyse(
        self,
        resume_text: str,
        job_description: str = "",
        candidate_id: Optional[str] = None,
        target_role: str = "Target Role",
    ) -> AgentResult:
        """
        Run the full analysis pipeline for a single candidate.

        Parameters
        ----------
        resume_text : str
            Raw text extracted from the resume PDF/DOCX.
        job_description : str, optional
            Job description text for matching and gap analysis.
        candidate_id : str, optional
            Unique identifier (file name, DB id, etc.).
        target_role : str, optional
            Human-readable role name for reports.

        Returns
        -------
        AgentResult
        """
        pipeline_start = time.monotonic()
        result = AgentResult(candidate_id=candidate_id or "")
        logger.info("[%s] Starting pipeline for candidate_id=%s", self.name, candidate_id)

        # ----------------------------------------------------------------
        # Step 1: Parse resume
        # ----------------------------------------------------------------
        parsed, step_ms, error = await self._run_async_agent(
            "ResumeParser",
            self.parser_agent.parse(resume_text),
        )
        result.agent_timings["ResumeParser"] = step_ms
        if error:
            result.errors.append(error)
            result.parsed_resume = self._empty_profile()
            result.pipeline_status = "partial"
        else:
            result.parsed_resume = parsed
            result.candidate_name = parsed.get("name", "Unknown Candidate")
            result.candidate_id = candidate_id or parsed.get("email", "") or str(id(parsed))
        logger.info("[%s] ✅ Step 1/7 — Parser complete (%.0fms)", self.name, step_ms)

        # ----------------------------------------------------------------
        # Step 2: Skill extraction & normalisation
        # ----------------------------------------------------------------
        jd_skills = self._extract_jd_skills_simple(job_description)
        skill_analysis, step_ms, error = await self._run_sync_agent(
            "SkillExtractor",
            lambda: self.skill_agent.analyse(
                result.parsed_resume.get("skills", []),
                jd_skills=jd_skills,
            ),
        )
        result.agent_timings["SkillExtractor"] = step_ms
        if error:
            result.errors.append(error)
        else:
            result.skill_analysis = skill_analysis
            result.total_skills = skill_analysis.total_skills_found
            # Update parsed resume with normalised skills
            result.parsed_resume["skills"] = skill_analysis.normalised_skills
        logger.info("[%s] ✅ Step 2/7 — Skill extractor complete (%.0fms)", self.name, step_ms)

        # ----------------------------------------------------------------
        # Step 3: ATS analysis
        # ----------------------------------------------------------------
        ats_report, step_ms, error = await self._run_sync_agent(
            "ATSAnalyser",
            lambda: self.ats_agent.analyse(
                result.parsed_resume,
                resume_text,
                job_description,
            ),
        )
        result.agent_timings["ATSAnalyser"] = step_ms
        if error:
            result.errors.append(error)
            result.ats_score = 50.0
        else:
            result.ats_report = ats_report
            result.ats_score = ats_report.overall_score
        logger.info("[%s] ✅ Step 3/7 — ATS analyser complete (%.0fms)", self.name, step_ms)

        # ----------------------------------------------------------------
        # Step 4: Job matching
        # ----------------------------------------------------------------
        job_match_report, step_ms, error = await self._run_sync_agent(
            "JobMatcher",
            lambda: self.job_match_agent.match(result.parsed_resume, job_description),
        )
        result.agent_timings["JobMatcher"] = step_ms
        if error:
            result.errors.append(error)
            result.skill_match_pct = 50.0
            result.job_fit_pct = 50.0
        else:
            result.job_match_report = job_match_report
            result.skill_match_pct  = job_match_report.skill_match_pct
            result.job_fit_pct      = job_match_report.overall_fit_pct
            result.experience_years = job_match_report.experience_years_candidate
        logger.info("[%s] ✅ Step 4/7 — Job matcher complete (%.0fms)", self.name, step_ms)

        # ----------------------------------------------------------------
        # Step 5: Recruiter brief (LLM)
        # ----------------------------------------------------------------
        recruiter_brief, step_ms, error = await self._run_async_agent(
            "RecruiterAgent",
            self.recruiter_agent.generate_brief(
                result.parsed_resume,
                result.ats_report,
                result.job_match_report,
                job_description,
            ),
        )
        result.agent_timings["RecruiterAgent"] = step_ms
        if error:
            result.errors.append(error)
            result.warnings.append("Recruiter brief generation failed — using fallback")
        else:
            result.recruiter_brief = recruiter_brief
        logger.info("[%s] ✅ Step 5/7 — Recruiter agent complete (%.0fms)", self.name, step_ms)

        # ----------------------------------------------------------------
        # Step 6: Skill gap analysis
        # ----------------------------------------------------------------
        missing_skills = (
            job_match_report.missing_skills
            if result.job_match_report else
            getattr(result.skill_analysis, "missing_skills", [])
        )
        skill_gap_report, step_ms, error = await self._run_sync_agent(
            "SkillGapAgent",
            lambda: self.skill_gap_agent.analyse(
                result.parsed_resume,
                missing_skills,
                job_description,
                target_role,
            ),
        )
        result.agent_timings["SkillGapAgent"] = step_ms
        if error:
            result.errors.append(error)
        else:
            result.skill_gap_report = skill_gap_report
            result.total_skill_gaps = skill_gap_report.total_gaps
        logger.info("[%s] ✅ Step 6/7 — Skill gap agent complete (%.0fms)", self.name, step_ms)

        # ----------------------------------------------------------------
        # Step 7: Hiring decision
        # ----------------------------------------------------------------
        composite = self._compute_composite(result)
        hiring_decision, step_ms, error = await self._run_sync_agent(
            "HiringDecision",
            lambda: self.hiring_agent.decide(
                result.parsed_resume,
                result.ats_report,
                result.job_match_report,
                ranking_score=composite,
                recruiter_brief=result.recruiter_brief,
            ),
        )
        result.agent_timings["HiringDecision"] = step_ms
        if error:
            result.errors.append(error)
        else:
            result.hiring_decision    = hiring_decision
            result.final_decision     = hiring_decision.decision
            result.final_decision_emoji = hiring_decision.decision_emoji
            result.composite_score    = hiring_decision.composite_score
        logger.info("[%s] ✅ Step 7/7 — Hiring decision complete (%.0fms)", self.name, step_ms)

        # ----------------------------------------------------------------
        # Finalise
        # ----------------------------------------------------------------
        pipeline_elapsed = (time.monotonic() - pipeline_start) * 1000
        result.pipeline_duration_ms = round(pipeline_elapsed, 1)

        if result.errors and not result.pipeline_status == "partial":
            result.pipeline_status = "partial" if len(result.errors) < 3 else "failed"

        logger.info(
            "[%s] 🏁 Pipeline complete for '%s' in %.0fms — Decision: %s %s",
            self.name,
            result.candidate_name,
            pipeline_elapsed,
            result.final_decision_emoji,
            result.final_decision,
        )
        return result

    # ------------------------------------------------------------------
    # Batch pipeline (multiple candidates + ranking)
    # ------------------------------------------------------------------

    async def analyse_batch(
        self,
        resumes: List[Dict[str, str]],
        job_description: str = "",
        target_role: str = "Target Role",
        max_concurrency: int = 3,
    ) -> BatchRankingResult:
        """
        Analyse multiple candidates concurrently and produce a ranked leaderboard.

        Parameters
        ----------
        resumes : list[dict]
            Each dict must have keys: ``resume_text`` and optionally
            ``candidate_id``, ``candidate_name``.
        job_description : str
        target_role : str
        max_concurrency : int
            Maximum parallel pipelines (default 3, to respect Ollama limits).

        Returns
        -------
        BatchRankingResult
        """
        batch_start = time.monotonic()
        logger.info(
            "[%s] Batch pipeline starting — %d candidates (max_concurrency=%d)",
            self.name, len(resumes), max_concurrency,
        )

        semaphore = asyncio.Semaphore(max_concurrency)
        pipeline_errors: List[str] = []

        async def _run_one(resume_data: Dict[str, str]) -> AgentResult:
            async with semaphore:
                try:
                    return await self.analyse(
                        resume_text=resume_data["resume_text"],
                        job_description=job_description,
                        candidate_id=resume_data.get("candidate_id"),
                        target_role=target_role,
                    )
                except Exception as exc:
                    cid = resume_data.get("candidate_id", "unknown")
                    msg = f"Pipeline failed for candidate_id={cid}: {exc}"
                    logger.error("[%s] %s", self.name, msg)
                    pipeline_errors.append(msg)
                    return self._error_result(resume_data)

        individual_results = await asyncio.gather(*[_run_one(r) for r in resumes])

        # ---- Ranking ----
        ranking_report = None
        try:
            ranking_inputs = []
            for res in individual_results:
                if res.pipeline_status == "failed":
                    continue
                ranking_input = RankingAgent.build_candidate_input(
                    candidate_id=res.candidate_id,
                    candidate_name=res.candidate_name,
                    ats_report=res.ats_report,
                    job_match_report=res.job_match_report,
                    parsed_resume=res.parsed_resume,
                    strengths=getattr(res.recruiter_brief, "strengths", []),
                    concerns=getattr(res.recruiter_brief, "risks", []),
                )
                ranking_inputs.append(ranking_input)

            if ranking_inputs:
                ranking_report = self.ranking_agent.rank(ranking_inputs)
                logger.info("[%s] Ranking complete — top: %s", self.name, ranking_report.top_candidate.candidate_name)
        except Exception as exc:
            msg = f"Ranking failed: {exc}"
            logger.error("[%s] %s", self.name, msg)
            pipeline_errors.append(msg)

        batch_elapsed = (time.monotonic() - batch_start) * 1000
        logger.info(
            "[%s] 🏁 Batch complete in %.0fms — %d/%d successful",
            self.name,
            batch_elapsed,
            len([r for r in individual_results if r.pipeline_status != "failed"]),
            len(resumes),
        )
        return BatchRankingResult(
            individual_results=list(individual_results),
            ranking_report=ranking_report,
            batch_duration_ms=round(batch_elapsed, 1),
            total_candidates=len(resumes),
            pipeline_errors=pipeline_errors,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _run_async_agent(
        self,
        agent_name: str,
        coroutine,
    ) -> tuple:
        """Run an async agent step, returning (result, elapsed_ms, error)."""
        start = time.monotonic()
        try:
            result = await coroutine
            elapsed = (time.monotonic() - start) * 1000
            return result, round(elapsed, 1), None
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            error = AgentError(
                agent_name=agent_name,
                error_type=type(exc).__name__,
                error_message=str(exc),
                traceback_snippet=traceback.format_exc()[-500:],
            )
            logger.error("[%s] Agent '%s' failed: %s", self.name, agent_name, exc)
            return None, round(elapsed, 1), error

    async def _run_sync_agent(
        self,
        agent_name: str,
        callable_fn,
    ) -> tuple:
        """Run a synchronous agent step in the event loop, returning (result, elapsed_ms, error)."""
        start = time.monotonic()
        try:
            result = await asyncio.get_event_loop().run_in_executor(None, callable_fn)
            elapsed = (time.monotonic() - start) * 1000
            return result, round(elapsed, 1), None
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            error = AgentError(
                agent_name=agent_name,
                error_type=type(exc).__name__,
                error_message=str(exc),
                traceback_snippet=traceback.format_exc()[-500:],
            )
            logger.error("[%s] Agent '%s' failed: %s", self.name, agent_name, exc)
            return None, round(elapsed, 1), error

    def _compute_composite(self, result: AgentResult) -> float:
        """Compute the weighted composite score from available sub-scores."""
        ats   = result.ats_score
        skill = result.skill_match_pct
        exp   = getattr(result.job_match_report, "experience_match_pct", 50.0) if result.job_match_report else 50.0
        edu   = getattr(result.job_match_report, "education_match_pct", 50.0) if result.job_match_report else 50.0
        certs = len(result.parsed_resume.get("certifications", []))
        cert_score = min(100.0, certs * 20)
        return round(
            ats * 0.40 + skill * 0.25 + exp * 0.20 + edu * 0.10 + cert_score * 0.05,
            1,
        )

    @staticmethod
    def _extract_jd_skills_simple(jd: str) -> List[str]:
        """Quick extraction of skill tokens from a JD for SkillAgent gap analysis."""
        import re
        known = [
            "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust",
            "React", "Vue", "Angular", "Next.js", "Node.js",
            "FastAPI", "Django", "Flask", "Spring Boot",
            "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
            "Docker", "Kubernetes", "Terraform", "AWS", "Azure", "GCP",
            "CI/CD", "Git", "REST API", "GraphQL", "Microservices",
            "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch",
            "Pandas", "NumPy", "Spark", "Kafka", "Airflow",
            "Power BI", "Tableau", "Scrum", "Agile", "Linux",
        ]
        jd_lower = jd.lower()
        return [s for s in known if s.lower() in jd_lower]

    @staticmethod
    def _empty_profile() -> Dict[str, Any]:
        return {
            "name": "Unknown Candidate",
            "email": "", "phone": "", "linkedin": "", "github": "",
            "summary": "", "education": [], "skills": [],
            "certifications": [], "projects": [], "work_experience": [],
        }

    @staticmethod
    def _error_result(resume_data: Dict[str, str]) -> AgentResult:
        return AgentResult(
            candidate_id=resume_data.get("candidate_id", "error"),
            candidate_name=resume_data.get("candidate_name", "Unknown"),
            pipeline_status="failed",
            final_decision="Error",
            final_decision_emoji="❌",
        )

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def result_to_dict(result: AgentResult) -> Dict[str, Any]:
        """
        Serialise an AgentResult to a plain dict suitable for JSON / database storage.
        Uses dataclasses.asdict-style traversal with safe fallbacks.
        """
        def _safe(obj: Any) -> Any:
            """Recursively convert dataclasses / objects to dicts."""
            if obj is None:
                return None
            if isinstance(obj, (str, int, float, bool)):
                return obj
            if isinstance(obj, list):
                return [_safe(i) for i in obj]
            if isinstance(obj, dict):
                return {k: _safe(v) for k, v in obj.items()}
            if hasattr(obj, "__dataclass_fields__"):
                import dataclasses
                return {k: _safe(v) for k, v in dataclasses.asdict(obj).items()}
            return str(obj)

        return {
            "candidate_id":          result.candidate_id,
            "candidate_name":        result.candidate_name,
            "ats_score":             result.ats_score,
            "skill_match_pct":       result.skill_match_pct,
            "job_fit_pct":           result.job_fit_pct,
            "experience_years":      result.experience_years,
            "total_skills":          result.total_skills,
            "total_skill_gaps":      result.total_skill_gaps,
            "composite_score":       result.composite_score,
            "final_decision":        result.final_decision,
            "final_decision_emoji":  result.final_decision_emoji,
            "pipeline_status":       result.pipeline_status,
            "pipeline_duration_ms":  result.pipeline_duration_ms,
            "agent_timings":         result.agent_timings,
            "parsed_resume":         _safe(result.parsed_resume),
            "skill_analysis":        _safe(result.skill_analysis),
            "ats_report":            _safe(result.ats_report),
            "job_match_report":      _safe(result.job_match_report),
            "recruiter_brief":       _safe(result.recruiter_brief),
            "skill_gap_report":      _safe(result.skill_gap_report),
            "hiring_decision":       _safe(result.hiring_decision),
            "errors": [
                {
                    "agent":   e.agent_name,
                    "type":    e.error_type,
                    "message": e.error_message,
                }
                for e in result.errors
            ],
            "warnings": result.warnings,
        }


# ---------------------------------------------------------------------------
# Singleton helper
# ---------------------------------------------------------------------------

_coordinator: Optional[CoordinatorAgent] = None


def get_coordinator(
    ollama_client: Any,
    ranking_weights: Optional[Dict[str, float]] = None,
) -> CoordinatorAgent:
    """Return the module-level CoordinatorAgent singleton."""
    global _coordinator
    if _coordinator is None:
        _coordinator = CoordinatorAgent(
            ollama_client=ollama_client,
            ranking_weights=ranking_weights,
        )
    return _coordinator
