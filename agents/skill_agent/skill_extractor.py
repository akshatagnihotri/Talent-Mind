"""
TalentMind AI — Skill Extractor & Normaliser Agent
====================================================
Responsibilities:
    • Normalise raw skill strings (e.g. "PowerBI" → "Power BI")
    • Classify skills as Technical or Soft
    • Group skills by domain (Frontend, Backend, Data, Cloud, …)
    • Detect missing skills when a Job Description is supplied

Author: TalentMind AI
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class SkillAnalysis:
    """Structured output returned by the agent."""
    raw_skills: List[str]
    normalised_skills: List[str]
    technical_skills: List[str]
    soft_skills: List[str]
    groups: Dict[str, List[str]]
    missing_skills: List[str]
    matched_skills: List[str]
    skill_coverage_pct: float
    total_skills_found: int
    total_jd_skills: int


# ---------------------------------------------------------------------------
# Skill Agent
# ---------------------------------------------------------------------------

class SkillExtractorAgent:
    """
    Normalises, classifies, and groups skills extracted from a resume.

    Parameters
    ----------
    ollama_client : Any, optional
        If provided, used for ambiguous skill classification (fallback
        to rule-based when absent or failing).
    """

    name = "Skill Extractor Agent"

    # ------------------------------------------------------------------
    # Normalisation map — common misspellings / alternate forms
    # ------------------------------------------------------------------
    NORMALISATION_MAP: Dict[str, str] = {
        # BI & Visualisation
        "powerbi": "Power BI",
        "power-bi": "Power BI",
        "power bi": "Power BI",
        "ms power bi": "Power BI",
        "tableau desktop": "Tableau",
        "tableau server": "Tableau",
        "looker studio": "Looker",
        "google data studio": "Looker",
        # Cloud
        "amazon web services": "AWS",
        "amazon aws": "AWS",
        "google cloud platform": "GCP",
        "google cloud": "GCP",
        "gcp": "GCP",
        "microsoft azure": "Azure",
        "ms azure": "Azure",
        # Databases
        "postgresql": "PostgreSQL",
        "postgres": "PostgreSQL",
        "mysql db": "MySQL",
        "microsoft sql server": "MSSQL",
        "ms sql": "MSSQL",
        "mongo": "MongoDB",
        "mongo db": "MongoDB",
        "elastic search": "Elasticsearch",
        "elastic": "Elasticsearch",
        "dynamo db": "DynamoDB",
        "amazon dynamodb": "DynamoDB",
        # Languages
        "py": "Python",
        "golang": "Go",
        "node": "Node.js",
        "nodejs": "Node.js",
        "node js": "Node.js",
        "react js": "React",
        "reactjs": "React",
        "react.js": "React",
        "vue js": "Vue",
        "vuejs": "Vue",
        "angular js": "Angular",
        "angularjs": "Angular",
        "next js": "Next.js",
        "nextjs": "Next.js",
        "ts": "TypeScript",
        "js": "JavaScript",
        "javascript es6": "JavaScript",
        # ML / AI
        "ml": "Machine Learning",
        "ai": "Artificial Intelligence",
        "dl": "Deep Learning",
        "natural language processing": "NLP",
        "computer vision": "Computer Vision",
        "cv": "Computer Vision",
        "scikit learn": "Scikit-learn",
        "sklearn": "Scikit-learn",
        "sci-kit learn": "Scikit-learn",
        "tensorflow 2": "TensorFlow",
        "tf": "TensorFlow",
        "pytorch": "PyTorch",
        "torch": "PyTorch",
        # DevOps
        "k8s": "Kubernetes",
        "kube": "Kubernetes",
        "docker containers": "Docker",
        "containerization": "Docker",
        "tf cloud": "Terraform",
        "iac": "Terraform",
        "github actions": "GitHub Actions",
        "gitlab ci/cd": "GitLab CI",
        "cicd": "CI/CD",
        "ci-cd": "CI/CD",
        # Methodology
        "agile scrum": "Agile/Scrum",
        "scrum master": "Scrum",
        "product backlog": "Scrum",
        "tdd": "Test-Driven Development",
        "bdd": "Behaviour-Driven Development",
        "restful api": "REST API",
        "rest apis": "REST API",
        "restful": "REST API",
        "micro services": "Microservices",
        "micro-services": "Microservices",
    }

    # ------------------------------------------------------------------
    # Technical skill taxonomy
    # ------------------------------------------------------------------
    SKILL_GROUPS: Dict[str, Set[str]] = {
        "Frontend": {
            "React", "Vue", "Angular", "Next.js", "Nuxt.js", "Svelte",
            "HTML", "CSS", "SASS", "SCSS", "Tailwind", "Bootstrap",
            "Material UI", "Redux", "Zustand", "TypeScript", "JavaScript",
            "jQuery", "WebSockets", "PWA",
        },
        "Backend": {
            "Python", "Java", "Go", "Rust", "C++", "C#", "Ruby", "PHP",
            "Node.js", "Express", "FastAPI", "Django", "Flask",
            "Spring Boot", "ASP.NET", "Laravel", "Rails", "Gin", "Fiber",
            "REST API", "GraphQL", "gRPC", "Microservices",
            "Event-Driven", "Message Queue", "RabbitMQ", "Kafka",
        },
        "Database": {
            "SQL", "PostgreSQL", "MySQL", "SQLite", "Oracle", "MSSQL",
            "MongoDB", "Cassandra", "DynamoDB", "Firestore", "Redis",
            "Elasticsearch", "CouchDB", "InfluxDB", "Neo4j",
            "Database Design", "ORM", "Data Modelling",
        },
        "Cloud & DevOps": {
            "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform",
            "Ansible", "Jenkins", "GitHub Actions", "GitLab CI",
            "CircleCI", "Helm", "Prometheus", "Grafana", "Nginx",
            "Apache", "Linux", "CI/CD", "DevOps", "SRE",
            "Serverless", "Lambda", "Cloud Functions",
        },
        "Data & Analytics": {
            "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
            "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "XGBoost",
            "LightGBM", "Pandas", "NumPy", "SciPy", "Matplotlib",
            "Seaborn", "Plotly", "Spark", "Hadoop", "Airflow", "dbt",
            "Snowflake", "Power BI", "Tableau", "Looker", "Excel",
            "Artificial Intelligence", "Data Science", "Data Engineering",
            "ETL", "Data Warehouse", "Data Pipeline",
        },
        "Mobile": {
            "iOS", "Android", "Swift", "Kotlin", "React Native",
            "Flutter", "Dart", "Objective-C", "Xamarin",
        },
        "Security": {
            "Cybersecurity", "Penetration Testing", "CISSP", "CEH",
            "OWASP", "OAuth", "JWT", "SSL/TLS", "Zero Trust",
            "IAM", "SIEM", "SOC",
        },
        "Testing & QA": {
            "Selenium", "Cypress", "Jest", "Pytest", "JUnit",
            "Test-Driven Development", "Behaviour-Driven Development",
            "Postman", "SoapUI", "Load Testing", "JMeter", "QA",
        },
        "Methodology": {
            "Agile", "Scrum", "Kanban", "JIRA", "Confluence",
            "Agile/Scrum", "Design Patterns", "System Design",
            "Domain-Driven Design", "Git", "Code Review",
        },
    }

    SOFT_SKILLS: Set[str] = {
        "Leadership", "Communication", "Teamwork", "Collaboration",
        "Problem Solving", "Critical Thinking", "Creativity",
        "Time Management", "Adaptability", "Attention to Detail",
        "Project Management", "Mentoring", "Coaching",
        "Conflict Resolution", "Negotiation", "Presentation",
        "Analytical Thinking", "Decision Making", "Self-motivated",
        "Customer Focus", "Stakeholder Management", "Strategic Planning",
        "Cross-functional Collaboration", "Work Ethic",
    }

    def __init__(self, ollama_client=None) -> None:
        self.ollama = ollama_client
        # Build a reverse lookup: canonical skill → group
        self._skill_to_group: Dict[str, str] = {}
        for group, skills in self.SKILL_GROUPS.items():
            for skill in skills:
                self._skill_to_group[skill.lower()] = group

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyse(
        self,
        raw_skills: List[str],
        jd_skills: Optional[List[str]] = None,
    ) -> SkillAnalysis:
        """
        Main entry point.

        Parameters
        ----------
        raw_skills : list[str]
            Skills as extracted by the parser (may be messy).
        jd_skills : list[str], optional
            Skill requirements from the Job Description.

        Returns
        -------
        SkillAnalysis
        """
        logger.info("[%s] Analysing %d raw skills", self.name, len(raw_skills))

        normalised = self._normalise_all(raw_skills)
        technical, soft = self._classify(normalised)
        groups = self._group(technical)
        jd_normalised = self._normalise_all(jd_skills or [])
        missing, matched = self._gap_analysis(normalised, jd_normalised)
        coverage = (
            round(len(matched) / len(jd_normalised) * 100, 1)
            if jd_normalised
            else 100.0
        )

        return SkillAnalysis(
            raw_skills=raw_skills,
            normalised_skills=normalised,
            technical_skills=technical,
            soft_skills=soft,
            groups=groups,
            missing_skills=missing,
            matched_skills=matched,
            skill_coverage_pct=coverage,
            total_skills_found=len(normalised),
            total_jd_skills=len(jd_normalised),
        )

    # ------------------------------------------------------------------
    # Normalisation
    # ------------------------------------------------------------------

    def _normalise(self, skill: str) -> str:
        """Return the canonical form of a single skill string."""
        cleaned = skill.strip()
        key = cleaned.lower()
        if key in self.NORMALISATION_MAP:
            return self.NORMALISATION_MAP[key]
        # Title-case if all lowercase / all uppercase
        if cleaned == cleaned.lower() or cleaned == cleaned.upper():
            cleaned = cleaned.title()
        return cleaned

    def _normalise_all(self, skills: List[str]) -> List[str]:
        """Deduplicated, normalised skill list."""
        seen: Set[str] = set()
        result: List[str] = []
        for s in skills:
            # Handle comma-separated strings inside a single element
            for part in re.split(r"[,;/]", s):
                norm = self._normalise(part)
                if norm and norm.lower() not in seen:
                    seen.add(norm.lower())
                    result.append(norm)
        return result

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    def _classify(self, skills: List[str]) -> tuple:
        """Split skills into (technical, soft) lists."""
        technical: List[str] = []
        soft: List[str] = []
        soft_lower = {s.lower() for s in self.SOFT_SKILLS}
        for skill in skills:
            if skill.lower() in soft_lower:
                soft.append(skill)
            else:
                technical.append(skill)
        return technical, soft

    # ------------------------------------------------------------------
    # Grouping
    # ------------------------------------------------------------------

    def _group(self, technical_skills: List[str]) -> Dict[str, List[str]]:
        """Map each technical skill to its domain group."""
        groups: Dict[str, List[str]] = {g: [] for g in self.SKILL_GROUPS}
        groups["Other"] = []
        for skill in technical_skills:
            group = self._skill_to_group.get(skill.lower())
            if group:
                groups[group].append(skill)
            else:
                groups["Other"].append(skill)
        # Remove empty groups
        return {g: skills for g, skills in groups.items() if skills}

    # ------------------------------------------------------------------
    # Gap analysis
    # ------------------------------------------------------------------

    def _gap_analysis(
        self,
        candidate_skills: List[str],
        jd_skills: List[str],
    ) -> tuple:
        """Return (missing_skills, matched_skills)."""
        candidate_lower = {s.lower() for s in candidate_skills}
        missing: List[str] = []
        matched: List[str] = []
        for skill in jd_skills:
            if skill.lower() in candidate_lower:
                matched.append(skill)
            else:
                missing.append(skill)
        return missing, matched


# ---------------------------------------------------------------------------
# Singleton helper
# ---------------------------------------------------------------------------

_skill_agent: Optional[SkillExtractorAgent] = None


def get_skill_agent(ollama_client=None) -> SkillExtractorAgent:
    global _skill_agent
    if _skill_agent is None:
        _skill_agent = SkillExtractorAgent(ollama_client)
    return _skill_agent
