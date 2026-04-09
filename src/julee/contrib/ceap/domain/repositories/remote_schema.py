from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class RemoteSchemaRepository(Protocol):
    async def fetch(self, url: str) -> dict[str, Any]:
        """Fetch and return the JSON document at url."""
        ...
