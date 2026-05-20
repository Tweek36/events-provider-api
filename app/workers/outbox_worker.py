import asyncio

import httpx
import structlog

from app.client.capashino import CapashinoClient
from app.database import AsyncSessionLocal
from app.models import Ticket
from app.repositories.idempotency import IdempotencyRepository
from app.repositories.outbox import OutboxRepository
from app.services.tickets import TicketsService
from app.settings import settings

logger = structlog.get_logger()


class OutboxWorker:
    """Воркер для обработки событий из outbox."""

    def __init__(self):
        self.is_running = False
        self.task = None

    async def process_events(self) -> None:
        """Основной цикл обработки событий."""
        self.is_running = True
        logger.info("outbox_worker_started")

        while self.is_running:
            try:
                async with AsyncSessionLocal() as session:
                    outbox_repo = OutboxRepository(session)

                    # Получить pending события
                    events = await outbox_repo.get_pending_events(limit=100)

                    if events:
                        logger.info("outbox_worker_processing", event_count=len(events))

                    for event in events:
                        try:
                            # Проверить лимит попыток
                            if event.attempts >= settings.OUTBOX_MAX_ATTEMPTS:
                                logger.error(
                                    "outbox_event_max_attempts_reached",
                                    event_id=str(event.id),
                                    event_type=event.event_type,
                                    attempts=event.attempts,
                                )
                                await outbox_repo.mark_as_failed(event.id)
                                await session.commit()
                                continue

                            # Обработка события ticket_purchased
                            if event.event_type == "ticket_purchased":
                                ticket_id = event.payload.get("ticket_id")

                                if not ticket_id:
                                    logger.error(
                                        "outbox_event_missing_ticket_id",
                                        event_id=str(event.id),
                                    )
                                    await outbox_repo.mark_as_failed(event.id)
                                    await session.commit()
                                    continue

                                ticket_service = TicketsService(session)
                                ticket = await ticket_service.ticket_repository.get_by_id(
                                    ticket_id, selectin=[Ticket.event]
                                )

                                if not ticket:
                                    logger.error(
                                        "outbox_event_ticket_not_found",
                                        event_id=str(event.id),
                                        ticket_id=str(ticket_id),
                                    )
                                    await outbox_repo.mark_as_failed(event.id)
                                    await session.commit()
                                    continue

                                # Отправить уведомление через Capashino
                                capashino_client = CapashinoClient(
                                    str(settings.CAPASHINO_BASE_URL),
                                    settings.CAPASHINO_API_KEY,
                                )

                                message = f"Вы успешно зарегистрированы на мероприятие - {ticket.event.name}"
                                idempotency_repository = IdempotencyRepository(session)
                                idempotency_key = await idempotency_repository.get_by_ticket_id(ticket_id)

                                idempotency_key_str = (
                                    idempotency_key.idempotency_key if idempotency_key else f"ticket_{ticket_id}"
                                )

                                try:
                                    await capashino_client.send_notification(
                                        message=message,
                                        reference_id=ticket_id,
                                        idempotency_key=idempotency_key_str,
                                    )

                                    # Успешная отправка
                                    await outbox_repo.mark_as_sent(event.id)
                                    await session.commit()

                                except httpx.HTTPStatusError as e:
                                    # 4xx ошибки (кроме 409) - не повторять
                                    if 400 <= e.response.status_code < 500 and e.response.status_code != 409:
                                        logger.error(
                                            "outbox_event_client_error",
                                            event_id=str(event.id),
                                            status_code=e.response.status_code,
                                        )
                                        await outbox_repo.mark_as_failed(event.id)
                                        await session.commit()
                                    else:
                                        # 5xx или сетевые ошибки - повторить
                                        await outbox_repo.increment_attempts(event.id)
                                        await session.commit()

                                except (
                                    httpx.TimeoutException,
                                    httpx.NetworkError,
                                ) as e:
                                    # Сетевые ошибки - повторить
                                    logger.warning(
                                        "outbox_event_network_error",
                                        event_id=str(event.id),
                                        error_type=type(e).__name__,
                                    )
                                    await outbox_repo.increment_attempts(event.id)
                                    await session.commit()
                            else:
                                logger.warning(
                                    "outbox_event_unknown_type",
                                    event_id=str(event.id),
                                    event_type=event.event_type,
                                )
                                await outbox_repo.mark_as_failed(event.id)
                                await session.commit()

                        except Exception as e:
                            logger.error(
                                "outbox_event_processing_error",
                                event_id=str(event.id),
                                error_type=type(e).__name__,
                                error_msg=str(e),
                            )
                            await outbox_repo.increment_attempts(event.id)
                            await session.commit()

                # Ждать перед следующей итерацией
                await asyncio.sleep(settings.OUTBOX_WORKER_INTERVAL)

            except Exception as e:
                logger.error("outbox_worker_error", error_type=type(e).__name__, error_msg=str(e))
                await asyncio.sleep(settings.OUTBOX_WORKER_INTERVAL)

    async def start(self) -> None:
        """Запустить воркер."""
        if not self.task or self.task.done():
            self.task = asyncio.create_task(self.process_events())

    async def stop(self) -> None:
        """Остановить воркер."""
        logger.info("outbox_worker_stopping")
        self.is_running = False
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("outbox_worker_stopped")


# Глобальный экземпляр воркера
outbox_worker = OutboxWorker()
