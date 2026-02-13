from enum import StrEnum

from pydantic import BaseModel


def validate_redis_id(v: str) -> str:
    # Basic check: Redis IDs usually contain a hyphen
    if "-" not in v:
        raise ValueError(
            "Invalid Redis Stream ID format. Expected 'timestamp-sequence'."
        )
    return v


class ReadingStatus(StrEnum):
    ACCEPTED = "accepted"


class ReadingInput(BaseModel):
    site_id: str
    device_id: str
    power_reading: float
    timestamp: str  # validate datetime
    # version: Literal[1] = 1


class ReadingOutput(BaseModel):
    status: ReadingStatus
    stream_id: str
    # version: Literal[1] = 1
