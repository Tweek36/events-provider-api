from app.models import Place
from app.repositories.base import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession


class PlaceRepository(BaseRepository[Place]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=Place)
