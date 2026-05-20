import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OutboxEvent
from app.repositories.base import BaseRepository
from app.types import OutboxStatus


class OutboxRepository(BaseRepository[OutboxEvent]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=OutboxEvent)

    async def get_pending_events(self, limit: int = 100) -> list[OutboxEvent]:
        """Получить события со статусом pending для обработки."""
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.status == OutboxStatus.PENDING)
            .order_by(OutboxEvent.created_at)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_as_sent(self, event_id: uuid.UUID) -> None:
        """Пометить событие как успешно отправленное."""
        event = await self.get_by_id(event_id)
        if event:
            event.status = OutboxStatus.SENT
            event.processed_at = datetime.now(datetime.UTC)
            await self.session.flush()

    async def increment_attempts(self, event_id: uuid.UUID) -> None:
        """Увеличить счетчик попыток отправки."""
        event = await self.get_by_id(event_id)
        if event:
            event.attempts += 1
            await self.session.flush()

    async def mark_as_failed(self, event_id: uuid.UUID) -> None:
        """Пометить событие как неудачное после исчерпания попыток."""
        event = await self.get_by_id(event_id)
        if event:
            event.status = OutboxStatus.FAILED
            event.processed_at = datetime.now(datetime.UTC)
            await self.session.flush()
