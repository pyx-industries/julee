"""DerivePersonasUseCase with co-located request/response.

Use case for deriving personas from stories and epics.

Supports two persona sources:
1. Defined personas: Explicitly created via define-persona directive
2. Derived personas: Extracted from user story "As a..." clauses

Defined personas are authoritative and get enriched with story data.
Derived personas fill gaps when stories reference undefined personas.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

from julee.hcd.entities.persona import Persona
from julee.hcd.repositories.epic import EpicRepository
from julee.hcd.repositories.story import StoryRepository
from julee.hcd.utils import normalize_name

if TYPE_CHECKING:
    from julee.hcd.repositories.persona import PersonaRepository


class DerivePersonasRequest(BaseModel):
    """Request for deriving personas from stories and epics."""

    pass


class DerivePersonasResponse(BaseModel):
    """Response from deriving personas."""

    personas: list[Persona]


class DerivePersonasUseCase:
    """Use case for deriving and merging personas.

    .. usecase-documentation:: julee.hcd.domain.use_cases.queries.derive_personas:DerivePersonasUseCase

    Combines defined personas (from PersonaRepository) with derived
    personas (from stories). Defined personas are authoritative and
    get enriched with app_slugs/epic_slugs from their stories.
    """

    def __init__(
        self,
        story_repo: StoryRepository,
        epic_repo: EpicRepository,
        persona_repo: PersonaRepository | None = None,
    ) -> None:
        """Initialize with repository dependencies.

        Args:
            story_repo: Story repository instance
            epic_repo: Epic repository instance
            persona_repo: Optional persona repository for defined personas
        """
        self.story_repo = story_repo
        self.epic_repo = epic_repo
        self.persona_repo = persona_repo

    async def execute(self, request: DerivePersonasRequest) -> DerivePersonasResponse:
        """Derive and merge personas from all sources.

        Process:
        1. Fetch defined personas from PersonaRepository (if available)
        2. Derive personas from stories (extract from "As a..." clauses)
        3. Merge: defined personas get enriched with app_slugs/epic_slugs
        4. Derived personas without definitions are included as fallback

        Args:
            request: Derive personas request (extensible for filtering)

        Returns:
            Response containing merged list of personas
        """
        stories = await self.story_repo.list_all()
        epics = await self.epic_repo.list_all()

        # Get defined personas (if repository available)
        defined_personas: dict[str, Persona] = {}
        if self.persona_repo:
            defined_list = await self.persona_repo.list_all()
            for persona in defined_list:
                defined_personas[persona.normalized_name] = persona

        # Collect derived persona data from stories
        derived_data: dict[str, dict] = {}  # normalized_name -> {name, apps, epics}

        for story in stories:
            normalized = story.persona_normalized
            if normalized == "unknown":
                continue

            if normalized not in derived_data:
                derived_data[normalized] = {
                    "name": story.persona,
                    "apps": set(),
                    "epics": set(),
                }

            derived_data[normalized]["apps"].add(story.app_slug)

        # Build lookup of normalized story title -> normalized persona
        story_to_persona: dict[str, str] = {}
        for story in stories:
            story_to_persona[normalize_name(story.feature_title)] = (
                story.persona_normalized
            )

        # Find epics for each persona
        for epic in epics:
            for story_ref in epic.story_refs:
                story_normalized = normalize_name(story_ref)
                persona_normalized = story_to_persona.get(story_normalized)
                if persona_normalized and persona_normalized in derived_data:
                    derived_data[persona_normalized]["epics"].add(epic.slug)

        # Merge defined + derived personas
        result_personas: list[Persona] = []
        seen_normalized: set[str] = set()

        # First, process defined personas (they take priority)
        for normalized_name, defined_persona in defined_personas.items():
            seen_normalized.add(normalized_name)

            # Check if we have derived data to merge
            if normalized_name in derived_data:
                data = derived_data[normalized_name]
                # Create a derived persona to merge with
                derived_persona = Persona(
                    name=data["name"],
                    app_slugs=sorted(data["apps"]),
                    epic_slugs=sorted(data["epics"]),
                )
                # Merge defined persona with derived data
                merged = defined_persona.merge_with_derived(derived_persona)
                result_personas.append(merged)
            else:
                # Defined persona with no stories - include as-is
                result_personas.append(defined_persona)

        # Then, add derived personas that have no definition
        for normalized_name, data in derived_data.items():
            if normalized_name in seen_normalized:
                continue  # Already handled via defined persona

            # Create derived-only persona (no slug, no docname)
            persona = Persona(
                name=data["name"],
                app_slugs=sorted(data["apps"]),
                epic_slugs=sorted(data["epics"]),
            )
            result_personas.append(persona)

        sorted_personas = sorted(result_personas, key=lambda p: p.name)
        return DerivePersonasResponse(personas=sorted_personas)
