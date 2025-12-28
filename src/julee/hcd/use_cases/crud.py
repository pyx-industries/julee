"""CRUD use cases for HCD entities.

Uses generic_crud.generate() for standard CRUD operations.
Custom response methods and validators are added via class extension.
"""

from typing import Any

from pydantic import Field, field_validator

from julee.core.use_cases import generic_crud
from julee.hcd.entities.accelerator import Accelerator
from julee.hcd.entities.app import App, AppType
from julee.hcd.entities.epic import Epic
from julee.hcd.entities.integration import Integration
from julee.hcd.entities.journey import Journey
from julee.hcd.entities.persona import Persona
from julee.hcd.entities.story import Story
from julee.hcd.repositories.accelerator import AcceleratorRepository
from julee.hcd.repositories.app import AppRepository
from julee.hcd.repositories.epic import EpicRepository
from julee.hcd.repositories.integration import IntegrationRepository
from julee.hcd.repositories.journey import JourneyRepository
from julee.hcd.repositories.persona import PersonaRepository
from julee.hcd.repositories.story import StoryRepository

# =============================================================================
# Story - with custom list response methods
# =============================================================================

generic_crud.generate(
    Story,
    StoryRepository,
    filters=["app_slug", "persona"],
)


# Extend generated response with grouping methods
class ListStoriesResponse(ListStoriesResponse):  # type: ignore[no-redef]  # noqa: F821
    """Stories list response with grouping methods."""

    def grouped_by_persona(self) -> dict[str, list[Story]]:
        """Group stories by persona."""
        result: dict[str, list[Story]] = {}
        for story in self.entities:
            result.setdefault(story.persona, []).append(story)
        return result

    def grouped_by_app(self) -> dict[str, list[Story]]:
        """Group stories by app slug."""
        result: dict[str, list[Story]] = {}
        for story in self.entities:
            result.setdefault(story.app_slug, []).append(story)
        return result


# Update use case to use extended response
ListStoriesUseCase.response_cls = ListStoriesResponse  # type: ignore[attr-defined]  # noqa: F821


# =============================================================================
# Epic - with custom list request (typed filters) and response
# =============================================================================

# Generate with filters to get FilterableListUseCase
generic_crud.generate(Epic, EpicRepository, filters=["has_stories", "contains_story"])


# Override list request with typed filters (generated one has str | None)
class ListEpicsRequest(ListEpicsRequest):  # type: ignore[no-redef]  # noqa: F821
    """List epics with optional filters."""

    has_stories: bool | None = Field(
        default=None, description="Filter to epics with/without stories"
    )
    contains_story: str | None = Field(
        default=None, description="Filter to epics containing this story"
    )


class ListEpicsResponse(ListEpicsResponse):  # type: ignore[no-redef]  # noqa: F821
    """Epics list response with total stories."""

    @property
    def total_stories(self) -> int:
        """Total number of stories across all epics."""
        return sum(len(epic.story_refs) for epic in self.entities)


ListEpicsUseCase.response_cls = ListEpicsResponse  # type: ignore[attr-defined]  # noqa: F821


# =============================================================================
# Persona - simple CRUD
# =============================================================================

generic_crud.generate(Persona, PersonaRepository)

# Backward compatibility aliases (tests use GetPersonaBySlug* names)
GetPersonaBySlugRequest = GetPersonaRequest  # type: ignore[name-defined] # noqa: F821
GetPersonaBySlugResponse = GetPersonaResponse  # type: ignore[name-defined] # noqa: F821
GetPersonaBySlugUseCase = GetPersonaUseCase  # type: ignore[name-defined] # noqa: F821


# =============================================================================
# Journey - with filters
# =============================================================================

generic_crud.generate(
    Journey,
    JourneyRepository,
    filters=["contains_story"],
)


# =============================================================================
# App - with custom validators and response methods
# =============================================================================

generic_crud.generate(
    App,
    AppRepository,
    filters=["app_type", "has_accelerator"],
)


class ListAppsResponse(ListAppsResponse):  # type: ignore[no-redef]  # noqa: F821
    """Apps list response with grouping methods."""

    def grouped_by_type(self) -> dict[str, list[App]]:
        """Group apps by app type."""
        result: dict[str, list[App]] = {}
        for app in self.entities:
            type_key = app.app_type.value if app.app_type else "unknown"
            result.setdefault(type_key, []).append(app)
        return result


ListAppsUseCase.response_cls = ListAppsResponse  # type: ignore[attr-defined]  # noqa: F821


# Custom Create/Update requests with AppType coercion
class CreateAppRequest(CreateAppRequest):  # type: ignore[no-redef]  # noqa: F821
    """Create app request with enum coercion."""

    @field_validator("app_type", mode="before")
    @classmethod
    def coerce_app_type(cls, v: Any) -> AppType:
        """Coerce string to AppType enum."""
        if isinstance(v, str):
            return AppType.from_string(v)
        return v


class UpdateAppRequest(UpdateAppRequest):  # type: ignore[no-redef]  # noqa: F821
    """Update app request with enum coercion."""

    @field_validator("app_type", mode="before")
    @classmethod
    def coerce_app_type(cls, v: Any) -> AppType | None:
        """Coerce string to AppType enum."""
        if v is None:
            return None
        if isinstance(v, str):
            return AppType.from_string(v)
        return v


# =============================================================================
# Accelerator - with filters
# =============================================================================

generic_crud.generate(
    Accelerator,
    AcceleratorRepository,
    filters=["status"],
)


# =============================================================================
# Integration - simple CRUD
# =============================================================================

generic_crud.generate(Integration, IntegrationRepository)


# =============================================================================
# ContribModule - simple CRUD
# =============================================================================

from julee.hcd.entities.contrib import ContribModule
from julee.hcd.repositories.contrib import ContribRepository

generic_crud.generate(ContribModule, ContribRepository)


# =============================================================================
# BoundedContextInfo (CodeInfo) - Get only (no create/update/delete/list)
# Code info is populated via introspection, not CRUD operations
# =============================================================================

from pydantic import BaseModel

from julee.core.decorators import use_case
from julee.hcd.entities.code_info import BoundedContextInfo
from julee.hcd.repositories.code_info import CodeInfoRepository


class GetCodeInfoRequest(BaseModel):
    """Request to get code info for a bounded context."""

    slug: str


class GetCodeInfoResponse(BaseModel):
    """Response containing code info for a bounded context."""

    code_info: BoundedContextInfo | None = None


@use_case
class GetCodeInfoUseCase:
    """Get code introspection info for a bounded context by slug."""

    def __init__(self, repo: CodeInfoRepository) -> None:
        self.repo = repo

    async def execute(self, request: GetCodeInfoRequest) -> GetCodeInfoResponse:
        code_info = await self.repo.get(request.slug)
        return GetCodeInfoResponse(code_info=code_info)
