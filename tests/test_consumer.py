import asyncio
import json
from unittest.mock import ANY, AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient, codes
from redis.exceptions import RedisError

# Adjust import based on your actual file
from services.consumer.main import app, consume_stream
from shared_lib.model import HEALTH_CHECK_DICT, ReadingInput

MOCK_SITE_ID = "site123"
MOCK_STREAM_ID = "1705314600000-0"
MOCK_PAYLOAD = ReadingInput(
    site_id=MOCK_SITE_ID,
    device_id="dev456",
    power_reading=50.5,
    timestamp="2024-01-15T10:30:00Z",
).model_dump()

# --- API Tests ---


@pytest.mark.asyncio
async def test_health_check_success() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/health")

    assert response.status_code == codes.OK
    assert response.json() == HEALTH_CHECK_DICT


@pytest.mark.asyncio
async def test_get_site_readings_success() -> None:
    mock_redis = AsyncMock()
    # Redis returns strings in decode_responses=True mode
    mock_redis.lrange.return_value = [json.dumps(MOCK_PAYLOAD)]
    app.state.redis = mock_redis

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get(f"/sites/{MOCK_SITE_ID}/readings")

    assert response.status_code == codes.OK
    assert response.json() == [MOCK_PAYLOAD]
    mock_redis.lrange.assert_called_with(f"readings:site:{MOCK_SITE_ID}", 0, -1)


@pytest.mark.asyncio
async def test_get_site_readings_redis_error() -> None:
    mock_redis = AsyncMock()
    mock_redis.lrange.side_effect = RedisError("Connection lost")
    app.state.redis = mock_redis

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get(f"/sites/{MOCK_SITE_ID}/readings")

    assert response.status_code == codes.OK
    assert response.json() == []  # App handles error by returning empty list


# --- Consumer Logic Tests ---


@pytest.mark.asyncio
async def test_consume_stream_processes_and_acks() -> None:
    """Tests that a valid message is parsed, stored in a list, and acknowledged."""
    mock_redis = AsyncMock()
    # Mock xreadgroup to return one message, then empty to avoid infinite loop in test
    mock_redis.xreadgroup.side_effect = [
        [("mystream", [(MOCK_STREAM_ID, MOCK_PAYLOAD)])],
        asyncio.CancelledError(),  # Break the loop
    ]

    app.state.redis = mock_redis

    with pytest.raises(asyncio.CancelledError):
        await consume_stream(app)

    # Verify storage
    storage_key = f"readings:site:{MOCK_SITE_ID}"
    mock_redis.lpush.assert_called_once_with(storage_key, json.dumps(MOCK_PAYLOAD))
    mock_redis.ltrim.assert_called_once_with(storage_key, 0, 999)
    # Verify ACK
    mock_redis.xack.assert_called_once_with(ANY, ANY, MOCK_STREAM_ID)


@pytest.mark.asyncio
async def test_consume_stream_invalid_data_acks_and_skips() -> None:
    """Tests that invalid Pydantic data is skipped but ACKed to clear the stream."""
    mock_redis = AsyncMock()
    invalid_payload = {"malformed": "data"}

    mock_redis.xreadgroup.side_effect = [
        [("mystream", [(MOCK_STREAM_ID, invalid_payload)])],
        asyncio.CancelledError(),
    ]

    app.state.redis = mock_redis

    with pytest.raises(asyncio.CancelledError):
        await consume_stream(app)

    # Should NOT attempt to store
    mock_redis.lpush.assert_not_called()
    # Should still ACK to prevent stuck message
    mock_redis.xack.assert_called_once_with(ANY, ANY, MOCK_STREAM_ID)


@pytest.mark.asyncio
async def test_consume_stream_redis_storage_error_still_acks() -> None:
    """Tests that if storage fails, we still ACK to prevent blocking the group."""
    mock_redis = AsyncMock()
    mock_redis.xreadgroup.side_effect = [
        [("mystream", [(MOCK_STREAM_ID, MOCK_PAYLOAD)])],
        asyncio.CancelledError(),
    ]
    # Simulate failure during LPUSH
    mock_redis.lpush.side_effect = RedisError("Storage Full")

    app.state.redis = mock_redis

    with pytest.raises(asyncio.CancelledError):
        await consume_stream(app)

    # ACK should still happen based on your code logic
    mock_redis.xack.assert_called_once_with(ANY, ANY, MOCK_STREAM_ID)
