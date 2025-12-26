"""Architectural doctrine constants.

This module defines the structural naming conventions and rules enforced by
doctrine tests. It serves as the canonical reference for Clean Architecture
naming patterns in Julee.

CHANGE MANAGEMENT
-----------------
These constants are negotiated with framework early adopters. Changes here
will produce diffs that should be reviewed carefully:

1. Naming changes (e.g., UseCase -> Command) affect all existing code
2. Layer changes affect dependency rule enforcement
3. Reserved word changes affect bounded context discovery

When proposing changes, update this file first - the diff becomes the
proposal document.

NAMING CONVENTION
-----------------
Constants use SCREAMING_SNAKE_CASE.
Suffix constants end with _SUFFIX (singular) or _SUFFIXES (collection).
Layer constants end with _LAYERS.
"""

from typing import Final

# =============================================================================
# ARTIFACT NAMING SUFFIXES
# =============================================================================
# These suffixes identify Clean Architecture artifacts by their role.
# The suffix is the contract - code scanning relies on these patterns.

USE_CASE_SUFFIX: Final[str] = "UseCase"
"""Suffix for use case classes.

Use cases orchestrate business logic. They accept a Request, coordinate
domain objects and repositories, and return a Response.

Example: CreateJourneyUseCase, ListPersonasUseCase

Rationale: "UseCase" is explicit about the class's role in Clean Architecture.
Alternative considered: "Command" (CQRS terminology) - may revisit.
"""

REQUEST_SUFFIX: Final[str] = "Request"
"""Suffix for use case request classes.

Requests carry input data to use cases. They validate and transform
external input into domain-safe structures.

Example: CreateJourneyRequest, ListPersonasRequest

Rationale: Pairs with Response; clear input/output semantics.
"""

RESPONSE_SUFFIX: Final[str] = "Response"
"""Suffix for use case response classes.

Responses carry output data from use cases. They structure domain
results for consumption by the application layer.

Example: CreateJourneyResponse, ListPersonasResponse

Rationale: Pairs with Request; clear input/output semantics.
"""

ITEM_SUFFIX: Final[str] = "Item"
"""Suffix for nested compound types within requests.

Items are not top-level requests - they represent complex nested
structures within a request that need their own validation.

Example: JourneyStepItem (nested within CreateJourneyRequest)

Rationale: Distinguishes nested input types from top-level requests.
"""

REPOSITORY_SUFFIX: Final[str] = "Repository"
"""Suffix for repository protocol classes.

Repositories define persistence abstractions. They are protocols
(interfaces) that use cases depend on, with implementations in
infrastructure.

Example: JourneyRepository, PersonaRepository

Rationale: Standard Clean Architecture / DDD terminology.
"""

SERVICE_SUFFIX: Final[str] = "Service"
"""Suffix for service protocol classes.

Services define external service abstractions (APIs, LLMs, etc).
Like repositories, they are protocols with infrastructure implementations.

Example: KnowledgeService, ValidationService

Rationale: Distinguishes from repositories (persistence vs. behavior).
"""

# Collected for iteration
ARTIFACT_SUFFIXES: Final[dict[str, str]] = {
    "use_case": USE_CASE_SUFFIX,
    "request": REQUEST_SUFFIX,
    "response": RESPONSE_SUFFIX,
    "item": ITEM_SUFFIX,
    "repository": REPOSITORY_SUFFIX,
    "service": SERVICE_SUFFIX,
}


# =============================================================================
# ENTITY CONSTRAINTS
# =============================================================================
# Entities (domain models) have naming restrictions to prevent confusion
# with other artifact types.

ENTITY_FORBIDDEN_SUFFIXES: Final[tuple[str, ...]] = (
    USE_CASE_SUFFIX,
    REQUEST_SUFFIX,
    RESPONSE_SUFFIX,
)
"""Suffixes that entities MUST NOT use.

Entities represent domain concepts - they should not be confused with
application-layer artifacts like use cases or request/response classes.

Example violation: InvoiceUseCase as an entity name
"""


# =============================================================================
# REQUIRED BASE CLASSES
# =============================================================================
# These define inheritance requirements for different artifact types.

ENTITY_BASE: Final[str] = "BaseModel"
"""Required base class for entities.

All entities MUST inherit from pydantic.BaseModel for:
- Immutability (frozen=True)
- Validation
- Serialization

Rationale: Pydantic provides the guarantees we need for domain objects.
"""

REQUEST_BASE: Final[str] = "BaseModel"
"""Required base class for requests.

All requests MUST inherit from pydantic.BaseModel for:
- Input validation
- Type coercion
- Serialization

Rationale: Requests are the boundary - validation is critical.
"""

RESPONSE_BASE: Final[str] = "BaseModel"
"""Required base class for responses.

All responses MUST inherit from pydantic.BaseModel for:
- Output structure guarantee
- Serialization
- API compatibility

Rationale: Consistency with requests; serialization support.
"""

PROTOCOL_BASES: Final[tuple[str, ...]] = ("Protocol", "Protocol[T]")
"""Required base classes for repository and service protocols.

Protocols MUST inherit from typing.Protocol (or generic variant) to
define structural subtyping contracts.

Rationale: Protocol enables dependency inversion without ABC inheritance.
"""


# =============================================================================
# ARCHITECTURE LAYERS
# =============================================================================
# Clean Architecture defines a layer hierarchy. Dependencies must point
# inward (toward the center).

LAYER_ENTITIES: Final[str] = "entities"
"""Innermost layer: domain entities.

Contains: Entity classes, value objects, domain events
Can import: Nothing (except standard library, pydantic)
"""

LAYER_USE_CASES: Final[str] = "use_cases"
"""Middle layer: application business rules.

Contains: Use case classes, request/response classes
Can import: models, repositories (protocols), services (protocols)
"""

LAYER_REPOSITORIES: Final[str] = "repositories"
"""Protocol layer: persistence abstractions.

Contains: Repository protocol definitions
Can import: models (for type hints)
Same level as: use_cases, services
"""

LAYER_SERVICES: Final[str] = "services"
"""Protocol layer: external service abstractions.

Contains: Service protocol definitions
Can import: models (for type hints)
Same level as: use_cases, repositories
"""

LAYER_INFRASTRUCTURE: Final[str] = "infrastructure"
"""Outer layer: framework and driver implementations.

Contains: Repository implementations, service implementations
Can import: Everything inward
"""

LAYER_APPS: Final[str] = "apps"
"""Application layer: delivery mechanisms.

Contains: FastAPI routers, MCP servers, CLI commands
Can import: Everything inward
"""

LAYER_DEPLOYMENT: Final[str] = "deployment"
"""Outermost layer: deployment configuration.

Contains: Docker, Kubernetes, CI/CD configuration
Can import: Everything
"""

# Layer keywords for import classification
# Maps directory/module names to canonical layer names
LAYER_KEYWORDS: Final[dict[str, str]] = {
    # Innermost
    "entities": LAYER_ENTITIES,
    # Middle
    "use_cases": LAYER_USE_CASES,
    "usecases": LAYER_USE_CASES,  # alternative spelling
    "repositories": LAYER_REPOSITORIES,
    "services": LAYER_SERVICES,
    # Outer
    "infrastructure": LAYER_INFRASTRUCTURE,
    "apps": LAYER_APPS,
    "deployment": LAYER_DEPLOYMENT,
}

# Dependency rule: what each layer is forbidden from importing
LAYER_FORBIDDEN_IMPORTS: Final[dict[str, frozenset[str]]] = {
    LAYER_ENTITIES: frozenset(
        {
            LAYER_USE_CASES,
            LAYER_REPOSITORIES,
            LAYER_SERVICES,
            LAYER_INFRASTRUCTURE,
            LAYER_APPS,
            LAYER_DEPLOYMENT,
        }
    ),
    LAYER_USE_CASES: frozenset(
        {
            LAYER_INFRASTRUCTURE,
            LAYER_APPS,
            LAYER_DEPLOYMENT,
        }
    ),
    LAYER_REPOSITORIES: frozenset(
        {
            LAYER_INFRASTRUCTURE,
            LAYER_APPS,
            LAYER_DEPLOYMENT,
        }
    ),
    LAYER_SERVICES: frozenset(
        {
            LAYER_INFRASTRUCTURE,
            LAYER_APPS,
            LAYER_DEPLOYMENT,
        }
    ),
    # Infrastructure and apps can import from anywhere inward
    LAYER_INFRASTRUCTURE: frozenset({LAYER_APPS, LAYER_DEPLOYMENT}),
    LAYER_APPS: frozenset({LAYER_DEPLOYMENT}),
    LAYER_DEPLOYMENT: frozenset(),
}


# =============================================================================
# DIRECTORY STRUCTURE
# =============================================================================
# Filesystem layout patterns for bounded contexts.
# Structure is flat: {bc}/entities/, {bc}/use_cases/, etc.
# No nested domain/ directory.

ENTITIES_PATH: Final[tuple[str, ...]] = ("entities",)
"""Path to entities directory: {bc}/entities/"""

USE_CASES_PATH: Final[tuple[str, ...]] = ("use_cases",)
"""Path to use cases directory: {bc}/use_cases/"""

REPOSITORIES_PATH: Final[tuple[str, ...]] = ("repositories",)
"""Path to repository protocols directory: {bc}/repositories/"""

SERVICES_PATH: Final[tuple[str, ...]] = ("services",)
"""Path to service protocols directory: {bc}/services/"""

INFRASTRUCTURE_PATH: Final[tuple[str, ...]] = ("infrastructure",)
"""Path to infrastructure directory: {bc}/infrastructure/"""


# =============================================================================
# BOUNDED CONTEXT DISCOVERY
# =============================================================================
# Configuration for finding bounded contexts in the filesystem.

SEARCH_ROOT: Final[str] = "src/julee"
"""Root directory for bounded context discovery.

Bounded contexts are discovered under this path. The search excludes
reserved words and requires Clean Architecture structure markers.
"""

CONTRIB_DIR: Final[str] = "contrib"
"""Directory for contributed/plugin bounded contexts.

Contexts under {SEARCH_ROOT}/contrib/ are marked is_contrib=True.
"""


# =============================================================================
# RESERVED WORDS
# =============================================================================
# Directory names that are NOT bounded contexts because they have special
# structural meaning. Reserved words are utility/infrastructure directories
# that don't follow bounded context structure.
#
# NOTE: Nested solutions (like contrib/) are NOT reserved words. They are
# solution containers that hold bounded contexts and follow the same doctrine.

RESERVED_STRUCTURAL: Final[frozenset[str]] = frozenset(
    {
        "docs",  # Documentation
        "deployment",  # Deployment configuration
    }
)
"""Structural directories that are not bounded contexts.

These directories have special meaning in the project layout but don't
contain domain logic.
"""

RESERVED_COMMON: Final[frozenset[str]] = frozenset(
    {
        "util",  # Utilities
        "utils",  # Utilities (alternative spelling)
        "common",  # Common code
        "tests",  # Test directories
        "maintenance",  # Developer tooling (release scripts, etc.)
    }
)
"""Common utility directories that are not bounded contexts.

These are typical names for shared/utility code that shouldn't be
treated as bounded contexts because they lack domain identity.

NOTE: 'core' is NOT reserved - it's a foundational bounded context.
"""

RESERVED_WORDS: Final[frozenset[str]] = RESERVED_STRUCTURAL | RESERVED_COMMON
"""All reserved words: union of structural and common."""


# =============================================================================
# VIEWPOINTS
# =============================================================================
# Special bounded contexts that represent architectural viewpoints.

VIEWPOINT_SLUGS: Final[frozenset[str]] = frozenset(
    {
        "hcd",  # Human-Centered Design viewpoint
        "c4",  # C4 Architecture viewpoint
    }
)
"""Bounded contexts that are architectural viewpoints.

Viewpoints provide different lenses for viewing the system:
- hcd: User journeys, personas, stories (human-centered)
- c4: Containers, components, relationships (technical)

Contexts matching these slugs are marked is_viewpoint=True.
"""


# =============================================================================
# SPECIAL CONTEXTS
# =============================================================================
# Bounded contexts with special handling requirements.

CORE_CONTEXT_SLUG: Final[str] = "core"
"""The core/foundational bounded context.

The 'core' context contains cross-cutting concerns used by all other
contexts. It is a reserved word (not discovered as a normal bounded
context) but still contains domain code that must comply with doctrine.

Special handling required for:
- Service protocol method matching (core services need core requests)
- Import analysis (core is allowed as an import source)
"""


# =============================================================================
# PIPELINE PATTERN
# =============================================================================
# A Pipeline is a UseCase that has been appropriately treated (with decorators
# and proxies) to run as a Temporal workflow.
#
# See: docs/architecture/solutions/pipelines.rst
#
# Key invariants:
# - A Pipeline MUST wrap a corresponding UseCase
# - A Pipeline MUST NOT contain business logic directly
# - A Pipeline lives in apps/worker/pipelines.py
# - A Pipeline is decorated with @workflow.defn

PIPELINE_SUFFIX: Final[str] = "Pipeline"
"""Suffix for pipeline classes.

Pipelines wrap use cases with Temporal workflow treatment for durable execution.
The pipeline delegates to the use case - it does NOT contain business logic.

Example: ExtractAssemblePipeline wraps ExtractAssembleDataUseCase

Naming convention:
- {Prefix}Pipeline MUST have a corresponding {Prefix}UseCase or {Prefix}DataUseCase
- Pipeline lives at: {bc}/apps/worker/pipelines.py
- UseCase lives at: {bc}/use_cases/
"""

PIPELINE_LOCATION: Final[str] = "apps/worker/pipelines.py"
"""Canonical location for pipeline definitions within a bounded context.

Pipelines are application-layer artifacts (apps/) that provide durable
execution of domain use cases via Temporal workflows.
"""

PIPELINE_DECORATOR: Final[str] = "@workflow.defn"
"""Required decorator for pipeline classes.

All pipelines MUST be decorated with Temporal's @workflow.defn to enable
workflow registration and execution.
"""

PIPELINE_RUN_DECORATOR: Final[str] = "@workflow.run"
"""Required decorator for the pipeline's run method.

The run method is the entry point for workflow execution. It MUST:
1. Create the wrapped UseCase with workflow-safe proxies
2. Delegate to the UseCase's execute() method
3. Return the UseCase's response
"""


# =============================================================================
# APPLICATION DISCOVERY
# =============================================================================
# Configuration for finding applications in the filesystem.
# Applications are orthogonal to bounded contexts - they are deployable
# compositions that depend on one or more BCs.

APPS_ROOT: Final[str] = "apps"
"""Root directory for application discovery.

Applications are discovered under this path. Each top-level directory
represents a deployable application.

Note: 'apps' is a reserved word - it cannot be a bounded context name.
"""

APP_TYPE_MARKERS: Final[dict[str, tuple[str, ...]]] = {
    "REST-API": ("routers",),
    "MCP": ("tools",),
    "SPHINX-EXTENSION": ("directives",),
    "TEMPORAL-WORKER": ("pipelines",),
    "CLI": ("commands",),
}
"""Directory markers used to infer application type.

Each app type has characteristic subdirectories. Detection uses these
to classify applications when app_type is not explicitly declared.
"""

APP_BC_ORGANIZATION_EXCLUDES: Final[frozenset[str]] = frozenset(
    {
        "shared",
        "tests",
        "__pycache__",
        "common",
    }
)
"""Subdirectory names that do NOT indicate BC-based organization.

When detecting whether an app uses BC-based organization, these
directories are excluded from consideration.
"""
