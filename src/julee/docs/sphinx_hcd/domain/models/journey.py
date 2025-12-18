"""Journey domain model.

Represents a user journey in the HCD documentation system.
Journeys are defined via RST directives and track a persona's path
through the system to achieve a goal.
"""

from enum import Enum

from pydantic import BaseModel, Field, field_validator

from ...utils import normalize_name


class StepType(str, Enum):
    """Type of journey step."""

    STORY = "story"
    EPIC = "epic"
    PHASE = "phase"

    @classmethod
    def from_string(cls, value: str) -> "StepType":
        """Convert string to StepType."""
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Invalid step type: {value}")


class JourneyStep(BaseModel):
    """A step within a journey.

    Steps can be stories (feature references), epics (epic references),
    or phases (grouping labels for subsequent steps).

    Attributes:
        step_type: The type of step (story, epic, phase)
        ref: Reference identifier (story title, epic slug, or phase title)
        description: Optional description (primarily for phases)
    """

    step_type: StepType
    ref: str
    description: str = ""

    @field_validator("ref", mode="before")
    @classmethod
    def validate_ref(cls, v: str) -> str:
        """Validate ref is not empty."""
        if not v or not v.strip():
            raise ValueError("ref cannot be empty")
        return v.strip()

    @classmethod
    def story(cls, title: str) -> "JourneyStep":
        """Create a story step.

        Args:
            title: Story feature title

        Returns:
            JourneyStep with type STORY
        """
        return cls(step_type=StepType.STORY, ref=title)

    @classmethod
    def epic(cls, slug: str) -> "JourneyStep":
        """Create an epic step.

        Args:
            slug: Epic slug

        Returns:
            JourneyStep with type EPIC
        """
        return cls(step_type=StepType.EPIC, ref=slug)

    @classmethod
    def phase(cls, title: str, description: str = "") -> "JourneyStep":
        """Create a phase step.

        Args:
            title: Phase title
            description: Optional phase description

        Returns:
            JourneyStep with type PHASE
        """
        return cls(step_type=StepType.PHASE, ref=title, description=description)

    @property
    def is_story(self) -> bool:
        """Check if this is a story step."""
        return self.step_type == StepType.STORY

    @property
    def is_epic(self) -> bool:
        """Check if this is an epic step."""
        return self.step_type == StepType.EPIC

    @property
    def is_phase(self) -> bool:
        """Check if this is a phase step."""
        return self.step_type == StepType.PHASE


class Journey(BaseModel):
    """User journey entity.

    A journey represents a persona's path through the system to achieve
    a goal. It captures the user's motivation, the value delivered, and
    the sequence of steps they follow.

    Attributes:
        slug: URL-safe identifier (e.g., "build-vocabulary")
        persona: The persona undertaking this journey
        persona_normalized: Lowercase persona for matching
        intent: What the persona wants (their motivation)
        outcome: What success looks like (business value)
        goal: Activity description (what they do)
        depends_on: Journey slugs that must be completed first
        steps: Sequence of journey steps
        preconditions: Conditions that must be true before starting
        postconditions: Conditions that will be true after completion
        docname: RST document name (for incremental builds)
    """

    slug: str
    persona: str = ""
    persona_normalized: str = ""
    intent: str = ""
    outcome: str = ""
    goal: str = ""
    depends_on: list[str] = Field(default_factory=list)
    steps: list[JourneyStep] = Field(default_factory=list)
    preconditions: list[str] = Field(default_factory=list)
    postconditions: list[str] = Field(default_factory=list)
    docname: str = ""

    @field_validator("slug", mode="before")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug is not empty."""
        if not v or not v.strip():
            raise ValueError("slug cannot be empty")
        return v.strip()

    @field_validator("persona_normalized", mode="before")
    @classmethod
    def compute_persona_normalized(cls, v: str, info) -> str:
        """Compute normalized persona from persona if not provided."""
        if v:
            return v
        persona = info.data.get("persona", "")
        return normalize_name(persona) if persona else ""

    def model_post_init(self, __context) -> None:
        """Ensure normalized fields are computed after init."""
        if not self.persona_normalized and self.persona:
            object.__setattr__(self, "persona_normalized", normalize_name(self.persona))

    def matches_persona(self, persona_name: str) -> bool:
        """Check if this journey matches the given persona (case-insensitive).

        Args:
            persona_name: Persona name to match against

        Returns:
            True if normalized names match
        """
        return self.persona_normalized == normalize_name(persona_name)

    def has_dependency(self, journey_slug: str) -> bool:
        """Check if this journey depends on another journey.

        Args:
            journey_slug: Slug of potential dependency

        Returns:
            True if this journey depends on the given journey
        """
        return journey_slug in self.depends_on

    def add_step(self, step: JourneyStep) -> None:
        """Add a step to this journey.

        Args:
            step: JourneyStep to add
        """
        self.steps.append(step)

    def get_story_refs(self) -> list[str]:
        """Get all story references from steps.

        Returns:
            List of story titles referenced in steps
        """
        return [step.ref for step in self.steps if step.is_story]

    def get_epic_refs(self) -> list[str]:
        """Get all epic references from steps.

        Returns:
            List of epic slugs referenced in steps
        """
        return [step.ref for step in self.steps if step.is_epic]

    @property
    def display_title(self) -> str:
        """Get formatted title for display."""
        return self.slug.replace("-", " ").title()

    @property
    def has_steps(self) -> bool:
        """Check if journey has any steps."""
        return len(self.steps) > 0

    @property
    def step_count(self) -> int:
        """Get number of steps."""
        return len(self.steps)
