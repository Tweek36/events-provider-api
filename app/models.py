import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import UUID, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.types import EventStatus, SyncStatusType


class MetadataModel(Base):
    __tablename__ = "metadata"

    key = mapped_column(
        String,
        primary_key=True,
        index=True,
        default="metadata",
        server_default="metadata",
    )

    last_sync_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=None, nullable=True
    )
    last_changed_at: Mapped[str] = mapped_column(
        String,
        server_default="2000-01-01",
        nullable=False,
    )
    sync_status: Mapped[SyncStatusType] = mapped_column(
        String, server_default="unsynced", nullable=False
    )


class Place(Base):
    __tablename__ = "places"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, index=True)

    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    name: Mapped[str] = mapped_column(String)
    city: Mapped[str] = mapped_column(String)
    address: Mapped[str] = mapped_column(String)
    seats_pattern: Mapped[str] = mapped_column(String)

    events: Mapped[list["Event"]] = relationship(
        back_populates="place", lazy="selectin"
    )


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, index=True)

    place_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("places.id", ondelete="CASCADE"), index=True
    )

    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    name: Mapped[str] = mapped_column(String)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    registration_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[EventStatus] = mapped_column(String)
    number_of_visitors: Mapped[int] = mapped_column(Integer)
    status_changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    place: Mapped["Place"] = relationship(back_populates="events")

    tickets: Mapped[list["Ticket"]] = relationship(
        back_populates="event", lazy="selectin"
    )


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, index=True)

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("events.id", ondelete="CASCADE"), index=True
    )
    seat: Mapped[str] = mapped_column(String)

    event: Mapped["Event"] = relationship(back_populates="tickets")
