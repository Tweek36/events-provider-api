from sqlalchemy.ext.asyncio import AsyncSession
from app.models import MetadataModel
from datetime import datetime
from app.types import SyncStatusType


class MetadataRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._data = None

    async def _fetch_metadata(self) -> None:
        self._data = await self.session.get(MetadataModel, "metadata")
        if not self._data:
            self._data = MetadataModel(
                key="metadata",
                last_sync_time=None,
                last_changed_at="2000-01-01",
                sync_status="unsynced",
            )
            self.session.add(self._data)
            await self.session.flush()

    async def get_metadata(self) -> MetadataModel:
        if not self._data:
            await self._fetch_metadata()
        return self._data

    async def update_sync_status(self, sync_status: SyncStatusType) -> None:
        (await self.get_metadata()).sync_status = sync_status
        await self.session.flush()

    async def update_last_sync_time(self, sync_time: datetime) -> None:
        (await self.get_metadata()).last_sync_time = sync_time
        await self.session.flush()

    async def update_last_changed_at(self, changed_at: datetime) -> None:
        (await self.get_metadata()).last_changed_at = changed_at
        await self.session.flush()
