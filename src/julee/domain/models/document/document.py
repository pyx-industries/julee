"""
Document domain models for the Capture, Extract, Assemble, Publish workflow.

This module contains the core document domain objects that represent
documents and their metadata in the CEAP workflow system.

All domain models use Pydantic BaseModel for validation, serialization,
and type safety, following the patterns established in the sample project.
"""

from collections.abc import Callable
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator

from julee.domain.models.custom_fields.content_stream import (
    ContentStream,
)


def delegate_to_content(*method_names: str) -> Callable[[type], type]:
    """Decorator to delegate IO methods to the content stream property."""

    def decorator(cls: type) -> type:
        for method_name in method_names:

            def make_delegated_method(name: str) -> Callable[..., Any]:
                def delegated_method(self: Any, *args: Any, **kwargs: Any) -> Any:
                    return getattr(self.content, name)(*args, **kwargs)

                delegated_method.__name__ = name
                delegated_method.__doc__ = f"Delegate {name} to content stream."
                return delegated_method

            setattr(cls, method_name, make_delegated_method(method_name))
        return cls

    return decorator


class DocumentStatus(str, Enum):
    """Status of a document through the Capture, Extract, Assemble, Publish
    pipeline."""

    CAPTURED = "captured"
    REGISTERED = "registered"  # Registered with knowledge service
    # Assembly specification types determined
    ASSEMBLY_SPECIFICATION_IDENTIFIED = "assembly_specification_identified"
    EXTRACTED = "extracted"  # Extractions completed
    ASSEMBLED = "assembled"  # Template rendered and policies applied
    PUBLISHED = "published"
    FAILED = "failed"


@delegate_to_content("read", "seek", "tell")
class Document(BaseModel):
    """Complete document entity including content and metadata.

    This is the primary domain model that represents a complete document
    in the CEAP workflow system. Content is provided as a ContentStream
    for efficient handling of both small and large documents.

    The content stream is excluded from JSON serialization - use separate
    content endpoints for streaming binary data over HTTP.
    """

    # Core document identification
    document_id: str
    original_filename: str
    content_type: str
    size_bytes: int = Field(gt=0, description="Size must be positive")
    content_multihash: str = Field(
        description="Multihash of document content for integrity verification"
    )

    # Document processing state
    status: DocumentStatus = DocumentStatus.CAPTURED
    knowledge_service_id: str | None = None
    assembly_types: list[str] = Field(default_factory=list)

    # Timestamps
    created_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Additional data and content stream
    additional_metadata: dict[str, Any] = Field(default_factory=dict)
    content: ContentStream | None = Field(default=None, exclude=True)
    content_string: str | None = Field(
        default=None,
        description="Small content as string (few KB max). Use for "
        "workflow-generated content to avoid ContentStream serialization "
        "issues. For larger content, use content or content_bytes instead.",
    )

    content_bytes: Optional[bytes] = Field(
        default=None,
        description="Raw content as bytes for cases where direct in-memory "
        "binary payloads are preferred over ContentStream.",
    )

    @field_validator("document_id")
    @classmethod
    def document_id_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Document ID cannot be empty")
        return v.strip()

    @field_validator("original_filename")
    @classmethod
    def filename_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Original filename cannot be empty")
        return v.strip()

    @field_validator("content_type")
    @classmethod
    def content_type_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Content type cannot be empty")
        return v.strip()

    @field_validator("content_multihash")
    @classmethod
    def content_multihash_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Content multihash cannot be empty")
        return v.strip()

    @model_validator(mode="after")
    def validate_content_fields(self, info: ValidationInfo) -> "Document":
        """Ensure document has at least content, content_string, or content_bytes."""

        # Skip validation in Temporal deserialization context
        if info.context and info.context.get("temporal_validation"):
            return self

        has_content = self.content is not None
        has_content_string = self.content_string is not None
        has_content_bytes = self.content_bytes is not None

        provided = sum([has_content, has_content_string, has_content_bytes])

        if provided == 0:
            raise ValueError(
                "Document must have one of: content, content_string, or content_bytes."
            )

        return self
