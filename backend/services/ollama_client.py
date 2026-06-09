"""
TalentMind AI — Ollama LLM Client
Wraps the Ollama REST API with availability detection, structured prompting,
and a built-in demo-mode fallback that returns realistic dummy data when
Ollama is not running or DEMO_MODE=true.
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)

# ── Demo-mode canned responses ────────────────────────────────────────────────
DEMO_PARSED_RESUME: Dict[str, Any] = {
    "name": "Demo Candidate",
    "email": "demo@example.com",
    "phone": "+1-555-0100",
    "linkedin": "linkedin.com/in/democandidate",
    "education": [
        {"degree": "B.S. Computer Science", "institution": "MIT", "year": "2020"}
    ],
    "skills": [
        "Python", "Machine Learning", "SQL", "React", "FastAPI",
        "Docker", "AWS", "TypeScript", "PostgreSQL", "Redis",
    ],
    "certifications": ["AWS Certified Developer", "Google Cloud Professional"],
    "projects": [
        {
            "name": "AI Chatbot",
            "description": "Built an NLP chatbot achieving 95% intent accuracy using Rasa and BERT.",
        }
    ],
    "work_experience": [
        {
            "title": "Senior Software Engineer",
            "company": "TechCorp Inc.",
            "years": "2021-2024",
            "description": "Led a team of 5 engineers; increased deployment frequency by 40%.",
        },
        {
            "title": "Software Engineer",
            "company": "StartupXYZ",
            "years": "2020-2021",
            "description": "Built microservices handling 1M+ daily requests.",
        },
    ],
}

DEMO_ANALYSIS: Dict[str, Any] = {
    "summary": (
        "This candidate demonstrates strong technical expertise with 3+ years of experience. "
        "They show exceptional skills in Python and Machine Learning, making them a strong fit "
        "for technical roles. Their educational background from MIT and AWS certification add "
        "significant value to the team."
    ),
    "strengths": [
        "Strong proficiency in Python and modern web frameworks",
        "Demonstrated leadership experience managing a team of 5",
        "Quantified achievements showing measurable impact",
        "Relevant cloud certifications (AWS, GCP)",
    ],
    "risks": [
        "Limited experience with enterprise-scale distributed systems",
        "No explicit mention of agile/scrum certifications",
    ],
    "interview_questions": [
        "Describe your experience deploying ML models at scale in production.",
        "How did you approach mentoring junior engineers at TechCorp?",
        "Walk me through a time you increased system reliability under pressure.",
        "What monitoring and observability tools have you used?",
        "How do you handle technical debt in a fast-moving startup environment?",
    ],
    "hiring_recommendation": "Strong Hire",
    "recommendation_justification": (
        "The candidate's combination of ML expertise, leadership experience, and measurable "
        "impact makes them an excellent match for senior technical roles."
    ),
    "skill_gaps": {
        "missing": ["Kubernetes", "Terraform", "Kafka"],
        "matched": ["Python", "FastAPI", "Docker", "AWS", "PostgreSQL"],
        "recommended_paths": [
            {
                "skill": "Kubernetes",
                "resources": [
                    "Kubernetes: Up and Running (O'Reilly)",
                    "CKAD Certification course on Udemy",
                ],
            }
        ],
    },
}

DEMO_QUESTIONS: List[str] = DEMO_ANALYSIS["interview_questions"]


# ── Client ────────────────────────────────────────────────────────────────────
class OllamaClient:
    """
    Async client for the Ollama local LLM API.

    Falls back to demo mode when:
    - The Ollama server is unreachable
    - ``settings.DEMO_MODE`` is ``True``
    """

    def __init__(self) -> None:
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_MODEL
        self.available: bool = False
        self._checked: bool = False

    async def check_availability(self) -> bool:
        """Probe Ollama once and cache the result."""
        if self._checked:
            return self.available
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                self.available = response.status_code == 200
        except Exception:
            self.available = False
        self._checked = True
        logger.info("Ollama availability: %s", self.available)
        return self.available

    async def generate(self, prompt: str, system: str = "") -> str:
        """
        Send a prompt to Ollama and return the text response.
        Automatically falls back to demo data on error.
        """
        is_available = await self.check_availability()
        if not is_available or settings.DEMO_MODE:
            return self._demo_response(prompt)

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                payload: Dict[str, Any] = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                }
                if system:
                    payload["system"] = system
                response = await client.post(
                    f"{self.base_url}/api/generate", json=payload
                )
                response.raise_for_status()
                return response.json().get("response", "")
        except Exception as exc:
            logger.warning("Ollama generate failed (%s); using demo response.", exc)
            return self._demo_response(prompt)

    async def parse_resume(self, raw_text: str) -> Dict[str, Any]:
        """
        Ask the LLM to extract structured candidate data from raw resume text.
        Returns a validated dictionary with all expected fields.
        """
        system = (
            "You are an expert resume parser. Extract structured information from the "
            "resume text below and return ONLY valid JSON with these fields: "
            "name, email, phone, linkedin, education (list), skills (list of strings), "
            "certifications (list), projects (list with name+description), "
            "work_experience (list with title, company, years, description). "
            "Do not include any explanation or markdown — only raw JSON."
        )
        prompt = f"Parse this resume and return JSON:\n\n{raw_text[:6000]}"
        response = await self.generate(prompt, system)
        return self._parse_json_response(response, DEMO_PARSED_RESUME)

    async def analyze_resume(
        self,
        parsed_resume: Dict[str, Any],
        job_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a narrative analysis, strengths, risks, interview questions,
        and hiring recommendation for a candidate.
        """
        system = (
            "You are a senior HR analyst. Analyse the candidate's profile against the job "
            "description (if provided) and return ONLY valid JSON with these fields: "
            "summary (string), strengths (list), risks (list), interview_questions (list), "
            "hiring_recommendation (string: Strong Hire|Hire|Consider|Reject), "
            "recommendation_justification (string), "
            "skill_gaps (object with missing, matched, recommended_paths)."
        )
        jd_section = (
            f"\n\nJob Description:\n{job_description[:3000]}" if job_description else ""
        )
        prompt = (
            f"Candidate Profile:\n{json.dumps(parsed_resume, indent=2)[:4000]}"
            f"{jd_section}\n\nReturn analysis JSON:"
        )
        response = await self.generate(prompt, system)
        return self._parse_json_response(response, DEMO_ANALYSIS)

    async def generate_interview_questions(
        self,
        parsed_resume: Dict[str, Any],
        job_description: Optional[str] = None,
        count: int = 5,
    ) -> List[str]:
        """Generate a list of tailored interview questions."""
        system = (
            "You are an expert technical interviewer. Based on the candidate's profile, "
            f"generate exactly {count} targeted interview questions. "
            "Return ONLY a JSON array of question strings."
        )
        jd_part = f"\nJob: {job_description[:1000]}" if job_description else ""
        prompt = (
            f"Candidate skills: {parsed_resume.get('skills', [])}\n"
            f"Experience: {parsed_resume.get('work_experience', [])}{jd_part}\n"
            f"Generate {count} interview questions as a JSON array."
        )
        response = await self.generate(prompt, system)
        result = self._parse_json_response(response, DEMO_QUESTIONS)
        if isinstance(result, list):
            return result[:count]
        return DEMO_QUESTIONS[:count]

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _demo_response(self, prompt: str) -> str:
        """Return the appropriate demo JSON string based on prompt keywords."""
        pl = prompt.lower()
        if any(kw in pl for kw in ("parse", "extract", "resume")):
            return json.dumps(DEMO_PARSED_RESUME)
        if any(kw in pl for kw in ("question", "interview")):
            return json.dumps(DEMO_QUESTIONS)
        return json.dumps(DEMO_ANALYSIS)

    def _parse_json_response(self, response: str, fallback: Any) -> Any:
        """
        Try to extract valid JSON from the LLM response.
        Falls back to ``fallback`` if parsing fails.
        """
        # Strip markdown code fences if present
        text = response.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])

        # Find first JSON structure (object or array)
        for start_char, end_char in [("{", "}"), ("[", "]")]:
            start = text.find(start_char)
            end = text.rfind(end_char)
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start : end + 1])
                except json.JSONDecodeError:
                    pass

        logger.warning("Could not parse LLM JSON response; using fallback.")
        return fallback


# Singleton instance shared across the application
ollama_client = OllamaClient()
