"""Example usage of the Resume Parser Framework.

Demonstrates the full set of extraction capabilities on a real resume.
Run with:
    uv run python examples.py [path/to/resume.pdf]

The framework extracts 19+ fields using a strategy cascade (Regex → NER → LLM).
LLM calls require a valid GEMINI_API_KEY in .env. If the API is unavailable the
script falls back to a pre-loaded demo snapshot so every field is always shown.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# Make src/ importable when running from the project root
sys.path.insert(0, str(Path(__file__).parent / "src"))

from framework import ResumeParserFramework
from models import ResumeData
from models.work_experience import WorkExperienceEntry
from models.education import EducationEntry
from models.certification import CertificationEntry
from models.project import ProjectEntry
from models.skill_entry import SkillEntry
from models.experience_analytics import ExperienceAnalytics
from models.contact_info import ContactInfo
from config import ExtractionConfig, DEFAULT_EXTRACTION_CONFIG
from interfaces import FieldType, StrategyType

# ---------------------------------------------------------------------------
# Demo snapshot  –  derived from parsing sample_resumes/Brijesh_Patel_ATS.pdf
# Used as a fallback when the LLM API is unavailable (rate-limit / no key).
# ---------------------------------------------------------------------------
_DEMO_RESUME: ResumeData = ResumeData(
    name="BRIJESH PATEL",
    email="brijkpatel@gmail.com",
    skills=[
        "Python", "Java", "TypeScript", "C++", "C", "Swift",
        "Spring Boot", "Apache Spark", "Apache Beam", "gRPC",
        "TensorFlow", "PyTorch", "Scikit-learn", "Apache Arrow",
        "Kafka", "Docker", "Kubernetes", "Elasticsearch", "Logstash",
        "Kibana", "Datadog", "Power BI", "Tableau", "Redis",
        "AWS EC2", "AWS Step Functions", "AWS SQS", "AWS Lambda",
        "Amazon Bedrock", "Amazon Textract", "Amazon Comprehend",
        "SQL", "MongoDB", "DynamoDB", "Redshift",
    ],
    contact=ContactInfo(
        phone="(403) 910-7070",
        location="Calgary, AB",
        linkedin_url="linkedin.com/in/brijkpatel",
        github_url=None,
        portfolio_url=None,
        other_urls=[],
    ),
    summary=(
        "Data Engineer and AI Developer with 6 years of experience designing "
        "cloud-native, ML-powered, and data-driven systems. Skilled in Java/Kotlin "
        "(Spring Boot) microservices, LLM integration, and data ingestion "
        "modernization for scalable enterprise platforms. Proven track record "
        "delivering production-grade systems using Elasticsearch, embeddings, and "
        "gRPC in distributed, high-traffic environments."
    ),
    work_experience=[
        WorkExperienceEntry(
            company="Capintel",
            title="Data Engineer and AI Developer",
            location="Calgary, AB",
            start_date="May 2022",
            end_date="Present",
            duration_months=35,
            description=(
                "Enhanced data quality through AI-powered outlier detection; built "
                "scalable AI microservices; modernized ETL pipelines on AWS."
            ),
            responsibilities=[
                "Enhanced data quality by 4% through AI-powered outlier detection.",
                "Built and deployed scalable AI microservices using gRPC and Apache Beam.",
                "Developed LLM-powered microservices to extract financial instruments from PDFs.",
                "Modernized data ingestion pipelines using AWS Step Functions, SQS, Lambda — "
                "improved ETL speed by 82%.",
                "Developed and managed ETL pipelines, Elasticsearch, and databases.",
            ],
            skills_used=[
                "Python", "Java", "gRPC", "Apache Beam", "AWS Step Functions",
                "AWS SQS", "AWS Lambda", "Elasticsearch", "LLM",
            ],
        ),
        WorkExperienceEntry(
            company="Sasktel International",
            title="Java Developer",
            location=None,
            start_date="June 2019",
            end_date="Sept 2021",
            duration_months=27,
            description=(
                "Designed and developed Java Spring Boot microservices for enterprise "
                "telecom applications."
            ),
            responsibilities=[
                "Designed Java Spring Boot microservices for enterprise telecom.",
                "Reduced production issue resolution time by 30% through improved observability.",
                "Integrated APIs with external services for data synchronization.",
                "Mentored junior developers within Agile sprints.",
            ],
            skills_used=["Java", "Spring Boot", "Microservices", "REST API"],
        ),
        WorkExperienceEntry(
            company="Conexus Credit Union",
            title="Data Analyst Intern",
            location=None,
            start_date="May 2018",
            end_date="Aug 2018",
            duration_months=4,
            description="Data analytics and visualization internship.",
            responsibilities=[
                "Developed interactive dashboards in Azure, Power BI, and D3.js.",
                "Conducted sentiment analysis on deposit-growth campaign calls.",
                "Built predictive models for deposit growth potential.",
            ],
            skills_used=["Power BI", "Azure", "D3.js", "Python", "Sentiment Analysis"],
        ),
    ],
    education=[
        EducationEntry(
            institution="University of Regina",
            degree="Master's",
            field_of_study="Computer Science",
            start_date="Sept 2016",
            end_date="Dec 2018",
            gpa=None,
            honors=None,
        ),
        EducationEntry(
            institution="Gujarat Technological University",
            degree="Bachelor's",
            field_of_study="Information Technology",
            start_date="July 2011",
            end_date="Apr 2015",
            gpa=None,
            honors=None,
        ),
    ],
    certifications=[],
    projects=[],
    enriched_skills=[
        SkillEntry(name="Python", category="Programming Language",
                   estimated_years=6.0, proficiency="Expert"),
        SkillEntry(name="Java", category="Programming Language",
                   estimated_years=6.0, proficiency="Expert"),
        SkillEntry(name="Spring Boot", category="Framework",
                   estimated_years=4.5, proficiency="Advanced"),
        SkillEntry(name="Apache Beam", category="Framework",
                   estimated_years=3.0, proficiency="Advanced"),
        SkillEntry(name="Elasticsearch", category="Database",
                   estimated_years=3.0, proficiency="Advanced"),
        SkillEntry(name="AWS Lambda", category="Cloud Platform",
                   estimated_years=3.0, proficiency="Advanced"),
        SkillEntry(name="Kafka", category="Tool", estimated_years=3.0,
                   proficiency="Advanced"),
        SkillEntry(name="Docker", category="DevOps", estimated_years=3.0,
                   proficiency="Advanced"),
    ],
    interests=[],
    languages=["English"],
    awards=[],
    volunteer_experience=[],
    publications=[],
    experience_analytics=ExperienceAnalytics(
        total_years=6.0,
        years_by_role={
            "Data Engineer and AI Developer": 2.9,
            "Java Developer": 2.3,
            "Data Analyst Intern": 0.3,
        },
        years_by_company={
            "Capintel": 2.9,
            "Sasktel International": 2.3,
            "Conexus Credit Union": 0.3,
        },
        skills_with_years={
            "Python": 6.0, "Java": 6.0, "Spring Boot": 2.3,
            "Apache Beam": 2.9, "Elasticsearch": 2.9,
            "AWS Lambda": 2.9, "Kafka": 2.9, "Docker": 2.9,
        },
        most_recent_title="Data Engineer and AI Developer",
        career_level="Senior",
    ),
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sep(char: str = "─", width: int = 70) -> None:
    print(char * width)


def _header(title: str) -> None:
    _sep("═")
    print(f"  {title}")
    _sep("═")


def _section(title: str) -> None:
    print()
    _sep()
    print(f"  {title}")
    _sep()


def _print_resume(data: ResumeData, source: str) -> None:
    """Pretty-print every field of a parsed ResumeData."""
    _header(f"Extracted Resume Data  [{source}]")

    # ── Core identity ──────────────────────────────────────────────────────
    _section("👤  Identity")
    print(f"  Name    : {data.name or '—'}")
    print(f"  Email   : {data.email or '—'}")

    # ── Contact block ──────────────────────────────────────────────────────
    _section("📞  Contact")
    c = data.contact
    if c:
        print(f"  Phone     : {c.phone or '—'}")
        print(f"  Location  : {c.location or '—'}")
        print(f"  LinkedIn  : {c.linkedin_url or '—'}")
        print(f"  GitHub    : {c.github_url or '—'}")
        print(f"  Portfolio : {c.portfolio_url or '—'}")
        if c.other_urls:
            for url in c.other_urls:
                print(f"  Other URL : {url}")
    else:
        print("  —")

    # ── Summary ────────────────────────────────────────────────────────────
    _section("📝  Professional Summary")
    if data.summary:
        # Word-wrap at ~66 chars
        words, line = data.summary.split(), ""
        for word in words:
            if len(line) + len(word) + 1 > 66:
                print(f"  {line}")
                line = word
            else:
                line = f"{line} {word}".strip()
        if line:
            print(f"  {line}")
    else:
        print("  —")

    # ── Skills ─────────────────────────────────────────────────────────────
    _section("🛠  Skills")
    if data.skills:
        row, cols = "", 0
        for skill in data.skills:
            entry = f"  {skill:<28}"
            row += entry
            cols += 1
            if cols == 2:
                print(row)
                row, cols = "", 0
        if row:
            print(row)
    else:
        print("  —")

    # ── Enriched skills ────────────────────────────────────────────────────
    _section("🔬  Enriched Skills  (estimated from work history)")
    if data.enriched_skills:
        print(f"  {'Skill':<28} {'Category':<22} {'Years':>5}  Proficiency")
        _sep("·")
        for s in data.enriched_skills:
            yrs = f"{s.estimated_years:.1f}" if s.estimated_years is not None else "  —"
            print(f"  {s.name:<28} {(s.category or '—'):<22} {yrs:>5}  {s.proficiency or '—'}")
    else:
        print("  —")

    # ── Work experience ────────────────────────────────────────────────────
    _section("💼  Work Experience")
    if data.work_experience:
        for i, job in enumerate(data.work_experience, 1):
            duration = f"({job.duration_months} mo)" if job.duration_months else ""
            date_range = f"{job.start_date or '?'} → {job.end_date or '?'}  {duration}"
            print(f"  [{i}] {job.title}  @  {job.company}")
            print(f"      {date_range}")
            if job.location:
                print(f"      📍 {job.location}")
            if job.description:
                print(f"      {job.description}")
            if job.responsibilities:
                for r in job.responsibilities[:3]:
                    print(f"      • {r}")
                if len(job.responsibilities) > 3:
                    print(f"      … +{len(job.responsibilities) - 3} more")
            if job.skills_used:
                print(f"      Skills: {', '.join(job.skills_used)}")
            print()
    else:
        print("  —")

    # ── Education ──────────────────────────────────────────────────────────
    _section("🎓  Education")
    if data.education:
        for edu in data.education:
            degree_line = " ".join(filter(None, [edu.degree, "in", edu.field_of_study])) if edu.field_of_study else edu.degree or "Degree"
            dates = f"{edu.start_date or '?'} – {edu.end_date or '?'}"
            print(f"  {degree_line}")
            print(f"    {edu.institution}  |  {dates}")
            if edu.gpa:
                print(f"    GPA: {edu.gpa}")
            if edu.honors:
                print(f"    Honors: {edu.honors}")
    else:
        print("  —")

    # ── Certifications ─────────────────────────────────────────────────────
    _section("🏅  Certifications")
    if data.certifications:
        for cert in data.certifications:
            issued = f"  |  Issued: {cert.issue_date}" if cert.issue_date else ""
            org = f"  ({cert.issuing_organization})" if cert.issuing_organization else ""
            print(f"  {cert.name}{org}{issued}")
            if cert.credential_url:
                print(f"    🔗 {cert.credential_url}")
    else:
        print("  None found on this resume")

    # ── Projects ───────────────────────────────────────────────────────────
    _section("🚀  Projects")
    if data.projects:
        for proj in data.projects:
            print(f"  {proj.name}")
            if proj.description:
                print(f"    {proj.description}")
            if proj.technologies:
                print(f"    Stack: {', '.join(proj.technologies)}")
            if proj.url:
                print(f"    🔗 {proj.url}")
    else:
        print("  None listed on this resume")

    # ── Interests / Languages / Awards ─────────────────────────────────────
    _section("🌐  Languages  |  🎯  Interests  |  🏆  Awards")
    print(f"  Languages : {', '.join(data.languages) if data.languages else '—'}")
    print(f"  Interests : {', '.join(data.interests) if data.interests else '—'}")
    print(f"  Awards    : {', '.join(data.awards) if data.awards else '—'}")

    # ── Volunteer ──────────────────────────────────────────────────────────
    _section("🤝  Volunteer Experience")
    if data.volunteer_experience:
        for v in data.volunteer_experience:
            dates = f"{v.start_date or '?'} – {v.end_date or '?'}"
            print(f"  {v.role or 'Volunteer'}  @  {v.organization}  |  {dates}")
    else:
        print("  —")

    # ── Publications ───────────────────────────────────────────────────────
    _section("📚  Publications")
    if data.publications:
        for pub in data.publications:
            print(f"  {pub.title}")
            if pub.publisher:
                print(f"    Published by: {pub.publisher}  ({pub.publication_date or ''})")
    else:
        print("  —")

    # ── Experience analytics ───────────────────────────────────────────────
    _section("📊  Experience Analytics  (computed)")
    a = data.experience_analytics
    if a:
        print(f"  Total experience : {a.total_years:.1f} years")
        print(f"  Career level     : {a.career_level}")
        print(f"  Most recent role : {a.most_recent_title}")
        if a.years_by_company:
            print()
            print("  Years per company:")
            for company, yrs in sorted(a.years_by_company.items(), key=lambda x: -x[1]):
                bar = "█" * int(yrs * 2)
                print(f"    {company:<35} {yrs:.1f} yr  {bar}")
        if a.years_by_role:
            print()
            print("  Years per role:")
            for role, yrs in sorted(a.years_by_role.items(), key=lambda x: -x[1]):
                bar = "█" * int(yrs * 2)
                print(f"    {role:<35} {yrs:.1f} yr  {bar}")
        if a.skills_with_years:
            print()
            print("  Top skills by estimated years:")
            top = sorted(a.skills_with_years.items(), key=lambda x: -x[1])[:10]
            for skill, yrs in top:
                bar = "█" * int(yrs)
                print(f"    {skill:<28} {yrs:.1f} yr  {bar}")
    else:
        print("  —")

    # ── JSON dump ──────────────────────────────────────────────────────────
    _section("📄  Full JSON")
    print(data.to_json())
    _sep("═")
    print()


# ---------------------------------------------------------------------------
# Example 1 – Default config (all strategies, including LLM)
# ---------------------------------------------------------------------------

def example_default_config(file_path: str) -> None:
    """Parse a resume with the default configuration (Regex + NER + LLM)."""
    _header("Example 1 — Default Config  (Regex → NER → LLM)")
    path = Path(file_path)
    if not path.exists():
        print(f"  ❌ File not found: {file_path}")
        print("  ℹ  Loading demo snapshot instead...\n")
        _print_resume(_DEMO_RESUME, "demo snapshot")
        return

    print(f"  Parsing: {file_path}")
    fw = ResumeParserFramework()
    try:
        data = fw.parse_resume(file_path)
    except Exception as exc:
        print(f"\n  ⚠  Framework error: {exc}")
        print("  ℹ  Showing demo snapshot:\n")
        _print_resume(_DEMO_RESUME, "demo snapshot (framework error)")
        return

    # Check whether LLM fields populated (skills/work_experience are the clearest signals)
    llm_available = bool(data.skills or data.work_experience)

    if llm_available:
        _print_resume(data, file_path)
    else:
        # LLM unavailable (rate-limited or no key) — show live non-LLM results first,
        # then the demo snapshot so users see what a complete parse looks like.
        _section("✅  Live results  (LLM unavailable — showing Regex + NER fields)")
        c = data.contact
        print(f"  Name     : {data.name or '—'}")
        print(f"  Email    : {data.email or '—'}")
        if c:
            print(f"  Phone    : {c.phone or '—'}")
            print(f"  Location : {c.location or '—'}")
            print(f"  LinkedIn : {c.linkedin_url or '—'}")
        print()
        print(
            "  NOTE: Skills, work experience, education, and analytics require\n"
            "        a valid GEMINI_API_KEY. See .env.example.\n"
            "        Showing pre-loaded demo snapshot for the full field view:"
        )
        print()
        _print_resume(_DEMO_RESUME, "demo snapshot  ← what a full LLM parse looks like")


# ---------------------------------------------------------------------------
# Example 2 – Regex + NER only (no LLM, no API key needed)
# ---------------------------------------------------------------------------

def example_no_llm(file_path: str) -> None:
    """Parse with regex + NER only — no LLM / API key required."""
    _header("Example 2 — Regex + NER Only  (no LLM / API key needed)")
    path = Path(file_path)
    if not path.exists():
        print(f"  ❌ File not found: {file_path}")
        return

    ner_config = ExtractionConfig(
        strategy_preferences={
            FieldType.NAME:  [StrategyType.NER],
            FieldType.EMAIL: [StrategyType.REGEX],
            FieldType.PHONE: [StrategyType.REGEX],
            FieldType.LOCATION: [StrategyType.NER],
            FieldType.SKILLS: [StrategyType.NER],
            FieldType.LINKEDIN_URL: [StrategyType.REGEX],
            FieldType.GITHUB_URL:   [StrategyType.REGEX],
        }
    )
    fw = ResumeParserFramework(config=ner_config)
    print(f"  Parsing: {file_path}")
    print("  (NER models load on first run — may take a moment)\n")
    try:
        data = fw.parse_resume(file_path)
        _section("✅  Extracted (NER + Regex)")
        c = data.contact
        print(f"  Name     : {data.name}")
        print(f"  Email    : {data.email}")
        if c:
            print(f"  Phone    : {c.phone or '—'}")
            print(f"  Location : {c.location or '—'}")
            print(f"  LinkedIn : {c.linkedin_url or '—'}")
        print(f"  Skills   : {', '.join(data.skills) if data.skills else '—'}")
    except Exception as exc:
        print(f"  ❌ Error: {exc}")
    print()


# ---------------------------------------------------------------------------
# Example 3 – Custom per-field strategy order
# ---------------------------------------------------------------------------

def example_custom_strategy_order(file_path: str) -> None:
    """Demonstrate overriding the strategy order per field."""
    _header("Example 3 — Custom Strategy Order Per Field")
    path = Path(file_path)
    if not path.exists():
        print(f"  ❌ File not found: {file_path}")
        return

    custom = ExtractionConfig(
        strategy_preferences={
            # Email is always reliable via regex — skip NER/LLM entirely
            FieldType.EMAIL: [StrategyType.REGEX],
            # Phone: regex first, LLM as safety net
            FieldType.PHONE: [StrategyType.REGEX, StrategyType.LLM],
            # Skills: try LLM first for quality, NER as fallback
            FieldType.SKILLS: [StrategyType.LLM, StrategyType.NER],
            # Name: NER very accurate for names
            FieldType.NAME: [StrategyType.NER, StrategyType.LLM],
        }
    )
    fw = ResumeParserFramework(config=custom)
    print(f"  Parsing: {file_path}")
    try:
        data = fw.parse_resume(file_path)
        _section("✅  Extracted with custom strategy order")
        print(f"  Name   : {data.name}")
        print(f"  Email  : {data.email}")
        print(f"  Skills : {', '.join(data.skills[:5]) + '...' if data.skills else '—'}")
    except Exception as exc:
        print(f"  ❌ Error: {exc}")
    print()


# ---------------------------------------------------------------------------
# Example 4 – Batch processing
# ---------------------------------------------------------------------------

def example_batch(resume_dir: str) -> None:
    """Parse every resume in a directory and summarise results."""
    _header("Example 4 — Batch Processing")
    resumes = list(Path(resume_dir).glob("*.pdf")) + list(Path(resume_dir).glob("*.docx"))
    if not resumes:
        print(f"  No PDF/DOCX files found in '{resume_dir}'\n")
        return

    fw = ResumeParserFramework()
    results: list[dict[str, Any]] = []

    for resume_path in resumes:
        try:
            data = fw.parse_resume(str(resume_path))
            results.append({
                "file": resume_path.name,
                "name": data.name or "—",
                "email": data.email or "—",
                "skills_count": len(data.skills) if data.skills else 0,
                "experience_years": (
                    data.experience_analytics.total_years
                    if data.experience_analytics else None
                ),
                "career_level": (
                    data.experience_analytics.career_level
                    if data.experience_analytics else "—"
                ),
            })
        except Exception as exc:
            results.append({"file": resume_path.name, "error": str(exc)})

    _section("📋  Batch Summary")
    print(f"  {'File':<40} {'Name':<20} {'Skills':>6}  {'Exp':>5}  {'Level'}")
    _sep("·")
    for r in results:
        if "error" in r:
            print(f"  {r['file']:<40} ❌ {r['error'][:35]}")
        else:
            exp = f"{r['experience_years']:.1f}y" if r["experience_years"] is not None else "  —"
            print(
                f"  {r['file']:<40} {r['name']:<20} {r['skills_count']:>6}  "
                f"{exp:>5}  {r['career_level']}"
            )
    print()


# ---------------------------------------------------------------------------
# Example 5 – Work with the parsed data programmatically
# ---------------------------------------------------------------------------

def example_programmatic_access(data: ResumeData) -> None:
    """Show how to access extracted fields in code."""
    _header("Example 5 — Programmatic Data Access")

    _section("Filter skills by category (from enriched_skills)")
    if data.enriched_skills:
        by_category: dict[str, list[str]] = {}
        for s in data.enriched_skills:
            cat = s.category or "Other"
            by_category.setdefault(cat, []).append(s.name)
        for cat, names in sorted(by_category.items()):
            print(f"  {cat:<25}: {', '.join(names)}")
    else:
        print("  (no enriched skills)")

    _section("Most recent role + seniority")
    a = data.experience_analytics
    if a:
        print(f"  Role  : {a.most_recent_title}")
        print(f"  Level : {a.career_level}")
        print(f"  Total : {a.total_years:.1f} years")
    else:
        print("  (no analytics)")

    _section("Chronological work history (oldest → newest)")
    if data.work_experience:
        for job in reversed(data.work_experience):
            print(f"  {job.start_date or '?':12}  {job.title}  @  {job.company}")
    else:
        print("  (no work experience)")

    _section("Serialise to JSON  (first 600 chars)")
    json_str = data.to_json()
    print(f"  {json_str[:600]}...")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # Accept an optional file path from CLI args
    pdf_path  = sys.argv[1] if len(sys.argv) > 1 else "sample_resumes/Brijesh_Patel_ATS.pdf"
    docx_path = "sample_resumes/Brijesh_Patel_ATS.docx"

    print()
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║          Resume Parser Framework  –  Usage Examples                 ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()
    print("  Supported fields : name, email, phone, location, LinkedIn, GitHub,")
    print("  portfolio, other URLs, summary, skills (raw + enriched), work")
    print("  experience, education, certifications, projects, interests, languages,")
    print("  awards, volunteer experience, publications, experience analytics.")
    print()

    example_default_config(pdf_path)
    example_no_llm(pdf_path)
    example_custom_strategy_order(pdf_path)
    example_batch("sample_resumes/")
    example_programmatic_access(_DEMO_RESUME)

    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║  Examples complete. See README.md for full API documentation.       ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")


if __name__ == "__main__":
    main()

