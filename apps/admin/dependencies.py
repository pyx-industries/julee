"""Dependency injection for julee-admin CLI.

Provides a DI container that constructs use cases with appropriate
repository implementations. Follows the same patterns as the API
applications but adapted for CLI context.
"""

import os
from functools import lru_cache
from pathlib import Path

from julee.core.entities.policy import SolutionPolicyConfig
from julee.core.infrastructure.repositories.introspection.application import (
    FilesystemApplicationRepository,
)
from julee.core.infrastructure.repositories.introspection.bounded_context import (
    FilesystemBoundedContextRepository,
)
from julee.core.infrastructure.repositories.introspection.deployment import (
    FilesystemDeploymentRepository,
)
from julee.core.infrastructure.repositories.introspection.solution import (
    FilesystemSolutionRepository,
)
from julee.core.use_cases.bounded_context.get import GetBoundedContextUseCase
from julee.core.use_cases.bounded_context.list import ListBoundedContextsUseCase
from julee.core.use_cases.code_artifact.list_entities import ListEntitiesUseCase
from julee.core.use_cases.code_artifact.list_repository_protocols import (
    ListRepositoryProtocolsUseCase,
)
from julee.core.use_cases.code_artifact.list_requests import ListRequestsUseCase
from julee.core.use_cases.code_artifact.list_responses import ListResponsesUseCase
from julee.core.use_cases.code_artifact.list_service_protocols import (
    ListServiceProtocolsUseCase,
)
from julee.core.use_cases.code_artifact.list_use_cases import ListUseCasesUseCase

PROJECT_ROOT_MARKERS = ("pyproject.toml", "setup.py", ".git")


def find_project_root(start_path: Path | None = None) -> Path:
    """Find the project root by walking up from start_path.

    Looks for common project markers (pyproject.toml, setup.py, .git)
    to identify the project root.

    Args:
        start_path: Path to start searching from. Defaults to cwd.

    Returns:
        Path to the project root, or cwd if not found.
    """
    path = start_path or Path.cwd()
    path = path.resolve()

    for parent in [path, *path.parents]:
        for marker in PROJECT_ROOT_MARKERS:
            if (parent / marker).exists():
                return parent

    # Fall back to cwd if no markers found
    return Path.cwd()


def get_project_root() -> Path:
    """Get the project root directory.

    Uses JULEE_PROJECT_ROOT environment variable if set,
    otherwise attempts to find the project root by looking
    for common markers (pyproject.toml, setup.py, .git).

    Returns:
        Path to the project root directory
    """
    root = os.getenv("JULEE_PROJECT_ROOT")
    if root:
        return Path(root)
    return find_project_root()


@lru_cache
def get_solution_config() -> SolutionPolicyConfig:
    """Get the solution configuration from pyproject.toml.

    Reads [tool.julee] configuration including search_root and docs_root.
    Results are cached.

    Returns:
        SolutionPolicyConfig with parsed settings

    Raises:
        ValueError: If this is a julee solution but search_root is not configured
    """
    from julee.core.infrastructure.repositories.file.solution_config import (
        FileSolutionConfigRepository,
    )

    repo = FileSolutionConfigRepository()
    return repo.get_policy_config_sync(get_project_root())


def require_search_root() -> str:
    """Get the search_root, raising an error if not configured.

    Returns:
        The configured search_root path

    Raises:
        ValueError: If search_root is not configured in [tool.julee]
    """
    config = get_solution_config()
    if config.search_root is None:
        raise ValueError(
            "search_root not configured in [tool.julee] section of pyproject.toml. "
            "Add: search_root = \"src/your_package\""
        )
    return config.search_root


def require_docs_root() -> str:
    """Get the docs_root, raising an error if not configured.

    Returns:
        The configured docs_root path

    Raises:
        ValueError: If docs_root is not configured in [tool.julee]
    """
    config = get_solution_config()
    if config.docs_root is None:
        raise ValueError(
            "docs_root not configured in [tool.julee] section of pyproject.toml. "
            "Add: docs_root = \"docs\""
        )
    return config.docs_root


@lru_cache
def get_bounded_context_repository() -> FilesystemBoundedContextRepository:
    """Get the bounded context repository singleton.

    Returns:
        Repository for discovering bounded contexts in the filesystem

    Raises:
        ValueError: If search_root is not configured
    """
    return FilesystemBoundedContextRepository(
        get_project_root(),
        require_search_root(),
    )


# =============================================================================
# Bounded Context Use Cases
# =============================================================================


def get_list_bounded_contexts_use_case() -> ListBoundedContextsUseCase:
    """Get ListBoundedContextsUseCase with repository dependency.

    Returns:
        Use case for listing bounded contexts
    """
    return ListBoundedContextsUseCase(get_bounded_context_repository())


def get_get_bounded_context_use_case() -> GetBoundedContextUseCase:
    """Get GetBoundedContextUseCase with repository dependency.

    Returns:
        Use case for getting a single bounded context
    """
    return GetBoundedContextUseCase(get_bounded_context_repository())


# =============================================================================
# Code Artifact Use Cases
# =============================================================================


def get_list_entities_use_case() -> ListEntitiesUseCase:
    """Get ListEntitiesUseCase with repository dependency.

    Returns:
        Use case for listing domain entities
    """
    return ListEntitiesUseCase(get_bounded_context_repository())


def get_list_use_cases_use_case() -> ListUseCasesUseCase:
    """Get ListUseCasesUseCase with repository dependency.

    Returns:
        Use case for listing use case classes
    """
    return ListUseCasesUseCase(get_bounded_context_repository())


def get_list_repository_protocols_use_case() -> ListRepositoryProtocolsUseCase:
    """Get ListRepositoryProtocolsUseCase with repository dependency.

    Returns:
        Use case for listing repository protocols
    """
    return ListRepositoryProtocolsUseCase(get_bounded_context_repository())


def get_list_service_protocols_use_case() -> ListServiceProtocolsUseCase:
    """Get ListServiceProtocolsUseCase with repository dependency.

    Returns:
        Use case for listing service protocols
    """
    return ListServiceProtocolsUseCase(get_bounded_context_repository())


def get_list_requests_use_case() -> ListRequestsUseCase:
    """Get ListRequestsUseCase with repository dependency.

    Returns:
        Use case for listing request DTOs
    """
    return ListRequestsUseCase(get_bounded_context_repository())


def get_list_responses_use_case() -> ListResponsesUseCase:
    """Get ListResponsesUseCase with repository dependency.

    Returns:
        Use case for listing response DTOs
    """
    return ListResponsesUseCase(get_bounded_context_repository())


# =============================================================================
# Solution Structure Repositories
# =============================================================================


@lru_cache
def get_solution_repository() -> FilesystemSolutionRepository:
    """Get the solution repository singleton.

    Returns:
        Repository for discovering the solution structure

    Raises:
        ValueError: If search_root is not configured
    """
    return FilesystemSolutionRepository(
        get_project_root(),
        require_search_root(),
    )


@lru_cache
def get_application_repository() -> FilesystemApplicationRepository:
    """Get the application repository singleton.

    Returns:
        Repository for discovering applications in the solution
    """
    return FilesystemApplicationRepository(get_project_root())


@lru_cache
def get_deployment_repository() -> FilesystemDeploymentRepository:
    """Get the deployment repository singleton.

    Returns:
        Repository for discovering deployments in the solution
    """
    return FilesystemDeploymentRepository(get_project_root())


# =============================================================================
# Doctrine Use Cases
# =============================================================================

# Framework paths for doctrine tests and entity definitions
_FRAMEWORK_ROOT = Path(__file__).parent.parent.parent
_DOCTRINE_DIR = _FRAMEWORK_ROOT / "src" / "julee" / "core" / "doctrine"
_ENTITIES_DIR = _FRAMEWORK_ROOT / "src" / "julee" / "core" / "entities"


@lru_cache
def get_doctrine_repository():
    """Get the doctrine repository singleton.

    Returns:
        Repository for extracting doctrine rules from test files
    """
    from julee.core.infrastructure.repositories.introspection.doctrine import (
        FilesystemDoctrineRepository,
    )

    return FilesystemDoctrineRepository(
        doctrine_dir=_DOCTRINE_DIR,
        entities_dir=_ENTITIES_DIR,
    )


def get_list_doctrine_areas_use_case():
    """Get ListDoctrineAreasUseCase with repository dependency.

    Returns:
        Use case for listing doctrine areas
    """
    from julee.core.use_cases.doctrine.list import ListDoctrineAreasUseCase

    return ListDoctrineAreasUseCase(doctrine_repository=get_doctrine_repository())


def get_list_doctrine_rules_use_case():
    """Get ListDoctrineRulesUseCase with repository dependency.

    Returns:
        Use case for listing doctrine rules
    """
    from julee.core.use_cases.doctrine.list import ListDoctrineRulesUseCase

    return ListDoctrineRulesUseCase(doctrine_repository=get_doctrine_repository())


def get_doctrine_verifier():
    """Get the doctrine verifier service.

    Returns:
        Service for running doctrine verification tests
    """
    from julee.core.infrastructure.services.doctrine_verifier import (
        PytestDoctrineVerifier,
    )

    return PytestDoctrineVerifier(
        doctrine_dir=_DOCTRINE_DIR,
        entities_dir=_ENTITIES_DIR,
    )


def get_verify_doctrine_use_case():
    """Get VerifyDoctrineUseCase with verifier dependency.

    Returns:
        Use case for verifying doctrine compliance
    """
    from julee.core.use_cases.doctrine.verify import VerifyDoctrineUseCase

    return VerifyDoctrineUseCase(doctrine_verifier=get_doctrine_verifier())


# =============================================================================
# Policy Use Cases
# =============================================================================


@lru_cache
def get_policy_repository():
    """Get the policy repository singleton.

    Returns:
        Repository for accessing available policies
    """
    from julee.core.infrastructure.repositories.memory.policy import (
        RegistryPolicyRepository,
    )

    return RegistryPolicyRepository()


def get_solution_config_repository():
    """Get the solution config repository.

    Returns:
        Repository for reading solution configuration from pyproject.toml
    """
    from julee.core.infrastructure.repositories.file.solution_config import (
        FileSolutionConfigRepository,
    )

    return FileSolutionConfigRepository()


def get_policy_adoption_service():
    """Get the policy adoption service.

    Returns:
        Service for computing effective policy adoptions
    """
    from julee.core.infrastructure.services.policy_adoption import (
        DefaultPolicyAdoptionService,
    )

    return DefaultPolicyAdoptionService()


def get_list_policies_use_case():
    """Get ListPoliciesUseCase with dependencies.

    Returns:
        Use case for listing available policies
    """
    from julee.core.use_cases.policy.list import ListPoliciesUseCase

    return ListPoliciesUseCase(policy_repository=get_policy_repository())


def get_effective_policies_use_case():
    """Get GetEffectivePoliciesUseCase with dependencies.

    Returns:
        Use case for computing effective policies for a solution
    """
    from julee.core.use_cases.policy.get_effective import GetEffectivePoliciesUseCase

    return GetEffectivePoliciesUseCase(
        solution_config_repository=get_solution_config_repository(),
        policy_repository=get_policy_repository(),
        policy_adoption_service=get_policy_adoption_service(),
    )


# =============================================================================
# HCD Repositories (RST file-backed)
# =============================================================================


def get_docs_path() -> Path:
    """Get the docs directory path for the solution.

    Returns:
        Path to the docs directory

    Raises:
        ValueError: If docs_root is not configured
    """
    return get_project_root() / require_docs_root()


@lru_cache
def get_persona_repository():
    """Get the persona repository singleton.

    Returns:
        RST file-backed PersonaRepository
    """
    from julee.hcd.infrastructure.repositories.rst.persona import RstPersonaRepository

    return RstPersonaRepository(get_docs_path() / "users" / "personas")


@lru_cache
def get_journey_repository():
    """Get the journey repository singleton.

    Returns:
        RST file-backed JourneyRepository
    """
    from julee.hcd.infrastructure.repositories.rst.journey import RstJourneyRepository

    return RstJourneyRepository(get_docs_path() / "users" / "journeys")


@lru_cache
def get_epic_repository():
    """Get the epic repository singleton.

    Returns:
        RST file-backed EpicRepository
    """
    from julee.hcd.infrastructure.repositories.rst.epic import RstEpicRepository

    return RstEpicRepository(get_docs_path() / "users" / "epics")


@lru_cache
def get_story_repository():
    """Get the story repository singleton.

    Returns:
        RST file-backed StoryRepository
    """
    from julee.hcd.infrastructure.repositories.rst.story import RstStoryRepository

    return RstStoryRepository(get_docs_path() / "users" / "stories")


@lru_cache
def get_app_repository():
    """Get the app repository singleton.

    Returns:
        RST file-backed AppRepository
    """
    from julee.hcd.infrastructure.repositories.rst.app import RstAppRepository

    return RstAppRepository(get_docs_path() / "domain" / "applications")


@lru_cache
def get_accelerator_repository():
    """Get the accelerator repository singleton.

    Returns:
        RST file-backed AcceleratorRepository
    """
    from julee.supply_chain.infrastructure.repositories.rst.accelerator import (
        RstAcceleratorRepository,
    )

    return RstAcceleratorRepository(get_docs_path() / "domain" / "accelerators")


@lru_cache
def get_integration_repository():
    """Get the integration repository singleton.

    Returns:
        RST file-backed IntegrationRepository
    """
    from julee.hcd.infrastructure.repositories.rst.integration import (
        RstIntegrationRepository,
    )

    return RstIntegrationRepository(get_docs_path() / "domain" / "integrations")


# =============================================================================
# HCD Use Cases
# =============================================================================


def get_list_personas_use_case():
    """Get ListPersonasUseCase with repository dependency.

    Returns:
        Use case for listing personas
    """
    from julee.hcd.use_cases.crud import ListPersonasUseCase

    return ListPersonasUseCase(repo=get_persona_repository())


def get_get_persona_use_case():
    """Get GetPersonaUseCase with repository dependency.

    Returns:
        Use case for getting a single persona
    """
    from julee.hcd.use_cases.crud import GetPersonaUseCase

    return GetPersonaUseCase(repo=get_persona_repository())


def get_list_journeys_use_case():
    """Get ListJourneysUseCase with repository dependency.

    Returns:
        Use case for listing journeys
    """
    from julee.hcd.use_cases.crud import ListJourneysUseCase

    return ListJourneysUseCase(repo=get_journey_repository())


def get_get_journey_use_case():
    """Get GetJourneyUseCase with repository dependency.

    Returns:
        Use case for getting a single journey
    """
    from julee.hcd.use_cases.crud import GetJourneyUseCase

    return GetJourneyUseCase(repo=get_journey_repository())


def get_list_epics_use_case():
    """Get ListEpicsUseCase with repository dependency.

    Returns:
        Use case for listing epics
    """
    from julee.hcd.use_cases.crud import ListEpicsUseCase

    return ListEpicsUseCase(repo=get_epic_repository())


def get_get_epic_use_case():
    """Get GetEpicUseCase with repository dependency.

    Returns:
        Use case for getting a single epic
    """
    from julee.hcd.use_cases.crud import GetEpicUseCase

    return GetEpicUseCase(repo=get_epic_repository())


def get_list_stories_use_case():
    """Get ListStoriesUseCase with repository dependency.

    Returns:
        Use case for listing stories
    """
    from julee.hcd.use_cases.crud import ListStoriesUseCase

    return ListStoriesUseCase(repo=get_story_repository())


def get_get_story_use_case():
    """Get GetStoryUseCase with repository dependency.

    Returns:
        Use case for getting a single story
    """
    from julee.hcd.use_cases.crud import GetStoryUseCase

    return GetStoryUseCase(repo=get_story_repository())


def get_list_apps_use_case():
    """Get ListAppsUseCase with repository dependency.

    Returns:
        Use case for listing apps
    """
    from julee.hcd.use_cases.crud import ListAppsUseCase

    return ListAppsUseCase(repo=get_app_repository())


def get_get_app_use_case():
    """Get GetAppUseCase with repository dependency.

    Returns:
        Use case for getting a single app
    """
    from julee.hcd.use_cases.crud import GetAppUseCase

    return GetAppUseCase(repo=get_app_repository())


def get_list_accelerators_use_case():
    """Get ListAcceleratorsUseCase with repository dependency.

    Returns:
        Use case for listing accelerators
    """
    from julee.hcd.use_cases.crud import ListAcceleratorsUseCase

    return ListAcceleratorsUseCase(repo=get_accelerator_repository())


def get_get_accelerator_use_case():
    """Get GetAcceleratorUseCase with repository dependency.

    Returns:
        Use case for getting a single accelerator
    """
    from julee.hcd.use_cases.crud import GetAcceleratorUseCase

    return GetAcceleratorUseCase(repo=get_accelerator_repository())


def get_list_integrations_use_case():
    """Get ListIntegrationsUseCase with repository dependency.

    Returns:
        Use case for listing integrations
    """
    from julee.hcd.use_cases.crud import ListIntegrationsUseCase

    return ListIntegrationsUseCase(repo=get_integration_repository())


def get_get_integration_use_case():
    """Get GetIntegrationUseCase with repository dependency.

    Returns:
        Use case for getting a single integration
    """
    from julee.hcd.use_cases.crud import GetIntegrationUseCase

    return GetIntegrationUseCase(repo=get_integration_repository())
