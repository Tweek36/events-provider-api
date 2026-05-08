from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl
from app.types import SyncStatusType, EventStatus


class Place(BaseModel):
    id: uuid.UUID = Field(..., description="Уникальный идентификатор места")
    changed_at: datetime = Field(
        ..., description="Дата и время последнего изменения места в формате ISO 8601"
    )
    created_at: datetime = Field(
        ..., description="Дата и время создания места в формате ISO 8601"
    )
    name: str = Field(..., description="Название места")
    city: str = Field(..., description="Город, в котором находится место")
    address: str = Field(..., description="Адрес места")
    seats_pattern: str = Field(
        ...,
        description="Строка, описывающая схему рассадки в формате '\{секция\}\{начало\}-\{конец\},\{секция\}\{начало\}-\{конец\},...', например 'A1-10,B1-20'",
        pattern=r"^[A-Z]\d+-\d+(,[A-Z]\d+-\d+)*$",
    )

    model_config = ConfigDict(from_attributes=True)


class Event(BaseModel):
    id: uuid.UUID = Field(..., description="Уникальный идентификатор события")
    place: Place = Field(..., description="Место проведения события")
    changed_at: datetime = Field(
        ..., description="Дата и время последнего изменения события в формате ISO 8601"
    )
    created_at: datetime = Field(
        ..., description="Дата и время создания события в формате ISO 8601"
    )
    name: str = Field(..., description="Название события")
    event_time: datetime = Field(
        ..., description="Дата и время проведения события в формате ISO 8601"
    )
    registration_deadline: datetime = Field(
        ...,
        description="Дата и время окончания регистрации на событие в формате ISO 8601",
    )
    status: EventStatus = Field(
        ..., description="Статус события: new, published, cancelled, finished"
    )
    number_of_visitors: int = Field(
        ..., description="Количество посетителей, зарегистрированных на событие"
    )
    status_changed_at: datetime = Field(
        ...,
        description="Дата и время последнего изменения статуса события в формате ISO 8601",
    )

    model_config = ConfigDict(from_attributes=True)


class EventsResponse(BaseModel):
    next: HttpUrl | None = Field(
        None, description="URL для получения следующей страницы событий"
    )
    previous: HttpUrl | None = Field(
        None, description="URL для получения предыдущей страницы событий"
    )
    results: list[Event] = Field(..., description="Список событий")

    model_config = ConfigDict(from_attributes=True)


class SeatsResponse(BaseModel):
    seats: list[str] = Field(
        ...,
        description="Список доступных мест в формате '\{секция\}\{номер\}', например 'A1', 'B15' и т.д.",
    )

    model_config = ConfigDict(from_attributes=True)


class RegisterRequest(BaseModel):
    first_name: str = Field(..., description="Имя посетителя")
    last_name: str = Field(..., description="Фамилия посетителя")
    seat: str = Field(
        ...,
        description="Выбранное место в формате '\{секция\}\{номер\}', например 'A1', 'B15' и т.д.",
        pattern=r"^[A-Z]\d+$",
    )
    email: EmailStr = Field(..., description="Электронная почта посетителя")

    model_config = ConfigDict(from_attributes=True)


class RegisterResponse(BaseModel):
    ticket_id: uuid.UUID = Field(
        ..., description="Уникальный идентификатор зарегистрированного билета"
    )

    model_config = ConfigDict(from_attributes=True)


class UnregisterRequest(BaseModel):
    ticket_id: uuid.UUID = Field(
        ..., description="Уникальный идентификатор зарегистрированного билета"
    )

    model_config = ConfigDict(from_attributes=True)


class UnregisterResponse(BaseModel):
    success: bool = Field(..., description="Статус успешности отмены регистрации")

    model_config = ConfigDict(from_attributes=True)


class Metadata(BaseModel):
    last_sync_time: datetime | None = Field(
        None,
        description="Дата и время последней синхронизации данных в формате ISO 8601",
    )
    last_changed_at: str | None = Field(
        None, description="Дата последнего изменения данных в формате 'YYYY-MM-DD'"
    )
    sync_status: SyncStatusType = Field(
        ...,
        description="Статус синхронизации данных, например 'unsynced', 'syncing', 'synced'",
    )

    model_config = ConfigDict(from_attributes=True)
