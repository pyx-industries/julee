"""Sphinx environment implementation of AppRepository."""

from typing import TYPE_CHECKING

from julee.hcd.entities.app import App, AppType
from julee.hcd.domain.repositories.app import AppRepository
from julee.hcd.utils import normalize_name

from .base import SphinxEnvRepositoryMixin

if TYPE_CHECKING:
    from sphinx.environment import BuildEnvironment


class SphinxEnvAppRepository(SphinxEnvRepositoryMixin[App], AppRepository):
    """Sphinx env-backed implementation of AppRepository.

    Stores apps in env.hcd_storage["apps"] for parallel-safe Sphinx builds.
    Data is serialized as dicts and merged via env-merge-info.
    """

    def __init__(self, env: "BuildEnvironment") -> None:
        """Initialize with Sphinx build environment."""
        self.env = env
        self.entity_name = "App"
        self.entity_key = "apps"
        self.id_field = "slug"
        self.entity_class = App

    async def get_by_type(self, app_type: AppType) -> list[App]:
        """Get all apps of a specific type."""
        storage = self._get_storage()
        result = []
        for data in storage.values():
            # AppType is serialized as its value string
            if data.get("app_type") == app_type.value:
                result.append(self._deserialize(data))
        return result

    async def get_by_name(self, name: str) -> App | None:
        """Get an app by its display name (case-insensitive)."""
        name_normalized = normalize_name(name)
        storage = self._get_storage()
        for data in storage.values():
            if data.get("name_normalized") == name_normalized:
                return self._deserialize(data)
        return None

    async def get_all_types(self) -> set[AppType]:
        """Get all unique app types that have apps."""
        storage = self._get_storage()
        types = set()
        for data in storage.values():
            app_type_str = data.get("app_type")
            if app_type_str:
                types.add(AppType(app_type_str))
        return types

    async def get_apps_with_accelerators(self) -> list[App]:
        """Get all apps that have accelerators defined."""
        storage = self._get_storage()
        result = []
        for data in storage.values():
            if data.get("accelerators"):
                result.append(self._deserialize(data))
        return result
