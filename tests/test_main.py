from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_tick_endpoint():
    response = client.post("/tick", json={
        "channel_webhook_url": "http://example.com/webhook",
        "language": "Spanish",
        "lesson_time": "08:00"
    })
    assert response.status_code == 200
    assert response.json() in [
        {"status": "Lesson scheduled for delivery"},
        {"status": "It's not time for the lesson yet."}
    ]
