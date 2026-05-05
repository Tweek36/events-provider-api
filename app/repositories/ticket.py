from app.models import Ticket
from app.repositories.base import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession


class TicketRepository(BaseRepository[Ticket]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=Ticket)
