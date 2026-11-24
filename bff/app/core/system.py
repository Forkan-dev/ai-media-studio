"""HTTP client for the system backend. System errors (404, 409, 422) are passed on to the UI unchanged."""
from typing import Any

import httpx
from fastapi import HTTPException

from app.core.config import settings

# long operations (topic discovery, detection) can take minutes
TIMEOUT = httpx.Timeout(10, read=900)


class SystemClient:
    def __init__(self) -> None:
        self.http = httpx.AsyncClient(base_url=settings.system_url, timeout=TIMEOUT)

    async def get(self, path: str, **params: Any) -> Any:
        return self._json(await self.http.get(path, params=params or None))

    async def post(self, path: str, body: Any = None, **params: Any) -> Any:
        return self._json(await self.http.post(path, json=body, params=params or None))

    async def put(self, path: str, body: Any) -> Any:
        return self._json(await self.http.put(path, json=body))

    async def post_file(self, path: str, filename: str, data: bytes, content_type: str) -> Any:
        """Forward an uploaded file (multipart, field "file")."""
        return self._json(await self.http.post(path, files={"file": (filename, data, content_type)}))

    async def put_empty(self, path: str, body: Any) -> None:
        """For endpoints that answer 204/202 with no body."""
        self._check(await self.http.put(path, json=body))

    async def post_empty(self, path: str, body: Any = None) -> None:
        self._check(await self.http.post(path, json=body))

    async def close(self) -> None:
        await self.http.aclose()

    @staticmethod
    def _json(resp: httpx.Response) -> Any:
        SystemClient._check(resp)
        return resp.json()

    @staticmethod
    def _check(resp: httpx.Response) -> None:
        if resp.is_error:
            try:
                detail = resp.json().get("detail", resp.text)
            except ValueError:
                detail = resp.text
            raise HTTPException(status_code=resp.status_code, detail=detail)


system = SystemClient()
