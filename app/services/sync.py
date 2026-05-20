import datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.client.events_provider import EventsProviderClient
from app.repositories.event import EventRepository
from app.repositories.metadata import MetadataRepository
from app.repositories.place import PlaceRepository
from app.schemes.client import Metadata
from app.settings import settings
from app.types import SyncStatusType

logger = structlog.get_logger()


class SyncService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.events_provider_client = EventsProviderClient(settings.EVENTS_PROVIDER_API_URL, settings.X_API_KEY)
        self.metadata_repository = MetadataRepository(session)
        self.event_repository = EventRepository(session)
        self.place_repository = PlaceRepository(session)

    async def trigger(self) -> SyncStatusType:
        try:
            logger.info("sync_started")
            await self.metadata_repository.update_sync_status("syncing")
            await self.session.commit()

            metadata = await self.metadata_repository.get_metadata()
            changed_at = metadata.last_changed_at

            # Накопители для батчей
            places_batch = []
            events_batch = []
            last_event = None

            logger.info("events_fetching_started")
            async for response in self.events_provider_client.fetch_events(changed_at):
                for event in response.results:
                    # Накапливаем данные для батчевой вставки
                    places_batch.append(event.place.model_dump())
                    events_batch.append(
                        {
                            **event.model_dump(exclude={"place"}),
                            "place_id": event.place.id,
                        }
                    )
                    last_event = event

                    # Вставляем батчами по 1000 записей
                    if len(places_batch) >= 1000:
                        await self.place_repository.bulk_upsert(places_batch)
                        await self.event_repository.bulk_upsert(events_batch)
                        places_batch.clear()
                        events_batch.clear()

            # Вставляем остатки
            if places_batch:
                await self.place_repository.bulk_upsert(places_batch)
                await self.event_repository.bulk_upsert(events_batch)

            logger.info("events_fetching_completed")

            # Обновляем метаданные одним запросом
            if last_event:
                await self.metadata_repository.bulk_update_metadata(
                    {
                        "sync_status": "synced",
                        "last_sync_time": datetime.datetime.now(datetime.UTC),
                        "last_changed_at": last_event.changed_at.strftime("%Y-%m-%d"),
                    }
                )
            else:
                await self.metadata_repository.update_sync_status("synced")
                await self.metadata_repository.update_last_sync_time(datetime.datetime.now(datetime.UTC))

            # Один коммит в конце
            await self.session.commit()
            logger.info("sync_completed", status="synced")
        except Exception as e:
            await self.session.rollback()
            await self.metadata_repository.update_sync_status("unsynced")
            await self.session.commit()
            logger.exception(
                "sync_failed",
                error_type=type(e).__name__,
                error_msg=str(e),
                metadata=Metadata.model_validate(await self.metadata_repository.get_metadata()).model_dump(
                    exclude={"key"}
                ),
                response=response.model_dump() if last_event else None,
            )
            logger.info("sync_finished_with_error", status="unsynced")
        return (await self.metadata_repository.get_metadata()).sync_status
