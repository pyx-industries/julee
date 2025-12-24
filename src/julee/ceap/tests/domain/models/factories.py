"""
Test factories for CEAP domain objects using factory_boy.

This module provides factory_boy factories for creating test instances of
CEAP domain objects with sensible defaults.
"""

import io
from datetime import datetime, timezone
from typing import Any

from factory.base import Factory
from factory.declarations import LazyAttribute, LazyFunction
from factory.faker import Faker

from julee.ceap.domain.models.assembly import Assembly, AssemblyStatus
from julee.ceap.domain.models.assembly_specification import (
    AssemblySpecification,
    AssemblySpecificationStatus,
)
from julee.ceap.domain.models.content_stream import ContentStream
from julee.ceap.domain.models.document import Document, DocumentStatus
from julee.ceap.domain.models.document_policy_validation import (
    DocumentPolicyValidation,
    DocumentPolicyValidationStatus,
)
from julee.ceap.domain.models.knowledge_service_query import KnowledgeServiceQuery


class AssemblyFactory(Factory):
    """Factory for creating Assembly instances with sensible test defaults."""

    class Meta:
        model = Assembly

    # Core assembly identification
    assembly_id = Faker("uuid4")
    assembly_specification_id = Faker("uuid4")
    input_document_id = Faker("uuid4")
    workflow_id = Faker("uuid4")

    # Assembly process tracking
    status = AssemblyStatus.PENDING
    assembled_document_id = None

    # Timestamps
    created_at = LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = LazyFunction(lambda: datetime.now(timezone.utc))


class AssemblySpecificationFactory(Factory):
    """Factory for creating AssemblySpecification instances with sensible
    test defaults."""

    class Meta:
        model = AssemblySpecification

    # Core assembly specification identification
    assembly_specification_id = Faker("uuid4")
    name = "Test Assembly Specification"
    applicability = "Test documents for automated testing purposes"

    # Valid JSON Schema for testing
    @LazyAttribute
    def jsonschema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"},
                "metadata": {
                    "type": "object",
                    "properties": {
                        "author": {"type": "string"},
                        "created_date": {"type": "string", "format": "date"},
                    },
                },
            },
            "required": ["title"],
        }

    # Assembly specification configuration
    status = AssemblySpecificationStatus.ACTIVE
    version = "0.1.0"

    # Timestamps
    created_at = LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = LazyFunction(lambda: datetime.now(timezone.utc))


class KnowledgeServiceQueryFactory(Factory):
    """Factory for creating KnowledgeServiceQuery instances with sensible
    test defaults."""

    class Meta:
        model = KnowledgeServiceQuery

    # Core query identification
    query_id = Faker("uuid4")
    name = "Test Knowledge Service Query"

    # Knowledge service configuration
    knowledge_service_id = "test-knowledge-service"
    prompt = "Extract test data from the document"

    # Timestamps
    created_at = LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = LazyFunction(lambda: datetime.now(timezone.utc))


class DocumentPolicyValidationFactory(Factory):
    """Factory for creating DocumentPolicyValidation instances with sensible
    test defaults."""

    class Meta:
        model = DocumentPolicyValidation

    # Core validation identification
    validation_id = Faker("uuid4")
    input_document_id = Faker("uuid4")
    policy_id = Faker("uuid4")

    # Validation state
    status = DocumentPolicyValidationStatus.PENDING
    validation_scores: list[tuple[str, int]] = []
    transformed_document_id = None
    post_transform_validation_scores = None
    passed = None
    error_message = None
    completed_at = None

    # Timestamps
    started_at = LazyFunction(lambda: datetime.now(timezone.utc))


class ContentStreamFactory(Factory):
    """Factory for creating ContentStream instances with sensible test defaults.

    Note: This factory doesn't use a Meta.model because ContentStream has a
    custom constructor that takes an io.IOBase. Instead, use the build() method
    with a content parameter.
    """

    class Meta:
        model = ContentStream

    @classmethod
    def _create(cls, model_class: type, *args: Any, **kwargs: Any) -> ContentStream:
        """Override create to handle ContentStream's custom constructor."""
        content = kwargs.pop("content", b"test content")
        if isinstance(content, bytes):
            stream = io.BytesIO(content)
        elif isinstance(content, str):
            stream = io.BytesIO(content.encode("utf-8"))
        elif isinstance(content, io.IOBase):
            stream = content
        else:
            stream = io.BytesIO(b"default test content")
        return ContentStream(stream)

    @classmethod
    def _build(cls, model_class: type, *args: Any, **kwargs: Any) -> ContentStream:
        """Override build to handle ContentStream's custom constructor."""
        return cls._create(model_class, *args, **kwargs)


class DocumentFactory(Factory):
    """Factory for creating Document instances with sensible test defaults."""

    class Meta:
        model = Document

    # Core document identification
    document_id = Faker("uuid4")
    original_filename = "test_document.txt"
    content_type = "text/plain"
    size_bytes = 12  # Length of "test content"
    content_multihash = "sha256:test-hash"

    # Document processing state
    status = DocumentStatus.CAPTURED
    knowledge_service_id = None
    assembly_types: list[str] = []

    # Timestamps
    created_at = LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = LazyFunction(lambda: datetime.now(timezone.utc))

    # Content stream
    @LazyAttribute
    def content(self) -> ContentStream:
        return ContentStreamFactory.build()
