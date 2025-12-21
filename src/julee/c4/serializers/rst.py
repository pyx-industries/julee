"""RST directive serializers.

Serializes C4 domain objects to RST directive format.
"""

from ..domain.models.component import Component
from ..domain.models.container import Container
from ..domain.models.deployment_node import DeploymentNode
from ..domain.models.dynamic_step import DynamicStep
from ..domain.models.relationship import Relationship
from ..domain.models.software_system import SoftwareSystem


def serialize_software_system(system: SoftwareSystem) -> str:
    """Serialize a SoftwareSystem to RST directive format.

    Produces RST matching the define-software-system directive:
        .. define-software-system:: <slug>
           :name: <name>
           :type: <system_type>
           :owner: <owner>
           :technology: <technology>
           :url: <url>
           :tags: <tag1>, <tag2>

           <description>

    Args:
        system: SoftwareSystem domain object to serialize

    Returns:
        RST directive content as string
    """
    lines = [f".. define-software-system:: {system.slug}"]

    # Add options
    lines.append(f"   :name: {system.name}")
    if system.system_type:
        lines.append(f"   :type: {system.system_type.value}")
    if system.owner:
        lines.append(f"   :owner: {system.owner}")
    if system.technology:
        lines.append(f"   :technology: {system.technology}")
    if system.url:
        lines.append(f"   :url: {system.url}")
    if system.tags:
        lines.append(f"   :tags: {', '.join(system.tags)}")

    lines.append("")

    # Add description as directive content
    if system.description:
        for line in system.description.split("\n"):
            lines.append(f"   {line}" if line.strip() else "")
        lines.append("")

    return "\n".join(lines)


def serialize_container(container: Container) -> str:
    """Serialize a Container to RST directive format.

    Produces RST matching the define-container directive:
        .. define-container:: <slug>
           :name: <name>
           :system: <system_slug>
           :type: <container_type>
           :technology: <technology>
           :url: <url>
           :tags: <tag1>, <tag2>

           <description>

    Args:
        container: Container domain object to serialize

    Returns:
        RST directive content as string
    """
    lines = [f".. define-container:: {container.slug}"]

    # Add options
    lines.append(f"   :name: {container.name}")
    lines.append(f"   :system: {container.system_slug}")
    if container.container_type:
        lines.append(f"   :type: {container.container_type.value}")
    if container.technology:
        lines.append(f"   :technology: {container.technology}")
    if container.url:
        lines.append(f"   :url: {container.url}")
    if container.tags:
        lines.append(f"   :tags: {', '.join(container.tags)}")

    lines.append("")

    # Add description as directive content
    if container.description:
        for line in container.description.split("\n"):
            lines.append(f"   {line}" if line.strip() else "")
        lines.append("")

    return "\n".join(lines)


def serialize_component(component: Component) -> str:
    """Serialize a Component to RST directive format.

    Produces RST matching the define-component directive:
        .. define-component:: <slug>
           :name: <name>
           :container: <container_slug>
           :system: <system_slug>
           :technology: <technology>
           :interface: <interface>
           :code-path: <code_path>
           :tags: <tag1>, <tag2>

           <description>

    Args:
        component: Component domain object to serialize

    Returns:
        RST directive content as string
    """
    lines = [f".. define-component:: {component.slug}"]

    # Add options
    lines.append(f"   :name: {component.name}")
    lines.append(f"   :container: {component.container_slug}")
    lines.append(f"   :system: {component.system_slug}")
    if component.technology:
        lines.append(f"   :technology: {component.technology}")
    if component.interface:
        lines.append(f"   :interface: {component.interface}")
    if component.code_path:
        lines.append(f"   :code-path: {component.code_path}")
    if component.tags:
        lines.append(f"   :tags: {', '.join(component.tags)}")

    lines.append("")

    # Add description as directive content
    if component.description:
        for line in component.description.split("\n"):
            lines.append(f"   {line}" if line.strip() else "")
        lines.append("")

    return "\n".join(lines)


def serialize_relationship(relationship: Relationship) -> str:
    """Serialize a Relationship to RST directive format.

    Produces RST matching the define-relationship directive:
        .. define-relationship:: <slug>
           :source-type: <source_type>
           :source: <source_slug>
           :destination-type: <destination_type>
           :destination: <destination_slug>
           :technology: <technology>
           :bidirectional: <true/false>
           :tags: <tag1>, <tag2>

           <description>

    Args:
        relationship: Relationship domain object to serialize

    Returns:
        RST directive content as string
    """
    lines = [f".. define-relationship:: {relationship.slug}"]

    # Add options
    lines.append(f"   :source-type: {relationship.source_type.value}")
    lines.append(f"   :source: {relationship.source_slug}")
    lines.append(f"   :destination-type: {relationship.destination_type.value}")
    lines.append(f"   :destination: {relationship.destination_slug}")
    if relationship.technology:
        lines.append(f"   :technology: {relationship.technology}")
    if relationship.bidirectional:
        lines.append("   :bidirectional: true")
    if relationship.tags:
        lines.append(f"   :tags: {', '.join(relationship.tags)}")

    lines.append("")

    # Add description as directive content
    if relationship.description:
        for line in relationship.description.split("\n"):
            lines.append(f"   {line}" if line.strip() else "")
        lines.append("")

    return "\n".join(lines)


def serialize_deployment_node(node: DeploymentNode) -> str:
    """Serialize a DeploymentNode to RST directive format.

    Produces RST matching the define-deployment-node directive:
        .. define-deployment-node:: <slug>
           :name: <name>
           :environment: <environment>
           :type: <node_type>
           :technology: <technology>
           :instances: <instances>
           :parent: <parent_slug>
           :tags: <tag1>, <tag2>

           <description>

        .. deploy-container:: <container_slug>
           :instances: <count>

    Args:
        node: DeploymentNode domain object to serialize

    Returns:
        RST directive content as string
    """
    lines = [f".. define-deployment-node:: {node.slug}"]

    # Add options
    lines.append(f"   :name: {node.name}")
    if node.environment:
        lines.append(f"   :environment: {node.environment}")
    if node.node_type:
        lines.append(f"   :type: {node.node_type.value}")
    if node.technology:
        lines.append(f"   :technology: {node.technology}")
    if node.instances != 1:
        lines.append(f"   :instances: {node.instances}")
    if node.parent_slug:
        lines.append(f"   :parent: {node.parent_slug}")
    if node.tags:
        lines.append(f"   :tags: {', '.join(node.tags)}")

    lines.append("")

    # Add description as directive content
    if node.description:
        for line in node.description.split("\n"):
            lines.append(f"   {line}" if line.strip() else "")
        lines.append("")

    # Add container instances
    for ci in node.container_instances:
        lines.append(f".. deploy-container:: {ci.container_slug}")
        if ci.instance_count != 1:
            lines.append(f"   :instances: {ci.instance_count}")
        lines.append("")

    return "\n".join(lines)


def serialize_dynamic_step(step: DynamicStep) -> str:
    """Serialize a DynamicStep to RST directive format.

    Produces RST matching the define-dynamic-step directive:
        .. define-dynamic-step:: <slug>
           :sequence: <sequence_name>
           :step: <step_number>
           :source-type: <source_type>
           :source: <source_slug>
           :destination-type: <destination_type>
           :destination: <destination_slug>
           :technology: <technology>
           :return: <return_value>
           :async: <true/false>

           <description>

    Args:
        step: DynamicStep domain object to serialize

    Returns:
        RST directive content as string
    """
    lines = [f".. define-dynamic-step:: {step.slug}"]

    # Add options
    lines.append(f"   :sequence: {step.sequence_name}")
    lines.append(f"   :step: {step.step_number}")
    lines.append(f"   :source-type: {step.source_type.value}")
    lines.append(f"   :source: {step.source_slug}")
    lines.append(f"   :destination-type: {step.destination_type.value}")
    lines.append(f"   :destination: {step.destination_slug}")
    if step.technology:
        lines.append(f"   :technology: {step.technology}")
    if step.return_value:
        lines.append(f"   :return: {step.return_value}")
    if step.is_async:
        lines.append("   :async: true")

    lines.append("")

    # Add description as directive content
    if step.description:
        for line in step.description.split("\n"):
            lines.append(f"   {line}" if line.strip() else "")
        lines.append("")

    return "\n".join(lines)
