"""Tests for UNTP use cases.

Tests projection and emission use cases with memory repositories.
"""

from datetime import datetime, timezone

import pytest

from julee.contrib.untp.entities.core import Identifier, Organization
from julee.contrib.untp.entities.credential import (
    ConformityAssessment,
    DCCSubject,
    DigitalConformityCredential,
    DigitalProductPassport,
    DigitalTraceabilityEvent,
    DPPSubject,
    DTESubject,
)
from julee.contrib.untp.infrastructure.repositories.memory.credential import (
    MemoryConformityCredentialRepository,
    MemoryCredentialRepository,
    MemoryProductPassportRepository,
    MemoryTraceabilityEventRepository,
)
from julee.contrib.untp.infrastructure.repositories.memory.projection import (
    MemoryProjectionMappingRepository,
)
from julee.contrib.untp.infrastructure.services.signing.unsigned import (
    MockSignedCredentialService,
    UnsignedCredentialService,
)


class TestMemoryCredentialRepository:
    """Tests for MemoryCredentialRepository."""

    @pytest.fixture
    def repo(self):
        return MemoryCredentialRepository()

    @pytest.fixture
    def sample_issuer(self):
        return Organization(
            id=Identifier(scheme="did", value="did:web:issuer.example.com"),
            name="Test Issuer",
        )

    @pytest.fixture
    def sample_dte(self, sample_issuer):
        return DigitalTraceabilityEvent(
            id="urn:uuid:dte-001",
            credential_type=["VerifiableCredential", "DigitalTraceabilityEvent"],
            issuer=sample_issuer,
            valid_from=datetime.now(timezone.utc),
            credential_subject=DTESubject(
                event_id="evt-001",
                event_type="TransformationEvent",
                event_time=datetime.now(timezone.utc),
            ),
        )

    @pytest.mark.asyncio
    async def test_save_and_get(self, repo, sample_dte):
        """Can save and retrieve a credential."""
        await repo.save(sample_dte)
        retrieved = await repo.get(sample_dte.id)
        assert retrieved is not None
        assert retrieved.id == sample_dte.id

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, repo):
        """Getting nonexistent credential returns None."""
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_all(self, repo, sample_dte):
        """Can list all credentials."""
        await repo.save(sample_dte)
        all_creds = await repo.list_all()
        assert len(all_creds) == 1
        assert all_creds[0].id == sample_dte.id

    @pytest.mark.asyncio
    async def test_delete(self, repo, sample_dte):
        """Can delete a credential."""
        await repo.save(sample_dte)
        deleted = await repo.delete(sample_dte.id)
        assert deleted is True
        assert await repo.get(sample_dte.id) is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, repo):
        """Deleting nonexistent credential returns False."""
        deleted = await repo.delete("nonexistent")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_get_by_type(self, repo, sample_dte):
        """Can filter credentials by type."""
        await repo.save(sample_dte)
        results = await repo.get_by_type("DigitalTraceabilityEvent")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_by_issuer(self, repo, sample_dte):
        """Can filter credentials by issuer."""
        await repo.save(sample_dte)
        results = await repo.get_by_issuer("did:web:issuer.example.com")
        assert len(results) == 1


class TestMemoryTraceabilityEventRepository:
    """Tests for MemoryTraceabilityEventRepository."""

    @pytest.fixture
    def repo(self):
        return MemoryTraceabilityEventRepository()

    @pytest.fixture
    def sample_issuer(self):
        return Organization(
            id=Identifier(scheme="did", value="did:web:issuer.example.com"),
            name="Test Issuer",
        )

    @pytest.fixture
    def sample_dte(self, sample_issuer):
        return DigitalTraceabilityEvent(
            id="urn:uuid:dte-001",
            credential_type=["VerifiableCredential", "DigitalTraceabilityEvent"],
            issuer=sample_issuer,
            valid_from=datetime.now(timezone.utc),
            credential_subject=DTESubject(
                event_id="evt-001",
                event_type="TransformationEvent",
                event_time=datetime.now(timezone.utc),
                event_data={"operation_id": "op-123"},
            ),
        )

    @pytest.mark.asyncio
    async def test_save_with_execution_id(self, repo, sample_dte):
        """Can save with execution_id for indexing."""
        await repo.save(sample_dte, execution_id="exec-001")
        results = await repo.get_by_execution_id("exec-001")
        assert len(results) == 1
        assert results[0].id == sample_dte.id

    @pytest.mark.asyncio
    async def test_get_by_operation_id(self, repo, sample_dte):
        """Can retrieve by operation_id from event_data."""
        await repo.save(sample_dte)
        result = await repo.get_by_operation_id("op-123")
        assert result is not None
        assert result.id == sample_dte.id


class TestMemoryProductPassportRepository:
    """Tests for MemoryProductPassportRepository."""

    @pytest.fixture
    def repo(self):
        return MemoryProductPassportRepository()

    @pytest.fixture
    def sample_issuer(self):
        return Organization(
            id=Identifier(scheme="did", value="did:web:issuer.example.com"),
            name="Test Issuer",
        )

    @pytest.fixture
    def sample_manufacturer(self):
        return Organization(
            id=Identifier(scheme="lei", value="5493001KJTIIGC8Y1R12"),
            name="Test Manufacturer",
        )

    @pytest.fixture
    def sample_dpp(self, sample_issuer, sample_manufacturer):
        return DigitalProductPassport(
            id="urn:uuid:dpp-001",
            credential_type=["VerifiableCredential", "DigitalProductPassport"],
            issuer=sample_issuer,
            valid_from=datetime.now(timezone.utc),
            credential_subject=DPPSubject(
                id=Identifier(scheme="gtin", value="01234567890123"),
                name="Test Product",
                manufacturer=sample_manufacturer,
            ),
        )

    @pytest.mark.asyncio
    async def test_get_by_product_id(self, repo, sample_dpp):
        """Can retrieve by product identifier."""
        await repo.save(sample_dpp)
        result = await repo.get_by_product_id("01234567890123")
        assert result is not None
        assert result.id == sample_dpp.id

    @pytest.mark.asyncio
    async def test_get_by_manufacturer(self, repo, sample_dpp):
        """Can list passports by manufacturer."""
        await repo.save(sample_dpp)
        results = await repo.get_by_manufacturer("5493001KJTIIGC8Y1R12")
        assert len(results) == 1


class TestMemoryConformityCredentialRepository:
    """Tests for MemoryConformityCredentialRepository."""

    @pytest.fixture
    def repo(self):
        return MemoryConformityCredentialRepository()

    @pytest.fixture
    def sample_issuer(self):
        return Organization(
            id=Identifier(scheme="did", value="did:web:certifier.example.com"),
            name="Test Certifier",
        )

    @pytest.fixture
    def sample_dcc(self, sample_issuer):
        return DigitalConformityCredential(
            id="urn:uuid:dcc-001",
            credential_type=["VerifiableCredential", "DigitalConformityCredential"],
            issuer=sample_issuer,
            valid_from=datetime.now(timezone.utc),
            credential_subject=DCCSubject(
                assessed_entity=Identifier(scheme="gtin", value="product-001"),
                assessed_entity_type="product",
                assessments=[
                    ConformityAssessment(
                        assessment_type="certification",
                        standard="ISO-14001",
                        result="pass",
                        assessed_date=datetime.now(timezone.utc),
                    ),
                ],
            ),
        )

    @pytest.mark.asyncio
    async def test_get_by_assessed_entity(self, repo, sample_dcc):
        """Can retrieve by assessed entity identifier."""
        await repo.save(sample_dcc)
        results = await repo.get_by_assessed_entity("product-001")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_by_standard(self, repo, sample_dcc):
        """Can retrieve by standard identifier."""
        await repo.save(sample_dcc)
        results = await repo.get_by_standard("ISO-14001")
        assert len(results) == 1


class TestUnsignedCredentialService:
    """Tests for UnsignedCredentialService (no-op signing)."""

    @pytest.fixture
    def service(self):
        return UnsignedCredentialService()

    @pytest.fixture
    def sample_issuer(self):
        return Organization(
            id=Identifier(scheme="did", value="did:web:issuer.example.com"),
            name="Test Issuer",
        )

    @pytest.fixture
    def sample_dte(self, sample_issuer):
        return DigitalTraceabilityEvent(
            id="urn:uuid:dte-001",
            credential_type=["VerifiableCredential", "DigitalTraceabilityEvent"],
            issuer=sample_issuer,
            valid_from=datetime.now(timezone.utc),
            credential_subject=DTESubject(
                event_id="evt-001",
                event_type="TransformationEvent",
                event_time=datetime.now(timezone.utc),
            ),
        )

    @pytest.mark.asyncio
    async def test_sign_returns_unchanged(self, service, sample_dte):
        """Sign returns credential unchanged (no-op)."""
        signed = await service.sign(sample_dte)
        assert signed.id == sample_dte.id
        assert signed.proof is None  # No proof added

    @pytest.mark.asyncio
    async def test_verify_always_true(self, service, sample_dte):
        """Verify always returns True."""
        result = await service.verify(sample_dte)
        assert result is True


class TestMockSignedCredentialService:
    """Tests for MockSignedCredentialService (fake signing for testing)."""

    @pytest.fixture
    def service(self):
        return MockSignedCredentialService()

    @pytest.fixture
    def sample_issuer(self):
        return Organization(
            id=Identifier(scheme="did", value="did:web:issuer.example.com"),
            name="Test Issuer",
        )

    @pytest.fixture
    def sample_dte(self, sample_issuer):
        return DigitalTraceabilityEvent(
            id="urn:uuid:dte-001",
            credential_type=["VerifiableCredential", "DigitalTraceabilityEvent"],
            issuer=sample_issuer,
            valid_from=datetime.now(timezone.utc),
            credential_subject=DTESubject(
                event_id="evt-001",
                event_type="TransformationEvent",
                event_time=datetime.now(timezone.utc),
            ),
        )

    @pytest.mark.asyncio
    async def test_sign_adds_mock_proof(self, service, sample_dte):
        """Sign adds a mock proof to the credential."""
        signed = await service.sign(sample_dte)
        assert signed.proof is not None
        assert signed.proof.proof_type == "DataIntegrityProof"
        assert signed.proof.proof_value == "mock-signature-for-testing"

    @pytest.mark.asyncio
    async def test_verify_signed_credential(self, service, sample_dte):
        """Verify returns True for mock-signed credentials."""
        signed = await service.sign(sample_dte)
        result = await service.verify(signed)
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_unsigned_credential(self, service, sample_dte):
        """Verify returns False for unsigned credentials."""
        result = await service.verify(sample_dte)
        assert result is False


class TestProjectionMappingRepository:
    """Tests for MemoryProjectionMappingRepository."""

    @pytest.fixture
    def repo(self):
        return MemoryProjectionMappingRepository()

    @pytest.mark.asyncio
    async def test_empty_repository(self, repo):
        """Empty repository returns empty list."""
        all_mappings = await repo.list_all()
        assert all_mappings == []

    @pytest.mark.asyncio
    async def test_list_slugs(self, repo):
        """List slugs returns all mapping IDs."""
        slugs = await repo.list_slugs()
        assert slugs == set()
