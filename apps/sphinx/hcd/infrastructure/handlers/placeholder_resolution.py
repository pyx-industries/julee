"""Placeholder resolution handler implementations for sphinx_hcd.

Each handler wraps existing placeholder processing logic, providing
a consistent interface for the handler registry.
"""

from typing import TYPE_CHECKING

from docutils import nodes

if TYPE_CHECKING:
    from sphinx.application import Sphinx

    from ...context import HCDContext


class AppPlaceholderHandler:
    """Handler for app-related placeholders."""

    name = "App"

    def handle(
        self,
        app: "Sphinx",
        doctree: nodes.document,
        docname: str,
        context: "HCDContext",
    ) -> None:
        """Process app placeholders."""
        from ...directives.app import (
            AppIndexPlaceholder,
            AppsForPersonaPlaceholder,
            DefineAppPlaceholder,
            build_app_content,
            build_app_index,
            build_apps_for_persona,
        )

        for node in doctree.traverse(DefineAppPlaceholder):
            app_slug = node["app_slug"]
            content = build_app_content(app_slug, docname, context)
            node.replace_self(content)

        for node in doctree.traverse(AppIndexPlaceholder):
            content = build_app_index(docname, context)
            node.replace_self(content)

        for node in doctree.traverse(AppsForPersonaPlaceholder):
            persona = node["persona"]
            content = build_apps_for_persona(docname, persona, context)
            node.replace_self(content)


class EpicPlaceholderHandler:
    """Handler for epic-related placeholders."""

    name = "Epic"

    def handle(
        self,
        app: "Sphinx",
        doctree: nodes.document,
        docname: str,
        context: "HCDContext",
    ) -> None:
        """Process epic placeholders."""
        from ...directives.epic import (
            EpicIndexPlaceholder,
            EpicsForPersonaPlaceholder,
            build_epic_index,
            build_epics_for_persona,
            render_epic_stories,
        )

        env = app.env
        epic_current = getattr(env, "epic_current", {})

        # Process epic stories placeholder
        epic_slug = epic_current.get(docname)
        if epic_slug:
            epic = context.epic_repo.get(epic_slug)
            if epic:
                for node in doctree.traverse(nodes.container):
                    if "epic-stories-placeholder" in node.get("classes", []):
                        stories_nodes = render_epic_stories(epic, docname, context)
                        node["classes"] = []
                        if stories_nodes:
                            node.replace_self(stories_nodes)
                        else:
                            node.replace_self([])
                        break

        # Process epic index placeholder
        for node in doctree.traverse(EpicIndexPlaceholder):
            index_node = build_epic_index(env, docname, context)
            node.replace_self(index_node)

        # Process epics-for-persona placeholder
        for node in doctree.traverse(EpicsForPersonaPlaceholder):
            persona = node["persona"]
            epics_node = build_epics_for_persona(env, docname, persona, context)
            node.replace_self(epics_node)


class AcceleratorPlaceholderHandler:
    """Handler for accelerator-related placeholders."""

    name = "Accelerator"

    def handle(
        self,
        app: "Sphinx",
        doctree: nodes.document,
        docname: str,
        context: "HCDContext",
    ) -> None:
        """Process accelerator placeholders."""
        from ...directives.accelerator import (
            AcceleratorDependencyDiagramPlaceholder,
            AcceleratorIndexPlaceholder,
            AcceleratorsForAppPlaceholder,
            DefineAcceleratorPlaceholder,
            build_accelerator_content,
            build_accelerator_index,
            build_accelerators_for_app,
            build_dependency_diagram,
        )

        for node in doctree.traverse(DefineAcceleratorPlaceholder):
            slug = node["accelerator_slug"]
            content = build_accelerator_content(slug, docname, context)
            node.replace_self(content)

        for node in doctree.traverse(AcceleratorIndexPlaceholder):
            content = build_accelerator_index(docname, context)
            node.replace_self(content)

        for node in doctree.traverse(AcceleratorsForAppPlaceholder):
            app_slug = node["app_slug"]
            content = build_accelerators_for_app(app_slug, docname, context)
            node.replace_self(content)

        for node in doctree.traverse(AcceleratorDependencyDiagramPlaceholder):
            content = build_dependency_diagram(docname, context)
            node.replace_self(content)


class IntegrationPlaceholderHandler:
    """Handler for integration-related placeholders."""

    name = "Integration"

    def handle(
        self,
        app: "Sphinx",
        doctree: nodes.document,
        docname: str,
        context: "HCDContext",
    ) -> None:
        """Process integration placeholders."""
        from ...directives.integration import (
            DependentAcceleratorsPlaceholder,
            IntegrationIndexPlaceholder,
            build_dependent_accelerators,
            build_integration_index,
        )

        for node in doctree.traverse(IntegrationIndexPlaceholder):
            content = build_integration_index(docname, context)
            node.replace_self(content)

        for node in doctree.traverse(DependentAcceleratorsPlaceholder):
            integration_slug = node["integration_slug"]
            content = build_dependent_accelerators(integration_slug, docname, context)
            node.replace_self(content)


class PersonaPlaceholderHandler:
    """Handler for persona-related placeholders."""

    name = "Persona"

    def handle(
        self,
        app: "Sphinx",
        doctree: nodes.document,
        docname: str,
        context: "HCDContext",
    ) -> None:
        """Process persona placeholders."""
        from ...directives.persona import (
            DefinePersonaPlaceholder,
            PersonaDiagramPlaceholder,
            PersonaIndexDiagramPlaceholder,
            PersonaIndexPlaceholder,
            build_persona_content,
            build_persona_diagram,
            build_persona_index,
            build_persona_index_diagram,
        )

        for node in doctree.traverse(DefinePersonaPlaceholder):
            persona_slug = node["persona_slug"]
            content = build_persona_content(persona_slug, docname, context)
            node.replace_self(content)

        for node in doctree.traverse(PersonaIndexPlaceholder):
            content = build_persona_index(docname, context)
            node.replace_self(content)

        for node in doctree.traverse(PersonaDiagramPlaceholder):
            persona_slug = node["persona_slug"]
            content = build_persona_diagram(persona_slug, docname, context)
            node.replace_self(content)

        for node in doctree.traverse(PersonaIndexDiagramPlaceholder):
            content = build_persona_index_diagram(docname, context)
            node.replace_self(content)


class JourneyPlaceholderHandler:
    """Handler for journey-related placeholders."""

    name = "Journey"

    def handle(
        self,
        app: "Sphinx",
        doctree: nodes.document,
        docname: str,
        context: "HCDContext",
    ) -> None:
        """Process journey dependency graph placeholder."""
        from ...directives.journey import (
            JourneyDependencyGraphPlaceholder,
            build_journey_dependency_graph,
        )

        for node in doctree.traverse(JourneyDependencyGraphPlaceholder):
            content = build_journey_dependency_graph(docname, context)
            node.replace_self(content)


class ContribPlaceholderHandler:
    """Handler for contrib-related placeholders."""

    name = "Contrib"

    def handle(
        self,
        app: "Sphinx",
        doctree: nodes.document,
        docname: str,
        context: "HCDContext",
    ) -> None:
        """Process contrib placeholders."""
        from ...directives.contrib import (
            ContribIndexPlaceholder,
            DefineContribPlaceholder,
            build_contrib_content,
            build_contrib_index,
        )

        for node in doctree.traverse(DefineContribPlaceholder):
            slug = node["slug"]
            content = build_contrib_content(slug, docname, context)
            node.replace_self(content)

        for node in doctree.traverse(ContribIndexPlaceholder):
            content = build_contrib_index(docname, context)
            node.replace_self(content)


class C4BridgePlaceholderHandler:
    """Handler for C4 bridge placeholders."""

    name = "C4Bridge"

    def handle(
        self,
        app: "Sphinx",
        doctree: nodes.document,
        docname: str,
        context: "HCDContext",
    ) -> None:
        """Process C4 bridge placeholders."""
        from ...directives.c4_bridge import (
            C4ContainerDiagramPlaceholder,
            build_c4_container_diagram,
        )

        for node in doctree.traverse(C4ContainerDiagramPlaceholder):
            content = build_c4_container_diagram(app, docname, context)
            node.replace_self(content)


class CodeLinksPlaceholderHandler:
    """Handler for code link placeholders."""

    name = "CodeLinks"

    def handle(
        self,
        app: "Sphinx",
        doctree: nodes.document,
        docname: str,
        context: "HCDContext",
    ) -> None:
        """Process code link placeholders."""
        from ...directives.code_links import (
            AcceleratorCodePlaceholder,
            AcceleratorEntityListPlaceholder,
            AcceleratorUseCaseListPlaceholder,
            build_accelerator_code,
            build_accelerator_entity_list,
            build_accelerator_usecase_list,
        )

        for node in doctree.traverse(AcceleratorCodePlaceholder):
            slug = node["accelerator_slug"]
            content = build_accelerator_code(slug, docname, context)
            node.replace_self(content)

        for node in doctree.traverse(AcceleratorEntityListPlaceholder):
            slug = node["accelerator_slug"]
            content = build_accelerator_entity_list(slug, docname, context)
            node.replace_self(content)

        for node in doctree.traverse(AcceleratorUseCaseListPlaceholder):
            slug = node["accelerator_slug"]
            content = build_accelerator_usecase_list(slug, docname, context)
            node.replace_self(content)


class EntityDiagramPlaceholderHandler:
    """Handler for entity diagram placeholders."""

    name = "EntityDiagram"

    def handle(
        self,
        app: "Sphinx",
        doctree: nodes.document,
        docname: str,
        context: "HCDContext",
    ) -> None:
        """Process entity diagram placeholders."""
        from ...directives.code_links import (
            AcceleratorEntityDiagramPlaceholder,
            build_entity_diagram,
        )

        for node in doctree.traverse(AcceleratorEntityDiagramPlaceholder):
            slug = node["accelerator_slug"]
            content = build_entity_diagram(slug, docname, context)
            node.replace_self(content)
