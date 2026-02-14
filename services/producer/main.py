from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Request, status
from redis import RedisError

from shared_lib.config import REDIS_URL, STREAM_NAME
from shared_lib.logger import logger
from shared_lib.model import (
    HEALTH_CHECK_DICT,
    ReadingInput,
    ReadingOutput,
    ReadingStatus,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, None]:
    # 1. CONFIGURATION: This runs ONCE when the process starts.
    # We create the connection pool here.
    async with redis.from_url(REDIS_URL, decode_responses=True) as r:
        app.state.redis = r
        # The app "pauses" here and handles all incoming requests
        yield


# This run on import, it is better to place this in a closure
app = FastAPI(lifespan=lifespan)


@app.post(
    "/readings", response_model=ReadingOutput, status_code=status.HTTP_201_CREATED
)
async def create_reading(reading: ReadingInput, request: Request) -> ReadingOutput:
    client_ip = request.client.host if request.client else "unknown"
    logger.debug("%s: Received new reading: %s", client_ip, reading)
    try:
        stream_id = await app.state.redis.xadd(STREAM_NAME, reading.model_dump())
    except RedisError as e:
        logger.exception("%s: Redis error occurred for %s", client_ip, reading)
        # 'from e' links the Redis error to the HTTP error in the traceback
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from e
    logger.debug("%s generated stream id for %s , %s", client_ip, reading, stream_id)
    return ReadingOutput(
        status=ReadingStatus.ACCEPTED,
        stream_id=stream_id,
    )


@app.get("/health")
async def health_check(request: Request) -> dict[str, str]:
    """Returns 200 if the service is alive."""
    client_ip = request.client.host if request.client else "unknown"
    logger.debug("%s: health check", client_ip)
    return HEALTH_CHECK_DICT
