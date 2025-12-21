"""Request DTOs for HCD API.

Following clean architecture principles, request models define the contract
between the API and external clients. They delegate validation to domain
models and reuse field descriptions to maintain single source of truth.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator

from julee.hcd.domain.models.accelerator import Accelerator, IntegrationReference
from julee.hcd.domain.models.app import App, AppType
from julee.hcd.domain.models.epic import Epic
from julee.hcd.domain.models.integration import (
    Direction,
    ExternalDependency,
    Integration,
)
from julee.hcd.domain.models.journey import Journey, JourneyStep
from julee.hcd.domain.models.persona import Persona
from julee.hcd.domain.models.story import Story

# =============================================================================
# Story DTOs
# =============================================================================


class CreateStoryRequest(BaseModel):
    """Request model for creating a story.

    Fields excluded from client control:
    - slug: Generated from feature_title + app_slug
    - persona_normalized/app_normalized: Computed by domain model
    """

    feature_title: str = Field(description="The Feature: line from the Gherkin file")
    persona: str = Field(description="The actor from 'As a <persona>'")
    app_slug: str = Field(description="The application this story belongs to")
    i_want: str = Field(
        default="do something", description="The action from 'I want to <action>'"
    )
    so_that: str = Field(
        default="achieve a goal", description="The benefit from 'So that <benefit>'"
    )
    file_path: str = Field(default="", description="Relative path to the .feature file")
    abs_path: str = Field(default="", description="Absolute path to the .feature file")
    gherkin_snippet: str = Field(
        default="", description="The story header portion of the feature file"
    )

    @field_validator("feature_title")
    @classmethod
    def validate_feature_title(cls, v: str) -> str:
        return Story.validate_feature_title(v)

    @field_validator("persona")
    @classmethod
    def validate_persona(cls, v: str) -> str:
        return Story.validate_persona(v)

    @field_validator("app_slug")
    @classmethod
    def validate_app_slug(cls, v: str) -> str:
        return Story.validate_app_slug(v)

    def to_domain_model(self) -> Story:
        """Convert to Story, generating slug from feature_title + app_slug."""
        return Story.from_feature_file(
            feature_title=self.feature_title,
            persona=self.persona,
            i_want=self.i_want,
            so_that=self.so_that,
            app_slug=self.app_slug,
            file_path=self.file_path,
            abs_path=self.abs_path,
            gherkin_snippet=self.gherkin_snippet,
        )


class GetStoryRequest(BaseModel):
    """Request for getting a story by slug."""

    slug: str


class ListStoriesRequest(BaseModel):
    """Request for listing stories (extensible for filtering/pagination)."""

    pass


class UpdateStoryRequest(BaseModel):
    """Request for updating a story (slug identifies target)."""

    slug: str
    feature_title: str | None = None
    persona: str | None = None
    i_want: str | None = None
    so_that: str | None = None
    file_path: str | None = None
    abs_path: str | None = None
    gherkin_snippet: str | None = None

    def apply_to(self, existing: Story) -> Story:
        """Apply non-None fields to existing story."""
        updates = {
            k: v
            for k, v in {
                "feature_title": self.feature_title,
                "persona": self.persona,
                "i_want": self.i_want,
                "so_that": self.so_that,
                "file_path": self.file_path,
                "abs_path": self.abs_path,
                "gherkin_snippet": self.gherkin_snippet,
            }.items()
            if v is not None
        }
        return existing.model_copy(update=updates) if updates else existing


class DeleteStoryRequest(BaseModel):
    """Request for deleting a story by slug."""

    slug: str


# =============================================================================
# Epic DTOs
# =============================================================================


class CreateEpicRequest(BaseModel):
    """Request model for creating an epic.

    Fields excluded from client control:
    - docname: Set when persisted
    """

    slug: str = Field(description="URL-safe identifier")
    description: str = Field(
        default="", description="Human-readable description of the epic"
    )
    story_refs: list[str] = Field(
        default_factory=list, description="List of story feature titles in this epic"
    )

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        return Epic.validate_slug(v)

    def to_domain_model(self) -> Epic:
        """Convert to Epic."""
        return Epic(
            slug=self.slug,
            description=self.description,
            story_refs=self.story_refs,
            docname="",
        )


class GetEpicRequest(BaseModel):
    """Request for getting an epic by slug."""

    slug: str


class ListEpicsRequest(BaseModel):
    """Request for listing epics."""

    pass


class UpdateEpicRequest(BaseModel):
    """Request for updating an epic."""

    slug: str
    description: str | None = None
    story_refs: list[str] | None = None

    def apply_to(self, existing: Epic) -> Epic:
        """Apply non-None fields to existing epic."""
        updates = {
            k: v
            for k, v in {
                "description": self.description,
                "story_refs": self.story_refs,
            }.items()
            if v is not None
        }
        return existing.model_copy(update=updates) if updates else existing


class DeleteEpicRequest(BaseModel):
    """Request for deleting an epic by slug."""

    slug: str


# =============================================================================
# Journey DTOs
# =============================================================================


class JourneyStepInput(BaseModel):
    """Input model for journey step."""

    step_type: str = Field(description="Type of step: story, epic, or phase")
    ref: str = Field(description="Reference identifier")
    description: str = Field(default="", description="Optional description")

    def to_domain_model(self) -> JourneyStep:
        """Convert to JourneyStep."""
        from julee.hcd.domain.models.journey import StepType

        return JourneyStep(
            step_type=StepType.from_string(self.step_type),
            ref=self.ref,
            description=self.description,
        )


class CreateJourneyRequest(BaseModel):
    """Request model for creating a journey.

    Fields excluded from client control:
    - persona_normalized: Computed by domain model
    - docname: Set when persisted
    """

    slug: str = Field(description="URL-safe identifier")
    persona: str = Field(default="", description="The persona undertaking this journey")
    intent: str = Field(
        default="", description="What the persona wants (their motivation)"
    )
    outcome: str = Field(
        default="", description="What success looks like (business value)"
    )
    goal: str = Field(default="", description="Activity description (what they do)")
    depends_on: list[str] = Field(
        default_factory=list, description="Journey slugs that must be completed first"
    )
    steps: list[JourneyStepInput] = Field(
        default_factory=list, description="Sequence of journey steps"
    )
    preconditions: list[str] = Field(
        default_factory=list, description="Conditions that must be true before starting"
    )
    postconditions: list[str] = Field(
        default_factory=list,
        description="Conditions that will be true after completion",
    )

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        return Journey.validate_slug(v)

    def to_domain_model(self) -> Journey:
        """Convert to Journey."""
        return Journey(
            slug=self.slug,
            persona=self.persona,
            intent=self.intent,
            outcome=self.outcome,
            goal=self.goal,
            depends_on=self.depends_on,
            steps=[s.to_domain_model() for s in self.steps],
            preconditions=self.preconditions,
            postconditions=self.postconditions,
            docname="",
        )


class GetJourneyRequest(BaseModel):
    """Request for getting a journey by slug."""

    slug: str


class ListJourneysRequest(BaseModel):
    """Request for listing journeys."""

    pass


class UpdateJourneyRequest(BaseModel):
    """Request for updating a journey."""

    slug: str
    persona: str | None = None
    intent: str | None = None
    outcome: str | None = None
    goal: str | None = None
    depends_on: list[str] | None = None
    steps: list[JourneyStepInput] | None = None
    preconditions: list[str] | None = None
    postconditions: list[str] | None = None

    def apply_to(self, existing: Journey) -> Journey:
        """Apply non-None fields to existing journey."""
        updates: dict[str, Any] = {}
        if self.persona is not None:
            updates["persona"] = self.persona
        if self.intent is not None:
            updates["intent"] = self.intent
        if self.outcome is not None:
            updates["outcome"] = self.outcome
        if self.goal is not None:
            updates["goal"] = self.goal
        if self.depends_on is not None:
            updates["depends_on"] = self.depends_on
        if self.steps is not None:
            updates["steps"] = [s.to_domain_model() for s in self.steps]
        if self.preconditions is not None:
            updates["preconditions"] = self.preconditions
        if self.postconditions is not None:
            updates["postconditions"] = self.postconditions
        return existing.model_copy(update=updates) if updates else existing


class DeleteJourneyRequest(BaseModel):
    """Request for deleting a journey by slug."""

    slug: str


# =============================================================================
# Accelerator DTOs
# =============================================================================


class IntegrationReferenceInput(BaseModel):
    """Input model for integration reference."""

    slug: str = Field(description="Integration slug")
    description: str = Field(default="", description="What is sourced/published")

    def to_domain_model(self) -> IntegrationReference:
        """Convert to IntegrationReference."""
        return IntegrationReference(slug=self.slug, description=self.description)


class CreateAcceleratorRequest(BaseModel):
    """Request model for creating an accelerator.

    Fields excluded from client control:
    - docname: Set when persisted
    """

    slug: str = Field(description="URL-safe identifier")
    status: str = Field(default="", description="Development status")
    milestone: str | None = Field(default=None, description="Target milestone")
    acceptance: str | None = Field(
        default=None, description="Acceptance criteria description"
    )
    objective: str = Field(default="", description="Business objective/description")
    sources_from: list[IntegrationReferenceInput] = Field(
        default_factory=list, description="Integrations this accelerator reads from"
    )
    feeds_into: list[str] = Field(
        default_factory=list, description="Other accelerators this one feeds data into"
    )
    publishes_to: list[IntegrationReferenceInput] = Field(
        default_factory=list, description="Integrations this accelerator writes to"
    )
    depends_on: list[str] = Field(
        default_factory=list, description="Other accelerators this one depends on"
    )

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        return Accelerator.validate_slug(v)

    def to_domain_model(self) -> Accelerator:
        """Convert to Accelerator."""
        return Accelerator(
            slug=self.slug,
            status=self.status,
            milestone=self.milestone,
            acceptance=self.acceptance,
            objective=self.objective,
            sources_from=[s.to_domain_model() for s in self.sources_from],
            feeds_into=self.feeds_into,
            publishes_to=[p.to_domain_model() for p in self.publishes_to],
            depends_on=self.depends_on,
            docname="",
        )


class GetAcceleratorRequest(BaseModel):
    """Request for getting an accelerator by slug."""

    slug: str


class ListAcceleratorsRequest(BaseModel):
    """Request for listing accelerators."""

    pass


class UpdateAcceleratorRequest(BaseModel):
    """Request for updating an accelerator."""

    slug: str
    status: str | None = None
    milestone: str | None = None
    acceptance: str | None = None
    objective: str | None = None
    sources_from: list[IntegrationReferenceInput] | None = None
    feeds_into: list[str] | None = None
    publishes_to: list[IntegrationReferenceInput] | None = None
    depends_on: list[str] | None = None

    def apply_to(self, existing: Accelerator) -> Accelerator:
        """Apply non-None fields to existing accelerator."""
        updates: dict[str, Any] = {}
        if self.status is not None:
            updates["status"] = self.status
        if self.milestone is not None:
            updates["milestone"] = self.milestone
        if self.acceptance is not None:
            updates["acceptance"] = self.acceptance
        if self.objective is not None:
            updates["objective"] = self.objective
        if self.sources_from is not None:
            updates["sources_from"] = [s.to_domain_model() for s in self.sources_from]
        if self.feeds_into is not None:
            updates["feeds_into"] = self.feeds_into
        if self.publishes_to is not None:
            updates["publishes_to"] = [p.to_domain_model() for p in self.publishes_to]
        if self.depends_on is not None:
            updates["depends_on"] = self.depends_on
        return existing.model_copy(update=updates) if updates else existing


class DeleteAcceleratorRequest(BaseModel):
    """Request for deleting an accelerator by slug."""

    slug: str


# =============================================================================
# Integration DTOs
# =============================================================================


class ExternalDependencyInput(BaseModel):
    """Input model for external dependency."""

    name: str = Field(description="Display name of the external system")
    url: str | None = Field(
        default=None, description="URL for documentation or reference"
    )
    description: str = Field(default="", description="Brief description")

    def to_domain_model(self) -> ExternalDependency:
        """Convert to ExternalDependency."""
        return ExternalDependency(
            name=self.name, url=self.url, description=self.description
        )


class CreateIntegrationRequest(BaseModel):
    """Request model for creating an integration.

    Fields excluded from client control:
    - name_normalized: Computed by domain model
    - manifest_path: Set when persisted
    """

    slug: str = Field(description="URL-safe identifier")
    module: str = Field(description="Python module name")
    name: str = Field(description="Display name")
    description: str = Field(default="", description="Human-readable description")
    direction: str = Field(
        default="bidirectional",
        description="Data flow direction: inbound, outbound, bidirectional",
    )
    depends_on: list[ExternalDependencyInput] = Field(
        default_factory=list, description="List of external dependencies"
    )

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        return Integration.validate_slug(v)

    @field_validator("module")
    @classmethod
    def validate_module(cls, v: str) -> str:
        return Integration.validate_module(v)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return Integration.validate_name(v)

    def to_domain_model(self) -> Integration:
        """Convert to Integration."""
        return Integration(
            slug=self.slug,
            module=self.module,
            name=self.name,
            description=self.description,
            direction=Direction.from_string(self.direction),
            depends_on=[d.to_domain_model() for d in self.depends_on],
            manifest_path="",
        )


class GetIntegrationRequest(BaseModel):
    """Request for getting an integration by slug."""

    slug: str


class ListIntegrationsRequest(BaseModel):
    """Request for listing integrations."""

    pass


class UpdateIntegrationRequest(BaseModel):
    """Request for updating an integration."""

    slug: str
    name: str | None = None
    description: str | None = None
    direction: str | None = None
    depends_on: list[ExternalDependencyInput] | None = None

    def apply_to(self, existing: Integration) -> Integration:
        """Apply non-None fields to existing integration."""
        updates: dict[str, Any] = {}
        if self.name is not None:
            updates["name"] = self.name
        if self.description is not None:
            updates["description"] = self.description
        if self.direction is not None:
            updates["direction"] = Direction.from_string(self.direction)
        if self.depends_on is not None:
            updates["depends_on"] = [d.to_domain_model() for d in self.depends_on]
        return existing.model_copy(update=updates) if updates else existing


class DeleteIntegrationRequest(BaseModel):
    """Request for deleting an integration by slug."""

    slug: str


# =============================================================================
# App DTOs
# =============================================================================


class CreateAppRequest(BaseModel):
    """Request model for creating an app.

    Fields excluded from client control:
    - name_normalized: Computed by domain model
    - manifest_path: Set when persisted
    """

    slug: str = Field(description="URL-safe identifier")
    name: str = Field(description="Display name")
    app_type: str = Field(
        default="unknown",
        description="Classification: staff, external, member-tool, unknown",
    )
    status: str | None = Field(default=None, description="Status indicator")
    description: str = Field(default="", description="Human-readable description")
    accelerators: list[str] = Field(
        default_factory=list, description="List of accelerator slugs"
    )

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        return App.validate_slug(v)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return App.validate_name(v)

    def to_domain_model(self) -> App:
        """Convert to App."""
        return App(
            slug=self.slug,
            name=self.name,
            app_type=AppType.from_string(self.app_type),
            status=self.status,
            description=self.description,
            accelerators=self.accelerators,
            manifest_path="",
        )


class GetAppRequest(BaseModel):
    """Request for getting an app by slug."""

    slug: str


class ListAppsRequest(BaseModel):
    """Request for listing apps."""

    pass


class UpdateAppRequest(BaseModel):
    """Request for updating an app."""

    slug: str
    name: str | None = None
    app_type: str | None = None
    status: str | None = None
    description: str | None = None
    accelerators: list[str] | None = None

    def apply_to(self, existing: App) -> App:
        """Apply non-None fields to existing app."""
        updates: dict[str, Any] = {}
        if self.name is not None:
            updates["name"] = self.name
        if self.app_type is not None:
            updates["app_type"] = AppType.from_string(self.app_type)
        if self.status is not None:
            updates["status"] = self.status
        if self.description is not None:
            updates["description"] = self.description
        if self.accelerators is not None:
            updates["accelerators"] = self.accelerators
        return existing.model_copy(update=updates) if updates else existing


class DeleteAppRequest(BaseModel):
    """Request for deleting an app by slug."""

    slug: str


# =============================================================================
# Query DTOs (for derived/computed operations)
# =============================================================================


class DerivePersonasRequest(BaseModel):
    """Request for deriving personas from stories and epics."""

    pass


class GetPersonaRequest(BaseModel):
    """Request for getting a persona by name."""

    name: str


# =============================================================================
# Persona DTOs
# =============================================================================


class CreatePersonaRequest(BaseModel):
    """Request model for creating a persona.

    Creates a first-class persona definition with HCD metadata.
    """

    slug: str = Field(description="URL-safe identifier")
    name: str = Field(description="Display name (used in Gherkin 'As a {name}')")
    goals: list[str] = Field(
        default_factory=list, description="What the persona wants to achieve"
    )
    frustrations: list[str] = Field(
        default_factory=list, description="Pain points and problems"
    )
    jobs_to_be_done: list[str] = Field(
        default_factory=list, description="JTBD framework items"
    )
    context: str = Field(default="", description="Background and situational context")

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("slug cannot be empty")
        return v.strip()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return Persona.validate_name(v)

    def to_domain_model(self, docname: str = "") -> Persona:
        """Convert to Persona."""
        return Persona.from_definition(
            slug=self.slug,
            name=self.name,
            goals=self.goals,
            frustrations=self.frustrations,
            jobs_to_be_done=self.jobs_to_be_done,
            context=self.context,
            docname=docname,
        )


class ListPersonasRequest(BaseModel):
    """Request for listing personas."""

    pass


class UpdatePersonaRequest(BaseModel):
    """Request for updating a persona."""

    slug: str
    name: str | None = None
    goals: list[str] | None = None
    frustrations: list[str] | None = None
    jobs_to_be_done: list[str] | None = None
    context: str | None = None

    def apply_to(self, existing: Persona) -> Persona:
        """Apply non-None fields to existing persona."""
        updates: dict[str, Any] = {}
        if self.name is not None:
            updates["name"] = self.name
        if self.goals is not None:
            updates["goals"] = self.goals
        if self.frustrations is not None:
            updates["frustrations"] = self.frustrations
        if self.jobs_to_be_done is not None:
            updates["jobs_to_be_done"] = self.jobs_to_be_done
        if self.context is not None:
            updates["context"] = self.context
        return existing.model_copy(update=updates) if updates else existing


class DeletePersonaRequest(BaseModel):
    """Request for deleting a persona by slug."""

    slug: str


# =============================================================================
# Validation DTOs
# =============================================================================


class ValidateAcceleratorsRequest(BaseModel):
    """Request for validating accelerators against code structure.

    Compares documented accelerators (from RST) with discovered bounded
    contexts (from src/ directory scanning).
    """

    pass
