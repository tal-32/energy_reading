from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Formatting to ISO 8601
DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


class ReadingStatus(StrEnum):
    ACCEPTED = "accepted"


HEALTH_CHECK_DICT = {"status": "healthy"}


class ReadingInput(BaseModel):
    site_id: str = Field(min_length=1)  # Cannot be ""
    device_id: str = Field(min_length=1)  # Cannot be ""
    power_reading: float
    timestamp: str  # validate datetime
    # version: Literal[1] = 1

    # immutable
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp_format(cls, v: str) -> str:
        try:
            new = datetime.strptime(v, DATE_FORMAT)
        except ValueError as err:
            raise ValueError(
                "Timestamp must be in format YYYY-MM-DDTHH:MM:SSZ"
            ) from err

        now = datetime.now(new.tzinfo) if new.tzinfo else datetime.now()
        if new > now:
            raise ValueError("datetime is in the future")
        return v


class StreamData(BaseModel):
    data: ReadingInput


class ReadingOutput(BaseModel):
    status: ReadingStatus
    stream_id: str = Field(min_length=1)  # Cannot be ""
    # version: Literal[1] = 1

    # immutable
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)
