import asyncio
import json
import os
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from enum import StrEnum
from typing import Any

import redis.asyncio as redis
from fastapi import FastAPI
from pydantic import ValidationError
from redis.exceptions import RedisError, ResponseError

# Assuming these are shared with your producer
from shared_lib.config import GROUP_NAME, REDIS_URL, STREAM_NAME
from shared_lib.logger import logger
from shared_lib.model import HEALTH_CHECK_DICT, ReadingInput

# Constants for this service
CONSUMER_NAME = os.getenv("HOSTNAME", f"default_consumer-{str(uuid.uuid4())[:8]}")


class StreamCreateStrategy(StrEnum):
    """IDs used when calling xgroup_create."""

    FROM_START = "0"  # Start from the oldest message available
    FROM_LATEST = "$"  # Start from messages arriving AFTER group creation


class StreamReadMode(StrEnum):
    """IDs used when calling xreadgroup."""

    NEW_UNDELIVERED = ">"  # Give me messages no one else has touched
    MY_PENDING = "0"  # Give me messages I claimed but haven't ACKnowledged


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, None]:
    # 1. Setup Redis Connection
    async with redis.from_url(REDIS_URL, decode_responses=True) as r:
        app.state.redis = r

        # 2. Ensure Consumer Group exists
        try:
            # MKSTREAM creates the stream if it doesn't exist
            await r.xgroup_create(
                STREAM_NAME,
                GROUP_NAME,
                id=StreamCreateStrategy.FROM_LATEST,
                mkstream=True,
            )
        except ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.info("Consumer group %s already exists", GROUP_NAME)
            else:
                raise e
        logger.info("Created consumer group: %s", GROUP_NAME)

        # 3. Start the background consumer task
        consumer_task = asyncio.create_task(consume_stream(app))

        yield

        # 4. Cleanup: Cancel the consumer task on shutdown
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            logger.info("Consumer task stopped.")


app = FastAPI(lifespan=lifespan)


async def consume_stream(app: FastAPI) -> None:
    """
    Background worker that reads from Redis Stream and stores data by site_id.
    """
    r = app.state.redis
    logger.info("Starting stream consumer...")

    while True:
        try:
            # Read new messages
            # (">" means messages not yet delivered to other consumers)
            # count=10: process in batches for efficiency
            # block=5000: wait up to 5 seconds if stream is empty
            streams = await r.xreadgroup(
                GROUP_NAME,
                CONSUMER_NAME,
                {STREAM_NAME: StreamReadMode.NEW_UNDELIVERED},
                count=10,
                block=5000,
            )
        except Exception as e:
            logger.error("Error in consumer loop: %s", e)
            await asyncio.sleep(2)  # Prevent rapid-fire crashing
            continue

        for _stream, messages in streams:
            for message_id, payload in messages:
                try:
                    # Validate and parse the raw_data into a ReadingInput object
                    reading = ReadingInput.model_validate(payload)
                except ValidationError as e:
                    logger.warning(
                        "Message %s from stream %s failed Pydantic validation: %s "
                        "- Data: %s",
                        message_id,
                        STREAM_NAME,
                        e,
                        payload,
                    )
                    # Acknowledge invalid messages to prevent reprocessing bad data
                    await r.xack(STREAM_NAME, GROUP_NAME, message_id)
                    continue

                site_id = reading.site_id

                # Store in a Redis List specific to the site
                storage_key = f"readings:site:{site_id}"

                try:
                    # LPUSH adds to the head, keeping latest readings first
                    # LTRIM keeps only the last 1000 readings
                    #   (optional, for memory safety)
                    # LPUSH the string, not the dict
                    await r.lpush(storage_key, json.dumps(payload))
                    await r.ltrim(storage_key, 0, 999)
                except redis.RedisError as e:
                    logger.error(
                        "Error processing message %s: %s - Data: %s",
                        message_id,
                        e,
                        payload,
                    )
                    # If any other error, still acknowledge to prevent stuck messages.\
                    await r.xack(STREAM_NAME, GROUP_NAME, message_id)
                    continue

                # Acknowledge the message
                await r.xack(STREAM_NAME, GROUP_NAME, message_id)
                logger.debug(
                    "Processed and ACKed message %s for site %s",
                    message_id,
                    site_id,
                )


@app.get("/sites/{site_id}/readings")
async def get_site_readings(site_id: str) -> list[Any]:
    """Returns all stored readings for the given site."""
    storage_key = f"readings:site:{site_id}"
    try:
        # Retrieve all items from the list
        readings = await app.state.redis.lrange(storage_key, 0, -1)
        # Parse strings back to JSON objects
        return [json.loads(r) for r in readings]
    except RedisError as e:
        logger.error("Failed to fetch readings for %s: %s", site_id, e)
        return []


@app.get("/health")
async def health_check() -> dict[str, str]:
    return HEALTH_CHECK_DICT
