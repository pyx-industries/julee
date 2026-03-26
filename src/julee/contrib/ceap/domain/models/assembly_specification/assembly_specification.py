"""
AssemblySpecification domain models for the Capture, Extract, Assemble,
Publish workflow.

This module contains the AssemblySpecification domain object that represents
assembly configurations in the CEAP workflow system.

An AssemblySpecification defines a type of document output (like "meeting
minutes"), includes information about its applicability and and specifies
which extractors are needed to collect the data for that output.

All domain models use Pydantic BaseModel for validation, serialization,
and type safety, following the patterns established in the sample project.
"""

from collections.abc import Mapping
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

import jsonpointer  # type: ignore
import jsonschema
from pydantic import Field, field_validator

from julee.core.entities.entity import Entity


class AssemblySpecificationStatus(StrEnum):
    """Status of an assembly specification configuration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    DEPRECATED = "deprecated"


class AssemblySpecification(Entity):
    """Assembly specification configuration that defines how to assemble
    documents of a specific type.

    An AssemblySpecification represents a type of document output (like
    "meeting minutes", "project report", etc.) and defines which extractors
    should be used to collect the necessary data from source documents.

    The AssemblySpecification does not contain the template itself - templates
    will be handled separately during the assembly rendering (or publishing?)
    phase. This separation allows the same AssemblySpecification definition to
    be used with different templates over time.
    """

    # Core assembly identification
    assembly_specification_id: str = Field(
        description="Unique identifier for this assembly specification"
    )
    name: str = Field(description="Human-readable name like 'meeting minutes'")
    applicability: str = Field(
        description="Text description identifying to what type of "
        "information this assembly applies, such as an online transcript "
        "of a video meeting. This information may be used by knowledge "
        "service for document-assembly matching"
    )

    jsonschema: Mapping[str, Any] = Field(
        description="JSON Schema defining the structure of data to be "
        "extracted for this assembly"
    )

    # AssemblySpecification configuration
    status: AssemblySpecificationStatus = AssemblySpecificationStatus.ACTIVE
    knowledge_service_queries: Mapping[str, str] = Field(
        default_factory=dict,
        description="Mapping from JSON Pointer paths to "
        "KnowledgeServiceQuery IDs. Keys are JSON Pointer strings "
        "(e.g., '/properties/attendees', '') and values are query IDs "
        "for extracting data for that schema section",
    )

    # AssemblySpecification metadata
    version: str = Field(default="0.1.0", description="Assembly definition version")
    created_at: datetime | None = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = Field(default_factory=lambda: datetime.now(UTC))
    # May later add a detailed description, change log, additional metadata
    # Timestamps

    @field_validator("assembly_specification_id")
    @classmethod
    def assembly_specification_id_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("AssemblySpecification ID cannot be empty")
        return v.strip()

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("AssemblySpecification name cannot be empty")
        return v.strip()

    @field_validator("applicability")
    @classmethod
    def applicability_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("AssemblySpecification applicability cannot be empty")
        return v.strip()

    @field_validator("jsonschema")
    @classmethod
    def jsonschema_must_be_valid(cls, v: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(v, dict):
            raise ValueError("JSON Schema must be a dictionary")

        if len(v) == 1 and "$ref" in v:
            # Bare $ref — accept as-is. Resolution and schema validation
            # happen at assembly time via RemoteSchemaRepository, not here.
            if not isinstance(v["$ref"], str) or not v["$ref"].strip():
                raise ValueError("$ref value must be a non-empty string")
            return v

        if "type" not in v:
            raise ValueError("JSON Schema must have a 'type' field")

        try:
            jsonschema.Draft7Validator.check_schema(v)
        except jsonschema.SchemaError as e:
            raise ValueError(f"Invalid JSON Schema: {e.message}")

        return v

    @field_validator("knowledge_service_queries")
    @classmethod
    def knowledge_service_queries_must_be_valid(
        cls, v: dict[str, str], info: Any
    ) -> dict[str, str]:
        if not isinstance(v, dict):
            raise ValueError("Knowledge service queries must be a dictionary")

        # Get the jsonschema field value to validate pointers against it
        jsonschema_value = info.data.get("jsonschema")
        if not jsonschema_value:
            raise ValueError("Cannot validate schema pointers without jsonschema field")

        is_ref_schema = (
            isinstance(jsonschema_value, dict)
            and len(jsonschema_value) == 1
            and "$ref" in jsonschema_value
        )

        cleaned_queries = {}
        for schema_pointer, query_id in v.items():
            # Validate schema pointer keys are strings
            if not isinstance(schema_pointer, str):
                raise ValueError("Schema pointer keys must be strings")

            # Validate JSON Pointer format; existence against the resolved
            # schema is only possible for inline schemas (not bare $refs —
            # those are resolved at assembly time via RemoteSchemaRepository).
            try:
                if schema_pointer == "":
                    # Empty string is valid - refers to root of schema
                    pass
                elif is_ref_schema:
                    # Format validation only — can't check existence without
                    # fetching the remote schema
                    jsonpointer.JsonPointer(schema_pointer)
                else:
                    ptr = jsonpointer.JsonPointer(schema_pointer)
                    ptr.resolve(jsonschema_value)
            except jsonpointer.JsonPointerException as e:
                raise ValueError(f"Invalid JSON Pointer '{schema_pointer}': {e}")
            except (KeyError, IndexError, TypeError):
                raise ValueError(
                    f"JSON Pointer '{schema_pointer}' does not exist in schema"
                )

            # Validate query ID values
            if not isinstance(query_id, str) or not query_id.strip():
                raise ValueError("Query ID values must be non-empty strings")

            cleaned_queries[schema_pointer] = query_id.strip()

        return cleaned_queries

    @field_validator("version")
    @classmethod
    def version_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("AssemblySpecification version cannot be empty")
        return v.strip()
