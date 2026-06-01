from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Ticket
from app.repositories.base import BaseRepository
from app.types import TicketStatus


class TicketRepository(BaseRepository[Ticket]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=Ticket)

    async def count_all(self) -> int:
        """Подсчитать общее количество билетов в БД."""
        result = await self.session.execute(select(func.count()).select_from(Ticket))
        return result.scalar_one()

    async def count_cancelled(self) -> int:
        """Подсчитать количество отменённых билетов."""
        result = await self.session.execute(
            select(func.count()).select_from(Ticket).where(Ticket.status == TicketStatus.CANCELLED)
        )
        return result.scalar_one()
