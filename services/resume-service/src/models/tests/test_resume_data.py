"""Tests for ResumeData data class."""

import json

from models.resume_data import ResumeData


class TestResumeDataCreation:
    """Test cases for creating ResumeData instances."""

    def test_create_valid_resume_data(self):
        """Test creating a valid ResumeData instance."""
        # Arrange & Act
        resume = ResumeData(
            name="John Doe",
            email="john.doe@example.com",
            skills=["Python", "Java", "SQL"],
        )

        # Assert
        assert resume.name == "John Doe"
        assert resume.email == "john.doe@example.com"
        assert resume.skills == ["Python", "Java", "SQL"]

    def test_create_with_single_skill(self):
        """Test creating ResumeData with a single skill."""
        # Arrange & Act
        resume = ResumeData(
            name="Jane Smith", email="jane@example.com", skills=["Python"]
        )

        # Assert
        assert resume.skills is not None
        assert len(resume.skills) == 1
        assert resume.skills[0] == "Python"

    def test_create_with_empty_skills_list(self):
        """Test creating ResumeData with an empty skills list."""
        # Arrange & Act
        resume = ResumeData(name="Bob Johnson", email="bob@example.com", skills=[])

        # Assert
        assert resume.skills is not None
        assert resume.skills == []
        assert len(resume.skills) == 0

    def test_create_with_many_skills(self):
        """Test creating ResumeData with many skills."""
        # Arrange
        skills = [
            "Python",
            "Java",
            "JavaScript",
            "SQL",
            "Docker",
            "Kubernetes",
            "AWS",
            "Machine Learning",
            "Django",
            "Flask",
        ]

        # Act
        resume = ResumeData(
            name="Alice Williams", email="alice@example.com", skills=skills
        )

        # Assert
        assert resume.skills is not None
        assert len(resume.skills) == 10
        assert resume.skills == skills


class TestResumeDataValidation:
    """Test suite for ResumeData - now allows None/empty values for graceful degradation."""

    def test_none_name_allowed(self):
        """Test that None name is allowed (extraction may fail)."""
        # Act
        resume = ResumeData(name=None, email="test@example.com", skills=["Python"])

        # Assert
        assert resume.name is None
        assert resume.email == "test@example.com"

    def test_none_email_allowed(self):
        """Test that None email is allowed (extraction may fail)."""
        # Act
        resume = ResumeData(name="John Doe", email=None, skills=["Python"])

        # Assert
        assert resume.name == "John Doe"
        assert resume.email is None

    def test_none_skills_allowed(self):
        """Test that None skills is allowed (extraction may fail)."""
        # Act
        resume = ResumeData(name="John Doe", email="john@example.com", skills=None)

        # Assert
        assert resume.name == "John Doe"
        assert resume.skills is None

    def test_empty_string_values_allowed(self):
        """Test that empty strings are allowed for graceful degradation."""
        # Act
        resume = ResumeData(name="", email="", skills=[])

        # Assert
        assert resume.name == ""
        assert resume.email == ""
        assert resume.skills == []

    def test_whitespace_only_name_passes(self):
        """Test that whitespace-only name is allowed."""
        resume = ResumeData(name=" ", email="test@example.com", skills=[])
        assert resume.name == " "


class TestResumeDataSerialization:
    """Test cases for ResumeData serialization methods."""

    def test_to_dict(self):
        """Test converting ResumeData to dictionary."""
        # Arrange
        resume = ResumeData(
            name="John Doe",
            email="john.doe@example.com",
            skills=["Python", "Java", "SQL"],
        )

        # Act
        result = resume.to_dict()

        # Assert
        assert isinstance(result, dict)
        assert result["name"] == "John Doe"
        assert result["email"] == "john.doe@example.com"
        assert result["skills"] == ["Python", "Java", "SQL"]

    def test_to_dict_structure(self):
        """Test that to_dict returns all expected keys."""
        # Arrange
        resume = ResumeData(
            name="Jane Smith", email="jane@example.com", skills=["Python"]
        )

        # Act
        result = resume.to_dict()

        # Assert
        assert set(result.keys()) == {"name", "email", "skills"}

    def test_to_json_valid_format(self):
        """Test converting ResumeData to JSON string."""
        # Arrange
        resume = ResumeData(
            name="John Doe",
            email="john.doe@example.com",
            skills=["Python", "Java", "SQL"],
        )

        # Act
        json_str = resume.to_json()

        # Assert
        assert isinstance(json_str, str)
        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["name"] == "John Doe"
        assert parsed["email"] == "john.doe@example.com"
        assert parsed["skills"] == ["Python", "Java", "SQL"]

    def test_to_json_with_custom_indent(self):
        """Test converting to JSON with custom indentation."""
        # Arrange
        resume = ResumeData(
            name="John Doe", email="john@example.com", skills=["Python"]
        )

        # Act
        json_str_4 = resume.to_json(indent=4)
        json_str_0 = resume.to_json(indent=0)

        # Assert
        assert len(json_str_4) > len(json_str_0)  # More indentation = more chars
        # Both should be valid JSON
        json.loads(json_str_4)
        json.loads(json_str_0)

    def test_to_json_default_indent(self):
        """Test that default indent is 2."""
        # Arrange
        resume = ResumeData(
            name="John Doe", email="john@example.com", skills=["Python"]
        )

        # Act
        json_str = resume.to_json()

        # Assert
        # Should have newlines and indentation
        assert "\n" in json_str
        # Verify it's valid JSON
        json.loads(json_str)


class TestResumeDataStringRepresentation:
    """Test cases for ResumeData string representations."""

    def test_str_representation(self):
        """Test string representation."""
        # Arrange
        resume = ResumeData(
            name="John Doe", email="john@example.com", skills=["Python", "Java"]
        )

        # Act
        result = str(resume)

        # Assert
        assert "John Doe" in result
        assert "john@example.com" in result
        assert "Python" in result
        assert "Java" in result
        assert "ResumeData" in result

    def test_repr_representation(self):
        """Test repr representation."""
        # Arrange
        resume = ResumeData(name="Jane Smith", email="jane@example.com", skills=["SQL"])

        # Act
        result = repr(resume)

        # Assert
        assert "Jane Smith" in result
        assert "jane@example.com" in result
        assert "SQL" in result
        assert "ResumeData" in result

    def test_str_and_repr_are_same(self):
        """Test that str and repr return the same value."""
        # Arrange
        resume = ResumeData(
            name="Bob Johnson", email="bob@example.com", skills=["Docker"]
        )

        # Act & Assert
        assert str(resume) == repr(resume)


class TestResumeDataImmutability:
    """Test cases for ResumeData immutability (dataclass behavior)."""

    def test_dataclass_is_not_frozen(self):
        """Test that dataclass allows modification (not frozen by default)."""
        # Note: The current implementation doesn't use frozen=True
        # This test documents current behavior
        # Arrange
        resume = ResumeData(
            name="John Doe", email="john@example.com", skills=["Python"]
        )

        # Act - Modify the name (this will work since frozen=True is not set)
        resume.name = "Jane Doe"

        # Assert
        assert resume.name == "Jane Doe"

    def test_skills_list_is_mutable(self):
        """Test that skills list can be modified."""
        # Arrange
        resume = ResumeData(
            name="John Doe", email="john@example.com", skills=["Python"]
        )

        # Act
        assert resume.skills is not None
        resume.skills.append("Java")

        # Assert
        assert len(resume.skills) == 2
        assert "Java" in resume.skills


class TestResumeDataEquality:
    """Test cases for ResumeData equality comparison."""

    def test_equal_resume_data(self):
        """Test that two ResumeData objects with same data are equal."""
        # Arrange
        resume1 = ResumeData(
            name="John Doe", email="john@example.com", skills=["Python", "Java"]
        )
        resume2 = ResumeData(
            name="John Doe", email="john@example.com", skills=["Python", "Java"]
        )

        # Act & Assert
        assert resume1 == resume2

    def test_different_name_not_equal(self):
        """Test that ResumeData objects with different names are not equal."""
        # Arrange
        resume1 = ResumeData(
            name="John Doe", email="john@example.com", skills=["Python"]
        )
        resume2 = ResumeData(
            name="Jane Doe", email="john@example.com", skills=["Python"]
        )

        # Act & Assert
        assert resume1 != resume2

    def test_different_skills_not_equal(self):
        """Test that ResumeData objects with different skills are not equal."""
        # Arrange
        resume1 = ResumeData(
            name="John Doe", email="john@example.com", skills=["Python"]
        )
        resume2 = ResumeData(name="John Doe", email="john@example.com", skills=["Java"])

        # Act & Assert
        assert resume1 != resume2
