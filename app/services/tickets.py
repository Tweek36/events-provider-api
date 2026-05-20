import datetime
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.client.events_provider import EventsProviderClient
from app.exceptions import (
    EventAlreadyOccurred,
    EventNotFound,
    IdempotencyConflict,
    RegistrationClosed,
    SeatAlreadyTaken,
    SeatUnavailable,
    TicketNotFound,
)
from app.models import Event, Ticket
from app.repositories.event import EventRepository
from app.repositories.idempotency import IdempotencyRepository
from app.repositories.outbox import OutboxRepository
from app.repositories.ticket import TicketRepository
from app.schemes.client import RegisterRequest, UnregisterRequest
from app.schemes.tickets import TicketsRequestBody
from app.settings import settings
from app.types import EventStatus


class TicketsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.events_provider_client = EventsProviderClient(settings.EVENTS_PROVIDER_API_URL, settings.X_API_KEY)
        self.ticket_repository = TicketRepository(session)
        self.event_repository = EventRepository(session)
        self.outbox_repository = OutboxRepository(session)
        self.idempotency_repository = IdempotencyRepository(session)

    def _is_seat_available(self, seat: str, seats_pattern: str) -> bool:
        seat_row, seat_num = seat[0], int(seat[1:])
        return any(
            seat_row == r[0] and (int(r[1:].split("-")[0])) <= seat_num <= int(r[1:].split("-")[1])
            for r in seats_pattern.split(",")
        )

    async def register(self, body: TicketsRequestBody):
        # Проверка идемпотентности
        if body.idempotency_key:
            existing = await self.idempotency_repository.get_by_key(body.idempotency_key)
            if existing:
                # Проверить, что данные запроса совпадают
                request_data = body.model_dump(exclude={"idempotency_key"})
                request_hash = self.idempotency_repository.compute_request_hash(request_data)

                if request_hash != existing.request_hash:
                    raise IdempotencyConflict("Idempotency key already used with different request data")

                # Вернуть существующий результат
                ticket = await self.ticket_repository.get_by_id(existing.ticket_id)
                from app.schemes.client import RegisterResponse

                return RegisterResponse(ticket_id=ticket.id)

        event = await self.event_repository.get_by_id(body.event_id, selectin=[Event.place, Event.tickets])
        if not event or event.status != EventStatus.PUBLISHED:
            raise EventNotFound("Event not found")
        if event.registration_deadline < datetime.datetime.now(datetime.UTC):
            raise RegistrationClosed("Registration deadline has passed")
        if not self._is_seat_available(body.seat, event.place.seats_pattern):
            raise SeatUnavailable("Seat is not available")
        if event.tickets and any(t.seat == body.seat for t in event.tickets):
            raise SeatAlreadyTaken("Seat is already taken")

        response = await self.events_provider_client.register(
            event_id=body.event_id,
            body=RegisterRequest(**body.model_dump(exclude={"idempotency_key"})),
        )

        await self.ticket_repository.create(
            {
                "id": response.ticket_id,
                "event_id": body.event_id,
                "seat": body.seat,
            }
        )

        # Создать запись в outbox для отправки уведомления
        await self.outbox_repository.create(
            {
                "event_type": "ticket_purchased",
                "payload": {
                    "ticket_id": str(response.ticket_id),
                    "event_id": str(body.event_id),
                },
                "created_at": datetime.datetime.now(datetime.UTC),
            }
        )

        # Сохранить ключ идемпотентности после успешной регистрации
        if body.idempotency_key:
            request_data = body.model_dump(exclude={"idempotency_key"})
            await self.idempotency_repository.create_key(
                idempotency_key=body.idempotency_key,
                ticket_id=response.ticket_id,
                request_data=request_data,
            )

        return response

    async def unregister(self, ticket_id: uuid.UUID):
        ticket = await self.ticket_repository.get_by_id(ticket_id, selectin=[Ticket.event])
        if not ticket:
            raise TicketNotFound("Ticket not found")
        if ticket.event.event_time <= datetime.datetime.now(datetime.UTC):
            raise EventAlreadyOccurred("Event has already occurred")
        response = await self.events_provider_client.unregister(
            event_id=ticket.event_id, body=UnregisterRequest(ticket_id=ticket_id)
        )
        await self.ticket_repository.delete(ticket_id)
        return response
