"""Tests for supply chain Party entity."""

import pytest

from julee.supply_chain.entities.party import (
    Party,
    PartyIdentifier,
    PartyType,
)


class TestPartyIdentifier:
    """Tests for PartyIdentifier value object."""

    def test_identifier_creation(self):
        """PartyIdentifier can be created with scheme and value."""
        identifier = PartyIdentifier(scheme="lei", value="5493001KJTIIGC8Y1R12")
        assert identifier.scheme == "lei"
        assert identifier.value == "5493001KJTIIGC8Y1R12"
        assert identifier.uri is None

    def test_identifier_with_uri(self):
        """PartyIdentifier can include a URI."""
        identifier = PartyIdentifier(
            scheme="gln",
            value="1234567890123",
            uri="https://id.gs1.org/gln/1234567890123",
        )
        assert identifier.uri == "https://id.gs1.org/gln/1234567890123"

    def test_identifier_is_immutable(self):
        """PartyIdentifier is frozen."""
        from pydantic import ValidationError

        identifier = PartyIdentifier(scheme="lei", value="123")
        with pytest.raises(ValidationError):
            identifier.value = "456"


class TestParty:
    """Tests for Party entity."""

    def test_party_creation(self):
        """Party can be created with required fields."""
        party = Party(id="party-001", name="Example Corp")
        assert party.id == "party-001"
        assert party.name == "Example Corp"
        assert party.party_types == []

    def test_party_with_types(self):
        """Party can have multiple types."""
        party = Party(
            id="party-002",
            name="ACME Manufacturing",
            party_types=[PartyType.MANUFACTURER, PartyType.SELLER],
        )
        assert PartyType.MANUFACTURER in party.party_types
        assert PartyType.SELLER in party.party_types

    def test_facility_party(self):
        """Party can represent a facility."""
        party = Party(
            id="facility-001",
            name="Main Factory",
            party_types=[PartyType.FACILITY],
            facility_type="factory",
            geo_location={"lat": -33.8688, "lon": 151.2093},
            parent_party_id="party-002",
        )
        assert party.is_facility()
        assert party.facility_type == "factory"
        assert party.geo_location["lat"] == -33.8688

    def test_certifier_party(self):
        """Party can represent a certification body."""
        party = Party(
            id="certifier-001",
            name="Global Cert Authority",
            party_types=[PartyType.CERTIFIER],
            country="AU",
        )
        assert party.is_certifier()
        assert party.country == "AU"

    def test_party_with_identifiers(self):
        """Party can have multiple identifiers."""
        party = Party(
            id="party-003",
            name="International Corp",
            identifiers=[
                PartyIdentifier(scheme="lei", value="5493001KJTIIGC8Y1R12"),
                PartyIdentifier(scheme="duns", value="123456789"),
                PartyIdentifier(scheme="abn", value="12345678901"),
            ],
        )
        assert len(party.identifiers) == 3

    def test_get_identifier(self):
        """Can retrieve identifier by scheme."""
        party = Party(
            id="party-004",
            name="Test Corp",
            identifiers=[
                PartyIdentifier(scheme="lei", value="LEI123"),
                PartyIdentifier(scheme="duns", value="DUNS456"),
            ],
        )
        lei = party.get_identifier("lei")
        assert lei is not None
        assert lei.value == "LEI123"

        gln = party.get_identifier("gln")
        assert gln is None

    def test_get_primary_identifier_prefers_lei(self):
        """Primary identifier prefers LEI if available."""
        party = Party(
            id="party-005",
            name="Test Corp",
            identifiers=[
                PartyIdentifier(scheme="duns", value="DUNS456"),
                PartyIdentifier(scheme="lei", value="LEI123"),
            ],
        )
        primary = party.get_primary_identifier()
        assert primary is not None
        assert primary.scheme == "lei"

    def test_get_primary_identifier_fallback(self):
        """Primary identifier falls back to first if no LEI."""
        party = Party(
            id="party-006",
            name="Test Corp",
            identifiers=[
                PartyIdentifier(scheme="duns", value="DUNS456"),
                PartyIdentifier(scheme="abn", value="ABN789"),
            ],
        )
        primary = party.get_primary_identifier()
        assert primary is not None
        assert primary.scheme == "duns"

    def test_party_is_immutable(self):
        """Party is frozen."""
        from pydantic import ValidationError

        party = Party(id="party-007", name="Test")
        with pytest.raises(ValidationError):
            party.name = "Changed"


class TestPartyType:
    """Tests for PartyType enum."""

    def test_party_types_are_strings(self):
        """PartyType values are strings."""
        assert PartyType.FACILITY.value == "facility"
        assert PartyType.MANUFACTURER.value == "manufacturer"
        assert PartyType.CERTIFIER.value == "certifier"

    def test_all_party_types(self):
        """All expected party types exist."""
        expected = {
            "facility",
            "manufacturer",
            "supplier",
            "buyer",
            "seller",
            "certifier",
            "regulator",
            "logistics",
            "trader",
            "other",
        }
        actual = {pt.value for pt in PartyType}
        assert actual == expected
