"""Unit tests for domain models (ResumeData, ResumeChunk)."""

import uuid
from dataclasses import fields

import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

from domain.models import ResumeChunk, ResumeData


class TestResumeData:
    def test_resume_data_has_tenant_id_field(self):
        """ResumeData must carry tenant_id for multi-tenant isolation."""
        field_names = {f.name for f in fields(ResumeData)}
        assert "tenant_id" in field_names

    def test_resume_data_has_user_id_field(self):
        field_names = {f.name for f in fields(ResumeData)}
        assert "user_id" in field_names

    def test_resume_data_has_resume_id_field(self):
        field_names = {f.name for f in fields(ResumeData)}
        assert "resume_id" in field_names

    def test_resume_data_resume_id_is_uuid(self):
        resume = ResumeData()
        assert isinstance(resume.resume_id, uuid.UUID)

    def test_resume_data_tenant_id_is_uuid(self):
        resume = ResumeData(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
        )
        assert isinstance(resume.tenant_id, uuid.UUID)

    def test_resume_data_each_instance_gets_unique_resume_id(self):
        r1 = ResumeData()
        r2 = ResumeData()
        assert r1.resume_id != r2.resume_id

    def test_resume_data_has_no_to_dict_method(self):
        """Serialisation is an infrastructure concern — not on the domain model."""
        assert not hasattr(ResumeData, "to_dict")

    def test_resume_data_has_no_to_json_method(self):
        assert not hasattr(ResumeData, "to_json")

    def test_resume_data_has_storage_object_field(self):
        """storage_object must be present for re-parse and audit."""
        field_names = {f.name for f in fields(ResumeData)}
        assert "storage_object" in field_names

    def test_resume_data_optional_fields_default_to_none(self):
        resume = ResumeData()
        assert resume.name is None
        assert resume.email is None
        assert resume.skills is None
        assert resume.work_experience is None

    def test_resume_data_str_includes_tenant_id(self):
        tenant = uuid.uuid4()
        resume = ResumeData(tenant_id=tenant)
        assert str(tenant) in str(resume)


class TestResumeChunk:
    def test_resume_chunk_has_no_embedding_field(self):
        """Embeddings are paired with chunks in infrastructure, not stored here."""
        field_names = {f.name for f in fields(ResumeChunk)}
        assert "embedding" not in field_names
        assert "vector" not in field_names

    def test_resume_chunk_has_required_fields(self):
        field_names = {f.name for f in fields(ResumeChunk)}
        assert {"chunk_id", "resume_id", "user_id", "section", "text"} <= field_names

    def test_resume_chunk_chunk_id_is_uuid(self):
        chunk = ResumeChunk()
        assert isinstance(chunk.chunk_id, uuid.UUID)

    def test_resume_chunk_each_instance_gets_unique_chunk_id(self):
        c1 = ResumeChunk()
        c2 = ResumeChunk()
        assert c1.chunk_id != c2.chunk_id

    def test_resume_chunk_section_and_text_default_to_empty_string(self):
        chunk = ResumeChunk()
        assert chunk.section == ""
        assert chunk.text == ""
