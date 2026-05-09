import uuid
from typing import AsyncGenerator
from urllib.parse import parse_qs, urljoin, urlparse, urlunparse

import httpx
import structlog

from app.exceptions import EventsProviderError
from app.schemes.client import (EventsResponse, RegisterRequest,
                                RegisterResponse, SeatsResponse,
                                UnregisterRequest, UnregisterResponse)
from app.validators import validate_date_format

logger = structlog.get_logger()


class EventsProviderClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = str(base_url)
        self.api_key = api_key
        self.next_page_url = None

    async def _request(
        self, method: str, url: str, params: dict = None, json: dict = None
    ) -> dict:
        try:
            async with httpx.AsyncClient(
                follow_redirects=True, headers={"x-api-key": self.api_key}
            ) as client:
                response = await client.request(
                    method,
                    url=url,
                    params=params,
                    json=json,
                )
                if response.status_code >= 400:
                    detail = response.json() if response.headers.get("content-type") == "application/json" else response.text
                    raise EventsProviderError(
                        status_code=response.status_code,
                        detail=str(detail),
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
        url = urljoin(self.base_url, "api/events/")
        response = await self._request(
            "GET", url, params={"changed_at": changed_at}
        )
        return EventsResponse(**response)

    async def seats(self, event_id: uuid.UUID) -> SeatsResponse:
        url = urljoin(self.base_url, f"api/events/{event_id}/seats/")
        response = await self._request("GET", url)
        return SeatsResponse(**response)

    async def register(
        self, event_id: uuid.UUID, body: RegisterRequest
    ) -> RegisterResponse:
        url = urljoin(self.base_url, f"api/events/{event_id}/register/")
        response = await self._request(
            "POST",
            url,
            json=body.model_dump(mode='json'),
        )
        return RegisterResponse(**response)

    async def unregister(
        self, event_id: uuid.UUID, body: UnregisterRequest
    ) -> UnregisterResponse:
        url = urljoin(self.base_url, f"api/events/{event_id}/unregister/")
        response = await self._request(
            "DELETE",
            url,
            json=body.model_dump(mode='json'),
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
            # Преобразуем списки значений в строки, так как parse_qs возвращает списки
            params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
            response = EventsResponse(**await self._request("GET", url, params=params))
