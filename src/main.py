from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import httpx
import json
from datetime import datetime
import pytz

app = FastAPI()

class Settings(BaseModel):
    channel_webhook_url: str
    language: str = "Spanish"
    lesson_time: str = "08:00"

async def fetch_daily_lesson(language: str) -> str:
    # Placeholder function to fetch the daily lesson
    # Replace with actual API calls to language learning services
    return f"Today's {language} lesson: [Lesson Content Here]"

async def send_lesson(webhook_url: str, lesson: str):
    message = {
        "text": lesson,
        "username": "Language Learning Assistant"
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(webhook_url, json=message)
        response.raise_for_status()

@app.post("/tick")
async def tick(settings: Settings, background_tasks: BackgroundTasks):
    # Check if the current time matches the lesson_time
    user_tz = pytz.timezone("Africa/Lagos")  # Adjust as needed
    current_time = datetime.now(user_tz).strftime("%H:%M")
    if current_time == settings.lesson_time:
        lesson = await fetch_daily_lesson(settings.language)
        background_tasks.add_task(send_lesson, settings.channel_webhook_url, lesson)
        return {"status": "Lesson scheduled for delivery"}
    else:
        return {"status": "It's not time for the lesson yet."}
