  from fastapi.testclient import TestClient
  from src.main import app, fetch_daily_lesson

  client = TestClient(app)

  def test_tick_endpoint():
      response = client.post("/tick", json={
          "channel_webhook_url": "http://example.com/webhook",
          "language": "Spanish",
          "lesson_time": "08:00"
      })
      assert response.status_code == 200
      assert response.json() == {"status": "Lesson scheduled for delivery"}

  def test_fetch_daily_lesson():
      lesson = fetch_daily_lesson("Spanish")
      assert "Today's Spanish lesson" in lesson

