"""Code link directives for sphinx_hcd.

Provides directives that generate links to AutoAPI documentation:
- list-accelerator-code: Links to accelerator domain/infrastructure code
- list-app-code: Links to application code
- list-contrib-code: Links to contrib module code
- entity-diagram: PlantUML class diagram of domain entities

Template-driven pattern (for code_links):
1. Directive creates placeholder with arguments
2. Processor calls use case to get code_info
3. Processor checks Sphinx filesystem (autoapi paths)
4. Processor calls rendering service with prepared data
5. Template renders RST
6. RST parsed to docutils nodes

PlantUML diagrams (entity-diagram) use Python rendering since they
generate PlantUML source, not RST.
"""

import logging
import os
from pathlib import Path

from docutils import nodes
from docutils.parsers.rst import directives
from jinja2 import Environment, FileSystemLoader

from apps.sphinx.directive_factory import parse_rst_to_nodes
from julee.hcd.use_cases.crud import GetCodeInfoRequest

from .base import HCDDirective

logger = logging.getLogger(__name__)

# Template directory for Core entity templates (code_info is Core entity)
_CORE_TEMPLATE_DIR = Path(__file__).parent.parent.parent.parent.parent / "src/julee/core/infrastructure/templates"

# Jinja environment for code links templates
_jinja_env: Environment | None = None


def _get_jinja_env() -> Environment:
    """Get or create Jinja environment for code links templates."""
    global _jinja_env
    if _jinja_env is None:
        _jinja_env = Environment(
            loader=FileSystemLoader(str(_CORE_TEMPLATE_DIR)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
    return _jinja_env


class AcceleratorCodePlaceholder(nodes.General, nodes.Element):
    """Placeholder for list-accelerator-code, replaced at doctree-resolved."""

    pass


class EntityDiagramPlaceholder(nodes.General, nodes.Element):
    """Placeholder for entity-diagram, replaced at doctree-resolved."""

    pass


class AcceleratorEntityListPlaceholder(nodes.General, nodes.Element):
    """Placeholder for accelerator-entity-list, replaced at doctree-resolved."""

    pass


class AcceleratorUseCaseListPlaceholder(nodes.General, nodes.Element):
    """Placeholder for accelerator-usecase-list, replaced at doctree-resolved."""

    pass


class AcceleratorEntityListDirective(HCDDirective):
    """Generate a list of domain entities with AutoAPI links.

    Usage::

        .. accelerator-entity-list:: ceap

    Generates a bullet list of entity classes, each linking to its AutoAPI docs.
    """

    required_arguments = 1
    has_content = False

    def run(self):
        accelerator_slug = self.arguments[0].lower()
        node = AcceleratorEntityListPlaceholder()
        node["accelerator_slug"] = accelerator_slug
        node["docname"] = self.env.docname
        return [node]


class AcceleratorUseCaseListDirective(HCDDirective):
    """Generate a list of use cases with AutoAPI links.

    Usage::

        .. accelerator-usecase-list:: ceap

    Generates a list of use case classes with:
    - Link to AutoAPI documentation
    - Docstring description

    For sequence diagrams, use the ``usecase-documentation`` directive
    in a dedicated documentation page.
    """

    required_arguments = 1
    has_content = False
    option_spec = {}

    def run(self):
        accelerator_slug = self.arguments[0].lower()
        node = AcceleratorUseCaseListPlaceholder()
        node["accelerator_slug"] = accelerator_slug
        node["docname"] = self.env.docname
        return [node]


class ListAcceleratorCodeDirective(HCDDirective):
    """Generate links to accelerator code documentation.

    Usage::

        .. list-accelerator-code:: ceap

    Generates a structured list of links to AutoAPI documentation for:
    - Domain: Entities, Repository Protocols, Service Protocols, Use Cases
    - Infrastructure: Repository Implementations, Service Implementations, Pipelines
    """

    required_arguments = 1
    has_content = False
    option_spec = {
        "show-empty": directives.flag,  # Show sections even if empty
    }

    def run(self):
        accelerator_slug = self.arguments[0].lower()
        node = AcceleratorCodePlaceholder()
        node["accelerator_slug"] = accelerator_slug
        node["show_empty"] = "show-empty" in self.options
        node["docname"] = self.env.docname
        return [node]


class EntityDiagramDirective(HCDDirective):
    """Generate PlantUML class diagram of domain entities.

    Usage::

        .. entity-diagram:: ceap

    Generates a PlantUML class diagram showing:
    - Entity classes with their fields and types
    - Inheritance relationships (extends arrows)
    - Field types that reference other entities
    """

    required_arguments = 1
    has_content = False
    option_spec = {
        "show-fields": directives.flag,  # Show class fields (default: yes)
        "show-types": directives.flag,  # Show field types (default: yes)
    }

    def run(self):
        accelerator_slug = self.arguments[0].lower()
        node = EntityDiagramPlaceholder()
        node["accelerator_slug"] = accelerator_slug
        node["docname"] = self.env.docname
        # Default to showing fields and types
        node["show_fields"] = "show-fields" not in self.options or True
        node["show_types"] = "show-types" not in self.options or True
        return [node]


def build_accelerator_code_links(
    accelerator_slug: str,
    docname: str,
    app,
    hcd_context,
    show_empty: bool = False,
) -> list[nodes.Node]:
    """Build code link nodes for an accelerator using template-driven rendering.

    Pattern:
    1. Call use case to get code_info (Core entity)
    2. Check Sphinx filesystem for autoapi paths (Sphinx-specific)
    3. Prepare data structure for template
    4. Render via Jinja template
    5. Parse RST to docutils nodes

    Args:
        accelerator_slug: The accelerator identifier (e.g., 'ceap', 'hcd', 'c4')
        docname: Current document name (for relative paths)
        app: Sphinx application
        hcd_context: HCD context with repositories
        show_empty: Whether to show sections with no items

    Returns:
        List of docutils nodes
    """
    from apps.sphinx.shared import path_to_root

    prefix = path_to_root(docname)

    # Get code info via use case
    response = hcd_context.get_code_info.execute_sync(
        GetCodeInfoRequest(slug=accelerator_slug)
    )
    code_info = response.code_info

    # Prepare data for template
    data = _prepare_code_links_data(
        accelerator_slug, code_info, app, prefix, show_empty
    )

    # Render template
    env = _get_jinja_env()
    template = env.get_template("code_links_detail.rst.j2")
    rst_content = template.render(**data)

    # Parse RST to nodes
    return parse_rst_to_nodes(rst_content, docname)


def _prepare_code_links_data(
    accelerator_slug: str,
    code_info,
    app,
    prefix: str,
    show_empty: bool,
) -> dict:
    """Prepare data structure for code_links template.

    Checks Sphinx filesystem for autoapi paths and builds the data
    structure expected by the template.

    Args:
        accelerator_slug: The accelerator identifier
        code_info: BoundedContextInfo from use case
        app: Sphinx application (for srcdir)
        prefix: Path prefix for relative links
        show_empty: Whether to include empty items

    Returns:
        Dict with domain_items, infrastructure_items, warning
    """
    autoapi_base = f"autoapi/julee/{accelerator_slug}"
    docs_dir = Path(app.srcdir)

    def check_path(subpath: str) -> tuple[bool, str, str]:
        """Check if autoapi path exists, return (exists, full_path, href)."""
        full_path = f"{autoapi_base}/{subpath}/index"
        rst_file = docs_dir / f"{full_path}.rst"
        exists = rst_file.exists()
        href = f"{prefix}{full_path}.html" if exists else None
        return exists, full_path, href

    domain_items = []
    infrastructure_items = []
    warning = None

    if not code_info:
        warning = (
            f"No code introspection data found for accelerator '{accelerator_slug}'. "
            f"Ensure it exists in src/julee/{accelerator_slug}/ with proper structure."
        )
        return {
            "accelerator_slug": accelerator_slug,
            "domain_items": domain_items,
            "infrastructure_items": infrastructure_items,
            "warning": warning,
        }

    # Domain items
    domain_checks = [
        ("domain/models", "Entities", len(code_info.entities)),
        ("domain/repositories", "Repository Protocols", len(code_info.repository_protocols)),
        ("domain/services", "Service Protocols", len(code_info.service_protocols)),
        ("domain/use_cases", "Use Cases", len(code_info.use_cases)),
    ]

    for subpath, label, count in domain_checks:
        exists, full_path, href = check_path(subpath)
        if exists or count > 0 or show_empty:
            domain_items.append({
                "label": label,
                "count": count,
                "href": href,
                "exists": exists,
            })
            if not exists and count > 0:
                logger.warning(
                    f"list-accelerator-code: Missing autoapi path for "
                    f"{accelerator_slug} {label.lower()}: {full_path}"
                )

    # Requests and Responses (link to use_cases)
    exists, _, href = check_path("domain/use_cases")
    for label, count in [
        ("Requests", len(code_info.requests)),
        ("Responses", len(code_info.responses)),
    ]:
        if count > 0 or show_empty:
            domain_items.append({
                "label": label,
                "count": count,
                "href": href if exists and count > 0 else None,
                "exists": exists and count > 0,
            })

    # Infrastructure items
    infra_checks = [
        ("repositories/memory", "Memory Repositories"),
        ("repositories/file", "File Repositories"),
        ("repositories", "Repository Implementations"),
    ]

    for subpath, label in infra_checks:
        exists, _, href = check_path(subpath)
        if exists:
            infrastructure_items.append({
                "label": label,
                "count": None,
                "href": href,
                "exists": True,
            })

    # Shared repositories
    shared_repo_path = "autoapi/julee/repositories/index"
    if (docs_dir / f"{shared_repo_path}.rst").exists():
        infrastructure_items.append({
            "label": "Shared Repositories",
            "count": None,
            "href": f"{prefix}{shared_repo_path}.html",
            "exists": True,
        })

    # Pipelines/Workflows
    workflows_path = "autoapi/julee/workflows/index"
    if (docs_dir / f"{workflows_path}.rst").exists():
        infrastructure_items.append({
            "label": "Pipelines (Workflows)",
            "count": None,
            "href": f"{prefix}{workflows_path}.html",
            "exists": True,
        })

    return {
        "accelerator_slug": accelerator_slug,
        "domain_items": domain_items,
        "infrastructure_items": infrastructure_items,
        "warning": warning,
    }


def build_accelerator_entity_list(
    accelerator_slug: str,
    docname: str,
    app,
    hcd_context,
) -> list[nodes.Node]:
    """Build a bullet list of entities with AutoAPI links using template.

    Args:
        accelerator_slug: The accelerator identifier
        docname: Current document name
        app: Sphinx application
        hcd_context: HCD context with repositories

    Returns:
        List of docutils nodes
    """
    from apps.sphinx.shared import path_to_root

    prefix = path_to_root(docname)
    docs_dir = Path(app.srcdir)

    # Get code info via use case
    response = hcd_context.get_code_info.execute_sync(
        GetCodeInfoRequest(slug=accelerator_slug)
    )
    code_info = response.code_info

    # Prepare entity data for template
    entities = []
    if code_info and code_info.entities:
        for entity in sorted(code_info.entities, key=lambda e: e.name):
            module_name = entity.file.replace(".py", "")
            href = _find_entity_href(
                accelerator_slug, module_name, entity.name, docs_dir, prefix
            )
            entities.append({
                "name": entity.name,
                "href": href,
                "docstring": entity.docstring,
            })

    # Render template
    env = _get_jinja_env()
    template = env.get_template("entity_list.rst.j2")
    rst_content = template.render(
        entities=entities,
        empty_message=f"No entities found for '{accelerator_slug}'",
    )

    return parse_rst_to_nodes(rst_content, docname)


def _find_entity_href(
    accelerator_slug: str,
    module_name: str,
    entity_name: str,
    docs_dir: Path,
    prefix: str,
) -> str | None:
    """Find AutoAPI href for an entity.

    Checks multiple path patterns for AutoAPI documentation.
    """
    # Try nested structure first
    nested_path = f"autoapi/julee/{accelerator_slug}/domain/models/{module_name}/{module_name}/index"
    if (docs_dir / f"{nested_path}.rst").exists():
        return f"{prefix}{nested_path}.html#julee.{accelerator_slug}.domain.models.{module_name}.{module_name}.{entity_name}"

    # Try flat structure
    flat_path = f"autoapi/julee/{accelerator_slug}/domain/models/{module_name}/index"
    if (docs_dir / f"{flat_path}.rst").exists():
        return f"{prefix}{flat_path}.html#julee.{accelerator_slug}.domain.models.{module_name}.{entity_name}"

    # Fallback to models index
    fallback_path = f"autoapi/julee/{accelerator_slug}/domain/models/index"
    if (docs_dir / f"{fallback_path}.rst").exists():
        return f"{prefix}{fallback_path}.html"

    return None


def build_accelerator_usecase_list(
    accelerator_slug: str,
    docname: str,
    app,
    hcd_context,
) -> list[nodes.Node]:
    """Build a list of use cases with AutoAPI links using template.

    Args:
        accelerator_slug: The accelerator identifier
        docname: Current document name
        app: Sphinx application
        hcd_context: HCD context with repositories

    Returns:
        List of docutils nodes
    """
    from apps.sphinx.shared import path_to_root

    prefix = path_to_root(docname)
    docs_dir = Path(app.srcdir)

    # Get code info via use case
    response = hcd_context.get_code_info.execute_sync(
        GetCodeInfoRequest(slug=accelerator_slug)
    )
    code_info = response.code_info

    # Prepare use case data for template
    use_cases = []
    if code_info and code_info.use_cases:
        for uc in sorted(code_info.use_cases, key=lambda u: u.name):
            href = _find_usecase_href(
                accelerator_slug, uc.file, uc.name, docs_dir, prefix
            )
            use_cases.append({
                "name": uc.name,
                "href": href,
                "docstring": uc.docstring,
            })

    # Render template
    env = _get_jinja_env()
    template = env.get_template("usecase_list.rst.j2")
    rst_content = template.render(
        use_cases=use_cases,
        empty_message=f"No use cases found for '{accelerator_slug}'",
    )

    return parse_rst_to_nodes(rst_content, docname)


def _find_usecase_href(
    accelerator_slug: str,
    file_path: str,
    use_case_name: str,
    docs_dir: Path,
    prefix: str,
) -> str | None:
    """Find AutoAPI href for a use case.

    Checks multiple path patterns for AutoAPI documentation.
    """
    module_path = file_path.replace(".py", "")
    module_dotted = module_path.replace("/", ".").replace("\\", ".")

    # Try direct path
    flat_path = f"autoapi/julee/{accelerator_slug}/domain/use_cases/{module_path}/index"
    if (docs_dir / f"{flat_path}.rst").exists():
        return f"{prefix}{flat_path}.html#julee.{accelerator_slug}.domain.use_cases.{module_dotted}.{use_case_name}"

    # Fallback to use_cases index
    fallback_path = f"autoapi/julee/{accelerator_slug}/domain/use_cases/index"
    if (docs_dir / f"{fallback_path}.rst").exists():
        return f"{prefix}{fallback_path}.html"

    return None


def build_entity_diagram(
    accelerator_slug: str,
    docname: str,
    hcd_context,
    show_fields: bool = True,
    show_types: bool = True,
) -> list[nodes.Node]:
    """Build PlantUML class diagram for domain entities.

    Args:
        accelerator_slug: The accelerator identifier
        docname: Current document name
        hcd_context: HCD context with repositories
        show_fields: Whether to show class fields
        show_types: Whether to show field type annotations

    Returns:
        List of docutils nodes containing the diagram
    """
    try:
        from sphinxcontrib.plantuml import plantuml
    except ImportError:
        para = nodes.paragraph()
        para += nodes.emphasis(text="PlantUML extension not available")
        return [para]

    # Get code info via use case
    response = hcd_context.get_code_info.execute_sync(
        GetCodeInfoRequest(slug=accelerator_slug)
    )
    code_info = response.code_info

    if not code_info or not code_info.entities:
        para = nodes.paragraph()
        para += nodes.emphasis(
            text=f"No entities found for accelerator '{accelerator_slug}'"
        )
        return [para]

    # Build PlantUML source
    lines = [
        "@startuml",
        "skinparam classAttributeIconSize 0",
        "skinparam classFontStyle bold",
        "hide empty members",
        "",
    ]

    # Build set of entity names for relationship detection
    entity_names = {e.name for e in code_info.entities}

    # Declare classes
    for entity in sorted(code_info.entities, key=lambda e: e.name):
        # Start class definition
        if entity.bases:
            # Filter to only show relevant bases (not BaseModel, etc.)
            relevant_bases = [
                b for b in entity.bases
                if b in entity_names or not b.startswith(("Base", "ABC"))
            ]
            if relevant_bases:
                extends = ", ".join(relevant_bases)
                lines.append(f"class {entity.name} extends {extends} {{")
            else:
                lines.append(f"class {entity.name} {{")
        else:
            lines.append(f"class {entity.name} {{")

        # Add fields if enabled
        if show_fields and entity.fields:
            for field in entity.fields:
                if show_types and field.type_annotation:
                    # Simplify complex type annotations for readability
                    type_str = _simplify_type(field.type_annotation)
                    lines.append(f"  {field.name}: {type_str}")
                else:
                    lines.append(f"  {field.name}")

        lines.append("}")
        lines.append("")

    # Add relationships based on field types referencing other entities
    for entity in code_info.entities:
        for field in entity.fields:
            if field.type_annotation:
                # Check if field type references another entity
                for other_name in entity_names:
                    if other_name != entity.name and other_name in field.type_annotation:
                        # Determine relationship type
                        if "list[" in field.type_annotation.lower():
                            lines.append(f'{entity.name} "1" *-- "many" {other_name}')
                        elif "optional[" in field.type_annotation.lower():
                            lines.append(f'{entity.name} "1" o-- "0..1" {other_name}')
                        else:
                            lines.append(f"{entity.name} --> {other_name}")

    lines.append("")
    lines.append("@enduml")

    puml_source = "\n".join(lines)
    node = plantuml(puml_source)
    node["uml"] = puml_source
    node["incdir"] = os.path.dirname(docname)
    node["filename"] = os.path.basename(docname)

    return [node]


def _simplify_type(type_annotation: str) -> str:
    """Simplify a type annotation for diagram display.

    Args:
        type_annotation: Full type annotation string

    Returns:
        Simplified version for readability
    """
    # Remove common prefixes
    result = type_annotation
    result = result.replace("typing.", "")
    result = result.replace("collections.abc.", "")

    # Shorten common patterns
    if result.startswith("list[") and result.endswith("]"):
        inner = result[5:-1]
        result = f"list[{_simplify_type(inner)}]"
    elif result.startswith("Optional[") and result.endswith("]"):
        inner = result[9:-1]
        result = f"{_simplify_type(inner)}?"
    elif " | None" in result:
        result = result.replace(" | None", "?")

    # Truncate very long types
    if len(result) > 30:
        result = result[:27] + "..."

    return result


def process_accelerator_code_placeholders(app, doctree, docname):
    """Replace accelerator code placeholders with rendered content."""
    from ..context import get_hcd_context

    hcd_context = get_hcd_context(app)

    for node in doctree.traverse(AcceleratorCodePlaceholder):
        accelerator_slug = node["accelerator_slug"]
        show_empty = node.get("show_empty", False)
        content = build_accelerator_code_links(
            accelerator_slug,
            docname,
            app,
            hcd_context,
            show_empty,
        )
        node.replace_self(content)


def process_entity_diagram_placeholders(app, doctree, docname):
    """Replace entity diagram placeholders with rendered content."""
    from ..context import get_hcd_context

    hcd_context = get_hcd_context(app)

    for node in doctree.traverse(EntityDiagramPlaceholder):
        accelerator_slug = node["accelerator_slug"]
        show_fields = node.get("show_fields", True)
        show_types = node.get("show_types", True)
        content = build_entity_diagram(
            accelerator_slug,
            docname,
            hcd_context,
            show_fields,
            show_types,
        )
        node.replace_self(content)


def process_accelerator_entity_list_placeholders(app, doctree, docname):
    """Replace accelerator entity list placeholders with rendered content."""
    from ..context import get_hcd_context

    hcd_context = get_hcd_context(app)

    for node in doctree.traverse(AcceleratorEntityListPlaceholder):
        accelerator_slug = node["accelerator_slug"]
        content = build_accelerator_entity_list(
            accelerator_slug,
            docname,
            app,
            hcd_context,
        )
        node.replace_self(content)


def process_accelerator_usecase_list_placeholders(app, doctree, docname):
    """Replace accelerator use case list placeholders with rendered content."""
    from ..context import get_hcd_context

    hcd_context = get_hcd_context(app)

    for node in doctree.traverse(AcceleratorUseCaseListPlaceholder):
        accelerator_slug = node["accelerator_slug"]
        content = build_accelerator_usecase_list(
            accelerator_slug,
            docname,
            app,
            hcd_context,
        )
        node.replace_self(content)
