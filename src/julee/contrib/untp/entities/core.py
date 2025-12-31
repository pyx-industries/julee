"""UNTP core entity definitions.

Foundational types used across all UNTP credentials: identifiers, organizations,
accreditations, trust anchors, and verifiable credential infrastructure.

.. seealso::

   `UNTP Core Vocabulary <https://test.uncefact.org/vocabulary/untp/core/about>`_
       Linked Data entities: Product, Location, Facility, Party, Standard, etc.

   `W3C VC Data Model 2.0 <https://www.w3.org/TR/vc-data-model-2.0/>`_
       Verifiable Credentials specification that UNTP credentials extend.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class IdentifierScheme(str, Enum):
    """Standard identifier schemes for supply chain entities.

    .. seealso::

       `GS1 Digital Link <https://www.gs1.org/standards/gs1-digital-link>`_
           GTIN, GLN identifier resolution standard.

       `GLEIF LEI <https://www.gleif.org/en/about-lei/>`_
           Legal Entity Identifier for organizations.

       `W3C DID <https://www.w3.org/TR/did-core/>`_
           Decentralized Identifiers specification.
    """

    DID = "did"
    GLN = "gln"  # Global Location Number
    GTIN = "gtin"  # Global Trade Item Number
    LEI = "lei"  # Legal Entity Identifier
    ABN = "abn"  # Australian Business Number
    URL = "url"


class Identifier(BaseModel):
    """A unique identifier with scheme and value.

    Used throughout UNTP to identify products, facilities, organizations,
    and credentials using established identifier schemes.
    """

    model_config = ConfigDict(frozen=True)

    scheme: str = Field(
        ...,
        description="Identifier scheme (e.g., 'did', 'gln', 'lei')",
    )
    value: str = Field(
        ...,
        description="The identifier value within the scheme",
    )
    uri: str | None = Field(
        default=None,
        description="Full URI representation if available",
    )


class SecureLink(BaseModel):
    """A cryptographically secured link to external content.

    Provides integrity verification via content hash, enabling tamper-evident
    references between credentials and supporting documents.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    target: str = Field(
        ...,
        description="URI of the linked resource",
    )
    link_type: str = Field(
        ...,
        alias="linkType",
        description="Type/relationship of the link",
    )
    hash_method: str | None = Field(
        default=None,
        alias="hashMethod",
        description="Hash algorithm used (e.g., 'sha256')",
    )
    hash_value: str | None = Field(
        default=None,
        alias="hashValue",
        description="Hash of the linked content for integrity",
    )


class Organization(BaseModel):
    """An organization entity in the supply chain.

    Represents any party: manufacturer, certifier, regulator, trader, etc.
    Organizations are identified via standard schemes (LEI, GLN, DID).
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    id: Identifier = Field(
        ...,
        description="Primary identifier for the organization",
    )
    name: str = Field(
        ...,
        description="Organization name",
    )
    other_identifiers: list[Identifier] = Field(
        default_factory=list,
        alias="otherIdentifiers",
        description="Additional identifiers (e.g., tax ID, registration numbers)",
    )
    address: str | None = Field(
        default=None,
        description="Physical address",
    )
    country: str | None = Field(
        default=None,
        description="ISO 3166-1 alpha-2 country code",
    )


class AccreditationStatus(str, Enum):
    """Status of an accreditation."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    EXPIRED = "expired"


class Accreditation(BaseModel):
    """Accreditation of an organization to issue credentials.

    Represents authority granted by an accreditation body to a conformity
    assessment body, following ISO/IEC 17011 accreditation principles.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    id: Identifier = Field(
        ...,
        description="Accreditation identifier",
    )
    accreditor: Organization = Field(
        ...,
        description="Organization granting the accreditation",
    )
    accredited_party: Organization = Field(
        ...,
        alias="accreditedParty",
        description="Organization receiving the accreditation",
    )
    scope: list[str] = Field(
        default_factory=list,
        description="Scope of accreditation (credential types, standards)",
    )
    valid_from: datetime = Field(
        ...,
        alias="validFrom",
        description="Accreditation start date",
    )
    valid_until: datetime | None = Field(
        default=None,
        alias="validUntil",
        description="Accreditation expiry date",
    )
    status: AccreditationStatus = Field(
        default=AccreditationStatus.ACTIVE,
        description="Current status of the accreditation",
    )


class TrustAnchor(BaseModel):
    """A trusted root entity in the UNTP trust hierarchy.

    Represents authoritative registers (business, trademark, land) that issue
    Digital Identity Anchors to cryptographically verify entity identity.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    id: Identifier = Field(
        ...,
        description="Trust anchor identifier",
    )
    name: str = Field(
        ...,
        description="Trust anchor name",
    )
    trust_anchor_type: str = Field(
        ...,
        alias="trustAnchorType",
        description="Type of trust anchor (e.g., 'government', 'regulator')",
    )
    jurisdiction: str | None = Field(
        default=None,
        description="Jurisdiction (country or region code)",
    )
    public_key: str | None = Field(
        default=None,
        alias="publicKey",
        description="Public key for signature verification",
    )
    accreditations_issued: list[SecureLink] = Field(
        default_factory=list,
        alias="accreditationsIssued",
        description="Links to accreditations issued by this trust anchor",
    )


class CredentialProof(BaseModel):
    """Cryptographic proof attached to a verifiable credential.

    Implements W3C Data Integrity proofs for credential authentication.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    proof_type: str = Field(
        ...,
        alias="type",
        description="Proof type (e.g., 'DataIntegrityProof')",
    )
    created: datetime = Field(
        ...,
        description="When the proof was created",
    )
    verification_method: str = Field(
        ...,
        alias="verificationMethod",
        description="URI of the verification method (public key)",
    )
    proof_purpose: str = Field(
        default="assertionMethod",
        alias="proofPurpose",
        description="Purpose of the proof",
    )
    proof_value: str = Field(
        ...,
        alias="proofValue",
        description="The cryptographic signature value",
    )


class CredentialStatus(BaseModel):
    """Status information for credential revocation checking.

    Uses W3C Bitstring Status List for efficient revocation lookups.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    id: str = Field(
        ...,
        description="Status list entry URI",
    )
    status_type: str = Field(
        ...,
        alias="type",
        description="Status type (e.g., 'BitstringStatusListEntry')",
    )
    status_purpose: str = Field(
        default="revocation",
        alias="statusPurpose",
        description="Purpose (revocation, suspension)",
    )
    status_list_index: int = Field(
        ...,
        alias="statusListIndex",
        description="Index in the status list",
    )
    status_list_credential: str = Field(
        ...,
        alias="statusListCredential",
        description="URI of the status list credential",
    )
