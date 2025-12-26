"""Tests for the release entity."""

import pytest

from julee.maintenance.entities.release import Release, ReleaseState


class TestRelease:
    """Tests for Release entity."""

    def test_release_creation_with_version(self):
        """Release should be creatable with semantic version."""
        release = Release(version="1.0.0")
        assert release.version == "1.0.0"
        assert release.state == ReleaseState.DRAFT

    def test_release_version_validation(self):
        """Release should reject invalid version formats."""
        with pytest.raises(ValueError, match="must be X.Y.Z format"):
            Release(version="invalid")

    def test_release_computed_branch_name(self):
        """Release should compute standard branch name."""
        release = Release(version="1.2.3")
        assert release.computed_branch_name == "release/v1.2.3"

    def test_release_computed_tag_name(self):
        """Release should compute standard tag name."""
        release = Release(version="1.2.3")
        assert release.computed_tag_name == "v1.2.3"

    def test_release_state_transitions(self):
        """Release should support state transitions."""
        release = Release(version="1.0.0", state=ReleaseState.PREPARED)
        assert release.state == ReleaseState.PREPARED

    def test_release_with_notes(self):
        """Release should store release notes."""
        release = Release(version="1.0.0", notes="Initial release")
        assert release.notes == "Initial release"
