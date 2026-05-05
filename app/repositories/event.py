from datetime import datetime
from typing import Sequence
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.models import Event
from app.repositories.base import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession


class EventRepository(BaseRepository[Event]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=Event)

    async def get_all(
        self, date_from: datetime, skip: int = 0, limit: int = 100
    ) -> Sequence[Event]:
        result = await self.session.execute(
            select(Event)
            .where(Event.event_time >= date_from)
            .options(selectinload(Event.place))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def count(self, date_from: datetime) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Event).where(Event.event_time >= date_from)
        )
        return result.scalar_one()
