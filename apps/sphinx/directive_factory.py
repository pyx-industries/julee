"""Generic directive factory for use-case-driven Sphinx directives.

Provides factory functions to generate Sphinx directives that:
1. Call a use case to get data
2. Render via DocumentationRenderingService
3. Convert the resulting RST to docutils nodes

This separates data fetching (use cases) from presentation (rendering service),
reducing boilerplate across bounded context documentation extensions.

Example:
    from apps.sphinx.directive_factory import generate_index_directive
    from julee.hcd.use_cases.crud import ListPersonasUseCase, ListPersonasRequest

    def _list_personas(ctx):
        return ListPersonasUseCase(ctx.persona_repo.async_repo)

    PersonaIndexDirective = generate_index_directive(
        entity_name="Persona",
        use_case_factory=_list_personas,
        request_factory=lambda opts: ListPersonasRequest(),
        rendering_service=rendering_service,
    )
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypeVar

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective

if TYPE_CHECKING:
    from pydantic import BaseModel

    from julee.core.services.documentation import DocumentationRenderingService

# Type for context objects (HCDContext, C4Context, etc.)
Ctx = TypeVar("Ctx")


def _to_snake_case(name: str) -> str:
    """Convert CamelCase to snake_case."""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _pluralize(name: str) -> str:
    """Simple English pluralization."""
    if name.endswith("y") and len(name) > 1 and name[-2] not in "aeiou":
        return name[:-1] + "ies"
    elif name.endswith("s") or name.endswith("x") or name.endswith("ch"):
        return name + "es"
    return name + "s"


def parse_rst_to_nodes(rst_text: str, source_name: str = "<rst>") -> list[nodes.Node]:
    """Parse RST text into docutils nodes.

    Args:
        rst_text: RST-formatted text to parse
        source_name: Name for error messages

    Returns:
        List of docutils nodes
    """
    from docutils.core import publish_doctree
    from docutils.parsers.rst import Parser

    doctree = publish_doctree(
        rst_text,
        source_path=source_name,
        parser=Parser(),
        settings_overrides={
            "report_level": 4,
            "halt_level": 5,
            "input_encoding": "unicode",
            "output_encoding": "unicode",
        },
    )

    return list(doctree.children)


def generate_index_directive(
    entity_name: str,
    use_case_factory: Callable[[Ctx], Any],
    request_factory: Callable[[dict], BaseModel],
    rendering_service_getter: Callable[[Any], DocumentationRenderingService],
    context_getter: Callable[[Any], Ctx],
    *,
    option_spec: dict[str, Any] | None = None,
    use_placeholder: bool = True,
) -> type[SphinxDirective]:
    """Generate an index directive that calls a use case and renders via service.

    Args:
        entity_name: Entity name for directive naming (e.g., "Persona")
        use_case_factory: Function(context) -> UseCase instance
        request_factory: Function(options) -> Request instance
        rendering_service_getter: Function(app) -> DocumentationRenderingService
        context_getter: Function(app) -> domain context (e.g., get_hcd_context)
        option_spec: Optional directive options (default: {"format": unchanged})
        use_placeholder: If True, use placeholder pattern for deferred rendering

    Returns:
        Generated directive class
    """
    slug = _to_snake_case(entity_name)

    default_option_spec = {
        "format": directives.unchanged,
    }
    final_option_spec = {**default_option_spec, **(option_spec or {})}

    if use_placeholder:
        # Create a unique placeholder class for this entity
        placeholder_cls = type(
            f"{entity_name}IndexPlaceholder",
            (nodes.General, nodes.Element),
            {"__doc__": f"Placeholder for {slug}-index directive."},
        )

        class GeneratedIndexDirective(SphinxDirective):
            __doc__ = f"Render index of all {slug}s."
            option_spec = final_option_spec

            # Expose placeholder class for registration
            placeholder_class = placeholder_cls

            def run(self):
                node = placeholder_cls()
                node["options"] = dict(self.options)
                node["docname"] = self.env.docname
                return [node]

            @staticmethod
            def resolve_placeholder(
                node: nodes.Element,
                app: Any,
            ) -> list[nodes.Node]:
                """Resolve placeholder to actual content.

                Called during doctree-resolved event.
                """
                ctx = context_getter(app)
                docname = node["docname"]
                options = node["options"]

                # Execute use case
                use_case = use_case_factory(ctx)
                request = request_factory(options)
                response = use_case.execute_sync(request)

                # Get entities from response (uses auto-derived field name)
                entities_field = _pluralize(_to_snake_case(entity_name))
                entities = getattr(response, entities_field, response.entities)

                # Render via service
                rendering_service = rendering_service_getter(app)
                rst_content = rendering_service.render_index(
                    entities=entities,
                    entity_type=slug,
                    docname=docname,
                    **options,
                )

                return parse_rst_to_nodes(rst_content, docname)

        GeneratedIndexDirective.__name__ = f"{entity_name}IndexDirective"
        return GeneratedIndexDirective

    else:
        # Direct rendering (no placeholder)
        class GeneratedIndexDirective(SphinxDirective):
            __doc__ = f"Render index of all {slug}s."
            option_spec = final_option_spec

            def run(self):
                ctx = context_getter(self.env.app)
                docname = self.env.docname

                # Execute use case
                use_case = use_case_factory(ctx)
                request = request_factory(self.options)
                response = use_case.execute_sync(request)

                # Get entities from response
                entities_field = _pluralize(_to_snake_case(entity_name))
                entities = getattr(response, entities_field, response.entities)

                # Render via service
                rendering_service = rendering_service_getter(self.env.app)
                rst_content = rendering_service.render_index(
                    entities=entities,
                    entity_type=slug,
                    docname=docname,
                    **dict(self.options),
                )

                return parse_rst_to_nodes(rst_content, docname)

        GeneratedIndexDirective.__name__ = f"{entity_name}IndexDirective"
        return GeneratedIndexDirective


def generate_define_directive(
    entity_name: str,
    create_use_case_factory: Callable[[Ctx], Any],
    request_cls: type[BaseModel],
    rendering_service_getter: Callable[[Any], DocumentationRenderingService],
    context_getter: Callable[[Any], Ctx],
    *,
    option_spec: dict[str, Any],
    option_to_request: Callable[[str, dict, list[str]], dict] | None = None,
) -> type[SphinxDirective]:
    """Generate a define directive that creates an entity via use case.

    Args:
        entity_name: Entity name (e.g., "Persona")
        create_use_case_factory: Function(context) -> CreateUseCase instance
        request_cls: Request class for the create use case
        rendering_service_getter: Function(app) -> DocumentationRenderingService
        context_getter: Function(app) -> domain context
        option_spec: Directive option specification
        option_to_request: Optional function(slug, options, content) -> request kwargs

    Returns:
        Generated directive class
    """
    slug = _to_snake_case(entity_name)

    class GeneratedDefineDirective(SphinxDirective):
        __doc__ = f"Define a {slug} with metadata."
        required_arguments = 1
        has_content = True
        option_spec = option_spec

        def run(self):
            entity_slug = self.arguments[0]
            docname = self.env.docname
            content = "\n".join(self.content).strip()

            ctx = context_getter(self.env.app)

            # Build request kwargs
            if option_to_request:
                request_kwargs = option_to_request(
                    entity_slug, dict(self.options), list(self.content)
                )
            else:
                request_kwargs = {
                    "slug": entity_slug,
                    **{k.replace("-", "_"): v for k, v in self.options.items()},
                    "docname": docname,
                }

            # Execute create use case
            use_case = create_use_case_factory(ctx)
            request = request_cls(**request_kwargs)
            response = use_case.execute_sync(request)

            # Get created entity from response
            entity_field = _to_snake_case(entity_name)
            entity = getattr(response, entity_field, response.entity)

            # Render via service
            rendering_service = rendering_service_getter(self.env.app)
            rst_content = rendering_service.render_entity(
                entity=entity,
                entity_type=slug,
                docname=docname,
                view_type="define",
                content=content,
            )

            return parse_rst_to_nodes(rst_content, docname)

    GeneratedDefineDirective.__name__ = f"Define{entity_name}Directive"
    return GeneratedDefineDirective


def make_placeholder_processor(
    placeholder_cls: type,
    resolve_fn: Callable[[nodes.Element, Any], list[nodes.Node]],
) -> Callable[[Any, Any, str], None]:
    """Create a placeholder processor function for doctree-resolved event.

    Args:
        placeholder_cls: The placeholder node class to find
        resolve_fn: Function(node, app) -> list of replacement nodes

    Returns:
        Event handler function for doctree-resolved
    """

    def process_placeholders(app, doctree, docname):
        for node in doctree.traverse(placeholder_cls):
            replacement = resolve_fn(node, app)
            node.replace_self(replacement)

    return process_placeholders


def generate_index_directive_from_build_fn(
    entity_name: str,
    build_function: Callable[[str, Ctx], list[nodes.Node]],
    context_getter: Callable[[Any], Ctx],
    *,
    option_spec: dict[str, Any] | None = None,
    env_getter: Callable[[Any], Any] | None = None,
) -> type[SphinxDirective]:
    """Generate an index directive using a custom build function.

    For complex indexes that need custom rendering logic beyond templates.
    The build function receives docname and context, returns docutils nodes.

    Args:
        entity_name: Entity name for directive naming (e.g., "Epic")
        build_function: Function(docname, context, **options) -> list[nodes.Node]
        context_getter: Function(app) -> domain context
        option_spec: Optional directive options
        env_getter: Optional function(app) -> env (for build functions that need it)

    Returns:
        Generated directive class with placeholder pattern
    """
    slug = _to_snake_case(entity_name)

    default_option_spec = {
        "format": directives.unchanged,
    }
    final_option_spec = {**default_option_spec, **(option_spec or {})}

    # Create placeholder class
    placeholder_cls = type(
        f"{entity_name}IndexPlaceholder",
        (nodes.General, nodes.Element),
        {"__doc__": f"Placeholder for {slug}-index directive."},
    )

    class GeneratedIndexDirective(SphinxDirective):
        __doc__ = f"Render index of all {slug}s."
        option_spec = final_option_spec

        placeholder_class = placeholder_cls

        def run(self):
            node = placeholder_cls()
            node["options"] = dict(self.options)
            node["docname"] = self.env.docname
            return [node]

        @staticmethod
        def resolve_placeholder(
            node: nodes.Element,
            app: Any,
        ) -> list[nodes.Node]:
            """Resolve placeholder to actual content."""
            ctx = context_getter(app)
            docname = node["docname"]
            options = node["options"]

            # Call build function with appropriate args
            if env_getter:
                env = env_getter(app)
                return build_function(env, docname, ctx, **options)
            else:
                return build_function(docname, ctx, **options)

    GeneratedIndexDirective.__name__ = f"{entity_name}IndexDirective"
    return GeneratedIndexDirective
