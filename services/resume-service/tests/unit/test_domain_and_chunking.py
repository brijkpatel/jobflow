from application.chunking import build_resume_chunks, calculate_years_of_experience
from domain.models import Education, Experience, ResumeData


def test_resume_data_round_trip_preserves_nested_fields():
    resume = ResumeData(
        name="Ada Lovelace",
        email="ada@example.com",
        skills=["Python", "SQL"],
        experience=[
            Experience(
                company="Analytical Engines Ltd",
                title="Engineer",
                start_date="2020-01",
                end_date="2022-01",
                bullets=["Built parsers"],
            )
        ],
        education=[Education(institution="Oxford", degree="BS", field="Math")],
    )

    restored = ResumeData.from_dict(resume.to_dict())

    assert restored == resume


def test_chunk_builder_and_experience_calculation_cover_expanded_sections():
    resume = ResumeData(
        summary="Backend engineer",
        skills=["Python", "Kafka"],
        experience=[
            Experience(
                company="Jobflow",
                title="Engineer",
                start_date="2020-01",
                end_date="2022-01",
                bullets=["Built event pipelines"],
            )
        ],
        languages=["English"],
    )

    years = calculate_years_of_experience(resume)
    chunks = build_resume_chunks(resume)

    assert years is not None
    assert years > 1.9
    assert [chunk.section_type for chunk in chunks] == [
        "summary",
        "skills",
        "experience",
        "languages",
    ]
