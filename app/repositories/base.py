from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class BaseRepository[ModelType]:
    def __init__(self, session: AsyncSession, model: type[ModelType]):
        self.session = session
        self.model = model

    async def get_by_id(self, id: Any, selectin: list | None = None) -> ModelType | None:
        stmt = select(self.model).where(self.model.id == id)
        if selectin:
            stmt = stmt.options(*[selectinload(i) for i in selectin])
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, obj_data: dict) -> ModelType:
        db_obj = self.model(**obj_data)
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def update(self, id: Any, update_data: dict) -> ModelType | None:
        obj = await self.get_by_id(id)
        if not obj:
            return None
        for key, value in update_data.items():
            setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: Any) -> bool:
        obj = await self.get_by_id(id)
        if not obj:
            return False
        await self.session.delete(obj)
        await self.session.flush()
        return True

    async def bulk_upsert(
        self,
        objects: list[dict],
        batch_size: int = 1000,
    ) -> None:
        """
        Массовая вставка записей с игнорированием дубликатов.
        Использует INSERT ... ON CONFLICT DO NOTHING для PostgreSQL.

        Args:
            objects: Список словарей с данными для вставки
            batch_size: Размер батча для вставки (по умолчанию 1000)
        """
        if not objects:
            return

        # Обработка батчами
        for i in range(0, len(objects), batch_size):
            batch = objects[i : i + batch_size]

            # INSERT ... ON CONFLICT DO NOTHING
            stmt = insert(self.model).values(batch)
            stmt = stmt.on_conflict_do_nothing(index_elements=["id"])

            await self.session.execute(stmt)
