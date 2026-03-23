import httpx
import os
from typing import List, Optional, Any, Dict
from app.core.config import settings
from app.core.logging import logger

class InsForgeClient:
    def __init__(self):
        self.base_url = settings.INSFORGE_BASE_URL or "https://ke6vx29r.us-east.insforge.app"
        self.anon_key = settings.INSFORGE_ANON_KEY
        self._client: Optional[httpx.AsyncClient] = None
        if not self.anon_key:
            logger.error("INSFORGE_ANON_KEY is not set in environment!")
            
        self.headers = {
            "Authorization": f"Bearer {self.anon_key}",
            "apikey": self.anon_key,
            "Content-Type": "application/json"
        }

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=5.0)
        return self._client

    async def _request(self, method: str, table: str, params: Optional[Dict[str, Any]] = None, json_data: Optional[Any] = None, headers: Optional[Dict[str, str]] = None) -> Any:
        url = f"{self.base_url}/api/database/records/{table}"
        req_headers = self.headers.copy()
        if headers:
            req_headers.update(headers)
            
        client = await self.get_client()
        try:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=req_headers
            )
            response.raise_for_status()
            return response.json() if response.status_code != 204 else None
        except httpx.HTTPStatusError as e:
            logger.error(f"InsForge API Error: {e.response.text}")
            raise e
        except Exception as e:
            logger.error(f"InsForge Connection Error: {str(e)}")
            raise e

    async def close(self):
        if self._client:
            await self._client.aclose()

    async def get_records(self, table: str, **filters) -> List[Dict[str, Any]]:
        # Map filters to PostgREST syntax (simple eq for now)
        params = {k: f"eq.{v}" for k, v in filters.items()}
        return await self._request("GET", table, params=params)

    async def get_one(self, table: str, **filters) -> Optional[Dict[str, Any]]:
        records = await self.get_records(table, **filters)
        return records[0] if records else None

    async def create_record(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        # PostgREST requires array for inserts
        # Use return=representation to get the created record
        headers = {"Prefer": "return=representation"}
        records = await self._request("POST", table, json_data=[data], headers=headers)
        return records[0] if records else {}

    async def update_record(self, table: str, filters: Dict[str, Any], data: Dict[str, Any]) -> List[Dict[str, Any]]:
        params = {k: f"eq.{v}" for k, v in filters.items()}
        headers = {"Prefer": "return=representation"}
        return await self._request("PATCH", table, params=params, json_data=data, headers=headers)

insforge = InsForgeClient()
