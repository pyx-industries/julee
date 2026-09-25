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

SERVICE_SUFFIX: Final[str] = "Service"
"""Suffix identifying service protocols (e.g. PollerService).

A name is a claim. A protocol in domain/services/ that ends in Service
says it is one, and doctrine holds it to what a service is. One that does
not is asked why, because the answer is usually either a name that drifted
or a protocol that does not belong in this directory at all.
"""

HANDLER_SUFFIX: Final[str] = "Handler"
"""Suffix identifying handler protocols (e.g. PollingResultHandler).

Handlers live in domain/services/ beside services and are a different
artifact with rules of their own (ADR 003).
"""

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
        "core",
        "shared",
        "tests",
        "utils",
        "common",
    }
)
"""Directory names that are not bounded contexts."""
