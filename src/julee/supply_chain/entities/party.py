"""Supply chain party entity.

A Party is any participant in a supply chain - organizations, facilities,
individuals, or other entities that can be subjects of credentials,
participants in transactions, or actors in events.

UNTP uses the term "SupplyChainActor" for this concept. We keep the generic
term "Party" in julee.supply_chain and let contrib/untp map to UNTP vocabulary.

Party Types
-----------
Parties have roles/types that determine their function in the supply chain:

- **facility**: A physical location (factory, warehouse, port, farm)
- **manufacturer**: Organization that produces goods
- **supplier**: Organization that supplies materials or components
- **buyer**: Organization that purchases goods
- **seller**: Organization that sells goods
- **certifier**: Conformity assessment body or certification authority
- **regulator**: Government or regulatory body
- **logistics**: Transportation, warehousing, or logistics provider
- **trader**: Import/export or trading entity

A single party may have multiple roles (e.g., both manufacturer and seller).

Semantic Relations
------------------
Party is the projection source for UNTP identity and facility credentials:

- DigitalFacilityRecord PROJECTS Party (facility-type parties)
- DigitalIdentityAttestation PROJECTS Party (any party's identity)
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class PartyType(str, Enum):
    """Types of supply chain parties.

    A party may have multiple types depending on their roles.
    """

    FACILITY = "facility"
    MANUFACTURER = "manufacturer"
    SUPPLIER = "supplier"
    BUYER = "buyer"
    SELLER = "seller"
    CERTIFIER = "certifier"
    REGULATOR = "regulator"
    LOGISTICS = "logistics"
    TRADER = "trader"
    OTHER = "other"


class PartyIdentifier(BaseModel):
    """An identifier for a party.

    Parties may have multiple identifiers from different schemes
    (LEI, DUNS, GLN, tax ID, etc.).
    """

    model_config = ConfigDict(frozen=True)

    scheme: str = Field(
        ...,
        description="Identifier scheme (e.g., 'lei', 'duns', 'gln', 'abn')",
    )
    value: str = Field(
        ...,
        description="Identifier value within the scheme",
    )
    uri: str | None = Field(
        default=None,
        description="Resolvable URI for the identifier",
    )


class Party(BaseModel):
    """A participant in a supply chain.

    Parties are organizations, facilities, or other entities that participate
    in supply chain operations. They can be:

    - Subjects of credentials (DFR for facilities, DIA for identity)
    - Actors in events (who performed a transformation, transaction, etc.)
    - Issuers of credentials (certifiers issuing DCCs)
    - Counterparties in transactions (buyer/seller)

    The party_types field indicates the roles this party plays in the
    supply chain. A single party may have multiple roles.
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(
        ...,
        description="Unique identifier for this party within the system",
    )
    name: str = Field(
        ...,
        description="Display name of the party",
    )
    party_types: list[PartyType] = Field(
        default_factory=list,
        description="Roles this party plays in the supply chain",
    )
    identifiers: list[PartyIdentifier] = Field(
        default_factory=list,
        description="External identifiers (LEI, DUNS, GLN, etc.)",
    )
    country: str | None = Field(
        default=None,
        description="ISO 3166-1 alpha-2 country code",
    )
    address: str | None = Field(
        default=None,
        description="Physical address",
    )
    description: str | None = Field(
        default=None,
        description="Description of the party",
    )

    # For facilities
    geo_location: dict[str, float] | None = Field(
        default=None,
        description="Geographic coordinates (lat, lon) for facility-type parties",
    )
    facility_type: str | None = Field(
        default=None,
        description="Type of facility (factory, warehouse, port, etc.)",
    )

    # Relationships
    parent_party_id: str | None = Field(
        default=None,
        description="Parent party ID (e.g., facility's owning organization)",
    )

    def is_facility(self) -> bool:
        """Check if this party is a facility."""
        return PartyType.FACILITY in self.party_types

    def is_certifier(self) -> bool:
        """Check if this party is a certification body."""
        return PartyType.CERTIFIER in self.party_types

    def get_identifier(self, scheme: str) -> PartyIdentifier | None:
        """Get identifier by scheme."""
        for identifier in self.identifiers:
            if identifier.scheme == scheme:
                return identifier
        return None

    def get_primary_identifier(self) -> PartyIdentifier | None:
        """Get the primary identifier (first in list, or LEI if available)."""
        lei = self.get_identifier("lei")
        if lei:
            return lei
        return self.identifiers[0] if self.identifiers else None
