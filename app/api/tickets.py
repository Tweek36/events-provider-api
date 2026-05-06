from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
from app.database import get_session
from app.schemes.tickets import TicketsRequestBody
from app.services.tickets import TicketsService
import uuid

router = APIRouter(prefix="/api/tickets", tags=["tickets"])
logger = structlog.get_logger()


@router.post("", status_code=201)
async def register(
    body: TicketsRequestBody,
    session: AsyncSession = Depends(get_session),
):
    try:
        return await TicketsService(session).register(body)
    except Exception as e:
        logger.error(
            "ticket_creation_failed_with_data",
            error_type=type(e).__name__,
            error_msg=str(e),
            event_id=body.event_id,
        )
        raise e


@router.delete("/{ticket_id}")
async def unregister(
    ticket_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    try:
        return await TicketsService(session).unregister(ticket_id)
    except Exception as e:
        logger.error(
            "ticket_deletion_failed",
            error_type=type(e).__name__,
            error_msg=str(e),
            ticket_id=ticket_id,
        )
        raise e
