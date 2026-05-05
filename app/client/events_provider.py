from fastapi import HTTPException
from typing import AsyncGenerator
import uuid
import httpx
import structlog
from app.schemes.client import (
    EventsResponse,
    SeatsResponse,
    RegisterRequest,
    RegisterResponse,
    UnregisterRequest,
    UnregisterResponse,
)
from app.validators import validate_date_format
from urllib.parse import urlparse, urlunparse, parse_qs

logger = structlog.get_logger()


class EventsProviderClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.next_page_url = None

    async def _request(
        self, method: str, url: str, params: dict = None, json: dict = None
    ) -> dict:
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.request(
                    method,
                    url=url,
                    params=params,
                    json=json,
                    headers={"x-api-key": self.api_key},
                )
                if response.status_code >= 300:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=response.json().get("detail"),
                    )
                return response.json()
        except Exception as e:
            logger.error(
                "event_provider_request_failed",
                error_type=type(e).__name__,
                error_msg=str(e),
                method=method,
                url=url,
                params=params,
            )
            raise e

    async def events(self, changed_at: str) -> EventsResponse:
        validate_date_format(changed_at)
        response = await self._request(
            "GET", f"{self.base_url}api/events/", params={"changed_at": changed_at}
        )
        return EventsResponse(**response)

    async def seats(self, event_id: uuid.UUID) -> SeatsResponse:
        response = await self._request(
            "GET", f"{self.base_url}api/events/{event_id}/seats/"
        )
        return SeatsResponse(**response)

    async def register(
        self, event_id: uuid.UUID, body: RegisterRequest
    ) -> RegisterResponse:
        response = await self._request(
            "POST",
            f"{self.base_url}api/events/{event_id}/register/",
            json=body.model_dump(),
        )
        return RegisterResponse(**response)

    async def unregister(
        self, event_id: uuid.UUID, body: UnregisterRequest
    ) -> UnregisterResponse:
        response = await self._request(
            "DELETE",
            f"{self.base_url}api/events/{event_id}/unregister/",
            json=body.model_dump(),
        )
        return UnregisterResponse(**response)

    async def fetch_events(
        self, changed_at: str
    ) -> AsyncGenerator[EventsResponse, None]:
        response = await self.events(changed_at)
        while True:
            yield response
            if not response.next:
                break
            parsed = urlparse(response.next.unicode_string())
            url = urlunparse(parsed._replace(query="", fragment=""))
            params = parse_qs(parsed.query)
            response = EventsResponse(**await self._request("GET", url, params=params))
