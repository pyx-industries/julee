"""Dynamic Step directive for C4 Sphinx integration.

Provides the define-dynamic-step directive.
"""

from docutils import nodes
from docutils.parsers.rst import directives

from julee.c4.entities.dynamic_step import DynamicStep
from julee.c4.entities.relationship import ElementType

from .base import C4Directive


class DefineDynamicStepDirective(C4Directive):
    """Define a step in a dynamic sequence diagram.

    Usage::

        .. define-dynamic-step::
           :sequence: user-login
           :step: 1
           :from: person:customer
           :to: container:web-app
           :description: Submits login credentials
           :technology: HTTPS

        .. define-dynamic-step::
           :sequence: user-login
           :step: 2
           :from: container:web-app
           :to: container:api-app
           :description: Validates credentials
           :technology: REST/JSON
    """

    has_content = False
    option_spec = {
        "sequence": directives.unchanged_required,
        "step": directives.positive_int,
        "from": directives.unchanged_required,
        "to": directives.unchanged_required,
        "description": directives.unchanged,
        "technology": directives.unchanged,
        "return": directives.unchanged,
        "tags": directives.unchanged,
    }

    def _parse_element_ref(self, ref: str) -> tuple[ElementType, str]:
        """Parse element reference like 'person:customer' or 'system:banking'.

        Args:
            ref: Element reference string

        Returns:
            Tuple of (ElementType, slug)
        """
        if ":" in ref:
            type_str, slug = ref.split(":", 1)
            type_map = {
                "person": ElementType.PERSON,
                "system": ElementType.SOFTWARE_SYSTEM,
                "container": ElementType.CONTAINER,
                "component": ElementType.COMPONENT,
            }
            return type_map.get(type_str.lower(), ElementType.SOFTWARE_SYSTEM), slug
        return ElementType.SOFTWARE_SYSTEM, ref

    def run(self) -> list[nodes.Node]:
        sequence_name = self.options.get("sequence", "")
        step_number = self.options.get("step", 1)
        from_ref = self.options.get("from", "")
        to_ref = self.options.get("to", "")
        description = self.options.get("description", "")
        technology = self.options.get("technology", "")
        return_desc = self.options.get("return", "")
        tags_str = self.options.get("tags", "")
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]

        source_type, source_slug = self._parse_element_ref(from_ref)
        dest_type, dest_slug = self._parse_element_ref(to_ref)

        # Generate slug
        slug = f"{sequence_name}-step-{step_number}"

        # Create dynamic step
        dynamic_step = DynamicStep(
            slug=slug,
            sequence_name=sequence_name,
            step_number=step_number,
            source_type=source_type,
            source_slug=source_slug,
            destination_type=dest_type,
            destination_slug=dest_slug,
            description=description,
            technology=technology,
            is_return=bool(return_desc),
            return_description=return_desc,
            tags=tags,
            docname=self.docname,
        )

        # Store in environment
        storage = self.get_c4_storage()
        storage["dynamic_steps"][slug] = dynamic_step

        # Build output nodes - minimal inline display
        result_nodes = []

        para = nodes.paragraph()
        para += nodes.strong(text=f"Step {step_number}: ")
        para += nodes.Text(f"{source_slug} -> {dest_slug}")
        if description:
            para += nodes.Text(f": {description}")
        if technology:
            para += nodes.Text(f" [{technology}]")

        result_nodes.append(para)
        return result_nodes
