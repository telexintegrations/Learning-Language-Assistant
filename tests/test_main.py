import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from src.main import app
from datetime import datetime
import pytz

@pytest.mark.anyio
async def test_read_root():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Language Learning Assistant API is running."}

@pytest.mark.anyio
async def test_tick_endpoint_not_time(monkeypatch):
    # Mock datetime to simulate a time that does NOT match lesson_time ("08:00")
    class MockDateTime:
        @classmethod
        def now(cls, tz=None):
            return datetime(2025, 1, 1, 7, 0, tzinfo=tz)  # 07:00 AM

    monkeypatch.setattr(pytz, 'datetime', MockDateTime)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/tick", json={
            "channel_webhook_url": "http://example.com/webhook",
            "language": "Spanish",
            "lesson_time": "08:00"
        })
    assert response.status_code == 200
    assert response.json() == {"status": "It's not time for the lesson yet."}

@pytest.mark.anyio
async def test_tick_endpoint_time(monkeypatch):
    # Mock datetime to simulate current time equals lesson_time ("08:00")
    class MockDateTime:
        @classmethod
        def now(cls, tz=None):
            return datetime(2025, 1, 1, 8, 0, tzinfo=tz)  # 08:00 AM

    monkeypatch.setattr(pytz, 'datetime', MockDateTime)

    # Mock external API calls to return dummy data
    async def mock_fetch_word_data(word: str):
        return "Dummy definition", "Dummy usage example."

    async def mock_fetch_pronunciation(word: str):
        return "https://dummyurl.com/audio.mp3"

    monkeypatch.setattr('src.main.fetch_word_data', mock_fetch_word_data)
    monkeypatch.setattr('src.main.fetch_pronunciation', mock_fetch_pronunciation)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/tick", json={
            "channel_webhook_url": "http://example.com/webhook",
            "language": "Spanish",
            "lesson_time": "08:00"
        })
    assert response.status_code == 200
    assert response.json() == {"status": "Lesson scheduled for delivery"}
