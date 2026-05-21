import asyncio
import logging

from celery import Celery

from app.celery_app import celery_app, daily_sync

logger = logging.getLogger(__name__)


class CeleryWorker:
    def __init__(self, celery_app: Celery):
        self.celery_app = celery_app
        self._worker_task: asyncio.Task | None = None
        self._beat_task: asyncio.Task | None = None

    async def start(self):
        """Запуск Celery worker и beat в фоновом режиме"""
        logger.info("Starting Celery worker and beat...")

        # Запускаем daily_sync сразу при старте
        daily_sync.delay()
        logger.info("Daily sync task triggered on startup")

        # Запускаем worker в отдельном потоке
        self._worker_task = asyncio.create_task(self._run_worker())

        # Запускаем beat в отдельном потоке
        self._beat_task = asyncio.create_task(self._run_beat())

        logger.info("Celery worker and beat started")

    async def _run_worker(self):
        """Запуск Celery worker"""
        try:
            # Запускаем worker в отдельном потоке, чтобы не блокировать event loop
            await asyncio.to_thread(
                self.celery_app.worker_main,
                argv=["worker", "--loglevel=info", "--pool=solo"],
            )
        except Exception as e:
            logger.error("Celery worker error: %s", e)

    async def _run_beat(self):
        """Запуск Celery beat"""
        try:
            # Запускаем beat в отдельном потоке
            await asyncio.to_thread(self.celery_app.start, argv=["beat", "--loglevel=info"])
        except Exception as e:
            logger.error("Celery beat error: %s", e)

    async def stop(self):
        """Остановка Celery worker и beat"""
        logger.info("Stopping Celery worker and beat...")

        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        if self._beat_task:
            self._beat_task.cancel()
            try:
                await self._beat_task
            except asyncio.CancelledError:
                pass

        logger.info("Celery worker and beat stopped")


celery_worker = CeleryWorker(celery_app)
