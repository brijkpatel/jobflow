from __future__ import annotations

import grpc

from application.parse_resume import ParseResumeUseCase
from domain.models import Certification, Education, Experience, Project, ResumeData

try:
    from .generated import resume_pb2, resume_pb2_grpc
except ImportError:  # pragma: no cover - generated during build/test setup
    resume_pb2 = None
    resume_pb2_grpc = None


class ResumeServiceHandler(
    resume_pb2_grpc.ResumeServiceServicer if resume_pb2_grpc is not None else object
):
    def __init__(self, use_case: ParseResumeUseCase) -> None:
        self._use_case = use_case

    async def ParseResume(self, request, context):  # noqa: N802
        result = await self._use_case.execute(
            file_bytes=request.file_bytes,
            filename=request.filename,
            tenant_id=request.tenant_id,
            user_id=request.user_id,
        )
        if resume_pb2 is None:
            return {"resume_id": result.resume_id, "resume": result.resume.to_dict()}
        return resume_pb2.ParseResumeResponse(
            resume_id=result.resume_id,
            resume=_resume_to_proto(result.resume),
        )

    async def GetResume(self, request, context):  # noqa: N802
        record = await self._use_case.get_resume(
            resume_id=request.resume_id,
            tenant_id=request.tenant_id,
        )
        if record is None:
            await context.abort(grpc.StatusCode.NOT_FOUND, f"resume {request.resume_id} not found")
        if resume_pb2 is None:
            return {"resume": record.resume.to_dict()}
        return resume_pb2.GetResumeResponse(resume=_resume_to_proto(record.resume))


def add_resume_service_to_server(server: grpc.aio.Server, handler: ResumeServiceHandler) -> None:
    if resume_pb2_grpc is None:
        raise RuntimeError("generated gRPC stubs are unavailable")
    resume_pb2_grpc.add_ResumeServiceServicer_to_server(handler, server)


def _resume_to_proto(resume: ResumeData):
    message = resume_pb2.ResumeData(
        skills=resume.skills,
        experience=[_experience_to_proto(item) for item in resume.experience],
        education=[_education_to_proto(item) for item in resume.education],
        certifications=[_certification_to_proto(item) for item in resume.certifications],
        languages=resume.languages,
        projects=[_project_to_proto(item) for item in resume.projects],
    )
    for field in [
        "name",
        "email",
        "phone",
        "location",
        "linkedin_url",
        "github_url",
        "portfolio_url",
        "summary",
    ]:
        value = getattr(resume, field)
        if value is not None:
            setattr(message, field, value)
    if resume.years_of_experience is not None:
        message.years_of_experience = resume.years_of_experience
    return message


def _experience_to_proto(experience: Experience):
    message = resume_pb2.Experience(
        company=experience.company,
        title=experience.title,
        start_date=experience.start_date,
        bullets=experience.bullets,
    )
    if experience.end_date is not None:
        message.end_date = experience.end_date
    if experience.location is not None:
        message.location = experience.location
    return message


def _education_to_proto(education: Education):
    message = resume_pb2.Education(
        institution=education.institution,
        degree=education.degree,
    )
    if education.field is not None:
        message.field = education.field
    if education.graduation_date is not None:
        message.graduation_date = education.graduation_date
    if education.gpa is not None:
        message.gpa = education.gpa
    return message


def _certification_to_proto(certification: Certification):
    message = resume_pb2.Certification(name=certification.name)
    if certification.issuer is not None:
        message.issuer = certification.issuer
    if certification.date is not None:
        message.date = certification.date
    return message


def _project_to_proto(project: Project):
    message = resume_pb2.Project(
        name=project.name,
        technologies=project.technologies,
    )
    if project.description is not None:
        message.description = project.description
    return message
