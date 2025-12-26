"""Tool generation for MCP server framework.

Dynamically creates MCP tools from discovered use cases.
"""

import functools
import inspect
from collections.abc import Callable
from typing import Any, get_type_hints

from fastmcp import FastMCP
from fastmcp.tools import Tool

from .discovery import get_use_case_summary
from .types import ServiceConfig, UseCaseMetadata

# Sentinel for unset defaults (None can be a valid default)
_UNSET = object()


def _create_tool_function(
    uc: UseCaseMetadata, slug: str
) -> tuple[Callable[..., Any], str]:
    """Create a tool function for a use case.

    Returns the function and its docstring.

    FastMCP requires explicit parameters (no **kwargs), so we dynamically
    build a function signature that matches the request class fields.
    """
    # Get the first sentence of the use case docstring for minimal docstring
    summary = get_use_case_summary(uc.use_case_cls)
    docstring = f"{summary} See {slug}://{uc.name}"

    # Get the request schema to understand parameters
    if hasattr(uc.request_cls, "model_fields"):
        fields = uc.request_cls.model_fields
    else:
        fields = {}

    # Build the function signature parameters
    params = []
    for field_name, field_info in fields.items():
        field_type = field_info.annotation

        # Determine default value
        if field_info.default is not None and not isinstance(
            field_info.default, type
        ):
            default = field_info.default
        elif field_info.default_factory is not None:
            # For factory defaults, mark as optional with None
            default = None
        else:
            default = inspect.Parameter.empty

        param = inspect.Parameter(
            field_name,
            inspect.Parameter.KEYWORD_ONLY,
            default=default,
            annotation=field_type,
        )
        params.append(param)

    sig = inspect.Signature(params, return_annotation=dict[str, Any])

    # Create the actual execution function
    async def _execute(request_kwargs: dict[str, Any]) -> dict[str, Any]:
        use_case = uc.factory()
        request = uc.request_cls(**request_kwargs)
        response = await use_case.execute(request)

        if hasattr(response, "model_dump"):
            return response.model_dump()
        return {"result": response}

    # Create a wrapper that collects kwargs and passes to _execute
    # This wrapper has the proper signature that FastMCP can parse
    @functools.wraps(_execute)
    async def tool_fn(*args: Any, **kwargs: Any) -> dict[str, Any]:
        # Bind args/kwargs to signature to get clean dict
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        return await _execute(dict(bound.arguments))

    # Set the proper signature, docstring, and name
    tool_fn.__signature__ = sig  # type: ignore
    tool_fn.__doc__ = docstring
    tool_fn.__name__ = _to_snake_case(uc.name)

    # Build annotations dict for FastMCP
    tool_fn.__annotations__ = {
        p.name: p.annotation for p in params if p.annotation != inspect.Parameter.empty
    }
    tool_fn.__annotations__["return"] = dict[str, Any]

    return tool_fn, docstring


def _to_snake_case(name: str) -> str:
    """Convert CamelCase to snake_case."""
    import re

    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _create_tool_name(uc: UseCaseMetadata, slug: str) -> str:
    """Create the MCP tool name for a use case."""
    # Format: mcp_{slug}_{operation}_{entity}
    # e.g., mcp_c4_create_software_system
    snake_name = _to_snake_case(uc.name)
    return f"mcp_{slug}_{snake_name}"


def register_use_case_tool(mcp: FastMCP, uc: UseCaseMetadata, slug: str) -> None:
    """Register a single use case as an MCP tool.

    Args:
        mcp: FastMCP server instance
        uc: Use case metadata
        slug: Service slug for tool naming
    """
    tool_fn, docstring = _create_tool_function(uc, slug)
    tool_name = _create_tool_name(uc, slug)

    # Create tool from function
    tool = Tool.from_function(
        fn=tool_fn,
        name=tool_name,
        description=docstring,
    )

    mcp.add_tool(tool)


def register_diagram_tool(
    mcp: FastMCP, slug: str, diagram_ucs: list[UseCaseMetadata]
) -> None:
    """Register a consolidated diagram tool.

    Instead of separate tools for each diagram type, creates a single
    tool with a diagram_type parameter.

    Args:
        mcp: FastMCP server instance
        slug: Service slug
        diagram_ucs: List of diagram use cases to consolidate
    """
    if not diagram_ucs:
        return

    # Build the type enum from available diagram types
    diagram_types = []
    uc_map: dict[str, UseCaseMetadata] = {}

    for uc in diagram_ucs:
        if uc.entity_name:
            # Convert "SystemContext" -> "system_context"
            diagram_type = _to_snake_case(uc.entity_name)
            diagram_types.append(diagram_type)
            uc_map[diagram_type] = uc

    if not diagram_types:
        return

    # Each diagram type has different parameters, so we need to collect all
    # possible parameters and make them optional
    all_params: dict[str, inspect.Parameter] = {}

    # Always have diagram_type as first required parameter
    all_params["diagram_type"] = inspect.Parameter(
        "diagram_type",
        inspect.Parameter.KEYWORD_ONLY,
        annotation=str,
    )

    # Collect parameters from all diagram use cases
    for uc in diagram_ucs:
        if hasattr(uc.request_cls, "model_fields"):
            for field_name, field_info in uc.request_cls.model_fields.items():
                if field_name not in all_params:
                    # Make all diagram-specific params optional
                    all_params[field_name] = inspect.Parameter(
                        field_name,
                        inspect.Parameter.KEYWORD_ONLY,
                        default=None,
                        annotation=field_info.annotation | None,
                    )

    sig = inspect.Signature(list(all_params.values()), return_annotation=dict[str, Any])

    # Create the actual execution function
    async def _execute(diagram_type: str, kwargs: dict[str, Any]) -> dict[str, Any]:
        uc = uc_map.get(diagram_type)
        if not uc:
            return {"error": f"Unknown diagram type: {diagram_type}"}

        # Filter kwargs to only include fields for this request type
        if hasattr(uc.request_cls, "model_fields"):
            valid_fields = set(uc.request_cls.model_fields.keys())
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_fields and v is not None}
        else:
            filtered_kwargs = kwargs

        use_case = uc.factory()
        request = uc.request_cls(**filtered_kwargs)
        response = await use_case.execute(request)

        if hasattr(response, "model_dump"):
            return response.model_dump()
        return {"result": response}

    # Create wrapper with proper signature
    @functools.wraps(_execute)
    async def diagram_fn(*args: Any, **kwargs: Any) -> dict[str, Any]:
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        arguments = dict(bound.arguments)
        dtype = arguments.pop("diagram_type")
        return await _execute(dtype, arguments)

    # Build docstring with available types
    types_list = ", ".join(sorted(diagram_types))
    diagram_fn.__signature__ = sig  # type: ignore
    diagram_fn.__doc__ = f"Generate a diagram. Types: {types_list}. See {slug}://"
    diagram_fn.__name__ = f"{slug}_diagram"
    diagram_fn.__annotations__ = {
        p.name: p.annotation for p in all_params.values()
    }
    diagram_fn.__annotations__["return"] = dict[str, Any]

    tool = Tool.from_function(
        fn=diagram_fn,
        name=f"mcp_{slug}_diagram",
        description=diagram_fn.__doc__,
    )

    mcp.add_tool(tool)


def register_tools(mcp: FastMCP, config: ServiceConfig) -> None:
    """Register all tools for a service.

    Args:
        mcp: FastMCP server instance
        config: Service configuration with discovered use cases
    """
    slug = config.slug

    # Separate diagram use cases for consolidation
    diagram_ucs = [uc for uc in config.use_cases if uc.is_diagram]
    other_ucs = [uc for uc in config.use_cases if not uc.is_diagram]

    # Register consolidated diagram tool if there are diagram use cases
    if diagram_ucs:
        register_diagram_tool(mcp, slug, diagram_ucs)

    # Register individual tools for all other use cases
    for uc in other_ucs:
        register_use_case_tool(mcp, uc, slug)
