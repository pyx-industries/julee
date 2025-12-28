"""Generated HCD directives using the directive factory.

This module creates directives by combining:
- Use cases from julee.hcd (data access)
- DocumentationRenderingService (presentation) OR custom build functions
- directive_factory (boilerplate reduction)

Each generated directive follows the same pattern:
1. Call a use case to get entities (or use existing build function)
2. Render via the rendering service or build function
3. Return docutils nodes

Simple indexes (persona) use templates for rendering.
Complex indexes (epic, app, accelerator, integration) use existing build functions
that have complex grouping logic, cross-entity queries, or PlantUML generation.
"""

from pathlib import Path

from apps.sphinx.directive_factory import (
    generate_index_directive,
    generate_index_directive_from_build_fn,
    make_placeholder_processor,
)
from julee.core.infrastructure.services.jinja_documentation import (
    JinjaDocumentationRenderer,
)
from julee.hcd.use_cases.crud import ListPersonasRequest

from .config import get_config
from .context import get_hcd_context

# Template directory for HCD entities
_HCD_TEMPLATE_DIR = Path(__file__).parent.parent.parent.parent / "src/julee/hcd/infrastructure/templates"

# Rendering service instance (lazily initialized per app)
_rendering_services: dict[int, JinjaDocumentationRenderer] = {}


def _get_rendering_service(app) -> JinjaDocumentationRenderer:
    """Get or create rendering service for a Sphinx app.

    The service is cached per app instance to avoid recreating
    the Jinja environment on every directive invocation.
    """
    app_id = id(app)
    if app_id not in _rendering_services:
        config = get_config()
        _rendering_services[app_id] = JinjaDocumentationRenderer(
            template_dirs=[_HCD_TEMPLATE_DIR],
            doc_paths={
                "personas": config.get_doc_path("personas"),
                "epics": config.get_doc_path("epics"),
                "journeys": config.get_doc_path("journeys"),
                "stories": config.get_doc_path("stories"),
                "applications": config.get_doc_path("applications"),
                "accelerators": config.get_doc_path("accelerators"),
                "integrations": config.get_doc_path("integrations"),
            },
        )
    return _rendering_services[app_id]


def _get_env(app):
    """Get Sphinx environment from app."""
    return app.env


# =============================================================================
# Generated Persona Directives (template-based)
# =============================================================================

def _list_personas_factory(ctx):
    """Create ListPersonasUseCase from context."""
    return ctx.list_personas


def _list_personas_request(options):
    """Create ListPersonasRequest from directive options."""
    config = get_config()
    return ListPersonasRequest(solution_slug=config.solution_slug)


# Generate PersonaIndexDirective
GeneratedPersonaIndexDirective = generate_index_directive(
    entity_name="Persona",
    use_case_factory=_list_personas_factory,
    request_factory=_list_personas_request,
    rendering_service_getter=_get_rendering_service,
    context_getter=get_hcd_context,
    use_placeholder=True,
)

# Create placeholder processor for generated directive
process_generated_persona_placeholders = make_placeholder_processor(
    GeneratedPersonaIndexDirective.placeholder_class,
    GeneratedPersonaIndexDirective.resolve_placeholder,
)


# =============================================================================
# Generated Epic Directives (build-function-based)
# =============================================================================

def _build_epic_index_wrapper(env, docname, ctx, **options):
    """Wrap build_epic_index for factory compatibility."""
    from .directives.epic import build_epic_index
    return build_epic_index(env, docname, ctx)


GeneratedEpicIndexDirective = generate_index_directive_from_build_fn(
    entity_name="Epic",
    build_function=_build_epic_index_wrapper,
    context_getter=get_hcd_context,
    env_getter=_get_env,
)


# =============================================================================
# Generated App Directives (build-function-based)
# =============================================================================

def _build_app_index_wrapper(docname, ctx, **options):
    """Wrap build_app_index for factory compatibility."""
    from .directives.app import build_app_index
    return build_app_index(docname, ctx)


GeneratedAppIndexDirective = generate_index_directive_from_build_fn(
    entity_name="App",
    build_function=_build_app_index_wrapper,
    context_getter=get_hcd_context,
)


# =============================================================================
# Generated Accelerator Directives (build-function-based)
# =============================================================================

def _build_accelerator_index_wrapper(docname, ctx, **options):
    """Wrap build_accelerator_index for factory compatibility."""
    from .directives.accelerator import build_accelerator_index
    return build_accelerator_index(docname, ctx)


GeneratedAcceleratorIndexDirective = generate_index_directive_from_build_fn(
    entity_name="Accelerator",
    build_function=_build_accelerator_index_wrapper,
    context_getter=get_hcd_context,
)


# =============================================================================
# Generated Integration Directives (build-function-based)
# =============================================================================

def _build_integration_index_wrapper(docname, ctx, **options):
    """Wrap build_integration_index for factory compatibility."""
    from .directives.integration import build_integration_index
    return build_integration_index(docname, ctx)


GeneratedIntegrationIndexDirective = generate_index_directive_from_build_fn(
    entity_name="Integration",
    build_function=_build_integration_index_wrapper,
    context_getter=get_hcd_context,
)
