"""CredentialRepository protocol.

Defines the interface for UNTP credential storage.
Credentials are stored after projection and signing.
"""

from datetime import datetime
from typing import Protocol, runtime_checkable

from julee.core.repositories.base import BaseRepository
from julee.contrib.untp.entities.credential import (
    BaseCredential,
    DigitalConformityCredential,
    DigitalProductPassport,
    DigitalTraceabilityEvent,
)


@runtime_checkable
class CredentialRepository(BaseRepository[BaseCredential], Protocol):
    """Repository protocol for UNTP credentials.

    Extends BaseRepository with credential-specific query methods.
    Supports all credential types (DPP, DCC, DFR, DTE, DIA) through
    the common BaseCredential interface.

    Note: Credentials are typically projected (not manually created),
    so this repository is primarily read-oriented. Create operations
    are handled by projection use cases.
    """

    async def get_by_issuer(self, issuer_id: str) -> list[BaseCredential]:
        """Get all credentials issued by a specific organization.

        Args:
            issuer_id: Identifier value of the issuer organization

        Returns:
            List of credentials issued by this organization
        """
        ...

    async def get_by_type(self, credential_type: str) -> list[BaseCredential]:
        """Get all credentials of a specific type.

        Args:
            credential_type: Credential type (e.g., 'DigitalProductPassport')

        Returns:
            List of credentials of this type
        """
        ...

    async def get_valid_at(self, timestamp: datetime) -> list[BaseCredential]:
        """Get credentials valid at a specific timestamp.

        Args:
            timestamp: Point in time to check validity

        Returns:
            List of credentials valid at this timestamp
        """
        ...

    async def get_by_subject_id(self, subject_id: str) -> list[BaseCredential]:
        """Get credentials for a specific subject.

        Args:
            subject_id: Identifier of the credential subject

        Returns:
            List of credentials about this subject
        """
        ...

    async def list_filtered(
        self,
        issuer_id: str | None = None,
        credential_type: str | None = None,
        valid_at: datetime | None = None,
    ) -> list[BaseCredential]:
        """List credentials matching filters.

        Args:
            issuer_id: Filter by issuer organization
            credential_type: Filter by credential type
            valid_at: Filter to credentials valid at this timestamp

        Returns:
            List of credentials matching all provided filters
        """
        ...


@runtime_checkable
class TraceabilityEventRepository(BaseRepository[DigitalTraceabilityEvent], Protocol):
    """Repository protocol specifically for traceability events.

    Provides event-specific query methods for DTE credentials.
    """

    async def get_by_operation_id(
        self, operation_id: str
    ) -> DigitalTraceabilityEvent | None:
        """Get the event projected from a specific operation.

        Args:
            operation_id: ID of the source OperationRecord

        Returns:
            The projected event, or None if not found
        """
        ...

    async def get_by_execution_id(
        self, execution_id: str
    ) -> list[DigitalTraceabilityEvent]:
        """Get all events from a specific use case execution.

        Args:
            execution_id: ID of the UseCaseExecution

        Returns:
            List of events projected from this execution
        """
        ...

    async def get_events_for_subject(
        self, subject_id: str
    ) -> list[DigitalTraceabilityEvent]:
        """Get all traceability events involving a subject.

        Args:
            subject_id: Identifier of the subject (product, facility, etc.)

        Returns:
            List of events involving this subject
        """
        ...


@runtime_checkable
class ProductPassportRepository(BaseRepository[DigitalProductPassport], Protocol):
    """Repository protocol specifically for Digital Product Passports.

    Provides DPP-specific query methods.
    """

    async def get_by_product_id(self, product_id: str) -> DigitalProductPassport | None:
        """Get the passport for a specific product.

        Args:
            product_id: Product identifier

        Returns:
            The product passport, or None if not found
        """
        ...

    async def get_by_manufacturer(
        self, manufacturer_id: str
    ) -> list[DigitalProductPassport]:
        """Get all passports for products from a manufacturer.

        Args:
            manufacturer_id: Manufacturer organization identifier

        Returns:
            List of passports from this manufacturer
        """
        ...


@runtime_checkable
class ConformityCredentialRepository(
    BaseRepository[DigitalConformityCredential], Protocol
):
    """Repository protocol specifically for Digital Conformity Credentials.

    Provides DCC-specific query methods.
    """

    async def get_by_assessed_entity(
        self, entity_id: str
    ) -> list[DigitalConformityCredential]:
        """Get all conformity credentials for an assessed entity.

        Args:
            entity_id: Identifier of the assessed entity

        Returns:
            List of conformity credentials for this entity
        """
        ...

    async def get_by_standard(self, standard: str) -> list[DigitalConformityCredential]:
        """Get all conformity credentials for a specific standard.

        Args:
            standard: Standard or regulation name

        Returns:
            List of conformity credentials for this standard
        """
        ...
