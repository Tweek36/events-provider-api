import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
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
        self.events_provider_client = EventsProviderClient(
            settings.EVENTS_PROVIDER_API_URL, settings.X_API_KEY
        )
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

            event = None
            logger.info("events_fetching_started")
            async for response in self.events_provider_client.fetch_events(changed_at):
                logger.info(
                    "events_page_fetched",
                    next=response.next,
                    events_count=len(response.results),
                )
                for event in response.results:
                    if not await self.place_repository.get_by_id(event.place.id):
                        await self.place_repository.create(event.place.model_dump())
                    if not await self.event_repository.get_by_id(event.id):
                        await self.event_repository.create(
                            {
                                **event.model_dump(exclude={"place"}),
                                "place_id": event.place.id,
                            }
                        )

            logger.info("events_fetching_completed")

            if event:
                await self.metadata_repository.update_last_changed_at(
                    event.changed_at.strftime("%Y-%m-%d")
                )

            await self.metadata_repository.update_sync_status("synced")
            await self.metadata_repository.update_last_sync_time(
                datetime.datetime.now(datetime.UTC)
            )
            logger.info("sync_completed", status="synced")
        except Exception as e:
            await self.session.rollback()
            await self.metadata_repository.update_sync_status("unsynced")
            logger.exception(
                "sync_failed",
                error_type=type(e).__name__,
                error_msg=str(e),
                metadata=Metadata.model_validate(
                    await self.metadata_repository.get_metadata()
                ).model_dump(exclude={"key"}),
            )
            logger.info("sync_finished_with_error", status="unsynced")
        return (await self.metadata_repository.get_metadata()).sync_status
