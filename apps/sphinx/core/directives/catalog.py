"""Catalog directives for auto-generated documentation.

These directives introspect modules to generate entity, repository,
and use case listings automatically.
"""

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective

from julee.core.introspection.catalog import (
    introspect_entities,
    introspect_repositories,
    introspect_use_cases,
)


class EntityCatalogDirective(SphinxDirective):
    """List all entities in a module with summaries.

    Usage::

        .. entity-catalog:: julee.hcd.entities
           :show-fields:
           :link-to-api:

    Options:
        :show-fields: Include field counts
        :link-to-api: Add cross-references to API docs
    """

    required_arguments = 1  # module.path
    optional_arguments = 0
    has_content = False

    option_spec = {
        "show-fields": directives.flag,
        "link-to-api": directives.flag,
    }

    def run(self) -> list[nodes.Node]:
        """Execute the directive."""
        module_path = self.arguments[0]

        try:
            entities = introspect_entities(module_path)
        except ImportError as e:
            error = self.state_machine.reporter.error(
                f"Cannot import module '{module_path}': {e}",
                nodes.literal_block(self.block_text, self.block_text),
                line=self.lineno,
            )
            return [error]

        if not entities:
            para = nodes.paragraph(text=f"No entities found in {module_path}")
            return [para]

        # Build bullet list
        bullet_list = nodes.bullet_list()

        for entity in entities:
            item = nodes.list_item()
            para = nodes.paragraph()

            # Entity name (optionally as cross-reference)
            if "link-to-api" in self.options:
                ref = nodes.reference(
                    "",
                    entity.class_name,
                    refuri=f"#py-class-{entity.full_path.replace('.', '-').lower()}",
                    internal=True,
                )
                para += nodes.strong("", "", ref)
            else:
                para += nodes.strong(text=entity.class_name)

            # Summary
            para += nodes.Text(f" - {entity.summary}")

            # Field count if requested
            if "show-fields" in self.options and entity.field_count > 0:
                para += nodes.Text(f" ({entity.field_count} fields)")

            item += para
            bullet_list += item

        return [bullet_list]


class RepositoryCatalogDirective(SphinxDirective):
    """List all repository protocols in a module.

    Usage::

        .. repository-catalog:: julee.domain.repositories
           :show-methods:
           :link-to-api:

    Options:
        :show-methods: Include method names
        :link-to-api: Add cross-references to API docs
    """

    required_arguments = 1
    optional_arguments = 0
    has_content = False

    option_spec = {
        "show-methods": directives.flag,
        "link-to-api": directives.flag,
    }

    def run(self) -> list[nodes.Node]:
        """Execute the directive."""
        module_path = self.arguments[0]

        try:
            repositories = introspect_repositories(module_path)
        except ImportError as e:
            error = self.state_machine.reporter.error(
                f"Cannot import module '{module_path}': {e}",
                nodes.literal_block(self.block_text, self.block_text),
                line=self.lineno,
            )
            return [error]

        if not repositories:
            para = nodes.paragraph(text=f"No repositories found in {module_path}")
            return [para]

        # Build definition list for more detail
        dl = nodes.definition_list()

        for repo in repositories:
            item = nodes.definition_list_item()

            # Term: repository name
            term = nodes.term()
            if "link-to-api" in self.options:
                ref = nodes.reference(
                    "",
                    repo.class_name,
                    refuri=f"#py-class-{repo.full_path.replace('.', '-').lower()}",
                    internal=True,
                )
                term += ref
            else:
                term += nodes.literal(text=repo.class_name)

            if repo.entity_type:
                term += nodes.Text(f" → {repo.entity_type}")

            item += term

            # Definition: summary and optionally methods
            definition = nodes.definition()
            summary_para = nodes.paragraph(text=repo.summary)
            definition += summary_para

            if "show-methods" in self.options and repo.method_names:
                methods_para = nodes.paragraph()
                methods_para += nodes.emphasis(text="Methods: ")
                methods_para += nodes.literal(text=", ".join(repo.method_names))
                definition += methods_para

            item += definition
            dl += item

        return [dl]


class UseCaseCatalogDirective(SphinxDirective):
    """List all use cases in a module with CRUD classification.

    Usage::

        .. usecase-catalog:: julee.hcd.use_cases
           :group-by-crud:
           :link-to-api:

    Options:
        :group-by-crud: Group use cases by CRUD type
        :link-to-api: Add cross-references to API docs
    """

    required_arguments = 1
    optional_arguments = 0
    has_content = False

    option_spec = {
        "group-by-crud": directives.flag,
        "link-to-api": directives.flag,
    }

    def run(self) -> list[nodes.Node]:
        """Execute the directive."""
        module_path = self.arguments[0]

        try:
            use_cases = introspect_use_cases(module_path)
        except ImportError as e:
            error = self.state_machine.reporter.error(
                f"Cannot import module '{module_path}': {e}",
                nodes.literal_block(self.block_text, self.block_text),
                line=self.lineno,
            )
            return [error]

        if not use_cases:
            para = nodes.paragraph(text=f"No use cases found in {module_path}")
            return [para]

        if "group-by-crud" in self.options:
            return self._render_grouped(use_cases)
        else:
            return self._render_flat(use_cases)

    def _render_flat(self, use_cases) -> list[nodes.Node]:
        """Render as a simple bullet list."""
        bullet_list = nodes.bullet_list()

        for uc in use_cases:
            item = nodes.list_item()
            para = nodes.paragraph()

            # Use case name
            if "link-to-api" in self.options:
                ref = nodes.reference(
                    "",
                    uc.class_name,
                    refuri=f"#py-class-{uc.full_path.replace('.', '-').lower()}",
                    internal=True,
                )
                para += nodes.strong("", "", ref)
            else:
                para += nodes.strong(text=uc.class_name)

            # CRUD type badge
            if uc.crud_type:
                para += nodes.Text(" ")
                para += nodes.inline(text=f"[{uc.crud_type}]", classes=["crud-badge"])

            # Summary
            para += nodes.Text(f" - {uc.summary}")

            item += para
            bullet_list += item

        return [bullet_list]

    def _render_grouped(self, use_cases) -> list[nodes.Node]:
        """Render grouped by CRUD type."""
        groups = {"Create": [], "Read": [], "Update": [], "Delete": [], "Other": []}

        for uc in use_cases:
            crud = uc.crud_type or "Other"
            groups[crud].append(uc)

        result_nodes = []

        for crud_type, items in groups.items():
            if not items:
                continue

            # Section header
            rubric = nodes.rubric(text=crud_type)
            result_nodes.append(rubric)

            # Bullet list for this group
            bullet_list = nodes.bullet_list()
            for uc in items:
                item = nodes.list_item()
                para = nodes.paragraph()

                if "link-to-api" in self.options:
                    ref = nodes.reference(
                        "",
                        uc.class_name,
                        refuri=f"#py-class-{uc.full_path.replace('.', '-').lower()}",
                        internal=True,
                    )
                    para += nodes.strong("", "", ref)
                else:
                    para += nodes.strong(text=uc.class_name)

                para += nodes.Text(f" - {uc.summary}")
                item += para
                bullet_list += item

            result_nodes.append(bullet_list)

        return result_nodes
