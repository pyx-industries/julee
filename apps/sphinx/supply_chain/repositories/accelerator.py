"""Sphinx environment implementation of AcceleratorRepository."""

from apps.sphinx.hcd.repositories.base import SphinxEnvRepositoryMixin
from julee.supply_chain.entities.accelerator import Accelerator
from julee.supply_chain.repositories.accelerator import AcceleratorRepository


class SphinxEnvAcceleratorRepository(
    SphinxEnvRepositoryMixin[Accelerator], AcceleratorRepository
):
    """Sphinx env-backed implementation of AcceleratorRepository.

    Stores accelerators in env.hcd_storage["accelerators"] for parallel-safe
    Sphinx builds. Data is serialized as dicts and merged via env-merge-info.
    """

    entity_class = Accelerator

    async def get_by_status(self, status: str) -> list[Accelerator]:
        """Get all accelerators with a specific status."""
        status_normalized = status.lower().strip()
        storage = self._get_storage()
        result = []
        for data in storage.values():
            entity = self._deserialize(data)
            if entity.status_normalized == status_normalized:
                result.append(entity)
        return result

    async def get_by_docname(self, docname: str) -> list[Accelerator]:
        """Get all accelerators defined in a specific document."""
        return await self.find_by_docname(docname)

    async def get_by_integration(
        self, integration_slug: str, relationship: str
    ) -> list[Accelerator]:
        """Get accelerators that have a relationship with an integration."""
        storage = self._get_storage()
        result = []
        for data in storage.values():
            entity = self._deserialize(data)
            if relationship == "sources_from":
                if integration_slug in entity.get_sources_from_slugs():
                    result.append(entity)
            elif relationship == "publishes_to":
                if integration_slug in entity.get_publishes_to_slugs():
                    result.append(entity)
        return result

    async def get_dependents(self, accelerator_slug: str) -> list[Accelerator]:
        """Get accelerators that depend on a specific accelerator."""
        storage = self._get_storage()
        result = []
        for data in storage.values():
            if accelerator_slug in data.get("depends_on", []):
                result.append(self._deserialize(data))
        return result

    async def get_fed_by(self, accelerator_slug: str) -> list[Accelerator]:
        """Get accelerators that feed into a specific accelerator."""
        storage = self._get_storage()
        result = []
        for data in storage.values():
            if accelerator_slug in data.get("feeds_into", []):
                result.append(self._deserialize(data))
        return result

    async def get_all_statuses(self) -> set[str]:
        """Get all unique statuses across all accelerators."""
        storage = self._get_storage()
        statuses = set()
        for data in storage.values():
            entity = self._deserialize(data)
            if entity.status_normalized:
                statuses.add(entity.status_normalized)
        return statuses
