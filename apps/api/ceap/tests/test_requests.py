"""
Tests for API request models.

Since the request models delegate validation to domain models, these tests
focus on verifying the delegation works correctly and that the API-specific
behavior (like field copying and conversion methods) functions as expected.
"""


import pytest
from pydantic import ValidationError

from julee.contrib.ceap.entities import (
    AssemblySpecification,
    KnowledgeServiceQuery,
)
from julee.contrib.ceap.use_cases.crud import (
    CreateAssemblySpecificationRequest,
    CreateKnowledgeServiceQueryRequest,
)

pytestmark = pytest.mark.unit


class TestCreateAssemblySpecificationRequest:
    """Test CreateAssemblySpecificationRequest model."""

    def test_valid_request_creation(self) -> None:
        """Test that a valid request can be created."""
        request = CreateAssemblySpecificationRequest(
            name="Meeting Minutes",
            applicability="Online video meeting transcripts",
            jsonschema={
                "type": "object",
                "properties": {"title": {"type": "string"}},
            },
        )

        assert request.name == "Meeting Minutes"
        assert request.applicability == "Online video meeting transcripts"
        assert request.jsonschema == {
            "type": "object",
            "properties": {"title": {"type": "string"}},
        }
        assert request.knowledge_service_queries == {}  # Default empty dict
        assert request.version == "0.1.0"  # Default version

    def test_validation_delegation_to_domain_model(self) -> None:
        """Test that validation is properly delegated to domain model."""
        # Test that domain model validation errors are raised
        with pytest.raises(ValidationError) as err:
            CreateAssemblySpecificationRequest(
                name="",  # Invalid empty name
                applicability="Valid applicability",
                jsonschema={"type": "object"},
            )
        errors = err.value.errors()
        # Check that the error is for the 'name' field and is a value error
        assert any(
            e["loc"] == ("name",)
            and e["type"].startswith("value_error")
            and "name cannot be empty" in e["msg"]
            for e in errors
        )

        with pytest.raises(ValidationError) as err:
            CreateAssemblySpecificationRequest(
                name="Valid Name",
                applicability="Valid applicability",
                jsonschema={"invalid": "schema"},  # Missing 'type' field
            )
        errors = err.value.errors()
        # Check that the error is for the 'jsonschema' field
        assert any(
            e["loc"] == ("jsonschema",)
            and e["type"].startswith("value_error")
            and "type" in e["msg"]
            for e in errors
        )

    def test_field_definitions_match_domain_model(self) -> None:
        """Test that field definitions are copied from domain model."""
        request_fields = CreateAssemblySpecificationRequest.model_fields
        domain_fields = AssemblySpecification.model_fields

        # Verify shared fields have identical definitions
        shared_field_names = [
            "name",
            "applicability",
            "jsonschema",
            "knowledge_service_queries",
            "version",
        ]

        for field_name in shared_field_names:
            assert field_name in request_fields
            assert field_name in domain_fields
            # Field descriptions should match
            assert (
                request_fields[field_name].description
                == domain_fields[field_name].description
            )
            # Default values should match where applicable
            if (
                hasattr(domain_fields[field_name], "default")
                and domain_fields[field_name].default is not None
            ):
                assert (
                    request_fields[field_name].default
                    == domain_fields[field_name].default
                )


class TestCreateKnowledgeServiceQueryRequest:
    """Test CreateKnowledgeServiceQueryRequest model."""

    def test_valid_request_creation(self) -> None:
        """Test that a valid request can be created."""
        request = CreateKnowledgeServiceQueryRequest(
            name="Extract Meeting Summary",
            knowledge_service_id="anthropic-claude",
            prompt="Extract the main summary from this meeting transcript",
        )

        assert request.name == "Extract Meeting Summary"
        assert request.knowledge_service_id == "anthropic-claude"
        assert request.prompt == "Extract the main summary from this meeting transcript"
        assert request.query_metadata == {}  # Default empty dict
        assert request.assistant_prompt is None  # Default None

    def test_validation_delegation_to_domain_model(self) -> None:
        """Test that validation is properly delegated to domain model."""
        # Test that domain model validation errors are raised
        with pytest.raises(ValidationError) as err:
            CreateKnowledgeServiceQueryRequest(
                name="",  # Invalid empty name
                knowledge_service_id="valid-service",
                prompt="Valid prompt",
            )
        errors = err.value.errors()
        # Check that the error is for the 'name' field
        assert any(
            e["loc"] == ("name",)
            and e["type"].startswith("value_error")
            and "name cannot be empty" in e["msg"]
            for e in errors
        )

        with pytest.raises(ValidationError) as err:
            CreateKnowledgeServiceQueryRequest(
                name="Valid Name",
                knowledge_service_id="",  # Invalid empty service ID
                prompt="Valid prompt",
            )
        errors = err.value.errors()
        # Check that the error is for the 'knowledge_service_id' field
        assert any(
            e["loc"] == ("knowledge_service_id",)
            and e["type"].startswith("value_error")
            and "service ID cannot be empty" in e["msg"]
            for e in errors
        )

    def test_field_definitions_match_domain_model(self) -> None:
        """Test that field definitions are copied from domain model."""
        request_fields = CreateKnowledgeServiceQueryRequest.model_fields
        domain_fields = KnowledgeServiceQuery.model_fields

        # Verify shared fields have identical descriptions
        shared_field_names = [
            "name",
            "knowledge_service_id",
            "prompt",
            "query_metadata",
            "assistant_prompt",
        ]

        for field_name in shared_field_names:
            assert field_name in request_fields
            assert field_name in domain_fields
            # Field descriptions should match
            assert (
                request_fields[field_name].description
                == domain_fields[field_name].description
            )
            # Default values should match where applicable
            if (
                hasattr(domain_fields[field_name], "default")
                and domain_fields[field_name].default is not None
            ):
                assert (
                    request_fields[field_name].default
                    == domain_fields[field_name].default
                )
