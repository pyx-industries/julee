"""Mounting what the adopted kits contribute to a FastAPI application.

A kit that serves something declares it::

    contributes={"fastapi.routers": "julee_ceap.apps.api.app:app"}

and a solution mounts every kit's routers without naming any of them.

This lives in an integration rather than the kernel because mounting a
router means importing FastAPI, and the kernel does not. Install it with
``julee[api]``.
"""

from .routers import include_kit_routers, kit_routers

__all__ = ["include_kit_routers", "kit_routers"]
