"""Tests for RelationTraversal service."""

import pytest

from apps.sphinx.shared.services.relation_traversal import (
    RelationTraversal,
    get_relation_traversal,
)
from julee.core.entities.semantic_relation import RelationType
from julee.hcd.entities.epic import Epic
from julee.hcd.entities.journey import Journey
from julee.hcd.entities.story import Story


class TestRelationTraversal:
    """Tests for RelationTraversal query methods."""

    def test_get_container_type_story(self):
        """Story should have App as container via PART_OF."""
        traversal = RelationTraversal()
        container = traversal.get_container_type(Story)

        assert container is not None
        assert container.__name__ == "App"

    def test_get_contained_types_epic(self):
        """Epic should contain Story via CONTAINS."""
        traversal = RelationTraversal()
        contained = traversal.get_contained_types(Epic)

        assert len(contained) == 1
        assert contained[0].__name__ == "Story"

    def test_get_contained_types_journey(self):
        """Journey should contain Story and Epic via CONTAINS."""
        traversal = RelationTraversal()
        contained = traversal.get_contained_types(Journey)

        names = {t.__name__ for t in contained}
        assert names == {"Story", "Epic"}

    def test_get_referenced_types_story(self):
        """Story should reference Persona via REFERENCES."""
        traversal = RelationTraversal()
        referenced = traversal.get_referenced_types(Story)

        assert len(referenced) == 1
        assert referenced[0].__name__ == "Persona"

    def test_get_referenced_types_journey(self):
        """Journey should reference Persona via REFERENCES."""
        traversal = RelationTraversal()
        referenced = traversal.get_referenced_types(Journey)

        assert len(referenced) == 1
        assert referenced[0].__name__ == "Persona"

    def test_get_projected_type_accelerator(self):
        """Accelerator should project BoundedContext via PROJECTS."""
        from julee.supply_chain.entities.accelerator import Accelerator

        traversal = RelationTraversal()
        projected = traversal.get_projected_type(Accelerator)

        assert projected is not None
        assert projected.__name__ == "BoundedContext"

    def test_get_projected_type_story(self):
        """Story should project UseCase via PROJECTS."""
        traversal = RelationTraversal()
        projected = traversal.get_projected_type(Story)

        assert projected is not None
        assert projected.__name__ == "UseCase"

    def test_get_container_type_integration(self):
        """Integration should have Accelerator as container via PART_OF."""
        from julee.hcd.entities.integration import Integration

        traversal = RelationTraversal()
        container = traversal.get_container_type(Integration)

        assert container is not None
        assert container.__name__ == "Accelerator"

    def test_build_entity_relation_summary_story(self):
        """Story relation summary should show PART_OF, REFERENCES, and PROJECTS."""
        traversal = RelationTraversal()
        summary = traversal.build_entity_relation_summary(Story)

        assert summary["part_of"] == "App"
        assert "Persona" in summary["references"]
        assert summary["contains"] == []
        assert summary["projects"] == "UseCase"

    def test_build_entity_relation_summary_epic(self):
        """Epic relation summary should show CONTAINS Story."""
        traversal = RelationTraversal()
        summary = traversal.build_entity_relation_summary(Epic)

        assert "Story" in summary["contains"]
        assert summary["part_of"] is None

    def test_build_entity_relation_summary_journey(self):
        """Journey relation summary should show CONTAINS and REFERENCES."""
        traversal = RelationTraversal()
        summary = traversal.build_entity_relation_summary(Journey)

        assert "Story" in summary["contains"]
        assert "Epic" in summary["contains"]
        assert "Persona" in summary["references"]

    def test_extract_references_groups_by_attribute(self):
        """extract_references should group entities by reference attribute."""
        from julee.hcd.entities.persona import Persona

        traversal = RelationTraversal()

        stories = [
            Story(
                slug="s1",
                feature_title="Story 1",
                persona="Developer",
                app_slug="app1",
                file_path="f1.feature",
            ),
            Story(
                slug="s2",
                feature_title="Story 2",
                persona="Developer",
                app_slug="app1",
                file_path="f2.feature",
            ),
            Story(
                slug="s3",
                feature_title="Story 3",
                persona="Tester",
                app_slug="app1",
                file_path="f3.feature",
            ),
        ]

        result = traversal.extract_references(stories, Persona, ref_attr="persona")

        assert "Developer" in result
        assert "Tester" in result
        assert len(result["Developer"]) == 2
        assert len(result["Tester"]) == 1


class TestNavigationGraph:
    """Tests for navigation graph building."""

    def test_build_entity_graph_returns_nodes_and_edges(self):
        """build_entity_graph should return nodes and edges."""
        traversal = RelationTraversal()
        graph = traversal.build_entity_graph()

        assert "nodes" in graph
        assert "edges" in graph
        assert len(graph["nodes"]) >= 6  # At least HCD entity types
        assert len(graph["edges"]) >= 5  # At least the declared relations

    def test_build_entity_graph_includes_hcd_entities(self):
        """Graph should include standard HCD entity types."""
        traversal = RelationTraversal()
        graph = traversal.build_entity_graph()

        node_ids = {n["id"] for n in graph["nodes"]}
        assert "Story" in node_ids
        assert "Epic" in node_ids
        assert "Journey" in node_ids
        assert "Persona" in node_ids
        assert "App" in node_ids

    def test_build_entity_graph_edge_relations(self):
        """Graph edges should have correct relation types."""
        traversal = RelationTraversal()
        graph = traversal.build_entity_graph()

        edge_relations = {(e["source"], e["relation"], e["target"]) for e in graph["edges"]}

        # Check key relations exist
        assert ("Story", "part_of", "App") in edge_relations
        assert ("Story", "references", "Persona") in edge_relations
        assert ("Epic", "contains", "Story") in edge_relations

    def test_build_navigation_structure(self):
        """build_navigation_structure should categorize relations."""
        traversal = RelationTraversal()
        nav = traversal.build_navigation_structure()

        assert "containers" in nav
        assert "aggregations" in nav
        assert "references" in nav
        assert "projections" in nav

        # App contains Story (via PART_OF inverse)
        assert "App" in nav["containers"]
        assert "Story" in nav["containers"]["App"]

        # Epic aggregates Story (via CONTAINS)
        assert "Epic" in nav["aggregations"]
        assert "Story" in nav["aggregations"]["Epic"]

        # Story references Persona
        assert "Story" in nav["references"]
        assert "Persona" in nav["references"]["Story"]

    def test_get_related_entity_types_direct(self):
        """get_related_entity_types should return direct relations."""
        traversal = RelationTraversal()
        related = traversal.get_related_entity_types(Story, include_inverse=False)

        assert "part_of" in related
        assert "references" in related
        assert any(t.__name__ == "App" for t in related["part_of"])
        assert any(t.__name__ == "Persona" for t in related["references"])

    def test_get_related_entity_types_with_inverse(self):
        """get_related_entity_types should include inverse relations."""
        from julee.hcd.entities.persona import Persona

        traversal = RelationTraversal()
        related = traversal.get_related_entity_types(Persona, include_inverse=True)

        # Persona is referenced by Story and Journey
        assert "inverse_references" in related
        types = [t.__name__ for t in related["inverse_references"]]
        assert "Story" in types
        assert "Journey" in types


class TestIsADiscovery:
    """Tests for IS_A relation discovery."""

    def test_get_is_a_target_returns_none_for_no_relation(self):
        """get_is_a_target should return None if no IS_A relation."""
        traversal = RelationTraversal()

        # Story has PART_OF and REFERENCES but no IS_A
        result = traversal.get_is_a_target(Story)
        assert result is None

    def test_get_is_a_target_with_is_a_relation(self):
        """get_is_a_target should return target type for IS_A relation."""
        from pydantic import BaseModel

        from julee.core.decorators import semantic_relation
        from julee.core.entities.semantic_relation import RelationType
        from julee.hcd.entities.persona import Persona

        # Create a test entity with IS_A relation
        @semantic_relation(Persona, RelationType.IS_A)
        class TestCustomerSegment(BaseModel):
            slug: str
            name: str

        traversal = RelationTraversal()
        result = traversal.get_is_a_target(TestCustomerSegment)

        assert result == Persona

    def test_discover_is_a_entities_empty_search(self):
        """discover_is_a_entities should return empty for no search paths."""
        from julee.hcd.entities.persona import Persona

        traversal = RelationTraversal()
        result = traversal.discover_is_a_entities(Persona, None)

        assert result == []

    def test_build_solution_entity_mapping_empty(self):
        """build_solution_entity_mapping should return empty for no search paths."""
        traversal = RelationTraversal()
        result = traversal.build_solution_entity_mapping(None)

        assert result == {}


class TestSingletonTraversal:
    """Tests for singleton access."""

    def test_get_relation_traversal_returns_singleton(self):
        """get_relation_traversal should return same instance."""
        t1 = get_relation_traversal()
        t2 = get_relation_traversal()
        assert t1 is t2
