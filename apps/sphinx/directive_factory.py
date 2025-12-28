"""Generic directive factory for use-case-driven Sphinx directives.

Provides factory functions to generate Sphinx directives that:
1. Call a use case to get data
2. Render a Jinja template with that data
3. Convert the resulting RST to docutils nodes

This separates data fetching (use cases) from presentation (templates),
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
        template_path="persona_index.rst.jinja",
    )
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

from docutils import nodes
from docutils.parsers.rst import directives
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import BaseModel
from sphinx.util.docutils import SphinxDirective

from apps.sphinx.shared import path_to_root

# Type for context objects (HCDContext, C4Context, etc.)
Ctx = TypeVar("Ctx")


def _to_snake_case(name: str) -> str:
    """Convert CamelCase to snake_case."""
    import re

    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _pluralize(name: str) -> str:
    """Simple English pluralization."""
    if name.endswith("y") and len(name) > 1 and name[-2] not in "aeiou":
        return name[:-1] + "ies"
    elif name.endswith("s") or name.endswith("x") or name.endswith("ch"):
        return name + "es"
    return name + "s"


def _title_case(slug: str) -> str:
    """Convert slug to title case."""
    return slug.replace("-", " ").replace("_", " ").title()


def _first_sentence(text: str) -> str:
    """Extract first sentence from text."""
    if not text:
        return ""
    for i, char in enumerate(text):
        if char in ".!?" and (i + 1 >= len(text) or text[i + 1] in " \n"):
            return text[: i + 1]
    return text


def _create_jinja_env(template_dir: Path) -> Environment:
    """Create a Jinja environment with common filters."""
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(disabled_extensions=["rst", "jinja"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Register common filters
    env.filters["snake_case"] = _to_snake_case
    env.filters["pluralize"] = _pluralize
    env.filters["title_case"] = _title_case
    env.filters["first_sentence"] = _first_sentence

    return env


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


class DirectiveContext:
    """Context passed to templates for link building and path resolution."""

    def __init__(self, docname: str, config: Any):
        self.docname = docname
        self.config = config
        self.prefix = path_to_root(docname)

    def doc_path(self, doc_type: str) -> str:
        """Get path for a documentation type."""
        return f"{self.prefix}{self.config.get_doc_path(doc_type)}"

    def relative_uri(self, target_doc: str, anchor: str | None = None) -> str:
        """Build relative URI from current doc to target."""
        from_parts = self.docname.split("/")
        target_parts = target_doc.split("/")

        common = 0
        for i in range(min(len(from_parts), len(target_parts))):
            if from_parts[i] == target_parts[i]:
                common += 1
            else:
                break

        up_levels = len(from_parts) - common - 1
        down_path = "/".join(target_parts[common:])

        if up_levels > 0:
            rel_path = "../" * up_levels + down_path + ".html"
        else:
            rel_path = down_path + ".html"

        if anchor:
            return f"{rel_path}#{anchor}"
        return rel_path


class IndexPlaceholder(nodes.General, nodes.Element):
    """Generic placeholder node for index directives.

    Stores directive metadata for resolution during doctree-resolved event.
    """

    pass


def generate_index_directive(
    entity_name: str,
    use_case_factory: Callable[[Ctx], Any],
    request_factory: Callable[[dict], BaseModel],
    template_dir: Path,
    template_name: str,
    context_getter: Callable[[Any], Ctx],
    config_getter: Callable[[], Any],
    *,
    option_spec: dict[str, Any] | None = None,
    use_placeholder: bool = True,
) -> type[SphinxDirective]:
    """Generate an index directive that calls a use case and renders a template.

    Args:
        entity_name: Entity name for directive naming (e.g., "Persona")
        use_case_factory: Function(context) -> UseCase instance
        request_factory: Function(options) -> Request instance
        template_dir: Directory containing templates
        template_name: Template filename (e.g., "persona_index.rst.jinja")
        context_getter: Function(app) -> domain context (e.g., get_hcd_context)
        config_getter: Function() -> config object
        option_spec: Optional directive options (default: {"format": unchanged})
        use_placeholder: If True, use placeholder pattern for deferred rendering

    Returns:
        Generated directive class
    """
    jinja_env = _create_jinja_env(template_dir)
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
                config = config_getter()
                docname = node["docname"]
                options = node["options"]

                # Execute use case
                use_case = use_case_factory(ctx)
                request = request_factory(options)
                response = use_case.execute_sync(request)

                # Build template context
                template_ctx = DirectiveContext(docname, config)

                # Get entities from response (uses auto-derived field name)
                entities_field = _pluralize(_to_snake_case(entity_name))
                entities = getattr(response, entities_field, response.entities)

                # Render template
                template = jinja_env.get_template(template_name)
                rst_content = template.render(
                    entities=entities,
                    response=response,
                    ctx=template_ctx,
                    options=options,
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
                config = config_getter()

                # Execute use case
                use_case = use_case_factory(ctx)
                request = request_factory(self.options)
                response = use_case.execute_sync(request)

                # Build template context
                template_ctx = DirectiveContext(self.env.docname, config)

                # Get entities from response
                entities_field = _pluralize(_to_snake_case(entity_name))
                entities = getattr(response, entities_field, response.entities)

                # Render template
                template = jinja_env.get_template(template_name)
                rst_content = template.render(
                    entities=entities,
                    response=response,
                    ctx=template_ctx,
                    options=self.options,
                )

                return parse_rst_to_nodes(rst_content, self.env.docname)

        GeneratedIndexDirective.__name__ = f"{entity_name}IndexDirective"
        return GeneratedIndexDirective


def generate_define_directive(
    entity_name: str,
    create_use_case_factory: Callable[[Ctx], Any],
    request_cls: type[BaseModel],
    template_dir: Path,
    template_name: str,
    context_getter: Callable[[Any], Ctx],
    config_getter: Callable[[], Any],
    *,
    option_spec: dict[str, Any],
    option_to_request: Callable[[str, dict, list[str]], dict] | None = None,
) -> type[SphinxDirective]:
    """Generate a define directive that creates an entity via use case.

    Args:
        entity_name: Entity name (e.g., "Persona")
        create_use_case_factory: Function(context) -> CreateUseCase instance
        request_cls: Request class for the create use case
        template_dir: Directory containing templates
        template_name: Template filename for rendering the defined entity
        context_getter: Function(app) -> domain context
        config_getter: Function() -> config object
        option_spec: Directive option specification
        option_to_request: Optional function(slug, options, content) -> request kwargs

    Returns:
        Generated directive class
    """
    jinja_env = _create_jinja_env(template_dir)
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
            config = config_getter()

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

            # Render template
            template_ctx = DirectiveContext(docname, config)
            template = jinja_env.get_template(template_name)
            rst_content = template.render(
                entity=entity,
                ctx=template_ctx,
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
