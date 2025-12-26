"""Progressive disclosure resources for MCP server framework.

Implements 3-level progressive disclosure pattern:
- Level 1: Service overview with entity and use case inventory
- Level 2: Entity details with associated CRUD operations
- Level 3: Full use case details with Request/Response schemas
"""

from typing import Any

from fastmcp import FastMCP
from fastmcp.resources import FunctionResource

from .discovery import (
    get_class_summary,
    get_module_description,
    get_use_case_summary,
)
from .types import EntityMetadata, ServiceConfig, UseCaseMetadata


def _get_request_schema(uc: UseCaseMetadata) -> dict[str, Any]:
    """Extract parameter schema from request class."""
    if hasattr(uc.request_cls, "model_json_schema"):
        schema = uc.request_cls.model_json_schema()
        # Extract properties and required fields
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        params = {}
        for name, prop in properties.items():
            param_info = {
                "type": prop.get("type", "any"),
                "required": name in required,
            }
            if "description" in prop:
                param_info["description"] = prop["description"]
            if "default" in prop:
                param_info["default"] = prop["default"]
            if "enum" in prop:
                param_info["enum"] = prop["enum"]
            params[name] = param_info
        return params
    return {}


def _get_response_schema(uc: UseCaseMetadata) -> dict[str, Any]:
    """Extract schema from response class."""
    if hasattr(uc.response_cls, "model_json_schema"):
        return uc.response_cls.model_json_schema()
    return {}


def register_discovery_resources(mcp: FastMCP, config: ServiceConfig) -> None:
    """Register 3-level progressive disclosure resources for a service.

    Creates:
    - {slug}:// - Service overview (Level 1)
    - {slug}://{entity} - Entity details (Level 2)
    - {slug}://{usecase} - Use case details (Level 3)
    """
    slug = config.slug

    # Level 1: Service overview
    @mcp.resource(f"{slug}://")
    def service_overview() -> dict[str, Any]:
        """Service overview with entities and use cases."""
        # Group use cases by type
        crud_by_entity: dict[str, list[str]] = {}
        other_use_cases: list[dict[str, str]] = []
        diagram_use_cases: list[dict[str, str]] = []

        for uc in config.use_cases:
            if uc.is_diagram:
                diagram_use_cases.append(
                    {
                        "name": uc.name,
                        "summary": get_use_case_summary(uc.use_case_cls),
                    }
                )
            elif uc.is_crud and uc.entity_name:
                if uc.entity_name not in crud_by_entity:
                    crud_by_entity[uc.entity_name] = []
                crud_by_entity[uc.entity_name].append(uc.crud_operation or uc.name)
            else:
                other_use_cases.append(
                    {
                        "name": uc.name,
                        "summary": get_use_case_summary(uc.use_case_cls),
                    }
                )

        # Build entities list with their CRUD operations
        entities_info = {}
        for entity in config.entities:
            ops = crud_by_entity.get(entity.name, [])
            entities_info[entity.name] = {
                "summary": entity.summary,
                "operations": ops,
                "details_uri": f"{slug}://{entity.name}",
            }

        return {
            "name": slug,
            "description": get_module_description(config.domain_module),
            "entities": entities_info,
            "other_use_cases": other_use_cases,
            "diagram_use_cases": diagram_use_cases,
        }

    # Level 2: Entity details (one resource per entity)
    for entity in config.entities:
        mcp.add_resource(
            _create_entity_resource(slug, entity),
        )

    # Level 3: Use case details (one resource per use case)
    for uc in config.use_cases:
        mcp.add_resource(
            _create_use_case_resource(slug, uc),
        )


def _create_entity_resource(slug: str, entity: EntityMetadata) -> FunctionResource:
    """Create a FunctionResource for an entity (Level 2).

    Uses FunctionResource instead of decorator to support static URIs.
    """

    def entity_details() -> dict[str, Any]:
        operations = {}
        for uc in entity.crud_use_cases:
            operations[uc.crud_operation or uc.name] = {
                "name": uc.name,
                "summary": get_use_case_summary(uc.use_case_cls),
                "details_uri": f"{slug}://{uc.name}",
            }

        return {
            "entity": entity.name,
            "summary": entity.summary,
            "description": (
                get_class_summary(entity.entity_cls) if entity.entity_cls else ""
            ),
            "operations": operations,
        }

    return FunctionResource(
        uri=f"{slug}://{entity.name}",
        fn=entity_details,
        name=f"{entity.name} entity details",
        description=f"Details and CRUD operations for {entity.name}",
    )


def _create_use_case_resource(slug: str, uc: UseCaseMetadata) -> FunctionResource:
    """Create a FunctionResource for a use case (Level 3).

    Uses FunctionResource instead of decorator to support static URIs.
    """

    def use_case_details() -> dict[str, Any]:
        return {
            "use_case": uc.name,
            "description": uc.use_case_cls.__doc__ or "",
            "is_crud": uc.is_crud,
            "crud_operation": uc.crud_operation,
            "entity": uc.entity_name,
            "is_diagram": uc.is_diagram,
            "parameters": _get_request_schema(uc),
            "response_schema": _get_response_schema(uc),
        }

    return FunctionResource(
        uri=f"{slug}://{uc.name}",
        fn=use_case_details,
        name=f"{uc.name} use case",
        description=get_use_case_summary(uc.use_case_cls),
    )
