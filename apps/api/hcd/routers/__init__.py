"""HCD API routers.

Provides FastAPI routers for HCD domain endpoints.
"""

from .hcd import router as hcd_router
from .solution import router as solution_router

__all__ = ["hcd_router", "solution_router"]
