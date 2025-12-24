"""Code link directives for sphinx_hcd.

Provides directives that generate links to AutoAPI documentation:
- list-accelerator-code: Links to accelerator domain/infrastructure code
- list-app-code: Links to application code
- list-contrib-code: Links to contrib module code
- entity-diagram: PlantUML class diagram of domain entities
"""

import logging
import os
from pathlib import Path

from docutils import nodes
from docutils.parsers.rst import directives

from .base import HCDDirective

logger = logging.getLogger(__name__)


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
    """Build code link nodes for an accelerator.

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
    result_nodes = []

    # Get code info from repository
    code_info = hcd_context.code_info_repo.get(accelerator_slug)

    # Build autoapi base path
    autoapi_base = f"autoapi/julee/{accelerator_slug}"

    # Check which autoapi paths exist
    docs_dir = Path(app.srcdir)

    def check_autoapi_path(subpath: str) -> tuple[bool, str]:
        """Check if autoapi path exists and return (exists, full_path)."""
        full_path = f"{autoapi_base}/{subpath}/index"
        rst_file = docs_dir / f"{full_path}.rst"
        return rst_file.exists(), full_path

    # Domain section
    domain_section = nodes.section()
    domain_section["ids"] = [f"{accelerator_slug}-domain-code"]
    domain_title = nodes.title(text="Domain")
    domain_section += domain_title

    domain_list = nodes.bullet_list()
    domain_items = []

    # Entities
    exists, path = check_autoapi_path("domain/models")
    count = len(code_info.entities) if code_info else 0
    if exists or show_empty:
        item = _make_code_link_item(
            "Entities",
            count,
            f"{prefix}{path}.html" if exists else None,
            exists,
        )
        domain_items.append(item)
        if not exists:
            logger.warning(
                f"list-accelerator-code: Missing autoapi path for "
                f"{accelerator_slug} entities: {path}"
            )

    # Repository Protocols
    exists, path = check_autoapi_path("domain/repositories")
    count = len(code_info.repository_protocols) if code_info else 0
    if exists or show_empty:
        item = _make_code_link_item(
            "Repository Protocols",
            count,
            f"{prefix}{path}.html" if exists else None,
            exists,
        )
        domain_items.append(item)
        if not exists:
            logger.warning(
                f"list-accelerator-code: Missing autoapi path for "
                f"{accelerator_slug} repository protocols: {path}"
            )

    # Service Protocols
    exists, path = check_autoapi_path("domain/services")
    count = len(code_info.service_protocols) if code_info else 0
    if exists or count > 0 or show_empty:
        item = _make_code_link_item(
            "Service Protocols",
            count,
            f"{prefix}{path}.html" if exists else None,
            exists,
        )
        domain_items.append(item)
        if not exists and count > 0:
            logger.warning(
                f"list-accelerator-code: Missing autoapi path for "
                f"{accelerator_slug} service protocols: {path}"
            )

    # Use Cases
    exists, path = check_autoapi_path("domain/use_cases")
    count = len(code_info.use_cases) if code_info else 0
    if exists or count > 0 or show_empty:
        item = _make_code_link_item(
            "Use Cases",
            count,
            f"{prefix}{path}.html" if exists else None,
            exists,
        )
        domain_items.append(item)
        if not exists and count > 0:
            logger.warning(
                f"list-accelerator-code: Missing autoapi path for "
                f"{accelerator_slug} use cases: {path}"
            )

    # Requests (use case input DTOs)
    requests_count = len(code_info.requests) if code_info else 0
    if requests_count > 0 or show_empty:
        # Requests are in use_cases/requests.py, link to use_cases index
        exists, path = check_autoapi_path("domain/use_cases")
        item = _make_code_link_item(
            "Requests",
            requests_count,
            f"{prefix}{path}.html" if exists else None,
            exists and requests_count > 0,
        )
        domain_items.append(item)

    # Responses (use case output DTOs)
    responses_count = len(code_info.responses) if code_info else 0
    if responses_count > 0 or show_empty:
        # Responses are in use_cases/responses.py, link to use_cases index
        exists, path = check_autoapi_path("domain/use_cases")
        item = _make_code_link_item(
            "Responses",
            responses_count,
            f"{prefix}{path}.html" if exists else None,
            exists and responses_count > 0,
        )
        domain_items.append(item)

    for item in domain_items:
        domain_list += item

    if domain_items:
        domain_section += domain_list
        result_nodes.append(domain_section)

    # Infrastructure section
    infra_section = nodes.section()
    infra_section["ids"] = [f"{accelerator_slug}-infrastructure-code"]
    infra_title = nodes.title(text="Infrastructure")
    infra_section += infra_title

    infra_list = nodes.bullet_list()
    infra_items = []

    # Repository Implementations (check multiple locations)
    repo_impl_paths = [
        ("repositories/memory", "Memory Repositories"),
        ("repositories/file", "File Repositories"),
        ("repositories", "Repository Implementations"),
    ]
    for subpath, label in repo_impl_paths:
        exists, path = check_autoapi_path(subpath)
        if exists:
            item = _make_code_link_item(label, None, f"{prefix}{path}.html", exists)
            infra_items.append(item)

    # Also check shared repositories
    shared_repo_path = "autoapi/julee/repositories/index"
    if (docs_dir / f"{shared_repo_path}.rst").exists():
        item = _make_code_link_item(
            "Shared Repositories",
            None,
            f"{prefix}{shared_repo_path}.html",
            True,
        )
        infra_items.append(item)

    # Pipelines/Workflows
    workflows_path = "autoapi/julee/workflows/index"
    if (docs_dir / f"{workflows_path}.rst").exists():
        item = _make_code_link_item(
            "Pipelines (Workflows)",
            None,
            f"{prefix}{workflows_path}.html",
            True,
        )
        infra_items.append(item)

    for item in infra_items:
        infra_list += item

    if infra_items:
        infra_section += infra_list
        result_nodes.append(infra_section)

    # Warning if no code info found
    if not code_info:
        warning = nodes.warning()
        warning_para = nodes.paragraph()
        warning_para += nodes.Text(
            f"No code introspection data found for accelerator '{accelerator_slug}'. "
            f"Ensure it exists in src/julee/{accelerator_slug}/ with proper structure."
        )
        warning += warning_para
        result_nodes.insert(0, warning)

    return result_nodes


def _make_code_link_item(
    label: str,
    count: int | None,
    href: str | None,
    exists: bool,
) -> nodes.list_item:
    """Create a bullet list item for a code link.

    Args:
        label: Display label (e.g., "Entities")
        count: Number of items (None to omit)
        href: Link target (None if doesn't exist)
        exists: Whether the target exists

    Returns:
        A list_item node
    """
    item = nodes.list_item()
    para = nodes.paragraph()

    if exists and href:
        ref = nodes.reference("", "", refuri=href)
        ref += nodes.strong(text=label)
        para += ref
    else:
        para += nodes.strong(text=label)
        if not exists:
            para += nodes.Text(" ")
            para += nodes.emphasis(text="(not found)")

    if count is not None:
        para += nodes.Text(f" ({count})")

    item += para
    return item


def build_accelerator_entity_list(
    accelerator_slug: str,
    docname: str,
    app,
    hcd_context,
) -> list[nodes.Node]:
    """Build a bullet list of entities with AutoAPI links.

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

    # Get code info from repository
    code_info = hcd_context.code_info_repo.get(accelerator_slug)

    if not code_info or not code_info.entities:
        para = nodes.paragraph()
        para += nodes.emphasis(text=f"No entities found for '{accelerator_slug}'")
        return [para]

    bullet_list = nodes.bullet_list()

    for entity in sorted(code_info.entities, key=lambda e: e.name):
        item = nodes.list_item()
        para = nodes.paragraph()

        # Build AutoAPI link path based on file location
        # Entities are in domain/models/, file name maps to module
        module_name = entity.file.replace(".py", "")

        # Try nested structure first: domain/models/{package}/{module}/index
        # (common in CEAP where assembly/assembly.py contains Assembly)
        nested_path = f"autoapi/julee/{accelerator_slug}/domain/models/{module_name}/{module_name}/index"
        flat_path = f"autoapi/julee/{accelerator_slug}/domain/models/{module_name}/index"

        if (docs_dir / f"{nested_path}.rst").exists():
            # Nested structure: link to julee.{slug}.domain.models.{package}.{module}.{Class}
            href = f"{prefix}{nested_path}.html#julee.{accelerator_slug}.domain.models.{module_name}.{module_name}.{entity.name}"
            ref = nodes.reference("", "", refuri=href)
            ref += nodes.literal(text=entity.name)
            para += ref
        elif (docs_dir / f"{flat_path}.rst").exists():
            # Flat structure: link to julee.{slug}.domain.models.{module}.{Class}
            href = f"{prefix}{flat_path}.html#julee.{accelerator_slug}.domain.models.{module_name}.{entity.name}"
            ref = nodes.reference("", "", refuri=href)
            ref += nodes.literal(text=entity.name)
            para += ref
        else:
            # Fallback: try the models index page
            fallback_path = f"autoapi/julee/{accelerator_slug}/domain/models/index"
            if (docs_dir / f"{fallback_path}.rst").exists():
                href = f"{prefix}{fallback_path}.html"
                ref = nodes.reference("", "", refuri=href)
                ref += nodes.literal(text=entity.name)
                para += ref
            else:
                para += nodes.literal(text=entity.name)

        # Add docstring if available
        if entity.docstring:
            para += nodes.Text(" — ")
            para += nodes.Text(entity.docstring)

        item += para
        bullet_list += item

    return [bullet_list]


def build_accelerator_usecase_list(
    accelerator_slug: str,
    docname: str,
    app,
    hcd_context,
) -> list[nodes.Node]:
    """Build a list of use cases with AutoAPI links.

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

    # Get code info from repository
    code_info = hcd_context.code_info_repo.get(accelerator_slug)

    if not code_info or not code_info.use_cases:
        para = nodes.paragraph()
        para += nodes.emphasis(text=f"No use cases found for '{accelerator_slug}'")
        return [para]

    result_nodes = []

    for use_case in sorted(code_info.use_cases, key=lambda u: u.name):
        # Create a container for this use case
        container = nodes.container()
        container["classes"].append("usecase-item")

        # Build AutoAPI link path
        # file can be "create.py" or "diagrams/container_diagram.py"
        module_path = use_case.file.replace(".py", "")  # "create" or "diagrams/container_diagram"
        # Convert path separators to dots for the anchor
        module_dotted = module_path.replace("/", ".").replace("\\", ".")

        # Build paths - autoapi uses directory structure
        flat_path = f"autoapi/julee/{accelerator_slug}/domain/use_cases/{module_path}/index"

        # Determine href
        href = None
        if (docs_dir / f"{flat_path}.rst").exists():
            href = f"{prefix}{flat_path}.html#julee.{accelerator_slug}.domain.use_cases.{module_dotted}.{use_case.name}"
        else:
            fallback_path = f"autoapi/julee/{accelerator_slug}/domain/use_cases/index"
            if (docs_dir / f"{fallback_path}.rst").exists():
                href = f"{prefix}{fallback_path}.html"

        # Add linked title
        title_para = nodes.paragraph()
        if href:
            ref = nodes.reference("", "", refuri=href)
            ref += nodes.strong(text=use_case.name)
            title_para += ref
        else:
            title_para += nodes.strong(text=use_case.name)
        container += title_para

        # Add docstring if available
        if use_case.docstring:
            desc_para = nodes.paragraph()
            desc_para += nodes.Text(use_case.docstring)
            container += desc_para

        result_nodes.append(container)

    return result_nodes


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

    # Get code info from repository
    code_info = hcd_context.code_info_repo.get(accelerator_slug)

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
