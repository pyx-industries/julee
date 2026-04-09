from typing import Any

import httpx

from julee.contrib.ceap.domain.repositories.remote_schema import RemoteSchemaRepository


class HttpRemoteSchemaRepository(RemoteSchemaRepository):
    async def fetch(self, url: str) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
