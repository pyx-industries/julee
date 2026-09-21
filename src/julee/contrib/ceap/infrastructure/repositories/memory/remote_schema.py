from typing import Any

from julee.contrib.ceap.domain.repositories.remote_schema import RemoteSchemaRepository


class MemoryRemoteSchemaRepository(RemoteSchemaRepository):
    def __init__(self, schemas: dict[str, dict] | None = None) -> None:
        self._schemas: dict[str, dict] = schemas or {}

    def register(self, url: str, schema: dict) -> None:
        self._schemas[url] = schema

    async def fetch(self, url: str) -> dict[str, Any]:
        if url not in self._schemas:
            raise ValueError(f"No schema registered for URL: {url}")
        return dict(self._schemas[url])
