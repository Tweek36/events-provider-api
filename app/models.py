import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import UUID, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.types import EventStatus, OutboxStatus, SyncStatusType, TicketStatus


class MetadataModel(Base):
    __tablename__ = "metadata"

    key = mapped_column(
        String,
        primary_key=True,
        index=True,
        default="metadata",
        server_default="metadata",
    )

    last_sync_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=None, nullable=True)
    last_changed_at: Mapped[str] = mapped_column(
        String,
        server_default="2000-01-01",
        nullable=False,
    )
    sync_status: Mapped[SyncStatusType] = mapped_column(String, server_default="unsynced", nullable=False)


class Place(Base):
    __tablename__ = "places"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, index=True)

    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    name: Mapped[str] = mapped_column(String)
    city: Mapped[str] = mapped_column(String)
    address: Mapped[str] = mapped_column(String)
    seats_pattern: Mapped[str] = mapped_column(String)

    events: Mapped[list["Event"]] = relationship(back_populates="place", lazy="selectin")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, index=True)

    place_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("places.id", ondelete="CASCADE"), index=True)

    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    name: Mapped[str] = mapped_column(String)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    registration_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[EventStatus] = mapped_column(String)
    number_of_visitors: Mapped[int] = mapped_column(Integer)
    status_changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    place: Mapped["Place"] = relationship(back_populates="events")

    tickets: Mapped[list["Ticket"]] = relationship(back_populates="event", lazy="selectin")


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, index=True)

    event_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("events.id", ondelete="CASCADE"), index=True)
    seat: Mapped[str] = mapped_column(String)
    status: Mapped[TicketStatus] = mapped_column(String, server_default=TicketStatus.ACTIVE, nullable=False)

    event: Mapped["Event"] = relationship(back_populates="tickets")


class OutboxEvent(Base):
    __tablename__ = "outbox"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, index=True, default=uuid.uuid4)

    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict] = mapped_column(type_=sa.JSON, nullable=False)
    status: Mapped[OutboxStatus] = mapped_column(String(20), nullable=False, default=OutboxStatus.PENDING)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.now)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, index=True, default=uuid.uuid4)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    ticket_id: Mapped[uuid.UUID] = mapped_column(UUID, nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now, index=True
    )
