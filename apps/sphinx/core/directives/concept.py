"""Core concept directives for reflexive documentation.

These directives render Python class docstrings as documentation, enabling
docstrings to BE the documentation rather than maintaining parallel content.
"""

import importlib
from typing import Any

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective

from apps.sphinx.hcd.directives.base import parse_rst_content


class CoreConceptDirective(SphinxDirective):
    """Render a Python class docstring as documentation.

    Usage::

        .. core-concept:: julee.core.entities.entity.Entity
           :show-fields:
           :link-to-source:

           Additional editorial commentary goes here.

    Options:
        :show-fields: Include Pydantic model fields
        :link-to-source: Add source reference
        :no-title: Suppress the class name rubric

    The directive imports the specified class, extracts its docstring,
    parses it as RST, and renders it in place. Any content in the
    directive body is appended as editorial addition.
    """

    required_arguments = 1  # module.path.ClassName
    optional_arguments = 0
    final_argument_whitespace = False
    has_content = True

    option_spec = {
        "show-fields": directives.flag,
        "link-to-source": directives.flag,
        "no-title": directives.flag,
    }

    def run(self) -> list[nodes.Node]:
        """Execute the directive."""
        class_path = self.arguments[0]

        # Import the class
        try:
            cls = self._import_class(class_path)
        except (ImportError, AttributeError) as e:
            error = self.state_machine.reporter.error(
                f"Cannot import class '{class_path}': {e}",
                nodes.literal_block(self.block_text, self.block_text),
                line=self.lineno,
            )
            return [error]

        result_nodes: list[nodes.Node] = []

        # Get docstring
        docstring = cls.__doc__
        if not docstring:
            warning = self.state_machine.reporter.warning(
                f"Class '{class_path}' has no docstring",
                line=self.lineno,
            )
            return [warning]

        # Add class name as subtitle if not suppressed
        if "no-title" not in self.options:
            rubric = nodes.rubric(text=cls.__name__)
            rubric["ids"] = [nodes.make_id(cls.__name__)]
            result_nodes.append(rubric)

        # Parse docstring as RST
        docstring_nodes = parse_rst_content(
            docstring.strip(),
            source_name=f"<{class_path}.__doc__>",
        )
        result_nodes.extend(docstring_nodes)

        # Show Pydantic fields if requested
        if "show-fields" in self.options:
            fields_section = self._create_fields_section(cls)
            if fields_section:
                result_nodes.append(fields_section)

        # Add link to source if requested
        if "link-to-source" in self.options:
            source_link = self._create_source_link(cls, class_path)
            result_nodes.append(source_link)

        # Append editorial content if provided
        if self.content:
            editorial_nodes = self._parse_content()
            result_nodes.extend(editorial_nodes)

        return result_nodes

    def _import_class(self, class_path: str) -> type:
        """Import a class from a dotted path.

        Args:
            class_path: Dotted path like 'julee.core.entities.Entity'

        Returns:
            The imported class
        """
        parts = class_path.rsplit(".", 1)
        if len(parts) != 2:
            raise ImportError(f"Invalid class path: {class_path}")

        module_path, class_name = parts
        module = importlib.import_module(module_path)
        return getattr(module, class_name)

    def _create_fields_section(self, cls: type) -> nodes.Node | None:
        """Create a section listing Pydantic model fields.

        Args:
            cls: The class to inspect

        Returns:
            Section node with field list, or None if not a Pydantic model
        """
        # Check if this is a Pydantic model
        if not hasattr(cls, "model_fields"):
            return None

        fields = cls.model_fields
        if not fields:
            return None

        # Create field list
        field_list = nodes.definition_list()

        for name, field_info in fields.items():
            # Get field type annotation
            annotation = field_info.annotation
            type_str = getattr(annotation, "__name__", str(annotation))

            # Get field description
            description = field_info.description or ""

            # Create definition list item
            term = nodes.term()
            term += nodes.literal(text=name)
            term += nodes.Text(f" : {type_str}")

            definition = nodes.definition()
            if description:
                definition += nodes.paragraph(text=description)
            else:
                definition += nodes.paragraph(text="(no description)")

            item = nodes.definition_list_item()
            item += term
            item += definition
            field_list += item

        # Wrap in a container with title
        container = nodes.container()
        title_para = nodes.paragraph()
        title_para += nodes.strong(text="Fields")
        container += title_para
        container += field_list

        return container

    def _create_source_link(self, cls: type, class_path: str) -> nodes.paragraph:
        """Create a link to the source code.

        Args:
            cls: The class
            class_path: The import path

        Returns:
            Paragraph with source link
        """
        para = nodes.paragraph()
        para += nodes.Text("Source: ")
        # Use Sphinx's :py:class: role reference
        ref = nodes.literal(text=class_path)
        para += ref
        return para

    def _parse_content(self) -> list[nodes.Node]:
        """Parse the directive content as RST."""
        content_text = "\n".join(self.content)
        return parse_rst_content(content_text, source_name="<directive-content>")


class DoctrineConstantDirective(SphinxDirective):
    """Render a doctrine constant with its value and docstring.

    Usage::

        .. doctrine-constant:: julee.core.doctrine_constants.USE_CASE_SUFFIX

    Renders the constant name, its value, and any associated documentation.
    """

    required_arguments = 1  # module.path.CONSTANT_NAME
    optional_arguments = 0
    has_content = False

    option_spec = {}

    def run(self) -> list[nodes.Node]:
        """Execute the directive."""
        const_path = self.arguments[0]

        # Import the constant
        try:
            value, docstring = self._import_constant(const_path)
        except (ImportError, AttributeError) as e:
            error = self.state_machine.reporter.error(
                f"Cannot import constant '{const_path}': {e}",
                nodes.literal_block(self.block_text, self.block_text),
                line=self.lineno,
            )
            return [error]

        result_nodes: list[nodes.Node] = []

        # Constant name as term
        const_name = const_path.rsplit(".", 1)[-1]

        # Create definition list item
        dl = nodes.definition_list()

        term = nodes.term()
        term += nodes.literal(text=const_name)

        definition = nodes.definition()

        # Value in code block
        value_para = nodes.paragraph()
        value_para += nodes.Text("Value: ")
        value_para += nodes.literal(text=repr(value))
        definition += value_para

        # Docstring if available
        if docstring:
            docstring_nodes = parse_rst_content(
                docstring.strip(),
                source_name=f"<{const_path}>",
            )
            definition.extend(docstring_nodes)

        item = nodes.definition_list_item()
        item += term
        item += definition
        dl += item

        result_nodes.append(dl)
        return result_nodes

    def _import_constant(self, const_path: str) -> tuple[Any, str | None]:
        """Import a constant and get its docstring.

        Args:
            const_path: Dotted path like 'module.CONSTANT'

        Returns:
            Tuple of (value, docstring or None)
        """
        parts = const_path.rsplit(".", 1)
        if len(parts) != 2:
            raise ImportError(f"Invalid constant path: {const_path}")

        module_path, const_name = parts
        module = importlib.import_module(module_path)
        value = getattr(module, const_name)

        # Try to get docstring from module's __doc__ annotations or comments
        # For now, return None - full implementation would parse AST
        docstring = None

        return value, docstring
