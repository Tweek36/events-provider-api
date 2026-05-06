from fastapi import HTTPException

from app.client.events_provider import EventsProviderClient
from app.models import Event
from app.repositories.event import EventRepository
from datetime import datetime
from app.settings import settings
from app.schemes.events import EventResponse, EventSeatsResponse, EventsResponse
import uuid


class EventsService:
    def __init__(self, session):
        self.session = session
        self.event_repository = EventRepository(session)
        self.events_provider_client = EventsProviderClient(
            settings.EVENTS_PROVIDER_API_URL, settings.X_API_KEY
        )
        self.settings.hostname = settings.HOSTNAME

    async def events(self, date_from: str, page: int, page_size: int):
        count = (
            await self.event_repository.count(datetime.strptime(date_from, "%Y-%m-%d"))
            + page_size
            - 1
        ) // page_size
        results = await self.event_repository.get_all(
            date_from=datetime.strptime(date_from, "%Y-%m-%d"),
            skip=(page - 1) * page_size,
            limit=page_size,
        )

        return EventsResponse(
            count=count,
            next=(
                f"http://{self.settings.hostname}/events?date_from={date_from}&page={page + 1}&page_size={page_size}"
                if page * page_size < count * page_size
                else None
            ),
            previous=(
                f"http://{self.settings.hostname}/events?date_from={date_from}&page={page - 1}&page_size={page_size}"
                if page > 1
                else None
            ),
            results=results,
        )

    async def get_event(self, event_id: uuid.UUID):
        event = await self.event_repository.get_by_id(event_id, selectin=[Event.place])
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return EventResponse.model_validate(event)

    async def get_event_seats(self, event_id: uuid.UUID):
        event = await self.event_repository.get_by_id(event_id)
        if not event or event.status != "published":
            raise HTTPException(status_code=404, detail="Event not found")
        response = await self.events_provider_client.seats(event_id)
        return EventSeatsResponse(event_id=event_id, available_seats=response.seats)
