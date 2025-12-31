"""Placeholder resolution handler implementations for sphinx_hcd.

Each handler wraps existing placeholder processing logic, providing
a consistent interface for the handler registry.
"""

from typing import TYPE_CHECKING

from docutils import nodes

from julee.hcd.use_cases.crud import GetEpicRequest

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
            AppsForPersonaPlaceholder,
            DefineAppPlaceholder,
            build_app_content,
            build_apps_for_persona,
        )
        from ...generated_directives import GeneratedAppIndexDirective

        for node in doctree.traverse(DefineAppPlaceholder):
            app_slug = node["app_slug"]
            content = build_app_content(app_slug, docname, context)
            node.replace_self(content)

        # Process app-index using generated directive
        placeholder_cls = GeneratedAppIndexDirective.placeholder_class
        for node in doctree.traverse(placeholder_cls):
            content = GeneratedAppIndexDirective.resolve_placeholder(node, app)
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
            EpicsForPersonaPlaceholder,
            build_epics_for_persona,
            render_epic_stories,
        )
        from ...generated_directives import GeneratedEpicIndexDirective

        env = app.env
        epic_current = getattr(env, "epic_current", {})

        # Process epic stories placeholder
        epic_slug = epic_current.get(docname)
        if epic_slug:
            epic_response = context.get_epic.execute_sync(
                GetEpicRequest(slug=epic_slug)
            )
            epic = epic_response.epic
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

        # Process epic-index using generated directive
        placeholder_cls = GeneratedEpicIndexDirective.placeholder_class
        for node in doctree.traverse(placeholder_cls):
            content = GeneratedEpicIndexDirective.resolve_placeholder(node, app)
            node.replace_self(content)

        # Process epics-for-persona placeholder
        for node in doctree.traverse(EpicsForPersonaPlaceholder):
            persona = node["persona"]
            epics_node = build_epics_for_persona(env, docname, persona, context)
            node.replace_self(epics_node)


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
            DefineIntegrationPlaceholder,
            build_integration_content,
        )
        from ...generated_directives import GeneratedIntegrationIndexDirective

        for node in doctree.traverse(DefineIntegrationPlaceholder):
            slug = node["integration_slug"]
            content = build_integration_content(slug, docname, context)
            node.replace_self(content)

        # Process integration-index using generated directive
        placeholder_cls = GeneratedIntegrationIndexDirective.placeholder_class
        for node in doctree.traverse(placeholder_cls):
            content = GeneratedIntegrationIndexDirective.resolve_placeholder(node, app)
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
            PersonaDiagramPlaceholder,
            PersonaIndexDiagramPlaceholder,
            build_persona_diagram,
            build_persona_index_diagram,
        )
        from ...generated_directives import GeneratedPersonaIndexDirective

        # Process persona-index using generated directive
        placeholder_cls = GeneratedPersonaIndexDirective.placeholder_class
        for node in doctree.traverse(placeholder_cls):
            content = GeneratedPersonaIndexDirective.resolve_placeholder(node, app)
            node.replace_self(content)

        for node in doctree.traverse(PersonaDiagramPlaceholder):
            persona_slug = node["persona_slug"]
            content = build_persona_diagram(persona_slug, docname, context)
            node.replace_self(content)

        for node in doctree.traverse(PersonaIndexDiagramPlaceholder):
            group_type = node["group_type"]
            content = build_persona_index_diagram(group_type, docname, context)
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
            build_dependency_graph_node,
        )

        for node in doctree.traverse(JourneyDependencyGraphPlaceholder):
            content = build_dependency_graph_node(app.env, context)
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
            ContribListPlaceholder,
            DefineContribPlaceholder,
            build_contrib_content,
            build_contrib_index,
            build_contrib_list,
        )

        for node in doctree.traverse(DefineContribPlaceholder):
            slug = node["contrib_slug"]
            content = build_contrib_content(slug, docname, context)
            node.replace_self(content)

        for node in doctree.traverse(ContribIndexPlaceholder):
            content = build_contrib_index(docname, context)
            node.replace_self(content)

        for node in doctree.traverse(ContribListPlaceholder):
            content = build_contrib_list(docname, context)
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
            AcceleratorListPlaceholder,
            AppListByInterfacePlaceholder,
            C4ContainerDiagramPlaceholder,
            build_accelerator_list,
            build_app_list_by_interface,
            build_c4_container_diagram,
        )

        for node in doctree.traverse(C4ContainerDiagramPlaceholder):
            content = build_c4_container_diagram(
                docname,
                context,
                title=node["title"],
                system_name=node["system_name"],
                show_foundation=node["show_foundation"],
                show_external=node["show_external"],
                foundation_name=node["foundation_name"],
                external_name=node["external_name"],
            )
            node.replace_self(content)

        for node in doctree.traverse(AppListByInterfacePlaceholder):
            content = build_app_list_by_interface(docname, context)
            node.replace_self(content)

        for node in doctree.traverse(AcceleratorListPlaceholder):
            content = build_accelerator_list(docname, context)
            node.replace_self(content)



