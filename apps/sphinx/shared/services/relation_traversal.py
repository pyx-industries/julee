"""Semantic relation traversal service for cross-reference generation.

Uses SemanticRelation declarations to traverse entity relationships
and generate cross-reference data for documentation templates.

This service enables reflexive documentation by introspecting declared
relations (PART_OF, CONTAINS, REFERENCES, PROJECTS) to build navigation
paths between entities.

Example:
    traversal = RelationTraversal()

    # Find all personas referenced by stories in an app
    personas = traversal.find_referenced(stories, Persona)

    # Find all stories contained in an epic
    stories = traversal.find_contained(epic, Story)

    # Build cross-reference data for a bounded context
    crossrefs = traversal.build_bc_persona_crossrefs(bc_slug, hcd_context)
"""

from collections import defaultdict
from typing import TYPE_CHECKING, Any

from julee.core.decorators import get_semantic_relations
from julee.core.entities.semantic_relation import RelationType

if TYPE_CHECKING:
    from apps.sphinx.hcd.context import HCDContext


class RelationTraversal:
    """Traverse semantic relations for cross-reference generation.

    Provides methods to:
    - Find related entities via declared relations
    - Build cross-reference data structures for templates
    - Navigate PART_OF, CONTAINS, REFERENCES, PROJECTS paths
    """

    def get_relations(
        self,
        entity_type: type,
        relation_type: RelationType | None = None,
    ) -> list:
        """Get semantic relations for an entity type.

        Args:
            entity_type: Entity class to introspect
            relation_type: Optional filter for specific relation type

        Returns:
            List of SemanticRelation objects
        """
        relations = get_semantic_relations(entity_type)
        if relation_type:
            relations = [r for r in relations if r.relation_type == relation_type]
        return relations

    def get_container_type(self, entity_type: type) -> type | None:
        """Get the container type for an entity via PART_OF relation.

        Args:
            entity_type: Entity class (e.g., Story)

        Returns:
            Container type (e.g., App) or None if not found
        """
        relations = self.get_relations(entity_type, RelationType.PART_OF)
        return relations[0].target_type if relations else None

    def get_contained_types(self, entity_type: type) -> list[type]:
        """Get types contained by an entity via CONTAINS relations.

        Args:
            entity_type: Entity class (e.g., Epic)

        Returns:
            List of contained types (e.g., [Story])
        """
        relations = self.get_relations(entity_type, RelationType.CONTAINS)
        return [r.target_type for r in relations]

    def get_referenced_types(self, entity_type: type) -> list[type]:
        """Get types referenced by an entity via REFERENCES relations.

        Args:
            entity_type: Entity class (e.g., Story)

        Returns:
            List of referenced types (e.g., [Persona])
        """
        relations = self.get_relations(entity_type, RelationType.REFERENCES)
        return [r.target_type for r in relations]

    def get_projected_type(self, entity_type: type) -> type | None:
        """Get the type projected by an entity via PROJECTS relation.

        Args:
            entity_type: Entity class (e.g., Accelerator)

        Returns:
            Projected type (e.g., BoundedContext) or None
        """
        relations = self.get_relations(entity_type, RelationType.PROJECTS)
        return relations[0].target_type if relations else None

    def extract_references(
        self,
        entities: list[Any],
        target_type: type,
        ref_attr: str | None = None,
    ) -> dict[str, list[Any]]:
        """Extract references from entities to a target type.

        Groups entities by their reference attribute value.

        Args:
            entities: List of entity instances
            target_type: Type being referenced (e.g., Persona)
            ref_attr: Override attribute name (defaults to {type_lower}_normalized or {type_lower})

        Returns:
            Dict mapping reference values to lists of entities
        """
        if not ref_attr:
            type_lower = target_type.__name__.lower()
            # Try normalized version first
            ref_attr = f"{type_lower}_normalized"
            if entities and not hasattr(entities[0], ref_attr):
                ref_attr = type_lower

        result: dict[str, list[Any]] = defaultdict(list)
        for entity in entities:
            ref_value = getattr(entity, ref_attr, None)
            if ref_value:
                result[ref_value].append(entity)

        return dict(result)

    def build_bc_persona_crossrefs(
        self,
        bc_slug: str,
        hcd_context: "HCDContext",
    ) -> list[dict]:
        """Build persona cross-references for a bounded context.

        Uses semantic relations to trace:
        BoundedContext ← PROJECTS ← Accelerator ← uses ← App ← PART_OF ← Story → REFERENCES → Persona

        Args:
            bc_slug: Bounded context slug (e.g., "hcd")
            hcd_context: HCD context for entity lookup

        Returns:
            List of dicts with persona, app_slug, app_name, story_count
        """
        from julee.hcd.use_cases.crud import ListAppsRequest, ListStoriesRequest

        # Step 1: Find apps using accelerators that project this BC
        # (Accelerator PROJECTS BoundedContext)
        apps_response = hcd_context.list_apps.execute_sync(ListAppsRequest())
        apps_using_bc = [
            app for app in apps_response.apps if bc_slug in app.accelerators
        ]

        if not apps_using_bc:
            return []

        # Step 2: Get stories for those apps (Story PART_OF App)
        # and extract persona references (Story REFERENCES Persona)
        persona_data: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

        for app in apps_using_bc:
            stories_response = hcd_context.list_stories.execute_sync(
                ListStoriesRequest(app_slug=app.slug)
            )

            # Use semantic relation to get reference attribute
            from julee.hcd.entities.story import Story

            ref_types = self.get_referenced_types(Story)
            # Story REFERENCES Persona, so use persona attribute
            ref_attr = "persona_normalized"

            for story in stories_response.stories:
                persona = getattr(story, ref_attr, None) or story.persona
                persona_data[persona][app.slug] += 1

        # Step 3: Build cross-reference list
        crossrefs = []
        for persona, apps_dict in sorted(persona_data.items()):
            for app_slug, story_count in sorted(apps_dict.items()):
                app_name = app_slug
                for app in apps_using_bc:
                    if app.slug == app_slug:
                        app_name = app.name
                        break

                crossrefs.append({
                    "persona": persona,
                    "persona_slug": persona.lower().replace(" ", "-"),
                    "app_slug": app_slug,
                    "app_name": app_name,
                    "story_count": story_count,
                })

        return crossrefs

    def build_epic_story_crossrefs(
        self,
        epic,
        hcd_context: "HCDContext",
    ) -> list[dict]:
        """Build story cross-references for an epic.

        Uses semantic relation: Epic CONTAINS Story

        Args:
            epic: Epic entity instance
            hcd_context: HCD context for story lookup

        Returns:
            List of dicts with story info grouped by app
        """
        from julee.hcd.use_cases.crud import ListStoriesRequest
        from julee.hcd.utils import normalize_name

        # Get all stories
        stories_response = hcd_context.list_stories.execute_sync(ListStoriesRequest())

        # Filter stories in this epic (by normalized title match)
        story_refs_normalized = [normalize_name(ref) for ref in epic.story_refs]
        stories_in_epic = [
            story
            for story in stories_response.stories
            if normalize_name(story.feature_title) in story_refs_normalized
        ]

        # Group by app (Story PART_OF App)
        stories_by_app: dict[str, list] = defaultdict(list)
        for story in stories_in_epic:
            stories_by_app[story.app_slug].append(story)

        return [
            {
                "app_slug": app_slug,
                "stories": stories,
                "story_count": len(stories),
            }
            for app_slug, stories in sorted(stories_by_app.items())
        ]

    def build_journey_step_crossrefs(
        self,
        journey,
        hcd_context: "HCDContext",
    ) -> list[dict]:
        """Build step cross-references for a journey.

        Uses semantic relations:
        - Journey CONTAINS Story
        - Journey CONTAINS Epic

        Args:
            journey: Journey entity instance
            hcd_context: HCD context for entity lookup

        Returns:
            List of dicts with step info including resolved entities
        """
        from julee.hcd.entities.journey import StepType
        from julee.hcd.use_cases.crud import (
            ListEpicsRequest,
            ListStoriesRequest,
        )
        from julee.hcd.utils import normalize_name

        # Get all stories and epics for lookup
        stories_response = hcd_context.list_stories.execute_sync(ListStoriesRequest())
        epics_response = hcd_context.list_epics.execute_sync(ListEpicsRequest())

        # Build lookup maps
        stories_by_title = {
            normalize_name(s.feature_title): s for s in stories_response.stories
        }
        epics_by_slug = {e.slug: e for e in epics_response.epics}

        # Resolve each step
        resolved_steps = []
        for step in journey.steps:
            step_data = {
                "step_type": step.step_type.value,
                "ref": step.ref,
                "description": step.description,
                "resolved": None,
            }

            if step.step_type == StepType.STORY:
                story = stories_by_title.get(normalize_name(step.ref))
                if story:
                    step_data["resolved"] = story
                    step_data["app_slug"] = story.app_slug

            elif step.step_type == StepType.EPIC:
                epic = epics_by_slug.get(step.ref)
                if epic:
                    step_data["resolved"] = epic
                    step_data["story_count"] = len(epic.story_refs)

            resolved_steps.append(step_data)

        return resolved_steps


    def build_epic_persona_crossrefs(
        self,
        epic,
        hcd_context: "HCDContext",
    ) -> list[dict]:
        """Build persona cross-references for an epic.

        Uses semantic relation: Story REFERENCES Persona
        Via epic's stories (Epic CONTAINS Story)

        Args:
            epic: Epic entity instance
            hcd_context: HCD context for story lookup

        Returns:
            List of dicts with persona, story_count grouped by persona
        """
        from julee.hcd.use_cases.crud import ListStoriesRequest
        from julee.hcd.utils import normalize_name

        # Get all stories
        stories_response = hcd_context.list_stories.execute_sync(ListStoriesRequest())

        # Filter stories in this epic
        story_refs_normalized = [normalize_name(ref) for ref in epic.story_refs]
        stories_in_epic = [
            story
            for story in stories_response.stories
            if normalize_name(story.feature_title) in story_refs_normalized
        ]

        # Group by persona (Story REFERENCES Persona)
        persona_data: dict[str, int] = defaultdict(int)
        for story in stories_in_epic:
            persona = story.persona_normalized or story.persona
            persona_data[persona] += 1

        return [
            {
                "persona": persona,
                "persona_slug": persona.lower().replace(" ", "-"),
                "story_count": count,
            }
            for persona, count in sorted(persona_data.items())
        ]

    def build_journey_persona_crossref(
        self,
        journey,
    ) -> dict | None:
        """Build persona cross-reference for a journey.

        Uses semantic relation: Journey REFERENCES Persona

        Args:
            journey: Journey entity instance

        Returns:
            Dict with persona info or None if no persona
        """
        if not journey.persona:
            return None

        return {
            "persona": journey.persona,
            "persona_slug": (journey.persona_normalized or journey.persona).lower().replace(" ", "-"),
        }

    def build_entity_relation_summary(
        self,
        entity_type: type,
    ) -> dict:
        """Build a summary of relations for an entity type.

        Useful for documentation and navigation generation.

        Args:
            entity_type: Entity class to summarize

        Returns:
            Dict with relation types and their targets
        """
        relations = get_semantic_relations(entity_type)

        summary = {
            "projects": None,
            "part_of": None,
            "contains": [],
            "references": [],
        }

        for rel in relations:
            if rel.relation_type == RelationType.PROJECTS:
                summary["projects"] = rel.target_type.__name__
            elif rel.relation_type == RelationType.PART_OF:
                summary["part_of"] = rel.target_type.__name__
            elif rel.relation_type == RelationType.CONTAINS:
                summary["contains"].append(rel.target_type.__name__)
            elif rel.relation_type == RelationType.REFERENCES:
                summary["references"].append(rel.target_type.__name__)

        return summary


    def build_entity_graph(
        self,
        entity_types: list[type] | None = None,
    ) -> dict:
        """Build a relationship graph of entity types.

        Creates a graph structure showing how entity types relate
        via semantic relations. Useful for navigation and visualization.

        Args:
            entity_types: List of entity types to include, or None for HCD defaults

        Returns:
            Dict with nodes (entity types) and edges (relations)
        """
        if entity_types is None:
            # Default HCD entity types
            from julee.hcd.entities.accelerator import Accelerator
            from julee.hcd.entities.app import App
            from julee.hcd.entities.epic import Epic
            from julee.hcd.entities.journey import Journey
            from julee.hcd.entities.persona import Persona
            from julee.hcd.entities.story import Story

            entity_types = [Story, Epic, Journey, Persona, App, Accelerator]

        nodes = []
        edges = []

        for entity_type in entity_types:
            # Add node
            summary = self.build_entity_relation_summary(entity_type)
            nodes.append({
                "id": entity_type.__name__,
                "type": entity_type.__name__,
                "module": entity_type.__module__,
                "relations": summary,
            })

            # Add edges from relations
            relations = get_semantic_relations(entity_type)
            for rel in relations:
                edges.append({
                    "source": entity_type.__name__,
                    "target": rel.target_type.__name__,
                    "relation": rel.relation_type.value,
                })

        return {
            "nodes": nodes,
            "edges": edges,
        }

    def build_navigation_structure(
        self,
        entity_types: list[type] | None = None,
    ) -> dict:
        """Build a navigation structure from entity relations.

        Creates a hierarchical structure based on PART_OF relations,
        with cross-references from REFERENCES and CONTAINS.

        Args:
            entity_types: List of entity types to include

        Returns:
            Dict with containers, contents, and cross-references
        """
        graph = self.build_entity_graph(entity_types)

        # Find container hierarchy (via PART_OF)
        containers: dict[str, list[str]] = defaultdict(list)
        for edge in graph["edges"]:
            if edge["relation"] == "part_of":
                containers[edge["target"]].append(edge["source"])

        # Find aggregations (via CONTAINS)
        aggregations: dict[str, list[str]] = defaultdict(list)
        for edge in graph["edges"]:
            if edge["relation"] == "contains":
                aggregations[edge["source"]].append(edge["target"])

        # Find references (via REFERENCES)
        references: dict[str, list[str]] = defaultdict(list)
        for edge in graph["edges"]:
            if edge["relation"] == "references":
                references[edge["source"]].append(edge["target"])

        # Find projections (via PROJECTS)
        projections: dict[str, str] = {}
        for edge in graph["edges"]:
            if edge["relation"] == "projects":
                projections[edge["source"]] = edge["target"]

        return {
            "containers": dict(containers),  # App contains [Story]
            "aggregations": dict(aggregations),  # Epic aggregates [Story]
            "references": dict(references),  # Story references [Persona]
            "projections": projections,  # Accelerator projects BoundedContext
        }

    def get_related_entity_types(
        self,
        entity_type: type,
        include_inverse: bool = True,
    ) -> dict[str, list[type]]:
        """Get all entity types related to a given type.

        Args:
            entity_type: Entity type to find relations for
            include_inverse: Whether to include inverse relations

        Returns:
            Dict mapping relation types to lists of related types
        """
        result: dict[str, list[type]] = defaultdict(list)

        # Direct relations
        relations = get_semantic_relations(entity_type)
        for rel in relations:
            result[rel.relation_type.value].append(rel.target_type)

        if include_inverse:
            # Find inverse relations from other types
            from julee.hcd.entities.accelerator import Accelerator
            from julee.hcd.entities.app import App
            from julee.hcd.entities.epic import Epic
            from julee.hcd.entities.journey import Journey
            from julee.hcd.entities.persona import Persona
            from julee.hcd.entities.story import Story

            all_types = [Story, Epic, Journey, Persona, App, Accelerator]

            for other_type in all_types:
                if other_type == entity_type:
                    continue

                other_relations = get_semantic_relations(other_type)
                for rel in other_relations:
                    if rel.target_type == entity_type:
                        # Add inverse relation
                        inverse_key = f"inverse_{rel.relation_type.value}"
                        result[inverse_key].append(other_type)

        return dict(result)


# Singleton instance
_traversal: RelationTraversal | None = None


def get_relation_traversal() -> RelationTraversal:
    """Get the singleton RelationTraversal instance.

    Returns:
        Configured RelationTraversal
    """
    global _traversal
    if _traversal is None:
        _traversal = RelationTraversal()
    return _traversal
