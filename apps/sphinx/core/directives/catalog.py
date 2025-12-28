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
        context = get_core_context(self.env.app)

        if self.arguments:
            # Single BC mode
            module_path = self.arguments[0]
            bc_info = context.get_bounded_context(module_path)

            if not bc_info or not bc_info.repository_protocols:
                para = nodes.paragraph(text=f"No repositories found in {module_path}")
                return [para]

            return self._render_repos(bc_info.repository_protocols, module_path)
        else:
            # All BCs mode
            return self._render_all_bcs(context)

    def _render_all_bcs(self, context) -> list[nodes.Node]:
        """Render repositories from all bounded contexts."""
        bounded_contexts = context.list_solution_bounded_contexts()
        result = []

        for bc in bounded_contexts:
            bc_info = context.get_bounded_context(f"julee.{bc.slug}")
            if not bc_info or not bc_info.repository_protocols:
                continue

            # BC heading
            rubric = nodes.rubric(text=bc.display_name)
            result.append(rubric)

            # Repo list for this BC
            result.extend(self._render_repos(bc_info.repository_protocols, f"julee.{bc.slug}"))

        if not result:
            para = nodes.paragraph()
            para += nodes.emphasis(text="No repository protocols found in solution.")
            return [para]

        return result

    def _render_repos(self, repos, module_path: str) -> list[nodes.Node]:
        """Render a list of repository protocols."""
        dl = nodes.definition_list()

        for repo in repos:
            item = nodes.definition_list_item()

            term = nodes.term()
            if "link-to-api" in self.options:
                ref = nodes.reference(
                    "",
                    repo.name,
                    refuri=f"#py-class-{module_path.replace('.', '-')}-{repo.name.lower()}",
                    internal=True,
                )
                term += ref
            else:
                term += nodes.literal(text=repo.name)

            entity_type = _infer_entity_type(repo.name)
            if entity_type:
                term += nodes.Text(f" → {entity_type}")

            item += term

            definition = nodes.definition()
            summary = _get_summary(repo)
            summary_para = nodes.paragraph(text=summary)
            definition += summary_para

            if "show-methods" in self.options and repo.methods:
                method_names = [m.name for m in repo.methods]
                methods_para = nodes.paragraph()
                methods_para += nodes.emphasis(text="Methods: ")
                methods_para += nodes.literal(text=", ".join(method_names))
                definition += methods_para

            item += definition
            dl += item

        return [dl]


class UseCaseCatalogDirective(SphinxDirective):
    """List all use cases in bounded context(s) with CRUD classification.

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
        context = get_core_context(self.env.app)

        if self.arguments:
            # Single BC mode
            module_path = self.arguments[0]
            bc_info = context.get_bounded_context(module_path)

            if not bc_info or not bc_info.use_cases:
                para = nodes.paragraph(text=f"No use cases found in {module_path}")
                return [para]

            if "group-by-crud" in self.options:
                return self._render_grouped(bc_info.use_cases, module_path)
            else:
                return self._render_flat(bc_info.use_cases, module_path)
        else:
            # All BCs mode
            return self._render_all_bcs(context)

    def _render_all_bcs(self, context) -> list[nodes.Node]:
        """Render use cases from all bounded contexts."""
        bounded_contexts = context.list_solution_bounded_contexts()
        result = []

        for bc in bounded_contexts:
            bc_info = context.get_bounded_context(f"julee.{bc.slug}")
            if not bc_info or not bc_info.use_cases:
                continue

            # BC heading
            rubric = nodes.rubric(text=bc.display_name)
            result.append(rubric)

            # Use case list for this BC
            if "group-by-crud" in self.options:
                result.extend(self._render_grouped(bc_info.use_cases, f"julee.{bc.slug}"))
            else:
                result.extend(self._render_flat(bc_info.use_cases, f"julee.{bc.slug}"))

        if not result:
            para = nodes.paragraph()
            para += nodes.emphasis(text="No use cases found in solution.")
            return [para]

        return result

    def _render_flat(self, use_cases: list[ClassInfo], module_path: str) -> list[nodes.Node]:
        """Render as a simple bullet list."""
        bullet_list = nodes.bullet_list()

        for uc in use_cases:
            item = nodes.list_item()
            para = nodes.paragraph()

            if "link-to-api" in self.options:
                ref = nodes.reference(
                    "",
                    uc.name,
                    refuri=f"#py-class-{module_path.replace('.', '-')}-{uc.name.lower()}",
                    internal=True,
                )
                para += nodes.strong("", "", ref)
            else:
                para += nodes.strong(text=uc.name)

            crud_type = _classify_crud_type(uc.name)
            if crud_type:
                para += nodes.Text(" ")
                para += nodes.inline(text=f"[{crud_type}]", classes=["crud-badge"])

            summary = _get_summary(uc)
            para += nodes.Text(f" - {summary}")

            item += para
            bullet_list += item

        return [bullet_list]

    def _render_grouped(self, use_cases: list[ClassInfo], module_path: str) -> list[nodes.Node]:
        """Render grouped by CRUD type."""
        groups: dict[str, list[ClassInfo]] = {
            "Create": [],
            "Read": [],
            "Update": [],
            "Delete": [],
            "Other": [],
        }

        for uc in use_cases:
            crud = _classify_crud_type(uc.name) or "Other"
            groups[crud].append(uc)

        result_nodes = []

        for crud_type, items in groups.items():
            if not items:
                continue

            rubric = nodes.rubric(text=crud_type)
            result_nodes.append(rubric)

            bullet_list = nodes.bullet_list()
            for uc in items:
                item = nodes.list_item()
                para = nodes.paragraph()

                if "link-to-api" in self.options:
                    ref = nodes.reference(
                        "",
                        uc.name,
                        refuri=f"#py-class-{module_path.replace('.', '-')}-{uc.name.lower()}",
                        internal=True,
                    )
                    para += nodes.strong("", "", ref)
                else:
                    para += nodes.strong(text=uc.name)

                summary = _get_summary(uc)
                para += nodes.Text(f" - {summary}")
                item += para
                bullet_list += item

            result_nodes.append(bullet_list)

        return result_nodes
