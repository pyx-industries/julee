"""Fixtures for admin app doctrine tests."""

from pathlib import Path

import pytest

# Admin app root
ADMIN_ROOT = Path(__file__).parent.parent


@pytest.fixture
def admin_root() -> Path:
    """Path to the admin app root directory."""
    return ADMIN_ROOT


@pytest.fixture
def admin_commands_dir() -> Path:
    """Path to the admin commands directory."""
    return ADMIN_ROOT / "commands"
