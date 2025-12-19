"""Tests for DynamicStep domain model."""

import pytest
from pydantic import ValidationError

from julee.docs.sphinx_c4.domain.models.dynamic_step import DynamicStep
from julee.docs.sphinx_c4.domain.models.relationship import ElementType


class TestDynamicStepCreation:
    """Test DynamicStep model creation and validation."""

    def test_create_with_required_fields(self) -> None:
        """Test creating a step with minimum required fields."""
        step = DynamicStep(
            slug="login-step-1",
            sequence_name="user-login",
            step_number=1,
            source_type=ElementType.PERSON,
            source_slug="customer",
            destination_type=ElementType.CONTAINER,
            destination_slug="web-app",
        )

        assert step.slug == "login-step-1"
        assert step.sequence_name == "user-login"
        assert step.step_number == 1
        assert step.source_type == ElementType.PERSON
        assert step.source_slug == "customer"
        assert step.description == ""
        assert step.is_async is False

    def test_create_with_all_fields(self) -> None:
        """Test creating a step with all fields."""
        step = DynamicStep(
            slug="login-step-1",
            sequence_name="user-login",
            step_number=1,
            source_type=ElementType.PERSON,
            source_slug="customer",
            destination_type=ElementType.CONTAINER,
            destination_slug="web-app",
            description="Submits login credentials",
            technology="HTTPS",
            return_value="JWT token",
            is_async=False,
            docname="architecture/sequences",
        )

        assert step.description == "Submits login credentials"
        assert step.technology == "HTTPS"
        assert step.return_value == "JWT token"

    def test_empty_slug_raises_error(self) -> None:
        """Test that empty slug raises validation error."""
        with pytest.raises(ValidationError, match="slug cannot be empty"):
            DynamicStep(
                slug="",
                sequence_name="test",
                step_number=1,
                source_type=ElementType.PERSON,
                source_slug="customer",
                destination_type=ElementType.CONTAINER,
                destination_slug="app",
            )

    def test_empty_sequence_name_raises_error(self) -> None:
        """Test that empty sequence_name raises validation error."""
        with pytest.raises(ValidationError, match="sequence_name cannot be empty"):
            DynamicStep(
                slug="test",
                sequence_name="",
                step_number=1,
                source_type=ElementType.PERSON,
                source_slug="customer",
                destination_type=ElementType.CONTAINER,
                destination_slug="app",
            )

    def test_zero_step_number_raises_error(self) -> None:
        """Test that step_number < 1 raises validation error."""
        with pytest.raises(ValidationError, match="step_number must be >= 1"):
            DynamicStep(
                slug="test",
                sequence_name="test",
                step_number=0,
                source_type=ElementType.PERSON,
                source_slug="customer",
                destination_type=ElementType.CONTAINER,
                destination_slug="app",
            )

    def test_negative_step_number_raises_error(self) -> None:
        """Test that negative step_number raises validation error."""
        with pytest.raises(ValidationError, match="step_number must be >= 1"):
            DynamicStep(
                slug="test",
                sequence_name="test",
                step_number=-1,
                source_type=ElementType.PERSON,
                source_slug="customer",
                destination_type=ElementType.CONTAINER,
                destination_slug="app",
            )

    def test_empty_source_slug_raises_error(self) -> None:
        """Test that empty source_slug raises validation error."""
        with pytest.raises(ValidationError, match="source_slug cannot be empty"):
            DynamicStep(
                slug="test",
                sequence_name="test",
                step_number=1,
                source_type=ElementType.PERSON,
                source_slug="",
                destination_type=ElementType.CONTAINER,
                destination_slug="app",
            )

    def test_empty_destination_slug_raises_error(self) -> None:
        """Test that empty destination_slug raises validation error."""
        with pytest.raises(ValidationError, match="destination_slug cannot be empty"):
            DynamicStep(
                slug="test",
                sequence_name="test",
                step_number=1,
                source_type=ElementType.PERSON,
                source_slug="customer",
                destination_type=ElementType.CONTAINER,
                destination_slug="",
            )


class TestDynamicStepProperties:
    """Test dynamic step properties."""

    @pytest.fixture
    def sample_step(self) -> DynamicStep:
        """Create a sample step for testing."""
        return DynamicStep(
            slug="login-step-1",
            sequence_name="user-login",
            step_number=1,
            source_type=ElementType.PERSON,
            source_slug="customer",
            destination_type=ElementType.CONTAINER,
            destination_slug="web-app",
            description="Submits credentials",
            technology="HTTPS",
        )

    def test_step_label(self, sample_step: DynamicStep) -> None:
        """Test step_label format."""
        assert sample_step.step_label == "1. "

    def test_full_label_without_technology(self) -> None:
        """Test full_label without technology."""
        step = DynamicStep(
            slug="test",
            sequence_name="test",
            step_number=2,
            source_type=ElementType.CONTAINER,
            source_slug="api",
            destination_type=ElementType.CONTAINER,
            destination_slug="db",
            description="Queries data",
        )
        assert step.full_label == "2. Queries data"

    def test_full_label_with_technology(self, sample_step: DynamicStep) -> None:
        """Test full_label with technology."""
        assert sample_step.full_label == "1. Submits credentials [HTTPS]"

    def test_is_person_interaction_source(self, sample_step: DynamicStep) -> None:
        """Test is_person_interaction when source is person."""
        assert sample_step.is_person_interaction is True

    def test_is_person_interaction_destination(self) -> None:
        """Test is_person_interaction when destination is person."""
        step = DynamicStep(
            slug="test",
            sequence_name="test",
            step_number=1,
            source_type=ElementType.CONTAINER,
            source_slug="app",
            destination_type=ElementType.PERSON,
            destination_slug="admin",
        )
        assert step.is_person_interaction is True

    def test_is_person_interaction_false(self) -> None:
        """Test is_person_interaction when no person involved."""
        step = DynamicStep(
            slug="test",
            sequence_name="test",
            step_number=1,
            source_type=ElementType.CONTAINER,
            source_slug="api",
            destination_type=ElementType.CONTAINER,
            destination_slug="db",
        )
        assert step.is_person_interaction is False


class TestDynamicStepSlugGeneration:
    """Test slug generation class method."""

    def test_generate_slug(self) -> None:
        """Test slug generation from sequence and step."""
        slug = DynamicStep.generate_slug("User Login", 1)
        assert slug == "user-login-step-1"

    def test_generate_slug_special_chars(self) -> None:
        """Test slug generation handles special characters."""
        slug = DynamicStep.generate_slug("Order Processing & Fulfillment", 5)
        assert slug == "order-processing-fulfillment-step-5"


class TestDynamicStepInvolvesElement:
    """Test involves_element method."""

    @pytest.fixture
    def sample_step(self) -> DynamicStep:
        """Create a sample step for testing."""
        return DynamicStep(
            slug="test",
            sequence_name="test",
            step_number=1,
            source_type=ElementType.CONTAINER,
            source_slug="api-app",
            destination_type=ElementType.CONTAINER,
            destination_slug="database",
        )

    def test_involves_element_source(self, sample_step: DynamicStep) -> None:
        """Test involves_element for source element."""
        assert sample_step.involves_element(ElementType.CONTAINER, "api-app") is True

    def test_involves_element_destination(self, sample_step: DynamicStep) -> None:
        """Test involves_element for destination element."""
        assert (
            sample_step.involves_element(ElementType.CONTAINER, "database") is True
        )

    def test_involves_element_not_involved(self, sample_step: DynamicStep) -> None:
        """Test involves_element for element not in step."""
        assert (
            sample_step.involves_element(ElementType.CONTAINER, "other") is False
        )

    def test_involves_element_wrong_type(self, sample_step: DynamicStep) -> None:
        """Test involves_element with wrong element type."""
        assert (
            sample_step.involves_element(ElementType.COMPONENT, "api-app") is False
        )
