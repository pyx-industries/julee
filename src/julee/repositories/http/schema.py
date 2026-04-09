from typing import Any

import httpx


class HttpRemoteSchemaRepository:
    async def fetch(self, url: str) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
