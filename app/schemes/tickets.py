import uuid

from pydantic import BaseModel, EmailStr, Field


class TicketsRequestBody(BaseModel):
    event_id: uuid.UUID = Field(..., description="Уникальный идентификатор события")
    first_name: str = Field(..., description="Имя посетителя", min_length=1)
    last_name: str = Field(..., description="Фамилия посетителя", min_length=1)
    email: EmailStr = Field(..., description="Электронная почта посетителя")
    seat: str = Field(
        ...,
        description="Место в зале",
        pattern=r"^[A-Z]\d+$",
    )
