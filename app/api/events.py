from cashews import cache
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.services.events import EventsService
import uuid

from app.types import DateStr

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("")
async def events(
    date_from: DateStr = Query(default="2000-01-01"),
    page: int = Query(default=1, gt=0),
    page_size: int | None = Query(default=20, gt=0),
    session: AsyncSession = Depends(get_session),
):
    return await EventsService(session).events(
        date_from=date_from, page=page, page_size=page_size
    )


@router.get("/{event_id}")
async def get_event(
    event_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    return await EventsService(session).get_event(event_id=event_id)


@router.get("/{event_id}/seats")
# @cache(ttl="30s", key="event_seats:{event_id}")
async def get_event_seats(
    event_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    return await EventsService(session).get_event_seats(event_id=event_id)
