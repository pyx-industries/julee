"""Response DTOs for HCD API.

Response models wrap domain models, enabling pagination and additional
metadata while maintaining type safety. Following clean architecture,
most responses wrap domain models rather than duplicating their structure.
"""

from pydantic import BaseModel

from julee.hcd.domain.models.accelerator import Accelerator
from julee.hcd.domain.models.app import App
from julee.hcd.domain.models.epic import Epic
from julee.hcd.domain.models.integration import Integration
from julee.hcd.domain.models.journey import Journey
from julee.hcd.domain.models.persona import Persona
from julee.hcd.domain.models.story import Story

# =============================================================================
# Story Responses
# =============================================================================


class CreateStoryResponse(BaseModel):
    """Response from creating a story."""

    story: Story


class GetStoryResponse(BaseModel):
    """Response from getting a story."""

    story: Story | None


class ListStoriesResponse(BaseModel):
    """Response from listing stories."""

    stories: list[Story]


class UpdateStoryResponse(BaseModel):
    """Response from updating a story."""

    story: Story | None
    found: bool = True


class DeleteStoryResponse(BaseModel):
    """Response from deleting a story."""

    deleted: bool


# =============================================================================
# Epic Responses
# =============================================================================


class CreateEpicResponse(BaseModel):
    """Response from creating an epic."""

    epic: Epic


class GetEpicResponse(BaseModel):
    """Response from getting an epic."""

    epic: Epic | None


class ListEpicsResponse(BaseModel):
    """Response from listing epics."""

    epics: list[Epic]


class UpdateEpicResponse(BaseModel):
    """Response from updating an epic."""

    epic: Epic | None
    found: bool = True


class DeleteEpicResponse(BaseModel):
    """Response from deleting an epic."""

    deleted: bool


# =============================================================================
# Journey Responses
# =============================================================================


class CreateJourneyResponse(BaseModel):
    """Response from creating a journey."""

    journey: Journey


class GetJourneyResponse(BaseModel):
    """Response from getting a journey."""

    journey: Journey | None


class ListJourneysResponse(BaseModel):
    """Response from listing journeys."""

    journeys: list[Journey]


class UpdateJourneyResponse(BaseModel):
    """Response from updating a journey."""

    journey: Journey | None
    found: bool = True


class DeleteJourneyResponse(BaseModel):
    """Response from deleting a journey."""

    deleted: bool


# =============================================================================
# Accelerator Responses
# =============================================================================


class CreateAcceleratorResponse(BaseModel):
    """Response from creating an accelerator."""

    accelerator: Accelerator


class GetAcceleratorResponse(BaseModel):
    """Response from getting an accelerator."""

    accelerator: Accelerator | None


class ListAcceleratorsResponse(BaseModel):
    """Response from listing accelerators."""

    accelerators: list[Accelerator]


class UpdateAcceleratorResponse(BaseModel):
    """Response from updating an accelerator."""

    accelerator: Accelerator | None
    found: bool = True


class DeleteAcceleratorResponse(BaseModel):
    """Response from deleting an accelerator."""

    deleted: bool


# =============================================================================
# Integration Responses
# =============================================================================


class CreateIntegrationResponse(BaseModel):
    """Response from creating an integration."""

    integration: Integration


class GetIntegrationResponse(BaseModel):
    """Response from getting an integration."""

    integration: Integration | None


class ListIntegrationsResponse(BaseModel):
    """Response from listing integrations."""

    integrations: list[Integration]


class UpdateIntegrationResponse(BaseModel):
    """Response from updating an integration."""

    integration: Integration | None
    found: bool = True


class DeleteIntegrationResponse(BaseModel):
    """Response from deleting an integration."""

    deleted: bool


# =============================================================================
# App Responses
# =============================================================================


class CreateAppResponse(BaseModel):
    """Response from creating an app."""

    app: App


class GetAppResponse(BaseModel):
    """Response from getting an app."""

    app: App | None


class ListAppsResponse(BaseModel):
    """Response from listing apps."""

    apps: list[App]


class UpdateAppResponse(BaseModel):
    """Response from updating an app."""

    app: App | None
    found: bool = True


class DeleteAppResponse(BaseModel):
    """Response from deleting an app."""

    deleted: bool


# =============================================================================
# Query Responses
# =============================================================================


class DerivePersonasResponse(BaseModel):
    """Response from deriving personas."""

    personas: list[Persona]


class GetPersonaResponse(BaseModel):
    """Response from getting a persona by name."""

    persona: Persona | None


# =============================================================================
# Persona Responses
# =============================================================================


class CreatePersonaResponse(BaseModel):
    """Response from creating a persona."""

    persona: Persona


class ListPersonasResponse(BaseModel):
    """Response from listing personas."""

    personas: list[Persona]


class UpdatePersonaResponse(BaseModel):
    """Response from updating a persona."""

    persona: Persona | None
    found: bool = True


class DeletePersonaResponse(BaseModel):
    """Response from deleting a persona."""

    deleted: bool


# =============================================================================
# Validation Responses
# =============================================================================


class AcceleratorValidationIssue(BaseModel):
    """A single validation issue for an accelerator."""

    slug: str
    issue_type: str  # "undocumented", "no_code", "mismatch"
    message: str


class ValidateAcceleratorsResponse(BaseModel):
    """Response from validating accelerators against code structure.

    Contains lists of matched accelerators and any issues found.
    """

    documented_slugs: list[str]
    discovered_slugs: list[str]
    matched_slugs: list[str]
    issues: list[AcceleratorValidationIssue]

    @property
    def is_valid(self) -> bool:
        """Check if validation passed with no issues."""
        return len(self.issues) == 0
