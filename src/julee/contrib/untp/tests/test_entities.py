"""Tests for UNTP entity definitions.

Verifies that UNTP entities can be instantiated, are immutable,
and have correct semantic relations.
"""

from datetime import datetime, timezone

import pytest

from julee.contrib.untp.entities.core import (
    Identifier,
    Organization,
    SecureLink,
)
from julee.contrib.untp.entities.credential import (
    Claim,
    DigitalConformityCredential,
    DigitalFacilityRecord,
    DigitalIdentityAttestation,
    DigitalProductPassport,
    DigitalTraceabilityEvent,
    DPPSubject,
    DTESubject,
    ProductCharacteristic,
)
from julee.contrib.untp.entities.event import (
    AggregationEvent,
    EventAction,
    EventDisposition,
    ObjectEvent,
    TransformationEvent,
)
from julee.core.decorators import get_semantic_relations
from julee.core.entities.semantic_relation import RelationType


class TestCoreEntities:
    """Tests for core UNTP entities."""

    def test_identifier_creation(self):
        """Identifier can be created with scheme and value."""
        id = Identifier(scheme="gtin", value="01234567890123")
        assert id.scheme == "gtin"
        assert id.value == "01234567890123"
        assert id.uri is None

    def test_identifier_with_uri(self):
        """Identifier can include a URI."""
        id = Identifier(
            scheme="did",
            value="did:web:example.com",
            uri="https://example.com/.well-known/did.json",
        )
        assert id.uri == "https://example.com/.well-known/did.json"

    def test_organization_creation(self):
        """Organization can be created with id and name."""
        org = Organization(
            id=Identifier(scheme="lei", value="5493001KJTIIGC8Y1R12"),
            name="Example Corp",
            country="AU",
        )
        assert org.name == "Example Corp"
        assert org.id.scheme == "lei"
        assert org.country == "AU"

    def test_secure_link_creation(self):
        """SecureLink can be created with target and type."""
        link = SecureLink(
            target="https://example.com/credential.json",
            link_type="conformity-credential",
            hash_method="sha256",
            hash_value="abc123",
        )
        assert link.target == "https://example.com/credential.json"
        assert link.link_type == "conformity-credential"


class TestCredentialEntities:
    """Tests for UNTP credential entities."""

    @pytest.fixture
    def sample_issuer(self):
        """Sample issuer organization."""
        return Organization(
            id=Identifier(scheme="did", value="did:web:issuer.example.com"),
            name="Test Issuer",
        )

    @pytest.fixture
    def sample_manufacturer(self):
        """Sample manufacturer organization."""
        return Organization(
            id=Identifier(scheme="lei", value="5493001KJTIIGC8Y1R12"),
            name="Test Manufacturer",
        )

    def test_digital_product_passport_creation(
        self, sample_issuer, sample_manufacturer
    ):
        """DigitalProductPassport can be created."""
        dpp = DigitalProductPassport(
            id="urn:uuid:12345678-1234-1234-1234-123456789abc",
            credential_type=["VerifiableCredential", "DigitalProductPassport"],
            issuer=sample_issuer,
            valid_from=datetime.now(timezone.utc),
            credential_subject=DPPSubject(
                id=Identifier(scheme="gtin", value="01234567890123"),
                name="Test Product",
                manufacturer=sample_manufacturer,
            ),
        )
        assert dpp.id == "urn:uuid:12345678-1234-1234-1234-123456789abc"
        assert dpp.credential_subject.name == "Test Product"

    def test_product_characteristic(self):
        """ProductCharacteristic can be created."""
        char = ProductCharacteristic(
            name="weight",
            value=1.5,
            unit="kg",
        )
        assert char.name == "weight"
        assert char.value == 1.5
        assert char.unit == "kg"

    def test_claim_with_evidence(self):
        """Claim can include evidence links."""
        claim = Claim(
            claim_type="carbon-footprint",
            claim_value="10kg CO2e",
            evidence=[
                SecureLink(
                    target="https://example.com/dcc.json",
                    link_type="conformity-credential",
                )
            ],
        )
        assert claim.claim_type == "carbon-footprint"
        assert len(claim.evidence) == 1

    def test_digital_traceability_event_creation(self, sample_issuer):
        """DigitalTraceabilityEvent can be created."""
        dte = DigitalTraceabilityEvent(
            id="urn:uuid:event-123",
            credential_type=["VerifiableCredential", "DigitalTraceabilityEvent"],
            issuer=sample_issuer,
            valid_from=datetime.now(timezone.utc),
            credential_subject=DTESubject(
                event_id="evt-001",
                event_type="TransformationEvent",
                event_time=datetime.now(timezone.utc),
            ),
        )
        assert dte.credential_subject.event_id == "evt-001"
        assert dte.credential_subject.event_type == "TransformationEvent"


class TestEventEntities:
    """Tests for UNTP event entities."""

    def test_transformation_event_creation(self):
        """TransformationEvent can be created."""
        event = TransformationEvent(
            event_id="evt-001",
            event_time=datetime.now(timezone.utc),
            input_items=[Identifier(scheme="gtin", value="input-123")],
            output_items=[Identifier(scheme="gtin", value="output-456")],
            transformation_type="manufacturing",
        )
        assert event.event_id == "evt-001"
        assert len(event.input_items) == 1
        assert len(event.output_items) == 1

    def test_transformation_event_from_operation(self):
        """TransformationEvent can be created from operation."""
        event = TransformationEvent.from_operation(
            operation_id="op-123",
            event_time=datetime.now(timezone.utc),
            transformation_type="assembly",
        )
        assert event.event_id == "evt-op-123"
        assert event.operation_id == "op-123"
        assert event.transformation_type == "assembly"

    def test_object_event_creation(self):
        """ObjectEvent can be created."""
        event = ObjectEvent(
            event_id="evt-002",
            event_time=datetime.now(timezone.utc),
            action=EventAction.OBSERVE,
            items=[Identifier(scheme="gtin", value="item-123")],
            disposition=EventDisposition.ACTIVE,
        )
        assert event.action == EventAction.OBSERVE
        assert event.disposition == EventDisposition.ACTIVE

    def test_aggregation_event_creation(self):
        """AggregationEvent can be created."""
        event = AggregationEvent(
            event_id="evt-003",
            event_time=datetime.now(timezone.utc),
            action=EventAction.ADD,
            parent_id=Identifier(scheme="sscc", value="pallet-001"),
            child_items=[
                Identifier(scheme="gtin", value="item-001"),
                Identifier(scheme="gtin", value="item-002"),
            ],
        )
        assert event.action == EventAction.ADD
        assert len(event.child_items) == 2


class TestEntityImmutability:
    """Tests that entities are frozen (immutable)."""

    def test_identifier_is_frozen(self):
        """Identifier is immutable."""
        from pydantic import ValidationError

        id = Identifier(scheme="gtin", value="123")
        with pytest.raises(ValidationError):
            id.value = "456"

    def test_organization_is_frozen(self):
        """Organization is immutable."""
        from pydantic import ValidationError

        org = Organization(
            id=Identifier(scheme="lei", value="123"),
            name="Test",
        )
        with pytest.raises(ValidationError):
            org.name = "Changed"


class TestSemanticRelations:
    """Tests for semantic relations on credential entities."""

    def test_dte_projects_operation_record(self):
        """DigitalTraceabilityEvent declares PROJECTS relation to OperationRecord."""
        relations = get_semantic_relations(DigitalTraceabilityEvent)
        assert len(relations) >= 1
        projects_relations = [
            r for r in relations if r.relation_type == RelationType.PROJECTS
        ]
        assert len(projects_relations) >= 1
        # Check target is OperationRecord
        target_names = [r.target_type.__name__ for r in projects_relations]
        assert "OperationRecord" in target_names

    def test_dpp_projects_pipeline_output(self):
        """DigitalProductPassport declares PROJECTS relation to PipelineOutput."""
        relations = get_semantic_relations(DigitalProductPassport)
        assert len(relations) >= 1
        projects_relations = [
            r for r in relations if r.relation_type == RelationType.PROJECTS
        ]
        assert len(projects_relations) >= 1
        # Check target is PipelineOutput
        target_names = [r.target_type.__name__ for r in projects_relations]
        assert "PipelineOutput" in target_names

    def test_dcc_projects_operation_record(self):
        """DigitalConformityCredential declares PROJECTS relation to OperationRecord."""
        relations = get_semantic_relations(DigitalConformityCredential)
        assert len(relations) >= 1
        projects_relations = [
            r for r in relations if r.relation_type == RelationType.PROJECTS
        ]
        assert len(projects_relations) >= 1
        # Check target is OperationRecord
        target_names = [r.target_type.__name__ for r in projects_relations]
        assert "OperationRecord" in target_names

    def test_dfr_projects_party(self):
        """DigitalFacilityRecord declares PROJECTS relation to Party."""

        relations = get_semantic_relations(DigitalFacilityRecord)
        assert len(relations) >= 1
        projects_relations = [
            r for r in relations if r.relation_type == RelationType.PROJECTS
        ]
        assert len(projects_relations) >= 1
        # Check target is Party
        target_names = [r.target_type.__name__ for r in projects_relations]
        assert "Party" in target_names

    def test_dia_projects_party(self):
        """DigitalIdentityAttestation declares PROJECTS relation to Party."""

        relations = get_semantic_relations(DigitalIdentityAttestation)
        assert len(relations) >= 1
        projects_relations = [
            r for r in relations if r.relation_type == RelationType.PROJECTS
        ]
        assert len(projects_relations) >= 1
        # Check target is Party
        target_names = [r.target_type.__name__ for r in projects_relations]
        assert "Party" in target_names
