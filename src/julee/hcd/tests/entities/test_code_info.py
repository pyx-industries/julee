"""Tests for CodeInfo domain models."""

import pytest
from pydantic import ValidationError

from julee.hcd.entities.code_info import (
    BoundedContextInfo,
    ClassInfo,
)


class TestClassInfo:
    """Test ClassInfo model."""

    def test_create_with_name_only(self) -> None:
        """Test creating with just name."""
        info = ClassInfo(name="Document")
        assert info.name == "Document"
        assert info.docstring == ""
        assert info.file == ""

    def test_create_with_all_fields(self) -> None:
        """Test creating with all fields."""
        info = ClassInfo(
            name="Document",
            docstring="A document entity.",
            file="document.py",
        )
        assert info.name == "Document"
        assert info.docstring == "A document entity."
        assert info.file == "document.py"

    def test_empty_name_raises_error(self) -> None:
        """Test that empty name raises validation error."""
        with pytest.raises(ValidationError, match="name cannot be empty"):
            ClassInfo(name="")

    def test_whitespace_name_raises_error(self) -> None:
        """Test that whitespace-only name raises validation error."""
        with pytest.raises(ValidationError, match="name cannot be empty"):
            ClassInfo(name="   ")

    def test_name_stripped(self) -> None:
        """Test that name is stripped of whitespace."""
        info = ClassInfo(name="  Document  ")
        assert info.name == "Document"


class TestBoundedContextInfoCreation:
    """Test BoundedContextInfo model creation and validation."""

    def test_create_minimal(self) -> None:
        """Test creating with minimum fields."""
        info = BoundedContextInfo(slug="vocabulary")
        assert info.slug == "vocabulary"
        assert info.entities == []
        assert info.use_cases == []
        assert info.repository_protocols == []
        assert info.service_protocols == []
        assert info.has_infrastructure is False
        assert info.code_dir == ""
        assert info.objective is None
        assert info.docstring is None

    def test_create_complete(self) -> None:
        """Test creating with all fields."""
        entities = [
            ClassInfo(
                name="Vocabulary", docstring="A vocabulary entity", file="vocabulary.py"
            ),
            ClassInfo(name="Term", docstring="A term in a vocabulary", file="term.py"),
        ]
        use_cases = [
            ClassInfo(
                name="CreateVocabulary",
                docstring="Create a vocabulary",
                file="create.py",
            ),
        ]
        repo_protocols = [
            ClassInfo(
                name="VocabularyRepository",
                docstring="Repository protocol",
                file="vocabulary.py",
            ),
        ]

        info = BoundedContextInfo(
            slug="vocabulary",
            entities=entities,
            use_cases=use_cases,
            repository_protocols=repo_protocols,
            service_protocols=[],
            has_infrastructure=True,
            code_dir="vocabulary",
            objective="Manage vocabulary catalogs",
            docstring="Full module documentation here.",
        )

        assert info.slug == "vocabulary"
        assert len(info.entities) == 2
        assert len(info.use_cases) == 1
        assert len(info.repository_protocols) == 1
        assert info.has_infrastructure is True
        assert info.objective == "Manage vocabulary catalogs"

    def test_empty_slug_raises_error(self) -> None:
        """Test that empty slug raises validation error."""
        with pytest.raises(ValidationError, match="slug cannot be empty"):
            BoundedContextInfo(slug="")


class TestBoundedContextInfoProperties:
    """Test BoundedContextInfo properties."""

    @pytest.fixture
    def sample_context(self) -> BoundedContextInfo:
        """Create a sample bounded context for testing."""
        return BoundedContextInfo(
            slug="vocabulary",
            entities=[
                ClassInfo(name="Vocabulary", file="vocabulary.py"),
                ClassInfo(name="Term", file="term.py"),
            ],
            use_cases=[
                ClassInfo(name="CreateVocabulary", file="create.py"),
            ],
            repository_protocols=[
                ClassInfo(name="VocabularyRepository", file="vocabulary.py"),
            ],
            service_protocols=[
                ClassInfo(name="NotificationService", file="notification.py"),
            ],
            has_infrastructure=True,
        )

    def test_entity_count(self, sample_context: BoundedContextInfo) -> None:
        """Test entity_count property."""
        assert sample_context.entity_count == 2

    def test_use_case_count(self, sample_context: BoundedContextInfo) -> None:
        """Test use_case_count property."""
        assert sample_context.use_case_count == 1

    def test_protocol_count(self, sample_context: BoundedContextInfo) -> None:
        """Test protocol_count property."""
        assert sample_context.protocol_count == 2  # 1 repo + 1 service

    def test_has_entities(self, sample_context: BoundedContextInfo) -> None:
        """Test has_entities property."""
        assert sample_context.has_entities is True

    def test_has_entities_empty(self) -> None:
        """Test has_entities with empty context."""
        info = BoundedContextInfo(slug="test")
        assert info.has_entities is False

    def test_has_use_cases(self, sample_context: BoundedContextInfo) -> None:
        """Test has_use_cases property."""
        assert sample_context.has_use_cases is True

    def test_has_use_cases_empty(self) -> None:
        """Test has_use_cases with empty context."""
        info = BoundedContextInfo(slug="test")
        assert info.has_use_cases is False

    def test_has_protocols(self, sample_context: BoundedContextInfo) -> None:
        """Test has_protocols property."""
        assert sample_context.has_protocols is True

    def test_has_protocols_empty(self) -> None:
        """Test has_protocols with empty context."""
        info = BoundedContextInfo(slug="test")
        assert info.has_protocols is False

    def test_get_entity_names(self, sample_context: BoundedContextInfo) -> None:
        """Test get_entity_names method."""
        names = sample_context.get_entity_names()
        assert names == ["Vocabulary", "Term"]

    def test_get_use_case_names(self, sample_context: BoundedContextInfo) -> None:
        """Test get_use_case_names method."""
        names = sample_context.get_use_case_names()
        assert names == ["CreateVocabulary"]

    def test_summary(self, sample_context: BoundedContextInfo) -> None:
        """Test summary method."""
        summary = sample_context.summary()
        assert "2 entities" in summary
        assert "1 use cases" in summary
        assert "1 repository protocols" in summary
        assert "1 service protocols" in summary

    def test_summary_empty(self) -> None:
        """Test summary with empty context."""
        info = BoundedContextInfo(slug="test")
        assert info.summary() == "empty"

    def test_summary_partial(self) -> None:
        """Test summary with partial data."""
        info = BoundedContextInfo(
            slug="test",
            entities=[ClassInfo(name="Entity", file="e.py")],
        )
        summary = info.summary()
        assert summary == "1 entities"


class TestBoundedContextInfoSerialization:
    """Test BoundedContextInfo serialization."""

    def test_to_dict(self) -> None:
        """Test serialization to dict."""
        info = BoundedContextInfo(
            slug="test",
            entities=[ClassInfo(name="Entity", file="e.py")],
            objective="Test objective",
        )

        data = info.model_dump()
        assert data["slug"] == "test"
        assert len(data["entities"]) == 1
        assert data["entities"][0]["name"] == "Entity"
        assert data["objective"] == "Test objective"

    def test_to_json(self) -> None:
        """Test serialization to JSON."""
        info = BoundedContextInfo(slug="test", objective="Test")
        json_str = info.model_dump_json()
        assert '"slug":"test"' in json_str
        assert '"objective":"Test"' in json_str
