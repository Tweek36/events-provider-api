from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
from app.database import get_session
from app.exceptions import (
    EventNotFound,
    RegistrationClosed,
    SeatUnavailable,
    SeatAlreadyTaken,
    TicketNotFound,
    EventAlreadyOccurred,
    EventsProviderError,
)
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
    except EventNotFound:
        raise HTTPException(status_code=404, detail="Event not found")
    except (RegistrationClosed, SeatUnavailable, SeatAlreadyTaken) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EventsProviderError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
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
    except TicketNotFound:
        raise HTTPException(status_code=404, detail="Ticket not found")
    except EventAlreadyOccurred as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EventsProviderError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.error(
            "ticket_deletion_failed",
            error_type=type(e).__name__,
            error_msg=str(e),
            ticket_id=ticket_id,
        )
        raise e
