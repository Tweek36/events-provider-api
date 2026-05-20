import hashlib
import json
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import IdempotencyKey
from app.repositories.base import BaseRepository


class IdempotencyRepository(BaseRepository[IdempotencyKey]):
    """Репозиторий для работы с ключами идемпотентности."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, IdempotencyKey)

    @staticmethod
    def compute_request_hash(request_data: dict) -> str:
        """
        Вычислить хэш запроса для проверки конфликтов.

        Args:
            request_data: Данные запроса

        Returns:
            str: SHA-256 хэш данных запроса
        """

        def default_serializer(obj):
            """Сериализатор для объектов, не поддерживаемых JSON по умолчанию."""
            if isinstance(obj, uuid.UUID):
                return str(obj)
            raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

        # Сортируем ключи для стабильного хэша
        sorted_data = json.dumps(request_data, sort_keys=True, default=default_serializer)
        return hashlib.sha256(sorted_data.encode()).hexdigest()

    async def get_by_key(self, idempotency_key: str) -> IdempotencyKey | None:
        """
        Получить запись по ключу идемпотентности.

        Args:
            idempotency_key: Ключ идемпотентности

        Returns:
            Optional[IdempotencyKey]: Запись или None
        """
        stmt = select(IdempotencyKey).where(IdempotencyKey.idempotency_key == idempotency_key)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_key(
        self,
        idempotency_key: str,
        ticket_id: uuid.UUID,
        request_data: dict,
    ) -> IdempotencyKey:
        """
        Создать новую запись ключа идемпотентности.

        Args:
            idempotency_key: Ключ идемпотентности
            ticket_id: ID созданного билета
            request_data: Данные запроса для вычисления хэша

        Returns:
            IdempotencyKey: Созданная запись
        """
        request_hash = self.compute_request_hash(request_data)

        key_record = IdempotencyKey(
            idempotency_key=idempotency_key,
            ticket_id=ticket_id,
            request_hash=request_hash,
        )

        self.session.add(key_record)
        await self.session.flush()
        return key_record
