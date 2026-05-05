from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.services.sync import SyncService

router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.post("/trigger")
async def trigger(
    session: AsyncSession = Depends(get_session),
):
    status = await SyncService(session).trigger()
    return {"status": status}
