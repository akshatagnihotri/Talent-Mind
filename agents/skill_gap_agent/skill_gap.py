"""
TalentMind AI — Skill Gap Agent
=================================
Identifies the delta between a candidate's current skill set and the
requirements of the target Job Description, then maps each gap to a
concrete, actionable learning path.

Output structure:
    • Categorised gap lists (Technical, Soft Skills, Certifications)
    • Priority classification (Critical / Important / Nice-to-Have)
    • Recommended courses / resources per skill
    • Estimated learning time per gap
    • Overall readiness score

Author: TalentMind AI
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class LearningResource:
    skill: str
    priority: str               # Critical / Important / Nice-to-Have
    category: str               # Technical / Soft Skill / Certification
    courses: List[Dict[str, str]]   # [{name, platform, url, level, duration}]
    estimated_weeks: int
    description: str


@dataclass
class SkillGapReport:
    candidate_name: str
    target_role: str
    total_gaps: int
    critical_gaps: List[str]
    important_gaps: List[str]
    nice_to_have_gaps: List[str]
    technical_gaps: List[str]
    soft_skill_gaps: List[str]
    certification_gaps: List[str]
    learning_paths: List[LearningResource]
    readiness_score: float          # 0–100 (100 = fully ready)
    readiness_label: str
    total_learning_weeks: int
    quick_wins: List[str]           # Skills achievable in < 2 weeks
    executive_summary: str


# ---------------------------------------------------------------------------
# Skill Gap Agent
# ---------------------------------------------------------------------------

class SkillGapAgent:
    """
    Identifies skill gaps and produces structured learning paths.
    """

    name = "Skill Gap Agent"

    # ------------------------------------------------------------------
    # Course catalogue — curated resource map per skill
    # ------------------------------------------------------------------
    COURSE_CATALOGUE: Dict[str, List[Dict[str, str]]] = {
        # ---------- Languages ----------
        "Python": [
            {"name": "Python for Everybody", "platform": "Coursera", "url": "https://coursera.org/specializations/python", "level": "Beginner", "duration": "4 weeks"},
            {"name": "Complete Python Bootcamp", "platform": "Udemy", "url": "https://udemy.com/course/complete-python-bootcamp", "level": "Beginner-Intermediate", "duration": "5 weeks"},
        ],
        "JavaScript": [
            {"name": "JavaScript Algorithms and Data Structures", "platform": "freeCodeCamp", "url": "https://freecodecamp.org", "level": "Beginner", "duration": "3 weeks"},
            {"name": "The Complete JavaScript Course", "platform": "Udemy", "url": "https://udemy.com/course/the-complete-javascript-course", "level": "Beginner-Advanced", "duration": "6 weeks"},
        ],
        "TypeScript": [
            {"name": "Understanding TypeScript", "platform": "Udemy", "url": "https://udemy.com/course/understanding-typescript", "level": "Intermediate", "duration": "3 weeks"},
            {"name": "TypeScript Handbook", "platform": "Official Docs", "url": "https://typescriptlang.org/docs", "level": "All Levels", "duration": "1 week"},
        ],
        "Go": [
            {"name": "Go: The Complete Developer's Guide", "platform": "Udemy", "url": "https://udemy.com/course/go-the-complete-developers-guide", "level": "Beginner", "duration": "4 weeks"},
            {"name": "Tour of Go", "platform": "Official Docs", "url": "https://tour.golang.org", "level": "Beginner", "duration": "1 week"},
        ],
        "Rust": [
            {"name": "The Rust Programming Language", "platform": "Official Docs", "url": "https://doc.rust-lang.org/book", "level": "Beginner", "duration": "5 weeks"},
        ],
        "Java": [
            {"name": "Java Programming Masterclass", "platform": "Udemy", "url": "https://udemy.com/course/java-the-complete-java-developer-course", "level": "Beginner", "duration": "6 weeks"},
        ],
        # ---------- Frontend ----------
        "React": [
            {"name": "React - The Complete Guide", "platform": "Udemy", "url": "https://udemy.com/course/react-the-complete-guide-incl-redux", "level": "Beginner-Advanced", "duration": "5 weeks"},
            {"name": "React Docs (Beta)", "platform": "Official Docs", "url": "https://react.dev", "level": "All Levels", "duration": "1 week"},
        ],
        "Vue": [
            {"name": "Vue - The Complete Guide", "platform": "Udemy", "url": "https://udemy.com/course/vuejs-2-the-complete-guide", "level": "Beginner", "duration": "4 weeks"},
        ],
        "Angular": [
            {"name": "Angular - The Complete Guide", "platform": "Udemy", "url": "https://udemy.com/course/the-complete-guide-to-angular-2", "level": "Beginner", "duration": "5 weeks"},
        ],
        "Next.js": [
            {"name": "Next.js & React - The Complete Guide", "platform": "Udemy", "url": "https://udemy.com/course/nextjs-react-the-complete-guide", "level": "Intermediate", "duration": "4 weeks"},
        ],
        # ---------- Backend ----------
        "FastAPI": [
            {"name": "FastAPI - The Complete Course", "platform": "Udemy", "url": "https://udemy.com/course/fastapi-the-complete-course", "level": "Intermediate", "duration": "2 weeks"},
            {"name": "FastAPI Official Tutorial", "platform": "Official Docs", "url": "https://fastapi.tiangolo.com/tutorial", "level": "Intermediate", "duration": "1 week"},
        ],
        "Django": [
            {"name": "Django for Beginners", "platform": "Udemy", "url": "https://udemy.com/course/python-and-django-full-stack-web-developer-bootcamp", "level": "Beginner", "duration": "4 weeks"},
        ],
        "Node.js": [
            {"name": "The Complete Node.js Developer Course", "platform": "Udemy", "url": "https://udemy.com/course/the-complete-nodejs-developer-course-2", "level": "Beginner", "duration": "4 weeks"},
        ],
        "Spring Boot": [
            {"name": "Spring & Hibernate for Beginners", "platform": "Udemy", "url": "https://udemy.com/course/spring-hibernate-tutorial", "level": "Intermediate", "duration": "5 weeks"},
        ],
        # ---------- Databases ----------
        "PostgreSQL": [
            {"name": "The Complete SQL Bootcamp", "platform": "Udemy", "url": "https://udemy.com/course/the-complete-sql-bootcamp", "level": "Beginner", "duration": "3 weeks"},
        ],
        "MongoDB": [
            {"name": "MongoDB - The Complete Developer's Guide", "platform": "Udemy", "url": "https://udemy.com/course/mongodb-the-complete-developers-guide", "level": "Beginner", "duration": "3 weeks"},
        ],
        "Redis": [
            {"name": "Redis Bootcamp for Beginners", "platform": "Udemy", "url": "https://udemy.com/course/redis-bootcamp-for-beginners", "level": "Beginner", "duration": "2 weeks"},
        ],
        "Elasticsearch": [
            {"name": "Elasticsearch 8 and ELK Stack", "platform": "Udemy", "url": "https://udemy.com/course/elasticsearch-complete-guide", "level": "Intermediate", "duration": "3 weeks"},
        ],
        # ---------- Cloud & DevOps ----------
        "AWS": [
            {"name": "AWS Certified Developer - Associate", "platform": "Udemy", "url": "https://udemy.com/course/aws-certified-developer-associate-dva-c01", "level": "Intermediate", "duration": "6 weeks"},
            {"name": "AWS Free Tier + Hands-on Labs", "platform": "AWS", "url": "https://aws.amazon.com/free", "level": "Beginner", "duration": "2 weeks"},
        ],
        "Azure": [
            {"name": "Microsoft Azure Fundamentals AZ-900", "platform": "Microsoft Learn", "url": "https://learn.microsoft.com/en-us/certifications/azure-fundamentals", "level": "Beginner", "duration": "4 weeks"},
        ],
        "GCP": [
            {"name": "Google Cloud Associate Cloud Engineer", "platform": "Google Cloud Skills", "url": "https://cloud.google.com/learn/training", "level": "Intermediate", "duration": "6 weeks"},
        ],
        "Docker": [
            {"name": "Docker & Kubernetes: The Practical Guide", "platform": "Udemy", "url": "https://udemy.com/course/docker-kubernetes-the-practical-guide", "level": "Beginner", "duration": "4 weeks"},
            {"name": "Play with Docker", "platform": "Docker Labs", "url": "https://labs.play-with-docker.com", "level": "Beginner", "duration": "1 week"},
        ],
        "Kubernetes": [
            {"name": "Certified Kubernetes Administrator (CKA)", "platform": "Udemy", "url": "https://udemy.com/course/certified-kubernetes-administrator-with-practice-tests", "level": "Advanced", "duration": "6 weeks"},
        ],
        "Terraform": [
            {"name": "HashiCorp Certified: Terraform Associate", "platform": "Udemy", "url": "https://udemy.com/course/terraform-beginner-to-advanced", "level": "Intermediate", "duration": "4 weeks"},
        ],
        "CI/CD": [
            {"name": "GitHub Actions - The Complete Guide", "platform": "Udemy", "url": "https://udemy.com/course/github-actions-the-complete-guide", "level": "Beginner", "duration": "2 weeks"},
        ],
        # ---------- Data & ML ----------
        "Machine Learning": [
            {"name": "Machine Learning Specialization", "platform": "Coursera (Andrew Ng)", "url": "https://coursera.org/specializations/machine-learning-introduction", "level": "Beginner-Intermediate", "duration": "8 weeks"},
        ],
        "Deep Learning": [
            {"name": "Deep Learning Specialization", "platform": "Coursera (Andrew Ng)", "url": "https://coursera.org/specializations/deep-learning", "level": "Intermediate", "duration": "12 weeks"},
        ],
        "TensorFlow": [
            {"name": "TensorFlow Developer Certificate", "platform": "Coursera", "url": "https://coursera.org/professional-certificates/tensorflow-in-practice", "level": "Intermediate", "duration": "4 weeks"},
        ],
        "PyTorch": [
            {"name": "PyTorch for Deep Learning", "platform": "Udemy", "url": "https://udemy.com/course/pytorch-for-deep-learning-with-python-bootcamp", "level": "Intermediate", "duration": "4 weeks"},
        ],
        "Scikit-learn": [
            {"name": "Scikit-Learn Official Tutorials", "platform": "Official Docs", "url": "https://scikit-learn.org/stable/tutorial", "level": "Intermediate", "duration": "2 weeks"},
        ],
        "Spark": [
            {"name": "Taming Big Data with Apache Spark", "platform": "Udemy", "url": "https://udemy.com/course/taming-big-data-with-apache-spark-hands-on", "level": "Intermediate", "duration": "4 weeks"},
        ],
        "Kafka": [
            {"name": "Apache Kafka Series - Learn Apache Kafka", "platform": "Udemy", "url": "https://udemy.com/course/apache-kafka", "level": "Intermediate", "duration": "4 weeks"},
        ],
        "Power BI": [
            {"name": "Microsoft Power BI - A Complete Introduction", "platform": "Udemy", "url": "https://udemy.com/course/powerbi-complete-introduction", "level": "Beginner", "duration": "2 weeks"},
            {"name": "PL-300: Microsoft Power BI Data Analyst", "platform": "Microsoft Learn", "url": "https://learn.microsoft.com/en-us/certifications/power-bi-data-analyst-associate", "level": "Intermediate", "duration": "4 weeks"},
        ],
        "Tableau": [
            {"name": "Tableau 2022 A-Z", "platform": "Udemy", "url": "https://udemy.com/course/tableau10", "level": "Beginner", "duration": "3 weeks"},
        ],
        # ---------- Soft Skills ----------
        "Leadership": [
            {"name": "Inspiring and Motivating Individuals", "platform": "Coursera (Michigan)", "url": "https://coursera.org/learn/motivate-people-teams", "level": "Intermediate", "duration": "3 weeks"},
        ],
        "Communication": [
            {"name": "Communication Skills for Engineers", "platform": "Coursera", "url": "https://coursera.org/learn/silicon-valley-product-management", "level": "Beginner", "duration": "2 weeks"},
        ],
        "Project Management": [
            {"name": "Google Project Management Certificate", "platform": "Coursera", "url": "https://coursera.org/professional-certificates/google-project-management", "level": "Beginner", "duration": "6 weeks"},
        ],
        "Agile": [
            {"name": "Agile with Atlassian JIRA", "platform": "Coursera", "url": "https://coursera.org/learn/agile-atlassian-jira", "level": "Beginner", "duration": "2 weeks"},
        ],
        "Scrum": [
            {"name": "Scrum Fundamentals Certified (SFC)", "platform": "SCRUMstudy", "url": "https://scrumstudy.com/certification/scrum-fundamentals-certified", "level": "Beginner", "duration": "1 week"},
        ],
    }

    CRITICAL_SKILLS = {
        "Python", "Java", "JavaScript", "TypeScript", "SQL",
        "React", "Node.js", "Docker", "AWS", "Machine Learning",
        "PostgreSQL", "FastAPI", "Django",
    }

    CERTIFICATION_SKILLS = {
        "AWS Certified", "Azure", "GCP", "Kubernetes", "PMP",
        "CISSP", "Terraform", "Power BI", "Scrum", "CKA",
    }

    SOFT_SKILLS = {
        "Leadership", "Communication", "Teamwork", "Project Management",
        "Agile", "Scrum", "Problem Solving", "Time Management", "Mentoring",
    }

    QUICK_WIN_SKILLS = {
        "Git", "REST API", "Agile", "Scrum", "Linux", "Postman",
        "GitHub Actions", "TypeScript", "Redis", "Tailwind",
    }

    def __init__(self, ollama_client=None) -> None:
        self.ollama = ollama_client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyse(
        self,
        parsed_resume: Dict[str, Any],
        missing_skills: List[str],
        job_description: str = "",
        target_role: str = "Target Role",
    ) -> SkillGapReport:
        """
        Analyse the skill gap and build learning paths.

        Parameters
        ----------
        parsed_resume : dict
        missing_skills : list[str]
            Skills the candidate lacks (from JobMatchAgent or SkillAgent).
        job_description : str
        target_role : str
        """
        candidate_name = parsed_resume.get("name", "Candidate")
        logger.info("[%s] Analysing skill gaps for: %s", self.name, candidate_name)

        # Categorise gaps
        technical, soft, certs = self._categorise_gaps(missing_skills)

        # Prioritise
        critical = [s for s in missing_skills if s in self.CRITICAL_SKILLS or s in technical[:3]]
        important = [s for s in technical if s not in critical][:6]
        nice_to_have = [s for s in soft + certs if s not in critical][:5]

        # Build learning paths
        learning_paths = self._build_learning_paths(missing_skills)

        # Quick wins
        quick_wins = [s for s in missing_skills if s in self.QUICK_WIN_SKILLS]

        # Readiness score
        readiness_score = self._calculate_readiness(
            parsed_resume.get("skills", []), missing_skills
        )
        readiness_label = self._readiness_label(readiness_score)

        # Total learning time
        total_weeks = sum(lp.estimated_weeks for lp in learning_paths)

        # Summary
        summary = self._build_summary(
            candidate_name, target_role, missing_skills, critical, readiness_score, total_weeks
        )

        report = SkillGapReport(
            candidate_name=candidate_name,
            target_role=target_role,
            total_gaps=len(missing_skills),
            critical_gaps=critical[:8],
            important_gaps=important[:8],
            nice_to_have_gaps=nice_to_have[:5],
            technical_gaps=technical,
            soft_skill_gaps=soft,
            certification_gaps=certs,
            learning_paths=learning_paths,
            readiness_score=round(readiness_score, 1),
            readiness_label=readiness_label,
            total_learning_weeks=total_weeks,
            quick_wins=quick_wins,
            executive_summary=summary,
        )
        logger.info(
            "[%s] Gap analysis complete — %d gaps, readiness: %.1f%%",
            self.name, len(missing_skills), readiness_score
        )
        return report

    # ------------------------------------------------------------------
    # Categorisation
    # ------------------------------------------------------------------

    def _categorise_gaps(
        self, missing_skills: List[str]
    ) -> tuple:
        technical: List[str] = []
        soft: List[str] = []
        certs: List[str] = []
        for skill in missing_skills:
            if any(cs.lower() in skill.lower() for cs in self.CERTIFICATION_SKILLS):
                certs.append(skill)
            elif skill in self.SOFT_SKILLS:
                soft.append(skill)
            else:
                technical.append(skill)
        return technical, soft, certs

    # ------------------------------------------------------------------
    # Learning path builder
    # ------------------------------------------------------------------

    def _build_learning_paths(
        self, missing_skills: List[str]
    ) -> List[LearningResource]:
        paths: List[LearningResource] = []
        for skill in missing_skills[:15]:  # Cap at 15 to keep report readable
            courses = self.COURSE_CATALOGUE.get(skill, self._generic_course(skill))
            priority = self._classify_priority(skill)
            category = self._classify_category(skill)
            est_weeks = self._estimate_weeks(skill, courses)

            paths.append(LearningResource(
                skill=skill,
                priority=priority,
                category=category,
                courses=courses[:2],  # Max 2 courses per skill
                estimated_weeks=est_weeks,
                description=self._skill_description(skill),
            ))
        # Sort by priority (Critical first)
        priority_order = {"Critical": 0, "Important": 1, "Nice-to-Have": 2}
        paths.sort(key=lambda p: priority_order.get(p.priority, 3))
        return paths

    def _classify_priority(self, skill: str) -> str:
        if skill in self.CRITICAL_SKILLS:
            return "Critical"
        if skill in self.SOFT_SKILLS or skill in self.CERTIFICATION_SKILLS:
            return "Important"
        return "Nice-to-Have"

    def _classify_category(self, skill: str) -> str:
        if any(cs.lower() in skill.lower() for cs in self.CERTIFICATION_SKILLS):
            return "Certification"
        if skill in self.SOFT_SKILLS:
            return "Soft Skill"
        return "Technical"

    def _estimate_weeks(self, skill: str, courses: List[Dict[str, str]]) -> int:
        for course in courses:
            duration = course.get("duration", "")
            import re
            match = re.search(r"(\d+)\s*week", duration, re.IGNORECASE)
            if match:
                return int(match.group(1))
        # Defaults by category
        if skill in self.CRITICAL_SKILLS:
            return 6
        if skill in self.SOFT_SKILLS:
            return 2
        return 3

    @staticmethod
    def _generic_course(skill: str) -> List[Dict[str, str]]:
        return [
            {
                "name": f"Complete {skill} Course",
                "platform": "Udemy / Coursera",
                "url": f"https://udemy.com/courses/search/?q={skill.replace(' ', '+')}",
                "level": "Beginner to Intermediate",
                "duration": "4 weeks",
            }
        ]

    @staticmethod
    def _skill_description(skill: str) -> str:
        descriptions = {
            "Python":      "High-level programming language widely used in data science, web dev, and automation",
            "React":       "Declarative JavaScript library for building interactive user interfaces",
            "Docker":      "Platform for containerising and deploying applications consistently across environments",
            "Kubernetes":  "Container orchestration system for automating deployment, scaling, and management",
            "AWS":         "Amazon cloud platform offering 200+ services for computing, storage, and ML",
            "Machine Learning": "Field of AI enabling systems to learn and improve from experience",
            "PostgreSQL":  "Powerful open-source relational database with advanced SQL features",
            "FastAPI":     "Modern, high-performance Python web framework for building APIs",
            "CI/CD":       "Continuous Integration & Deployment practices for automated software delivery",
            "Kafka":       "Distributed event-streaming platform for high-throughput real-time data pipelines",
        }
        return descriptions.get(skill, f"Core skill for modern {skill} development")

    # ------------------------------------------------------------------
    # Readiness scoring
    # ------------------------------------------------------------------

    def _calculate_readiness(
        self,
        candidate_skills: List[str],
        missing_skills: List[str],
    ) -> float:
        total = len(candidate_skills) + len(missing_skills)
        if total == 0:
            return 50.0
        readiness = len(candidate_skills) / total * 100
        # Penalise critical gaps more heavily
        critical_missing = [s for s in missing_skills if s in self.CRITICAL_SKILLS]
        penalty = len(critical_missing) * 5
        return max(0.0, min(100.0, readiness - penalty))

    @staticmethod
    def _readiness_label(score: float) -> str:
        if score >= 80:
            return "Job-Ready"
        if score >= 60:
            return "Mostly Ready"
        if score >= 40:
            return "Partially Ready"
        return "Needs Significant Development"

    # ------------------------------------------------------------------
    # Summary builder
    # ------------------------------------------------------------------

    def _build_summary(
        self,
        candidate_name: str,
        target_role: str,
        missing_skills: List[str],
        critical_gaps: List[str],
        readiness_score: float,
        total_weeks: int,
    ) -> str:
        summary = (
            f"{candidate_name} is currently {readiness_score:.0f}% ready for the {target_role} role. "
            f"There are {len(missing_skills)} identified skill gaps"
        )
        if critical_gaps:
            summary += f", of which {len(critical_gaps)} are critical ({', '.join(critical_gaps[:3])})"
        summary += ". "
        if total_weeks <= 8:
            summary += f"With approximately {total_weeks} weeks of focused learning, "
            summary += "the candidate could close most gaps and become a strong hire."
        elif total_weeks <= 20:
            summary += (
                f"A structured {total_weeks}-week learning plan is recommended to address all gaps. "
                "Consider hiring for a junior variant of the role in the interim."
            )
        else:
            summary += (
                "The skill gap is significant and may require 6+ months of intensive training. "
                "Recommend reassessing for a more junior position or after self-directed learning."
            )
        return summary


# ---------------------------------------------------------------------------
# Singleton helper
# ---------------------------------------------------------------------------

_skill_gap_agent: Optional[SkillGapAgent] = None


def get_skill_gap_agent(ollama_client=None) -> SkillGapAgent:
    global _skill_gap_agent
    if _skill_gap_agent is None:
        _skill_gap_agent = SkillGapAgent(ollama_client)
    return _skill_gap_agent
