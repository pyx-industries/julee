"""UNTP credential type definitions.

The five core UNTP credential types, all issued as W3C Verifiable Credentials:

- **DPP**: Digital Product Passport - product identity and sustainability
- **DCC**: Digital Conformity Credential - conformity attestations
- **DFR**: Digital Facility Record - facility information and compliance
- **DTE**: Digital Traceability Event - supply chain event records
- **DIA**: Digital Identity Attestation - organization identity verification

Each credential type declares a semantic relation to the core entity it projects:
- DTE PROJECTS OperationRecord (one event per operation within a use case)
- DPP PROJECTS PipelineOutput
- DCC PROJECTS validation/verification operations

.. seealso::

   `UNTP Specification <https://uncefact.github.io/spec-untp/docs/specification/>`_
       Complete specification for all credential types.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from julee.core.decorators import semantic_relation
from julee.core.entities.semantic_relation import RelationType

from julee.contrib.untp.entities.core import (
    CredentialProof,
    CredentialStatus,
    Identifier,
    Organization,
    SecureLink,
)


class CredentialType(str, Enum):
    """UNTP credential types."""

    DPP = "DigitalProductPassport"
    DCC = "DigitalConformityCredential"
    DFR = "DigitalFacilityRecord"
    DTE = "DigitalTraceabilityEvent"
    DIA = "DigitalIdentityAttestation"


class BaseCredential(BaseModel):
    """Base class for all UNTP credentials.

    Implements W3C Verifiable Credentials Data Model 2.0 structure with
    JSON-LD context, issuer, validity period, and cryptographic proof.

    .. seealso::

       `W3C VC Data Model 2.0 <https://www.w3.org/TR/vc-data-model-2.0/>`_
           Core verifiable credentials specification.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    context: list[str] = Field(
        default_factory=lambda: [
            "https://www.w3.org/ns/credentials/v2",
            "https://vocabulary.uncefact.org/untp/dpp/0.5.0/",
        ],
        alias="@context",
        description="JSON-LD context",
    )
    id: str = Field(
        ...,
        description="Credential URI",
    )
    credential_type: list[str] = Field(
        ...,
        alias="type",
        description="Credential types including VerifiableCredential",
    )
    issuer: Organization = Field(
        ...,
        description="Credential issuer",
    )
    valid_from: datetime = Field(
        ...,
        alias="validFrom",
        description="Credential validity start",
    )
    valid_until: datetime | None = Field(
        default=None,
        alias="validUntil",
        description="Credential expiry",
    )
    credential_status: CredentialStatus | None = Field(
        default=None,
        alias="credentialStatus",
        description="Revocation status information",
    )
    proof: CredentialProof | None = Field(
        default=None,
        description="Cryptographic proof",
    )


# =============================================================================
# Digital Product Passport (DPP)
# =============================================================================


class ProductCharacteristic(BaseModel):
    """A measurable characteristic of a product."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., description="Characteristic name")
    value: str | float = Field(..., description="Characteristic value")
    unit: str | None = Field(default=None, description="Unit of measure")


class Claim(BaseModel):
    """A sustainability or compliance claim about a product.

    Claims link to conformity evidence (DCCs) for verification.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    claim_type: str = Field(
        ...,
        alias="claimType",
        description="Type of claim (e.g., 'carbon-footprint', 'recyclability')",
    )
    claim_value: str = Field(
        ...,
        alias="claimValue",
        description="The claim value or statement",
    )
    evidence: list[SecureLink] = Field(
        default_factory=list,
        description="Links to supporting evidence",
    )


class DPPSubject(BaseModel):
    """Subject of a Digital Product Passport.

    The ProductPassport object containing product identification, manufacturer,
    characteristics, sustainability claims, and links to supporting credentials.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    id: Identifier = Field(
        ...,
        description="Product identifier (GTIN, serial number, etc.)",
    )
    name: str = Field(
        ...,
        description="Product name",
    )
    description: str | None = Field(
        default=None,
        description="Product description",
    )
    manufacturer: Organization = Field(
        ...,
        description="Product manufacturer",
    )
    product_class: str | None = Field(
        default=None,
        alias="productClass",
        description="Product classification code",
    )
    batch_id: str | None = Field(
        default=None,
        alias="batchId",
        description="Batch or lot identifier",
    )
    serial_number: str | None = Field(
        default=None,
        alias="serialNumber",
        description="Individual item serial number",
    )
    characteristics: list[ProductCharacteristic] = Field(
        default_factory=list,
        description="Product characteristics",
    )
    claims: list[Claim] = Field(
        default_factory=list,
        description="Sustainability and compliance claims",
    )
    conformity_evidence: list[SecureLink] = Field(
        default_factory=list,
        alias="conformityEvidence",
        description="Links to conformity credentials",
    )
    traceability_events: list[SecureLink] = Field(
        default_factory=list,
        alias="traceabilityEvents",
        description="Links to traceability event credentials",
    )


@semantic_relation(
    "julee.core.entities.pipeline_output.PipelineOutput",
    RelationType.PROJECTS,
)
class DigitalProductPassport(BaseCredential):
    """Digital Product Passport (DPP).

    The primary UNTP credential for product transparency. Encapsulates product
    identity, manufacturer, sustainability claims, and links to conformity
    evidence and traceability events.

    PROJECTS PipelineOutput - a DPP is projected from pipeline execution outputs.
    """

    credential_subject: DPPSubject = Field(
        ...,
        alias="credentialSubject",
        description="The product information",
    )


# Update forward reference
DigitalProductPassport.model_rebuild()


# =============================================================================
# Digital Conformity Credential (DCC)
# =============================================================================


class ConformityAssessment(BaseModel):
    """Result of a conformity assessment against a standard or regulation.

    Follows ISO/IEC 17000 conformity assessment vocabulary.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    assessment_type: str = Field(
        ...,
        alias="assessmentType",
        description="Type of assessment performed",
    )
    standard: str = Field(
        ...,
        description="Standard or regulation assessed against",
    )
    result: str = Field(
        ...,
        description="Assessment result (pass/fail/partial)",
    )
    assessed_date: datetime = Field(
        ...,
        alias="assessedDate",
        description="Date of assessment",
    )
    assessor: Organization | None = Field(
        default=None,
        description="Organization that performed assessment",
    )
    evidence: list[SecureLink] = Field(
        default_factory=list,
        description="Supporting evidence",
    )


class DCCSubject(BaseModel):
    """Subject of a Digital Conformity Credential.

    The ConformityAttestation containing assessed entity, assessment results,
    and certification details.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    assessed_entity: Identifier = Field(
        ...,
        alias="assessedEntity",
        description="Entity being assessed (product, facility, etc.)",
    )
    assessed_entity_type: str = Field(
        ...,
        alias="assessedEntityType",
        description="Type of assessed entity",
    )
    assessments: list[ConformityAssessment] = Field(
        default_factory=list,
        description="Conformity assessments performed",
    )
    certification_number: str | None = Field(
        default=None,
        alias="certificationNumber",
        description="Certificate number if applicable",
    )
    scope: str | None = Field(
        default=None,
        description="Scope of conformity",
    )


@semantic_relation(
    "julee.core.entities.operation_record.OperationRecord",
    RelationType.PROJECTS,
)
class DigitalConformityCredential(BaseCredential):
    """Digital Conformity Credential (DCC).

    Attests that a product, facility, or process conforms to standards.
    Issued by accredited conformity assessment bodies following ISO/CASCO
    principles.

    PROJECTS OperationRecord - DCC is projected from validation/verification operations.
    """

    credential_subject: DCCSubject = Field(
        ...,
        alias="credentialSubject",
        description="The conformity assessment information",
    )


# Update forward reference
DigitalConformityCredential.model_rebuild()


# =============================================================================
# Digital Facility Record (DFR)
# =============================================================================


class FacilityCapability(BaseModel):
    """A capability or certification of a facility."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    capability_type: str = Field(
        ...,
        alias="capabilityType",
        description="Type of capability",
    )
    description: str = Field(
        ...,
        description="Capability description",
    )
    certifications: list[SecureLink] = Field(
        default_factory=list,
        description="Links to supporting certifications",
    )


class DFRSubject(BaseModel):
    """Subject of a Digital Facility Record.

    The FacilityRecord containing facility identification, operator,
    location, capabilities, and conformity evidence.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    id: Identifier = Field(
        ...,
        description="Facility identifier",
    )
    name: str = Field(
        ...,
        description="Facility name",
    )
    operator: Organization = Field(
        ...,
        description="Organization operating the facility",
    )
    location: str | None = Field(
        default=None,
        description="Facility address",
    )
    geo_location: dict[str, float] | None = Field(
        default=None,
        alias="geoLocation",
        description="Geographic coordinates",
    )
    facility_type: str | None = Field(
        default=None,
        alias="facilityType",
        description="Type of facility",
    )
    capabilities: list[FacilityCapability] = Field(
        default_factory=list,
        description="Facility capabilities and certifications",
    )
    conformity_evidence: list[SecureLink] = Field(
        default_factory=list,
        alias="conformityEvidence",
        description="Links to conformity credentials",
    )


class DigitalFacilityRecord(BaseCredential):
    """Digital Facility Record (DFR).

    Organization-level credential describing a manufacturing or processing
    facility. Similar to DPP but for facilities rather than products.
    """

    credential_subject: DFRSubject = Field(
        ...,
        alias="credentialSubject",
        description="The facility information",
    )


# Update forward reference
DigitalFacilityRecord.model_rebuild()


# =============================================================================
# Digital Traceability Event (DTE)
# =============================================================================


class DTESubject(BaseModel):
    """Subject of a Digital Traceability Event credential.

    Generic event container; see event.py for typed event classes.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    event_id: str = Field(
        ...,
        alias="eventId",
        description="Unique event identifier",
    )
    event_type: str = Field(
        ...,
        alias="eventType",
        description="Type of event",
    )
    event_time: datetime = Field(
        ...,
        alias="eventTime",
        description="When the event occurred",
    )
    location: Identifier | None = Field(
        default=None,
        description="Where the event occurred",
    )
    actor: Organization | None = Field(
        default=None,
        description="Who performed the event",
    )
    event_data: dict[str, Any] = Field(
        default_factory=dict,
        alias="eventData",
        description="Event-specific data",
    )


@semantic_relation(
    "julee.core.entities.operation_record.OperationRecord",
    RelationType.PROJECTS,
)
class DigitalTraceabilityEvent(BaseCredential):
    """Digital Traceability Event (DTE).

    Records supply chain events: transformations, transactions, observations,
    and aggregations. Based on GS1 EPCIS 2.0 event model.

    PROJECTS OperationRecord - one DTE is projected from each service operation
    recorded during use case execution.

    .. seealso::

       See :mod:`~julee.contrib.untp.entities.event` for typed event classes
       (TransformationEvent, TransactionEvent, etc.).
    """

    credential_subject: DTESubject = Field(
        ...,
        alias="credentialSubject",
        description="The event information",
    )


# Update forward reference
DigitalTraceabilityEvent.model_rebuild()


# =============================================================================
# Digital Identity Attestation (DIA)
# =============================================================================


class DIASubject(BaseModel):
    """Subject of a Digital Identity Attestation.

    Contains the attested organization, attestation type, and any
    additional attributes verified by the authority.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    organization: Organization = Field(
        ...,
        description="The attested organization",
    )
    attestation_type: str = Field(
        ...,
        alias="attestationType",
        description="Type of attestation (e.g., 'legal-entity', 'authorized-trader')",
    )
    attested_attributes: dict[str, Any] = Field(
        default_factory=dict,
        alias="attestedAttributes",
        description="Additional attested attributes",
    )
    authority: Organization | None = Field(
        default=None,
        description="Authority making the attestation",
    )


class DigitalIdentityAttestation(BaseCredential):
    """Digital Identity Attestation (DIA).

    Issued by authoritative registers (business, trademark, land) to
    cryptographically verify organization identity. Accompanies other
    credentials to confirm the issuer is who they claim to be.
    """

    credential_subject: DIASubject = Field(
        ...,
        alias="credentialSubject",
        description="The identity attestation",
    )


# Update forward reference
DigitalIdentityAttestation.model_rebuild()
