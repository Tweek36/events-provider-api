from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Ticket
from app.repositories.base import BaseRepository


class TicketRepository(BaseRepository[Ticket]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=Ticket)
