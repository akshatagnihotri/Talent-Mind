"""
TalentMind AI — Resume Parser Agent
====================================
Responsible for converting raw resume text into a structured JSON object.

Strategy:
    1. Primary   — Ollama LLM (intelligent, contextual extraction)
    2. Fallback  — Regex + heuristic extraction (fast, deterministic)

Author: TalentMind AI
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Parser Agent
# ---------------------------------------------------------------------------

class ResumeParserAgent:
    """
    Parses raw resume text into a structured dictionary.

    The agent first attempts an LLM-based parse via the supplied Ollama client.
    On any failure it falls back to deterministic regex extraction so the
    pipeline never crashes on a bad LLM response.
    """

    name = "Resume Parser Agent"

    # Common technical / domain skills to scan for
    KNOWN_SKILLS: List[str] = [
        # Languages
        "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust", "C", "C++",
        "C#", "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "MATLAB",
        "Bash", "Shell", "PowerShell", "Groovy", "Dart", "Elixir", "Perl",
        # Frontend
        "React", "Vue", "Angular", "Next.js", "Nuxt.js", "Svelte", "HTML",
        "CSS", "SASS", "SCSS", "Tailwind", "Bootstrap", "Material UI",
        "Redux", "Zustand", "GraphQL", "Apollo",
        # Backend / Frameworks
        "Node.js", "Express", "FastAPI", "Django", "Flask", "Spring Boot",
        "ASP.NET", "Laravel", "Rails", "Gin", "Fiber",
        # Databases
        "SQL", "PostgreSQL", "MySQL", "SQLite", "Oracle", "MSSQL",
        "MongoDB", "Cassandra", "DynamoDB", "Firestore", "Redis",
        "Elasticsearch", "CouchDB", "InfluxDB", "Neo4j",
        # Cloud & DevOps
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform",
        "Ansible", "Jenkins", "GitHub Actions", "GitLab CI", "CircleCI",
        "Helm", "Prometheus", "Grafana", "Nginx", "Apache", "Linux",
        "CI/CD", "DevOps", "SRE", "Serverless", "Lambda",
        # Data / ML / AI
        "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
        "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "XGBoost",
        "LightGBM", "Pandas", "NumPy", "SciPy", "Matplotlib", "Seaborn",
        "Spark", "Hadoop", "Kafka", "Airflow", "dbt", "Snowflake",
        "Power BI", "Tableau", "Looker", "Excel",
        # Methods
        "Agile", "Scrum", "Kanban", "TDD", "BDD", "JIRA", "Confluence",
        "REST API", "Microservices", "Event-Driven", "Domain-Driven Design",
        "Design Patterns", "System Design", "Git",
    ]

    def __init__(self, ollama_client: Any) -> None:
        self.ollama = ollama_client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def parse(self, resume_text: str) -> Dict[str, Any]:
        """
        Parse *resume_text* and return a structured candidate profile.

        Returns
        -------
        Dict with keys:
            name, email, phone, linkedin, github, summary,
            education, skills, certifications, projects, work_experience
        """
        logger.info("[%s] Parsing resume (%d chars)", self.name, len(resume_text))

        parsed = await self._llm_parse(resume_text)

        if parsed is None:
            logger.warning("[%s] LLM parse failed — using regex fallback", self.name)
            parsed = self._regex_extract(resume_text)
        else:
            parsed = self._validate_and_fill(parsed, resume_text)

        logger.info("[%s] Parsing complete → candidate: %s", self.name, parsed.get("name"))
        return parsed

    # ------------------------------------------------------------------
    # LLM-based extraction
    # ------------------------------------------------------------------

    async def _llm_parse(self, resume_text: str) -> Optional[Dict[str, Any]]:
        """Ask Ollama to extract structured data; returns None on failure."""
        system_prompt = (
            "You are an expert resume parser. Extract ALL information from the resume "
            "and return ONLY valid JSON with exactly these keys:\n"
            "  name (string), email (string), phone (string), linkedin (string),\n"
            "  github (string), summary (string),\n"
            "  education (list of objects: degree, institution, year, gpa),\n"
            "  skills (list of strings),\n"
            "  certifications (list of strings),\n"
            "  projects (list of objects: name, description, technologies),\n"
            "  work_experience (list of objects: title, company, location, years, "
            "description, achievements)\n"
            "Return ONLY the JSON object — no markdown, no explanation, no extra text."
        )
        prompt = f"Parse this resume:\n\n{resume_text[:4000]}"

        try:
            response: str = await self.ollama.generate(prompt, system_prompt)
            # Strip possible markdown fences
            cleaned = re.sub(r"```(?:json)?\n?|```", "", response).strip()
            # Isolate first JSON object
            first_brace = cleaned.find("{")
            last_brace = cleaned.rfind("}")
            if first_brace == -1 or last_brace == -1:
                raise ValueError("No JSON object found in LLM response")
            json_str = cleaned[first_brace : last_brace + 1]
            return json.loads(json_str)
        except Exception as exc:
            logger.debug("[%s] LLM parse error: %s", self.name, exc)
            return None

    # ------------------------------------------------------------------
    # Validation & field filling
    # ------------------------------------------------------------------

    def _validate_and_fill(self, parsed: Dict[str, Any], text: str) -> Dict[str, Any]:
        """Ensure every required field is present and typed correctly."""
        # Scalar fields
        parsed.setdefault("name", "") or parsed.update({"name": self._extract_name(text)})
        parsed.setdefault("email", "") or parsed.update({"email": self._extract_email(text)})
        parsed.setdefault("phone", "") or parsed.update({"phone": self._extract_phone(text)})
        parsed.setdefault("linkedin", self._extract_linkedin(text))
        parsed.setdefault("github", self._extract_github(text))
        parsed.setdefault("summary", "")

        # Override with regex if LLM left blanks
        if not parsed["name"]:
            parsed["name"] = self._extract_name(text)
        if not parsed["email"]:
            parsed["email"] = self._extract_email(text)
        if not parsed["phone"]:
            parsed["phone"] = self._extract_phone(text)

        # List fields — ensure correct types
        for key in ("skills", "certifications"):
            if not isinstance(parsed.get(key), list):
                parsed[key] = []
        for key in ("education", "work_experience", "projects"):
            if not isinstance(parsed.get(key), list):
                parsed[key] = []

        # If skills list is empty, fall back to regex skill scan
        if not parsed["skills"]:
            parsed["skills"] = self._extract_skills(text)

        return parsed

    # ------------------------------------------------------------------
    # Regex / heuristic fallback
    # ------------------------------------------------------------------

    def _regex_extract(self, text: str) -> Dict[str, Any]:
        return {
            "name": self._extract_name(text),
            "email": self._extract_email(text),
            "phone": self._extract_phone(text),
            "linkedin": self._extract_linkedin(text),
            "github": self._extract_github(text),
            "summary": self._extract_summary(text),
            "education": self._extract_education(text),
            "skills": self._extract_skills(text),
            "certifications": self._extract_certifications(text),
            "projects": self._extract_projects(text),
            "work_experience": self._extract_experience(text),
        }

    # ------------------------------------------------------------------
    # Field-level extractors
    # ------------------------------------------------------------------

    def _extract_email(self, text: str) -> str:
        match = re.search(r"[\w.+\-]+@[\w\-]+\.[a-zA-Z]{2,}", text)
        return match.group().lower() if match else ""

    def _extract_phone(self, text: str) -> str:
        match = re.search(
            r"(\+?\d{1,3}[\s\-.]?)?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}", text
        )
        return match.group().strip() if match else ""

    def _extract_linkedin(self, text: str) -> str:
        match = re.search(r"linkedin\.com/in/[\w\-]+", text, re.IGNORECASE)
        return f"https://{match.group()}" if match else ""

    def _extract_github(self, text: str) -> str:
        match = re.search(r"github\.com/[\w\-]+", text, re.IGNORECASE)
        return f"https://{match.group()}" if match else ""

    def _extract_name(self, text: str) -> str:
        """
        Heuristic: the candidate name is almost always in the first few
        non-empty, non-contact lines of the resume.
        """
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        for line in lines[:5]:
            # Skip lines that look like contact info or section headers
            if re.search(r"[@+\d/\\|]", line):
                continue
            if re.match(
                r"^(resume|curriculum|vitae|profile|summary|objective|skills)$",
                line,
                re.IGNORECASE,
            ):
                continue
            words = line.split()
            if 2 <= len(words) <= 5 and all(w[0].isupper() for w in words if w):
                return line
        return lines[0] if lines else "Unknown Candidate"

    def _extract_summary(self, text: str) -> str:
        """Extract the professional summary / objective section."""
        pattern = re.compile(
            r"(?:summary|objective|profile|about me)[:\s]*(.+?)(?=\n[A-Z]{2,}|\n\n)",
            re.IGNORECASE | re.DOTALL,
        )
        match = pattern.search(text)
        if match:
            summary = " ".join(match.group(1).split())
            return summary[:600]
        return ""

    def _extract_education(self, text: str) -> List[Dict[str, str]]:
        edu_keywords = [
            "university", "college", "institute", "school", "academy",
            "b.s", "b.sc", "b.e", "b.tech", "m.s", "m.sc", "m.e", "m.tech",
            "master", "mba", "ph.d", "phd", "bachelor", "associate", "diploma",
        ]
        degree_patterns = re.compile(
            r"\b(bachelor|master|phd|ph\.d|mba|b\.s|b\.sc|b\.e|b\.tech|"
            r"m\.s|m\.sc|m\.tech|associate|diploma)\b",
            re.IGNORECASE,
        )
        lines = text.split("\n")
        education: List[Dict[str, str]] = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if any(kw in line.lower() for kw in edu_keywords) and len(line) > 5:
                entry: Dict[str, str] = {"degree": "", "institution": line, "year": "", "gpa": ""}
                # Check degree pattern
                if degree_patterns.search(line):
                    entry["degree"] = line
                    if i + 1 < len(lines) and lines[i + 1].strip():
                        entry["institution"] = lines[i + 1].strip()
                # Year
                year_match = re.search(r"\b(19|20)\d{2}\b", line)
                if year_match:
                    entry["year"] = year_match.group()
                # GPA
                gpa_match = re.search(r"(?:gpa|cgpa)[:\s]*([\d.]+)", line, re.IGNORECASE)
                if gpa_match:
                    entry["gpa"] = gpa_match.group(1)
                education.append(entry)
            i += 1
        return education[:6]

    def _extract_skills(self, text: str) -> List[str]:
        """Scan text for known skills (case-insensitive whole-word match)."""
        text_lower = text.lower()
        found: List[str] = []
        for skill in self.KNOWN_SKILLS:
            # Use word boundary to avoid partial matches
            pattern = re.compile(r"\b" + re.escape(skill.lower()) + r"\b")
            if pattern.search(text_lower):
                found.append(skill)
        return found

    def _extract_certifications(self, text: str) -> List[str]:
        cert_patterns = [
            r"AWS Certified[\w\s]+",
            r"Google Cloud[\w\s]+(?:Professional|Associate|Engineer)",
            r"Microsoft Certified[\w\s]+",
            r"Certified[\w\s]+(?:Professional|Engineer|Developer|Administrator|Architect)",
            r"\bPMP\b", r"\bCISSP\b", r"\bCEH\b", r"\bCPA\b", r"\bCFA\b",
            r"\bCKAD\b", r"\bCKA\b", r"\bCCNA\b", r"\bCCNP\b",
            r"Oracle Certified[\w\s]+",
            r"Salesforce Certified[\w\s]+",
            r"\b[A-Z]{3,6}\s+Certified\b",
        ]
        certs: List[str] = []
        for pattern in cert_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            certs.extend(m.strip() for m in matches)
        # Deduplicate preserving order
        seen: set = set()
        unique: List[str] = []
        for c in certs:
            key = c.lower()
            if key not in seen:
                seen.add(key)
                unique.append(c)
        return unique[:15]

    def _extract_projects(self, text: str) -> List[Dict[str, str]]:
        """Extract the projects section."""
        # Find projects block
        block_match = re.search(
            r"(?:projects?|personal projects?|side projects?)[:\s]*(.+?)"
            r"(?=\n(?:experience|education|skills|certif|volunteer|awards?|$))",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not block_match:
            return []

        block = block_match.group(1)
        lines = [ln.strip() for ln in block.split("\n") if ln.strip() and len(ln.strip()) > 5]
        projects: List[Dict[str, str]] = []
        i = 0
        while i < len(lines) and len(projects) < 8:
            name = lines[i]
            desc = lines[i + 1] if i + 1 < len(lines) else ""
            # Try to extract tech stack from description
            tech_match = re.search(
                r"(?:built with|technologies?[:\s]+|stack[:\s]+|using[:\s]+)([\w,\s.+#]+)",
                desc,
                re.IGNORECASE,
            )
            technologies = tech_match.group(1).strip() if tech_match else ""
            projects.append({"name": name, "description": desc, "technologies": technologies})
            i += 2
        return projects

    def _extract_experience(self, text: str) -> List[Dict[str, str]]:
        """Extract work experience entries."""
        # Find experience block
        block_match = re.search(
            r"(?:work\s+)?(?:professional\s+)?experience[:\s]*(.+?)"
            r"(?=\n(?:education|skills|projects?|certif|volunteer|awards?|$))",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not block_match:
            return []

        block = block_match.group(1)
        # Split on likely new-job boundary: line starting with capital word(s) without indentation
        entries = re.split(r"\n(?=[A-Z][a-z])", block)
        experience: List[Dict[str, str]] = []

        for entry in entries[:8]:
            entry = entry.strip()
            if len(entry) < 20:
                continue
            lines = [ln.strip() for ln in entry.split("\n") if ln.strip()]
            if not lines:
                continue

            # Year range
            year_match = re.search(
                r"(\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|"
                r"jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|"
                r"nov(?:ember)?|dec(?:ember)?)?\s*\d{4}\s*[-–—]\s*"
                r"(?:\d{4}|present|current|till date))",
                entry,
                re.IGNORECASE,
            )
            years = year_match.group(0).strip() if year_match else ""

            # Location
            loc_match = re.search(
                r"\b([A-Z][a-z]+(?:,\s*[A-Z]{2,})?)\b\s*(?:\||-|,|\n)", entry
            )
            location = loc_match.group(1) if loc_match else ""

            experience.append(
                {
                    "title": lines[0],
                    "company": lines[1] if len(lines) > 1 else "",
                    "location": location,
                    "years": years,
                    "description": " ".join(lines[2:4]) if len(lines) > 2 else "",
                    "achievements": [
                        ln.lstrip("•·-–* ") for ln in lines[2:]
                        if ln.lstrip("•·-–* ")
                    ][:5],
                }
            )
        return experience


# ---------------------------------------------------------------------------
# Singleton helper
# ---------------------------------------------------------------------------

_parser_agent: Optional[ResumeParserAgent] = None


def get_parser_agent(ollama_client: Any) -> ResumeParserAgent:
    """Return the module-level singleton, creating it on first call."""
    global _parser_agent
    if _parser_agent is None:
        _parser_agent = ResumeParserAgent(ollama_client)
    return _parser_agent
