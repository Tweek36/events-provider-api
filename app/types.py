import datetime
import re
from typing import Literal, Any
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

SyncStatusType = Literal["synced", "unsynced", "syncing"]


class DateStr(str):
    def __new__(cls, value: str):
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", value):
            raise ValueError("Invalid format")
        try:
            datetime.datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid date")
        return super().__new__(cls, value)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.str_schema(),
        )

    @classmethod
    def validate(cls, value: str) -> "DateStr":
        return cls(value)
