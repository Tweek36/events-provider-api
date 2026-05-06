import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.client.events_provider import EventsProviderClient
from app.schemes.client import (
    EventsResponse,
    SeatsResponse,
    RegisterRequest,
    RegisterResponse,
    UnregisterRequest,
    UnregisterResponse,
)


@pytest.fixture
def client():
    return EventsProviderClient(base_url="http://testserver/", api_key="test-api-key")


@pytest.fixture
def mock_httpx_client():
    """Мок для httpx.AsyncClient и его контекстного менеджера."""
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = MagicMock(return_value={})
    
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.request = AsyncMock(return_value=mock_response)
    
    return mock_client, mock_response


class TestEventsProviderClient:
    """Тесты для EventsProviderClient."""

    @pytest.mark.asyncio
    async def test_events_success(self, client, mock_httpx_client):
        """Тест успешного получения списка событий."""
        mock_client, mock_response = mock_httpx_client
        event_id = uuid.uuid4()
        place_id = uuid.uuid4()
        mock_response.json.return_value = {
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": str(event_id),
                    "place": {
                        "id": str(place_id),
                        "changed_at": "2026-05-05T10:00:00",
                        "created_at": "2026-05-01T10:00:00",
                        "name": "Test Place",
                        "city": "Moscow",
                        "address": "Test Address",
                        "seats_pattern": "A1-10",
                    },
                    "changed_at": "2026-05-05T10:00:00",
                    "created_at": "2026-05-01T10:00:00",
                    "name": "Test Event",
                    "event_time": "2026-06-01T19:00:00",
                    "registration_deadline": "2026-05-30T23:59:59",
                    "status": "published",
                    "number_of_visitors": 0,
                    "status_changed_at": "2026-05-05T10:00:00",
                }
            ],
        }

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await client.events("2026-05-01")

        assert isinstance(result, EventsResponse)
        assert len(result.results) == 1
        assert result.results[0].name == "Test Event"
        mock_client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_events_http_error(self, client, mock_httpx_client):
        """Тест обработки HTTP ошибки при получении событий."""
        mock_client, mock_response = mock_httpx_client
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Not found"}

        with patch("httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(Exception):
                await client.events("2026-05-01")

    @pytest.mark.asyncio
    async def test_events_invalid_date_format(self, client):
        """Тест обработки невалидного формата даты."""
        with pytest.raises(Exception):
            await client.events("invalid-date")

    @pytest.mark.asyncio
    async def test_seats_success(self, client, mock_httpx_client):
        """Тест успешного получения мест события."""
        mock_client, mock_response = mock_httpx_client
        event_id = uuid.uuid4()
        mock_response.json.return_value = {
            "seats": ["A1", "A2", "A3"]
        }

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await client.seats(event_id)

        assert isinstance(result, SeatsResponse)
        assert len(result.seats) == 3
        assert "A1" in result.seats

    @pytest.mark.asyncio
    async def test_seats_http_error(self, client, mock_httpx_client):
        """Тест обработки HTTP ошибки при получении мест."""
        mock_client, mock_response = mock_httpx_client
        mock_response.status_code = 500
        mock_response.json.return_value = {"detail": "Internal error"}
        event_id = uuid.uuid4()

        with patch("httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(Exception):
                await client.seats(event_id)

    @pytest.mark.asyncio
    async def test_register_success(self, client, mock_httpx_client):
        """Тест успешной регистрации на событие."""
        mock_client, mock_response = mock_httpx_client
        event_id = uuid.uuid4()
        ticket_id = uuid.uuid4()
        mock_response.json.return_value = {
            "ticket_id": str(ticket_id)
        }

        register_data = RegisterRequest(
            first_name="Ivan",
            last_name="Ivanov",
            seat="A1",
            email="ivan@example.com"
        )

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await client.register(event_id, register_data)

        assert isinstance(result, RegisterResponse)
        assert result.ticket_id == ticket_id
        # Проверяем, что json был передан в запрос
        call_args = mock_client.request.call_args
        assert call_args.kwargs["json"] is not None

    @pytest.mark.asyncio
    async def test_unregister_success(self, client, mock_httpx_client):
        """Тест успешной отмены регистрации."""
        mock_client, mock_response = mock_httpx_client
        event_id = uuid.uuid4()
        ticket_id = uuid.uuid4()
        mock_response.json.return_value = {
            "success": True
        }

        unregister_data = UnregisterRequest(ticket_id=ticket_id)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await client.unregister(event_id, unregister_data)

        assert isinstance(result, UnregisterResponse)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_fetch_events_single_page(self, client, mock_httpx_client):
        """Тест fetch_events для одной страницы (без next)."""
        mock_client, mock_response = mock_httpx_client
        event_id = uuid.uuid4()
        place_id = uuid.uuid4()
        mock_response.json.return_value = {
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": str(event_id),
                    "place": {
                        "id": str(place_id),
                        "changed_at": "2026-05-05T10:00:00",
                        "created_at": "2026-05-01T10:00:00",
                        "name": "Test Place",
                        "city": "Moscow",
                        "address": "Test Address",
                        "seats_pattern": "A1-10",
                    },
                    "changed_at": "2026-05-05T10:00:00",
                    "created_at": "2026-05-01T10:00:00",
                    "name": "Test Event",
                    "event_time": "2026-06-01T19:00:00",
                    "registration_deadline": "2026-05-30T23:59:59",
                    "status": "published",
                    "number_of_visitors": 0,
                    "status_changed_at": "2026-05-05T10:00:00",
                }
            ],
        }

        with patch("httpx.AsyncClient", return_value=mock_client):
            results = []
            async for response in client.fetch_events("2026-05-01"):
                results.append(response)

        assert len(results) == 1
        assert isinstance(results[0], EventsResponse)

    @pytest.mark.asyncio
    async def test_fetch_events_pagination(self, client, mock_httpx_client):
        """Тест fetch_events с пагинацией (несколько страниц)."""
        mock_client, mock_response = mock_httpx_client
        event_id_1 = uuid.uuid4()
        event_id_2 = uuid.uuid4()
        place_id = uuid.uuid4()
        
        # Настраиваем ответы для первого и второго запроса
        first_response = {
            "next": "http://testserver/api/events/?page=2",
            "previous": None,
            "results": [
                {
                    "id": str(event_id_1),
                    "place": {
                        "id": str(place_id),
                        "changed_at": "2026-05-05T10:00:00",
                        "created_at": "2026-05-01T10:00:00",
                        "name": "Test Place",
                        "city": "Moscow",
                        "address": "Test Address",
                        "seats_pattern": "A1-10",
                    },
                    "changed_at": "2026-05-05T10:00:00",
                    "created_at": "2026-05-01T10:00:00",
                    "name": "Event 1",
                    "event_time": "2026-06-01T19:00:00",
                    "registration_deadline": "2026-05-30T23:59:59",
                    "status": "published",
                    "number_of_visitors": 0,
                    "status_changed_at": "2026-05-05T10:00:00",
                }
            ],
        }
        second_response = {
            "next": None,
            "previous": "http://testserver/api/events/?page=1",
            "results": [
                {
                    "id": str(event_id_2),
                    "place": {
                        "id": str(place_id),
                        "changed_at": "2026-05-05T10:00:00",
                        "created_at": "2026-05-01T10:00:00",
                        "name": "Test Place",
                        "city": "Moscow",
                        "address": "Test Address",
                        "seats_pattern": "A1-10",
                    },
                    "changed_at": "2026-05-05T10:00:00",
                    "created_at": "2026-05-01T10:00:00",
                    "name": "Event 2",
                    "event_time": "2026-06-02T19:00:00",
                    "registration_deadline": "2026-05-30T23:59:59",
                    "status": "published",
                    "number_of_visitors": 0,
                    "status_changed_at": "2026-05-05T10:00:00",
                }
            ],
        }
        
        mock_response.json.side_effect = [first_response, second_response]

        with patch("httpx.AsyncClient", return_value=mock_client):
            results = []
            async for response in client.fetch_events("2026-05-01"):
                results.append(response)

        assert len(results) == 2
        assert results[0].results[0].name == "Event 1"
        assert results[1].results[0].name == "Event 2"

    @pytest.mark.asyncio
    async def test_request_logging_on_exception(self, client, mock_httpx_client):
        """Тест логирования при исключениях в _request."""
        mock_client, mock_response = mock_httpx_client
        mock_client.request.side_effect = Exception("Connection error")

        with patch("httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(Exception):
                await client.events("2026-05-01")