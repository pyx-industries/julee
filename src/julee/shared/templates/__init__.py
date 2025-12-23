"""Jinja2 templates for shared diagram generation.

Provides template-based rendering for PlantUML diagrams
and other cross-domain visualization needs.
"""

from jinja2 import Environment, PackageLoader

from ..introspection.usecase import UseCaseMetadata

# Create Jinja2 environment
_env = Environment(
    loader=PackageLoader("julee.shared", "templates"),
    trim_blocks=True,
    lstrip_blocks=True,
)


def _make_alias(name: str) -> str:
    """Convert a dependency name to a short alias for PlantUML."""
    return name.replace("_repo", "").replace("_service", "").replace("_", "")


# Register custom filters
_env.filters["make_alias"] = _make_alias


def render_ssd(metadata: UseCaseMetadata, title: str = "") -> str:
    """Render use case sequence diagram to PlantUML.

    Args:
        metadata: Use case metadata from introspection
        title: Optional diagram title

    Returns:
        PlantUML source code as string
    """
    template = _env.get_template("usecase_ssd.puml.j2")
    return template.render(uc=metadata, title=title)


def get_template(name: str):
    """Get a template by name for direct use.

    Args:
        name: Template filename (e.g., 'usecase_ssd.puml.j2')

    Returns:
        Jinja2 Template object
    """
    return _env.get_template(name)
