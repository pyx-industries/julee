"""Architectural doctrine constants.

Naming conventions and structural rules enforced by doctrine tests.
These are the canonical definitions for Clean Architecture patterns in Julee.

Constants here are negotiated with framework adopters — changes produce diffs
that should be reviewed carefully before landing.
"""

from typing import Final

# =============================================================================
# ARTIFACT NAMING SUFFIXES
# =============================================================================

USE_CASE_SUFFIX: Final[str] = "UseCase"
"""Suffix identifying use case classes (e.g. CreateJourneyUseCase)."""

REQUEST_SUFFIX: Final[str] = "Request"
"""Suffix identifying use case request classes (e.g. CreateJourneyRequest)."""

RESPONSE_SUFFIX: Final[str] = "Response"
"""Suffix identifying use case response classes (e.g. CreateJourneyResponse)."""

PIPELINE_SUFFIX: Final[str] = "Pipeline"
"""Suffix identifying Temporal workflow pipeline classes."""

# =============================================================================
# LAYER DIRECTORY PATHS
# =============================================================================
# Expressed as tuples so callers can join with Path() components.
# The layout is ADR 001's: a bounded context keeps its domain under
# domain/, and its use cases beside it.

ENTITIES_PATH: Final[tuple[str, ...]] = ("domain", "models")
USE_CASES_PATH: Final[tuple[str, ...]] = ("usecases",)
REPOSITORIES_PATH: Final[tuple[str, ...]] = ("domain", "repositories")
SERVICES_PATH: Final[tuple[str, ...]] = ("domain", "services")
INFRASTRUCTURE_PATH: Final[tuple[str, ...]] = ("infrastructure",)

# =============================================================================
# RESERVED DIRECTORY NAMES
# =============================================================================

CONTRIB_DIR: Final[str] = "contrib"
"""Directory for batteries-included contrib modules."""

APPS_ROOT: Final[str] = "apps"
"""Root directory for application entry points."""

DEPLOYMENTS_ROOT: Final[str] = "deployments"
"""Root directory for deployment configurations."""

DOCS_ROOT: Final[str] = "docs"
"""Root directory for solution documentation (required)."""

# =============================================================================
# PIPELINE CONVENTIONS
# =============================================================================

PIPELINE_LOCATION: Final[str] = "apps/worker/pipelines.py"
"""Canonical location for pipeline definitions within a bounded context."""

# =============================================================================
# APPLICATION DISCOVERY
# =============================================================================

APP_BC_ORGANIZATION_EXCLUDES: Final[frozenset[str]] = frozenset(
    {"shared", "tests", "__pycache__", "common"}
)
"""Subdirectory names excluded when detecting BC-based app organisation."""

RESERVED_WORDS: Final[frozenset[str]] = frozenset(
    {
        APPS_ROOT,
        DEPLOYMENTS_ROOT,
        DOCS_ROOT,
        CONTRIB_DIR,
        "core",
        "shared",
        "tests",
        "utils",
        "common",
    }
)
"""Directory names that are not bounded contexts."""
