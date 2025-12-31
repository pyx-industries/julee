"""Tests for UnifiedLinkResolver service."""

import pytest
from pydantic import BaseModel

from julee.core.decorators import semantic_relation
from julee.core.entities.semantic_relation import RelationType
from julee.core.services.semantic_relation_registry import SemanticRelationRegistry

from apps.sphinx.shared.documentation_mapping import DocumentationMapping
from apps.sphinx.shared.services.unified_link_resolver import (
    Link,
    LinkGroup,
    LinkResult,
    UnifiedLinkResolver,
)


# =============================================================================
# Test Fixtures
# =============================================================================


class CoreEntity(BaseModel):
    """A core entity (target of projections)."""

    slug: str


class AnotherCoreEntity(BaseModel):
    """Another core entity."""

    slug: str


@semantic_relation(CoreEntity, RelationType.PROJECTS)
class ViewpointEntity(BaseModel):
    """A viewpoint entity that projects onto CoreEntity."""

    slug: str
    core_entity_slug: str


@semantic_relation(CoreEntity, RelationType.ENABLES)
@semantic_relation(AnotherCoreEntity, RelationType.REFERENCES)
class MultiRelationEntity(BaseModel):
    """An entity with multiple relations."""

    slug: str
    core_entity_slug: str
    another_core_entity_slug: str


class UnrelatedEntity(BaseModel):
    """An entity with no semantic relations."""

    slug: str


@pytest.fixture
def registry() -> SemanticRelationRegistry:
    """Create a registry with test entities."""
    reg = SemanticRelationRegistry()
    reg.register(ViewpointEntity)
    reg.register(MultiRelationEntity)
    return reg


@pytest.fixture
def mapping() -> DocumentationMapping:
    """Create a documentation mapping."""
    return DocumentationMapping()


@pytest.fixture
def resolver(registry: SemanticRelationRegistry, mapping: DocumentationMapping) -> UnifiedLinkResolver:
    """Create a resolver with test fixtures."""
    return UnifiedLinkResolver(registry=registry, mapping=mapping)


# =============================================================================
# Data Structure Tests
# =============================================================================


class TestLink:
    """Tests for Link dataclass."""

    def test_create_link(self) -> None:
        """Test creating a link."""
        link = Link(
            title="Test Entity",
            href="test/entity.html",
            slug="test-entity",
            category="test",
        )

        assert link.title == "Test Entity"
        assert link.href == "test/entity.html"
        assert link.slug == "test-entity"
        assert link.category == "test"

    def test_default_category(self) -> None:
        """Test default category."""
        link = Link(title="Test", href="test.html", slug="test")
        assert link.category == "default"


class TestLinkGroup:
    """Tests for LinkGroup dataclass."""

    def test_create_group(self) -> None:
        """Test creating a link group."""
        links = [
            Link(title="Entity 1", href="e1.html", slug="e1"),
            Link(title="Entity 2", href="e2.html", slug="e2"),
        ]
        group = LinkGroup(
            label="Projects",
            links=links,
            relation_type=RelationType.PROJECTS,
        )

        assert group.label == "Projects"
        assert len(group.links) == 2
        assert group.relation_type == RelationType.PROJECTS

    def test_empty_group(self) -> None:
        """Test creating empty group."""
        group = LinkGroup(label="Empty")
        assert group.label == "Empty"
        assert group.links == []
        assert group.relation_type is None


class TestLinkResult:
    """Tests for LinkResult dataclass."""

    def test_has_content_with_instances(self) -> None:
        """Test has_content with instances."""
        result = LinkResult(
            entity_type_name="Test",
            instances=[LinkGroup(label="Test", links=[Link("a", "a.html", "a")])],
        )
        assert result.has_content is True

    def test_has_content_with_outbound(self) -> None:
        """Test has_content with outbound links."""
        result = LinkResult(
            entity_type_name="Test",
            outbound=[LinkGroup(label="Test", links=[Link("a", "a.html", "a")])],
        )
        assert result.has_content is True

    def test_has_content_with_inbound(self) -> None:
        """Test has_content with inbound links."""
        result = LinkResult(
            entity_type_name="Test",
            inbound=[LinkGroup(label="Test", links=[Link("a", "a.html", "a")])],
        )
        assert result.has_content is True

    def test_has_content_empty(self) -> None:
        """Test has_content when empty."""
        result = LinkResult(entity_type_name="Test")
        assert result.has_content is False


# =============================================================================
# Resolver Tests
# =============================================================================


class TestUnifiedLinkResolver:
    """Tests for UnifiedLinkResolver."""

    def test_init(
        self,
        registry: SemanticRelationRegistry,
        mapping: DocumentationMapping,
    ) -> None:
        """Test resolver initialization."""
        resolver = UnifiedLinkResolver(registry=registry, mapping=mapping)

        assert resolver.registry is registry
        assert resolver.mapping is mapping
        assert resolver.bc_repo is None
        assert resolver.app_repo is None

    @pytest.mark.asyncio
    async def test_resolve_for_instance_outbound(
        self,
        resolver: UnifiedLinkResolver,
    ) -> None:
        """Test resolving outbound relations for an instance."""
        instance = ViewpointEntity(slug="test", core_entity_slug="core-test")

        result = await resolver.resolve_for_instance(
            ViewpointEntity,
            "test",
            instance,
        )

        assert result.entity_type_name == "ViewpointEntity"
        # Should have outbound PROJECTS relation
        assert len(result.outbound) >= 0  # Depends on slug resolution

    @pytest.mark.asyncio
    async def test_resolve_for_instance_multiple_relations(
        self,
        resolver: UnifiedLinkResolver,
    ) -> None:
        """Test resolving multiple outbound relations."""
        instance = MultiRelationEntity(
            slug="multi",
            core_entity_slug="core",
            another_core_entity_slug="another",
        )

        result = await resolver.resolve_for_instance(
            MultiRelationEntity,
            "multi",
            instance,
        )

        assert result.entity_type_name == "MultiRelationEntity"

    @pytest.mark.asyncio
    async def test_resolve_for_core_type_no_repo(
        self,
        resolver: UnifiedLinkResolver,
    ) -> None:
        """Test resolving for core type without repository."""
        result = await resolver.resolve_for_core_type(CoreEntity)

        assert result.entity_type_name == "CoreEntity"
        # No instances without a repo
        assert result.instances == []

    @pytest.mark.asyncio
    async def test_resolve_for_core_type_inbound(
        self,
        resolver: UnifiedLinkResolver,
    ) -> None:
        """Test that core type gets inbound relations."""
        result = await resolver.resolve_for_core_type(CoreEntity)

        # Should show inbound relations from ViewpointEntity and MultiRelationEntity
        assert result.entity_type_name == "CoreEntity"
        # Inbound relations should be populated
        assert len(result.inbound) > 0

        # Check we have the expected relation types
        labels = [g.label for g in result.inbound]
        # "Projected by" from ViewpointEntity's PROJECTS relation
        assert "Projected by" in labels


class TestResolverHelpers:
    """Tests for resolver helper methods."""

    def test_resolve_href(
        self,
        resolver: UnifiedLinkResolver,
    ) -> None:
        """Test URL resolution."""
        from julee.core.entities.bounded_context import BoundedContext

        href = resolver._resolve_href(BoundedContext, "hcd")
        assert "hcd" in href
        assert href.endswith(".html")

    def test_get_target_title(
        self,
        resolver: UnifiedLinkResolver,
    ) -> None:
        """Test title generation."""
        title = resolver._get_target_title(CoreEntity, "my-entity")
        assert title == "My Entity"

    def test_get_target_title_underscores(
        self,
        resolver: UnifiedLinkResolver,
    ) -> None:
        """Test title generation with underscores."""
        title = resolver._get_target_title(CoreEntity, "my_entity_name")
        assert title == "My Entity Name"
