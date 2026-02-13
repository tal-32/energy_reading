from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient, codes

from services.producer.main import app
from shared_lib.model import (
    DATE_FORMAT,
    HEALTH_CHECK_DICT,
    ReadingInput,
    ReadingOutput,
    ReadingStatus,
)

MOCK_STRAM_ID = "1234567890-0"
MOCK_READING_INPUT = ReadingInput(
    site_id="site123",
    device_id="device456",
    power_reading=42.5,
    timestamp="2024-01-15T10:30:00Z",
)
MOCK_READING_OUTPUT = ReadingOutput(
    status=ReadingStatus.ACCEPTED, stream_id=MOCK_STRAM_ID
)


@pytest.mark.asyncio
async def test_health_check_success() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/health")

    # 4. Assertions
    assert response.status_code == codes.OK
    assert response.json() == HEALTH_CHECK_DICT


@pytest.mark.asyncio
async def test_create_reading_success() -> None:
    mock_redis = AsyncMock()
    mock_redis.xadd.return_value = MOCK_STRAM_ID
    app.state.redis = mock_redis

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/readings", json=MOCK_READING_INPUT.model_dump())

    assert response.status_code == codes.CREATED
    assert response.json() == MOCK_READING_OUTPUT.model_dump()
    mock_redis.xadd.assert_called_once()


@pytest.mark.parametrize(
    "payload",
    [
        dict(),
        dict(power_reading=42.5),
    ],
)
@pytest.mark.asyncio
async def test_create_reading_missing_params(payload: dict[str, str | float]) -> None:
    mock_redis = AsyncMock()
    app.state.redis = mock_redis

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/readings", json=payload)

    assert response.status_code == codes.UNPROCESSABLE_ENTITY
    mock_redis.xadd.assert_not_called()


@pytest.mark.asyncio
async def test_create_reading_success_with_extra_param() -> None:
    mock_redis = AsyncMock()
    mock_redis.xadd.return_value = MOCK_STRAM_ID
    app.state.redis = mock_redis

    # Prepare valid ReadingInput payload
    payload = MOCK_READING_INPUT.model_dump()
    payload["extra_arg"] = "unknown_extra"

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/readings", json=payload)

    assert response.status_code == codes.CREATED
    assert response.json() == MOCK_READING_OUTPUT.model_dump()
    mock_redis.xadd.assert_called_once()


@pytest.mark.parametrize(
    "payload_replacement",
    [
        dict(site_id=""),
        dict(device_id=""),
        dict(power_reading="high"),
        dict(timestamp=""),
        dict(timestamp="2024-51-51T10:30:00Z"),
    ],
)
@pytest.mark.asyncio
async def test_create_reading_invalid_params_value(
    payload_replacement: dict[str, str],
) -> None:
    mock_redis = AsyncMock()
    mock_redis.xadd.return_value = MOCK_STRAM_ID
    app.state.redis = mock_redis
    payload = MOCK_READING_INPUT.model_dump()
    payload.update(payload_replacement)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/readings", json=payload)

    assert response.status_code == codes.UNPROCESSABLE_ENTITY
    mock_redis.xadd.assert_not_called()


@pytest.mark.asyncio
async def test_create_reading_illogical_datetime_value() -> None:
    """
    testing datetime that is in the future
    """
    mock_redis = AsyncMock()
    app.state.redis = mock_redis

    payload = MOCK_READING_INPUT.model_dump()
    illogical_time = (datetime.now() + timedelta(hours=2)).strftime(DATE_FORMAT)
    payload.update(timestamp=illogical_time)
    print(payload)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/readings", json=payload)

    assert response.status_code == codes.UNPROCESSABLE_ENTITY
    mock_redis.xadd.assert_not_called()
