"""In-memory credential repository implementations.

For testing and development. Not for production use.
"""

from datetime import datetime
from typing import Any

from julee.contrib.untp.entities.credential import (
    BaseCredential,
    DigitalConformityCredential,
    DigitalProductPassport,
    DigitalTraceabilityEvent,
)


class MemoryCredentialRepository:
    """In-memory repository for UNTP credentials.

    Implements the CredentialRepository protocol for testing and development.
    Stores all credential types in a single dictionary keyed by credential ID.
    """

    def __init__(self) -> None:
        self._credentials: dict[str, BaseCredential] = {}

    async def get(self, entity_id: str) -> BaseCredential | None:
        return self._credentials.get(entity_id)

    async def get_many(self, entity_ids: list[str]) -> dict[str, BaseCredential | None]:
        return {eid: self._credentials.get(eid) for eid in entity_ids}

    async def save(self, entity: BaseCredential) -> None:
        self._credentials[entity.id] = entity

    async def list_all(self) -> list[BaseCredential]:
        return list(self._credentials.values())

    async def list_filtered(
        self,
        issuer_id: str | None = None,
        credential_type: str | None = None,
        valid_at: datetime | None = None,
    ) -> list[BaseCredential]:
        results = list(self._credentials.values())

        if issuer_id is not None:
            results = [c for c in results if c.issuer.id.value == issuer_id]

        if credential_type is not None:
            results = [c for c in results if credential_type in c.credential_type]

        if valid_at is not None:
            results = [
                c
                for c in results
                if c.valid_from <= valid_at
                and (c.valid_until is None or c.valid_until >= valid_at)
            ]

        return results

    async def delete(self, entity_id: str) -> bool:
        if entity_id in self._credentials:
            del self._credentials[entity_id]
            return True
        return False

    async def clear(self) -> None:
        self._credentials.clear()

    async def list_slugs(self) -> set[str]:
        return set(self._credentials.keys())

    async def get_by_issuer(self, issuer_id: str) -> list[BaseCredential]:
        return [c for c in self._credentials.values() if c.issuer.id.value == issuer_id]

    async def get_by_type(self, credential_type: str) -> list[BaseCredential]:
        return [
            c for c in self._credentials.values() if credential_type in c.credential_type
        ]

    async def get_valid_at(self, timestamp: datetime) -> list[BaseCredential]:
        return [
            c
            for c in self._credentials.values()
            if c.valid_from <= timestamp
            and (c.valid_until is None or c.valid_until >= timestamp)
        ]

    async def get_by_subject_id(self, subject_id: str) -> list[BaseCredential]:
        results = []
        for c in self._credentials.values():
            subject = c.credential_subject
            # Check various subject ID patterns
            if hasattr(subject, "id"):
                if hasattr(subject.id, "value") and subject.id.value == subject_id:
                    results.append(c)
            if hasattr(subject, "event_id") and subject.event_id == subject_id:
                results.append(c)
        return results


class MemoryTraceabilityEventRepository:
    """In-memory repository specifically for traceability events.

    Implements the TraceabilityEventRepository protocol.
    """

    def __init__(self) -> None:
        self._events: dict[str, DigitalTraceabilityEvent] = {}
        self._by_operation: dict[str, str] = {}  # operation_id -> credential_id
        self._by_execution: dict[str, list[str]] = {}  # execution_id -> [credential_ids]

    async def get(self, entity_id: str) -> DigitalTraceabilityEvent | None:
        return self._events.get(entity_id)

    async def get_many(
        self, entity_ids: list[str]
    ) -> dict[str, DigitalTraceabilityEvent | None]:
        return {eid: self._events.get(eid) for eid in entity_ids}

    async def save(
        self, entity: DigitalTraceabilityEvent, execution_id: str | None = None
    ) -> None:
        self._events[entity.id] = entity

        # Index by operation_id if available in the credential subject
        subject = entity.credential_subject
        if hasattr(subject, "event_data") and "operation_id" in subject.event_data:
            op_id = subject.event_data["operation_id"]
            self._by_operation[op_id] = entity.id

        # Index by execution_id if provided
        if execution_id is not None:
            if execution_id not in self._by_execution:
                self._by_execution[execution_id] = []
            self._by_execution[execution_id].append(entity.id)

    async def list_all(self) -> list[DigitalTraceabilityEvent]:
        return list(self._events.values())

    async def list_filtered(self, **filters: Any) -> list[DigitalTraceabilityEvent]:
        return list(self._events.values())

    async def delete(self, entity_id: str) -> bool:
        if entity_id in self._events:
            del self._events[entity_id]
            return True
        return False

    async def clear(self) -> None:
        self._events.clear()
        self._by_operation.clear()
        self._by_execution.clear()

    async def list_slugs(self) -> set[str]:
        return set(self._events.keys())

    async def get_by_operation_id(
        self, operation_id: str
    ) -> DigitalTraceabilityEvent | None:
        credential_id = self._by_operation.get(operation_id)
        if credential_id is None:
            return None
        return self._events.get(credential_id)

    async def get_by_execution_id(
        self, execution_id: str
    ) -> list[DigitalTraceabilityEvent]:
        credential_ids = self._by_execution.get(execution_id, [])
        return [self._events[cid] for cid in credential_ids if cid in self._events]

    async def get_events_for_subject(
        self, subject_id: str
    ) -> list[DigitalTraceabilityEvent]:
        results = []
        for event in self._events.values():
            subject = event.credential_subject
            # Check if subject_id appears in event data or items
            if hasattr(subject, "event_data"):
                data = subject.event_data
                if subject_id in str(data):
                    results.append(event)
        return results


class MemoryProductPassportRepository:
    """In-memory repository specifically for Digital Product Passports.

    Implements the ProductPassportRepository protocol.
    """

    def __init__(self) -> None:
        self._passports: dict[str, DigitalProductPassport] = {}
        self._by_product: dict[str, str] = {}  # product_id -> credential_id
        self._by_manufacturer: dict[str, list[str]] = {}  # manufacturer_id -> [ids]

    async def get(self, entity_id: str) -> DigitalProductPassport | None:
        return self._passports.get(entity_id)

    async def get_many(
        self, entity_ids: list[str]
    ) -> dict[str, DigitalProductPassport | None]:
        return {eid: self._passports.get(eid) for eid in entity_ids}

    async def save(self, entity: DigitalProductPassport) -> None:
        self._passports[entity.id] = entity

        # Index by product_id
        product_id = entity.credential_subject.id.value
        self._by_product[product_id] = entity.id

        # Index by manufacturer
        manufacturer_id = entity.credential_subject.manufacturer.id.value
        if manufacturer_id not in self._by_manufacturer:
            self._by_manufacturer[manufacturer_id] = []
        if entity.id not in self._by_manufacturer[manufacturer_id]:
            self._by_manufacturer[manufacturer_id].append(entity.id)

    async def list_all(self) -> list[DigitalProductPassport]:
        return list(self._passports.values())

    async def list_filtered(self, **filters: Any) -> list[DigitalProductPassport]:
        return list(self._passports.values())

    async def delete(self, entity_id: str) -> bool:
        if entity_id in self._passports:
            del self._passports[entity_id]
            return True
        return False

    async def clear(self) -> None:
        self._passports.clear()
        self._by_product.clear()
        self._by_manufacturer.clear()

    async def list_slugs(self) -> set[str]:
        return set(self._passports.keys())

    async def get_by_product_id(self, product_id: str) -> DigitalProductPassport | None:
        credential_id = self._by_product.get(product_id)
        if credential_id is None:
            return None
        return self._passports.get(credential_id)

    async def get_by_manufacturer(
        self, manufacturer_id: str
    ) -> list[DigitalProductPassport]:
        credential_ids = self._by_manufacturer.get(manufacturer_id, [])
        return [
            self._passports[cid] for cid in credential_ids if cid in self._passports
        ]


class MemoryConformityCredentialRepository:
    """In-memory repository specifically for Digital Conformity Credentials.

    Implements the ConformityCredentialRepository protocol.
    """

    def __init__(self) -> None:
        self._credentials: dict[str, DigitalConformityCredential] = {}
        self._by_entity: dict[str, list[str]] = {}  # assessed_entity_id -> [ids]
        self._by_standard: dict[str, list[str]] = {}  # standard -> [ids]

    async def get(self, entity_id: str) -> DigitalConformityCredential | None:
        return self._credentials.get(entity_id)

    async def get_many(
        self, entity_ids: list[str]
    ) -> dict[str, DigitalConformityCredential | None]:
        return {eid: self._credentials.get(eid) for eid in entity_ids}

    async def save(self, entity: DigitalConformityCredential) -> None:
        self._credentials[entity.id] = entity

        # Index by assessed entity
        assessed_id = entity.credential_subject.assessed_entity.value
        if assessed_id not in self._by_entity:
            self._by_entity[assessed_id] = []
        if entity.id not in self._by_entity[assessed_id]:
            self._by_entity[assessed_id].append(entity.id)

        # Index by standard
        for assessment in entity.credential_subject.assessments:
            standard = assessment.standard
            if standard not in self._by_standard:
                self._by_standard[standard] = []
            if entity.id not in self._by_standard[standard]:
                self._by_standard[standard].append(entity.id)

    async def list_all(self) -> list[DigitalConformityCredential]:
        return list(self._credentials.values())

    async def list_filtered(self, **filters: Any) -> list[DigitalConformityCredential]:
        return list(self._credentials.values())

    async def delete(self, entity_id: str) -> bool:
        if entity_id in self._credentials:
            del self._credentials[entity_id]
            return True
        return False

    async def clear(self) -> None:
        self._credentials.clear()
        self._by_entity.clear()
        self._by_standard.clear()

    async def list_slugs(self) -> set[str]:
        return set(self._credentials.keys())

    async def get_by_assessed_entity(
        self, entity_id: str
    ) -> list[DigitalConformityCredential]:
        credential_ids = self._by_entity.get(entity_id, [])
        return [
            self._credentials[cid] for cid in credential_ids if cid in self._credentials
        ]

    async def get_by_standard(self, standard: str) -> list[DigitalConformityCredential]:
        credential_ids = self._by_standard.get(standard, [])
        return [
            self._credentials[cid] for cid in credential_ids if cid in self._credentials
        ]
