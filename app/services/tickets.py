import datetime
import uuid
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.client.events_provider import EventsProviderClient
from app.models import Event, Ticket
from app.repositories.event import EventRepository
from app.repositories.ticket import TicketRepository
from app.schemes.client import RegisterRequest, UnregisterRequest
from app.schemes.tickets import TicketsRequestBody
from app.settings import EVENTS_PROVIDER_API_URL, X_API_KEY


class TicketsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.events_provider_client = EventsProviderClient(
            EVENTS_PROVIDER_API_URL, X_API_KEY
        )
        self.ticket_repository = TicketRepository(session)
        self.event_repository = EventRepository(session)

    def _is_seat_available(self, seat: str, seats_pattern: str) -> bool:
        seat_row, seat_num = seat[0], int(seat[1:])
        return any(
            seat_row == r[0]
            and (int(r[1:].split("-")[0])) <= seat_num <= int(r[1:].split("-")[1])
            for r in seats_pattern.split(",")
        )

    async def register(self, body: TicketsRequestBody):
        event = await self.event_repository.get_by_id(
            body.event_id, selectin=[Event.place]
        )
        if not event or event.status != "published":
            raise HTTPException(status_code=404, detail="Event not found")
        if event.registration_deadline < datetime.datetime.now(datetime.UTC):
            raise HTTPException(
                status_code=400, detail="Registration deadline has passed"
            )
        if not self._is_seat_available(body.seat, event.place.seats_pattern):
            raise HTTPException(status_code=400, detail="Seat is not available")
        return await self.events_provider_client.register(
            event_id=body.event_id, body=RegisterRequest(**body.model_dump())
        )

    async def unregister(self, ticket_id: uuid.UUID):
        ticket = await self.ticket_repository.get_by_id(
            ticket_id, selectin=[Ticket.event]
        )
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        if ticket.event.event_time >= datetime.datetime.now(datetime.UTC):
            raise HTTPException(status_code=400, detail="Event has already occurred")
        return await self.events_provider_client.unregister(
            event_id=ticket.event_id, body=UnregisterRequest(ticket_id=ticket_id)
        )
