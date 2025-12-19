"""MCP tools for C4 domain operations.

Tool modules for CRUD operations on C4 architecture model objects.
"""

from .components import (
    create_component,
    delete_component,
    get_component,
    list_components,
    update_component,
)
from .containers import (
    create_container,
    delete_container,
    get_container,
    list_containers,
    update_container,
)
from .deployment_nodes import (
    create_deployment_node,
    delete_deployment_node,
    get_deployment_node,
    list_deployment_nodes,
    update_deployment_node,
)
from .diagrams import (
    get_component_diagram,
    get_container_diagram,
    get_deployment_diagram,
    get_dynamic_diagram,
    get_system_context_diagram,
    get_system_landscape_diagram,
)
from .dynamic_steps import (
    create_dynamic_step,
    delete_dynamic_step,
    get_dynamic_step,
    list_dynamic_steps,
    update_dynamic_step,
)
from .relationships import (
    create_relationship,
    delete_relationship,
    get_relationship,
    list_relationships,
    update_relationship,
)
from .software_systems import (
    create_software_system,
    delete_software_system,
    get_software_system,
    list_software_systems,
    update_software_system,
)

__all__ = [
    # Software Systems
    "create_software_system",
    "get_software_system",
    "list_software_systems",
    "update_software_system",
    "delete_software_system",
    # Containers
    "create_container",
    "get_container",
    "list_containers",
    "update_container",
    "delete_container",
    # Components
    "create_component",
    "get_component",
    "list_components",
    "update_component",
    "delete_component",
    # Relationships
    "create_relationship",
    "get_relationship",
    "list_relationships",
    "update_relationship",
    "delete_relationship",
    # Deployment Nodes
    "create_deployment_node",
    "get_deployment_node",
    "list_deployment_nodes",
    "update_deployment_node",
    "delete_deployment_node",
    # Dynamic Steps
    "create_dynamic_step",
    "get_dynamic_step",
    "list_dynamic_steps",
    "update_dynamic_step",
    "delete_dynamic_step",
    # Diagrams
    "get_system_context_diagram",
    "get_container_diagram",
    "get_component_diagram",
    "get_system_landscape_diagram",
    "get_deployment_diagram",
    "get_dynamic_diagram",
]
