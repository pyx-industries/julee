"""Jinja2 templates for RST serialization.

Provides template-based rendering of domain entities to RST format,
enabling lossless round-trip: Entity → RST → Entity.
"""

from jinja2 import Environment, PackageLoader

# Create Jinja2 environment with RST-friendly settings
_env = Environment(
    loader=PackageLoader("julee.docs.sphinx_hcd", "templates"),
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
)


def render_entity(entity_type: str, entity) -> str:
    """Render an entity to RST using its Jinja2 template.

    Args:
        entity_type: Type name matching template file (e.g., 'journey', 'epic')
        entity: Domain entity (Pydantic model) to render

    Returns:
        RST content as string
    """
    template = _env.get_template(f"{entity_type}.rst.j2")
    return template.render(entity=entity)


def get_template(name: str):
    """Get a template by name for direct use.

    Args:
        name: Template filename (e.g., 'journey.rst.j2')

    Returns:
        Jinja2 Template object
    """
    return _env.get_template(name)
