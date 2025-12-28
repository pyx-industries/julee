"""Tests for Acknowledgement entity."""

import pytest

from julee.core.entities.acknowledgement import Acknowledgement


class TestAcknowledgement:
    """Tests for Acknowledgement entity."""

    def test_wilco_creates_compliant_ack(self):
        """wilco() should create an acknowledgement that will comply."""
        ack = Acknowledgement.wilco()

        assert ack.will_comply is True
        assert ack.errors == []

    def test_roger_creates_non_compliant_ack(self):
        """roger() should create a non-compliant acknowledgement with reason."""
        ack = Acknowledgement.roger("System overloaded")

        assert ack.will_comply is False
        assert "System overloaded" in ack.errors

    def test_non_compliance_requires_error(self):
        """Non-compliant acknowledgement must have at least one error."""
        with pytest.raises(ValueError, match="at least one error"):
            Acknowledgement(will_comply=False)

    def test_wilco_with_errors(self):
        """wilco can include errors (will comply despite issues)."""
        ack = Acknowledgement.wilco(errors=["Minor issue detected"])

        assert ack.will_comply is True
        assert "Minor issue detected" in ack.errors

    def test_wilco_with_warnings(self):
        """wilco can include warnings."""
        ack = Acknowledgement.wilco(warnings=["Deprecated feature used"])

        assert ack.will_comply is True
        assert "Deprecated feature used" in ack.warnings

    def test_roger_with_additional_errors(self):
        """roger can include additional errors beyond the reason."""
        ack = Acknowledgement.roger(
            "Primary failure",
            errors=["Secondary issue"],
        )

        assert ack.will_comply is False
        assert "Primary failure" in ack.errors
        assert "Secondary issue" in ack.errors

    def test_default_lists_are_empty(self):
        """Default message lists should be empty."""
        ack = Acknowledgement.wilco()

        assert ack.errors == []
        assert ack.warnings == []
        assert ack.info == []
        assert ack.debug == []

    def test_wilco_is_default(self):
        """Direct construction defaults to will_comply=True."""
        ack = Acknowledgement()

        assert ack.will_comply is True
