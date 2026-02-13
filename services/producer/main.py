from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, status

from redis import RedisError
from shared_lib.config import REDIS_URL, STREAM_NAME
from shared_lib.model import ReadingInput, ReadingOutput, ReadingStatus

# This run on import, it is better to place this in a closure
app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, None]:
    # 1. CONFIGURATION: This runs ONCE when the process starts.
    # We create the connection pool here.
    async with redis.from_url(REDIS_URL, decode_responses=True) as r:
        app.state.redis = r
        # The app "pauses" here and handles all incoming requests
        yield


@app.post(
    "/readings", response_model=ReadingOutput, status_code=status.HTTP_201_CREATED
)
async def create_reading(reading: ReadingInput) -> ReadingOutput:
    try:
        stream_id = await app.state.redis.xadd(STREAM_NAME, reading.model_dump_json())
    except RedisError as e:
        # 'from e' links the Redis error to the HTTP error in the traceback
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from e

    return ReadingOutput(
        status=ReadingStatus.ACCEPTED,
        stream_id=stream_id,
    )


@app.get("/health")
async def health_check():
    """Returns 200 if the service is alive."""
    # can check number of failed attempts
    # missing power reading
    return {"status": "healthy"}
