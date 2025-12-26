"""FastAPI dependency injection for C4 API.

Provides use-case factory functions for FastAPI's dependency injection.
"""

from apps.c4_mcp.context import (
    # Diagram use cases
    get_component_diagram_use_case,
    get_container_diagram_use_case,
    # Component use cases
    get_create_component_use_case,
    # Container use cases
    get_create_container_use_case,
    # Deployment Node use cases
    get_create_deployment_node_use_case,
    # Dynamic Step use cases
    get_create_dynamic_step_use_case,
    # Relationship use cases
    get_create_relationship_use_case,
    # Software System use cases
    get_create_software_system_use_case,
    get_delete_component_use_case,
    get_delete_container_use_case,
    get_delete_deployment_node_use_case,
    get_delete_dynamic_step_use_case,
    get_delete_relationship_use_case,
    get_delete_software_system_use_case,
    get_deployment_diagram_use_case,
    get_dynamic_diagram_use_case,
    get_get_component_use_case,
    get_get_container_use_case,
    get_get_deployment_node_use_case,
    get_get_dynamic_step_use_case,
    get_get_relationship_use_case,
    get_get_software_system_use_case,
    get_list_components_use_case,
    get_list_containers_use_case,
    get_list_deployment_nodes_use_case,
    get_list_dynamic_steps_use_case,
    get_list_relationships_use_case,
    get_list_software_systems_use_case,
    get_system_context_diagram_use_case,
    get_system_landscape_diagram_use_case,
    get_update_component_use_case,
    get_update_container_use_case,
    get_update_deployment_node_use_case,
    get_update_dynamic_step_use_case,
    get_update_relationship_use_case,
    get_update_software_system_use_case,
)

__all__ = [
    # Software System
    "get_create_software_system_use_case",
    "get_get_software_system_use_case",
    "get_list_software_systems_use_case",
    "get_update_software_system_use_case",
    "get_delete_software_system_use_case",
    # Container
    "get_create_container_use_case",
    "get_get_container_use_case",
    "get_list_containers_use_case",
    "get_update_container_use_case",
    "get_delete_container_use_case",
    # Component
    "get_create_component_use_case",
    "get_get_component_use_case",
    "get_list_components_use_case",
    "get_update_component_use_case",
    "get_delete_component_use_case",
    # Relationship
    "get_create_relationship_use_case",
    "get_get_relationship_use_case",
    "get_list_relationships_use_case",
    "get_update_relationship_use_case",
    "get_delete_relationship_use_case",
    # Deployment Node
    "get_create_deployment_node_use_case",
    "get_get_deployment_node_use_case",
    "get_list_deployment_nodes_use_case",
    "get_update_deployment_node_use_case",
    "get_delete_deployment_node_use_case",
    # Dynamic Step
    "get_create_dynamic_step_use_case",
    "get_get_dynamic_step_use_case",
    "get_list_dynamic_steps_use_case",
    "get_update_dynamic_step_use_case",
    "get_delete_dynamic_step_use_case",
    # Diagrams
    "get_system_context_diagram_use_case",
    "get_container_diagram_use_case",
    "get_component_diagram_use_case",
    "get_system_landscape_diagram_use_case",
    "get_deployment_diagram_use_case",
    "get_dynamic_diagram_use_case",
]
