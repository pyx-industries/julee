"""Catalog directives for auto-generated documentation.

These directives use the CoreContext to introspect bounded contexts
and render entity, repository, and use case listings.

Template-driven pattern:
1. Directive calls use case to get data
2. Data is passed to Jinja template
3. Template renders RST
4. RST is parsed to docutils nodes

This separates data fetching (use cases) from presentation (templates).
"""

from pathlib import Path

from docutils import nodes
from docutils.parsers.rst import directives
from jinja2 import Environment, FileSystemLoader
from sphinx.util.docutils import SphinxDirective

from apps.sphinx.directive_factory import parse_rst_to_nodes
from julee.core.entities.code_info import ClassInfo
from julee.core.use_cases.code_artifact.list_entities import (
    ListEntitiesRequest,
    ListEntitiesUseCase,
)
from julee.core.use_cases.code_artifact.list_repository_protocols import (
    ListRepositoryProtocolsRequest,
    ListRepositoryProtocolsUseCase,
)
from julee.core.use_cases.code_artifact.list_service_protocols import (
    ListServiceProtocolsRequest,
    ListServiceProtocolsUseCase,
)
from julee.core.use_cases.code_artifact.list_use_cases import (
    ListUseCasesRequest,
    ListUseCasesUseCase,
)

from ..context import get_core_context

# Template directory
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"

# Jinja environment with filters
_jinja_env: Environment | None = None


def _get_jinja_env() -> Environment:
    """Get or create the Jinja environment."""
    global _jinja_env
    if _jinja_env is None:
        _jinja_env = Environment(
            loader=FileSystemLoader(TEMPLATE_DIR),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        # Register filters
        _jinja_env.filters["title_case"] = lambda s: s.replace("-", " ").replace("_", " ").title()
        _jinja_env.filters["first_sentence"] = _first_sentence
    return _jinja_env


def _first_sentence(text: str) -> str:
    """Extract first sentence from text."""
    if not text:
        return "(no description)"
    for i, char in enumerate(text):
        if char in ".!?" and (i + 1 >= len(text) or text[i + 1] in " \n"):
            return text[: i + 1]
    return text.split("\n")[0].strip() if text else "(no description)"


def _get_summary(class_info: ClassInfo) -> str:
    """Extract first line of docstring as summary."""
    if not class_info.docstring:
        return "(no description)"
    return class_info.docstring.split("\n")[0].strip()


def _classify_crud_type(name: str) -> str | None:
    """Classify use case by CRUD type based on naming conventions."""
    name_lower = name.lower()

    if any(p in name_lower for p in ["create", "add", "register", "new"]):
        return "Create"
    if any(p in name_lower for p in ["get", "list", "find", "fetch", "query", "search"]):
        return "Read"
    if any(p in name_lower for p in ["update", "modify", "edit", "change", "set"]):
        return "Update"
    if any(p in name_lower for p in ["delete", "remove", "clear", "purge"]):
        return "Delete"
    return None


def _infer_entity_type(name: str) -> str | None:
    """Infer entity type from repository class name."""
    if name.endswith("Repository"):
        return name[:-10]
    return None


class EntityCatalogDirective(SphinxDirective):
    """List all entities in bounded context(s) with summaries.

    Uses template-driven rendering:
    1. Calls ListEntitiesUseCase to get entities
    2. Passes response to entity_catalog.rst.jinja template
    3. Template renders RST which is parsed to nodes

    Usage::

        .. entity-catalog:: julee.hcd
           :show-fields:
           :link-to-api:

    Or without argument to list all entities across all BCs::

        .. entity-catalog::
    """

    required_arguments = 0
    optional_arguments = 1
    has_content = False

    option_spec = {
        "show-fields": directives.flag,
        "link-to-api": directives.flag,
    }

    def run(self) -> list[nodes.Node]:
        """Execute the directive."""
        import asyncio

        context = get_core_context(self.env.app)

        # Determine filter (single BC or all)
        bc_filter = self.arguments[0] if self.arguments else None

        # Call use case
        use_case = ListEntitiesUseCase(context.bc_repository)
        request = ListEntitiesRequest(bounded_context=bc_filter)

        async def execute():
            return await use_case.execute(request)

        response = asyncio.run(execute())

        # Render template
        env = _get_jinja_env()
        template = env.get_template("entity_catalog.rst.jinja")
        rst_content = template.render(
            artifacts=response.artifacts,
            options=dict(self.options),
        )

        # Parse RST to nodes
        return parse_rst_to_nodes(rst_content, self.env.docname)


class RepositoryCatalogDirective(SphinxDirective):
    """List all repository protocols in bounded context(s).

    Uses template-driven rendering:
    1. Calls ListRepositoryProtocolsUseCase to get repos
    2. Passes response to repository_catalog.rst.jinja template
    3. Template renders RST which is parsed to nodes

    Usage::

        .. repository-catalog:: julee.hcd
           :show-methods:
           :link-to-api:

    Or without argument to list all repos across all BCs::

        .. repository-catalog::
    """

    required_arguments = 0
    optional_arguments = 1
    has_content = False

    option_spec = {
        "show-methods": directives.flag,
        "link-to-api": directives.flag,
    }

    def run(self) -> list[nodes.Node]:
        """Execute the directive."""
        import asyncio

        context = get_core_context(self.env.app)

        # Determine filter (single BC or all)
        bc_filter = self.arguments[0] if self.arguments else None

        # Call use case
        use_case = ListRepositoryProtocolsUseCase(context.bc_repository)
        request = ListRepositoryProtocolsRequest(bounded_context=bc_filter)

        async def execute():
            return await use_case.execute(request)

        response = asyncio.run(execute())

        # Render template
        env = _get_jinja_env()
        template = env.get_template("repository_catalog.rst.jinja")
        rst_content = template.render(
            artifacts=response.artifacts,
            options=dict(self.options),
        )

        # Parse RST to nodes
        return parse_rst_to_nodes(rst_content, self.env.docname)


class UseCaseCatalogDirective(SphinxDirective):
    """List all use cases in bounded context(s) with CRUD classification.

    Uses template-driven rendering:
    1. Calls ListUseCasesUseCase to get use cases
    2. Passes response to usecase_catalog.rst.jinja template
    3. Template renders RST which is parsed to nodes

    Usage::

        .. usecase-catalog:: julee.hcd
           :group-by-crud:
           :link-to-api:

    Or without argument to list all use cases across all BCs::

        .. usecase-catalog::
    """

    required_arguments = 0
    optional_arguments = 1
    has_content = False

    option_spec = {
        "group-by-crud": directives.flag,
        "link-to-api": directives.flag,
    }

    def run(self) -> list[nodes.Node]:
        """Execute the directive."""
        import asyncio

        context = get_core_context(self.env.app)

        # Determine filter (single BC or all)
        bc_filter = self.arguments[0] if self.arguments else None

        # Call use case
        use_case = ListUseCasesUseCase(context.bc_repository)
        request = ListUseCasesRequest(bounded_context=bc_filter)

        async def execute():
            return await use_case.execute(request)

        response = asyncio.run(execute())

        # Render template
        env = _get_jinja_env()
        template = env.get_template("usecase_catalog.rst.jinja")
        rst_content = template.render(
            artifacts=response.artifacts,
            options=dict(self.options),
            classify_crud=_classify_crud_type,
        )

        # Parse RST to nodes
        return parse_rst_to_nodes(rst_content, self.env.docname)


class ServiceProtocolCatalogDirective(SphinxDirective):
    """List all service protocols in bounded context(s).

    Uses template-driven rendering:
    1. Calls ListServiceProtocolsUseCase to get service protocols
    2. Passes response to service_protocol_catalog.rst.jinja template
    3. Template renders RST which is parsed to nodes

    Usage::

        .. service-protocol-catalog:: julee.hcd
           :show-methods:
           :link-to-api:

    Or without argument to list all service protocols across all BCs::

        .. service-protocol-catalog::
    """

    required_arguments = 0
    optional_arguments = 1
    has_content = False

    option_spec = {
        "show-methods": directives.flag,
        "link-to-api": directives.flag,
    }

    def run(self) -> list[nodes.Node]:
        """Execute the directive."""
        import asyncio

        context = get_core_context(self.env.app)

        # Determine filter (single BC or all)
        bc_filter = self.arguments[0] if self.arguments else None

        # Call use case
        use_case = ListServiceProtocolsUseCase(context.bc_repository)
        request = ListServiceProtocolsRequest(bounded_context=bc_filter)

        async def execute():
            return await use_case.execute(request)

        response = asyncio.run(execute())

        # Render template
        env = _get_jinja_env()
        template = env.get_template("service_protocol_catalog.rst.jinja")
        rst_content = template.render(
            artifacts=response.artifacts,
            options=dict(self.options),
        )

        # Parse RST to nodes
        return parse_rst_to_nodes(rst_content, self.env.docname)
