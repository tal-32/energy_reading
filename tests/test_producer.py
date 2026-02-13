from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient, codes

from services.producer.main import app
from shared_lib.model import ReadingInput, ReadingOutput, ReadingStatus

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
async def test_health_check_success():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/health")

    # 4. Assertions
    assert response.status_code == codes.OK
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_create_reading_success():
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
async def test_create_reading_mismatch_params(payload: dict[str, str | float]):
    mock_redis = AsyncMock()
    app.state.redis = mock_redis

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/readings", json=payload)

    assert response.status_code == codes.UNPROCESSABLE_ENTITY
    mock_redis.xadd.assert_not_called()


@pytest.mark.asyncio
async def test_create_reading_success_with_extra_param():
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
