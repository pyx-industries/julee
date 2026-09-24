"""Resolving the routers the adopted kits contribute."""

import logging
from pathlib import Path
from typing import Any

from julee.core.kits import contributions, resolve_contribution

__all__ = ["CONTRIBUTION_POINT", "include_kit_routers", "kit_routers"]

logger = logging.getLogger(__name__)

CONTRIBUTION_POINT = "fastapi.routers"
"""Where a kit says what it serves."""


def kit_routers(solution_root: Path) -> list[Any]:
    """The routers the adopted kits contribute, in adoption order.

    Args:
        solution_root: Path to the solution root directory

    Returns:
        Whatever each kit pointed at, resolved

    Raises:
        ImportError: If a kit names a module that is not there
        AttributeError: If a kit names an attribute a module does not have
    """
    return [
        resolve_contribution(path)
        for path in contributions(solution_root, CONTRIBUTION_POINT)
    ]


def include_kit_routers(app: Any, solution_root: Path, **kwargs: Any) -> int:
    """Mount every router the adopted kits contribute.

    The order is adoption order, so a solution decides which kit's routes
    are registered first by the order it lists its kits.

    Args:
        app: The FastAPI application to mount onto
        solution_root: Path to the solution root directory
        **kwargs: Passed to include_router, for a prefix or tags

    Returns:
        How many were mounted, for a solution that wants to log it
    """
    routers = kit_routers(solution_root)
    for router in routers:
        app.include_router(router, **kwargs)
    logger.debug("Mounted %d kit routers", len(routers))
    return len(routers)
