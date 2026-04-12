import pytest

from application.extraction import ResumeExtractionOrchestrator


class StaticStrategy:
    def __init__(self, value):
        self._value = value

    def extract(self, text: str):
        return self._value


class FakeLLMClient:
    async def extract_fields(self, text: str, fields: list[str]) -> dict:
        assert "skills" in fields
        return {
            "summary": "Platform engineer",
            "skills": ["Python", "Qdrant"],
            "experience": [{"company": "Jobflow", "title": "Engineer", "start_date": "2021-01"}],
            "education": [{"institution": "State U", "degree": "BS"}],
            "certifications": [{"name": "AWS SA"}],
            "languages": ["English"],
            "projects": [{"name": "Resume Parser", "technologies": ["Python"]}],
        }


@pytest.mark.asyncio
async def test_orchestrator_uses_simple_fields_and_batched_llm_payload():
    orchestrator = ResumeExtractionOrchestrator(
        llm_client=FakeLLMClient(),
        simple_field_strategies={
            "name": [StaticStrategy(["Ada Lovelace"])],
            "email": [StaticStrategy("ada@example.com")],
            "phone": [StaticStrategy("+1 555 0100")],
            "linkedin_url": [StaticStrategy("https://linkedin.com/in/ada")],
            "github_url": [StaticStrategy("https://github.com/ada")],
            "portfolio_url": [StaticStrategy(None)],
            "location": [StaticStrategy("London")],
        },
    )

    resume = await orchestrator.extract("resume text")

    assert resume.name == "Ada Lovelace"
    assert resume.email == "ada@example.com"
    assert resume.phone == "+1 555 0100"
    assert resume.summary == "Platform engineer"
    assert resume.skills == ["Python", "Qdrant"]
    assert resume.projects[0].name == "Resume Parser"
