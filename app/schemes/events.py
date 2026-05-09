import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.types import EventStatus


class Place(BaseModel):
    id: uuid.UUID = Field(..., description="Уникальный идентификатор места")
    name: str = Field(..., description="Название места")
    city: str = Field(..., description="Город, в котором находится место")
    address: str = Field(..., description="Адрес места")

    model_config = ConfigDict(from_attributes=True)


class Event(BaseModel):
    id: uuid.UUID = Field(..., description="Уникальный идентификатор события")
    name: str = Field(..., description="Название события")
    place: Place = Field(..., description="Место проведения события")
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

    model_config = ConfigDict(from_attributes=True)


class EventsResponse(BaseModel):
    count: int = Field(
        ..., description="Общее количество событий, доступных для получения"
    )
    next: HttpUrl | None = Field(
        None, description="URL для получения следующей страницы событий"
    )
    previous: HttpUrl | None = Field(
        None, description="URL для получения предыдущей страницы событий"
    )
    results: list[Event] = Field(..., description="Список событий")


class PlaceWithPattern(Place):
    seats_pattern: str = Field(
        ...,
        description="Строка, представляющая схему рассадки в месте проведения события",
        pattern=r"^[A-Z]\d+-\d+(,[A-Z]\d+-\d+)*$",
    )


class EventResponse(Event):
    place: PlaceWithPattern = Field(..., description="Место проведения события")


class EventSeatsResponse(BaseModel):
    event_id: uuid.UUID = Field(..., description="Уникальный идентификатор события")
    available_seats: list[str] = Field(
        ..., description="Список доступных мест для регистрации на событие"
    )
