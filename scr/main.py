from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import httpx
from datetime import datetime
import pytz
import random

app = FastAPI()

# Define the expected settings from the integration configuration
class Settings(BaseModel):
    channel_webhook_url: str
    language: str = "Spanish"
    lesson_time: str = "08:00"

# Dummy lessons data for demonstration
lessons = {
    "Spanish": [
        {
            "word": "Hola",
            "definition": "A greeting that means 'hello'.",
            "usage": "Used to greet someone, e.g., 'Hola, ¿cómo estás?'",
            "pronunciation_url": "https://example.com/audio/hola.mp3",
            "quiz_question": "What does 'Hola' mean?",
            "quiz_options": ["Hello", "Goodbye", "Please", "Thank you"],
            "correct_answer": "Hello"
        },
        {
            "word": "Gracias",
            "definition": "It means 'thank you'.",
            "usage": "Used to express gratitude, e.g., 'Muchas gracias por tu ayuda.'",
            "pronunciation_url": "https://example.com/audio/gracias.mp3",
            "quiz_question": "What does 'Gracias' mean?",
            "quiz_options": ["Sorry", "Thank you", "Please", "Hello"],
            "correct_answer": "Thank you"
        }
    ],
    # Add lessons for other languages as needed
}

# Function to fetch a daily lesson
async def fetch_daily_lesson(language: str) -> dict:
    lesson_list = lessons.get(language, [])
    if not lesson_list:
        return None
    return random.choice(lesson_list)

# Function to send the lesson to the Telex channel via webhook
async def send_lesson(webhook_url: str, lesson: dict):
    # Format the message payload
    message = {
        "text": (
            f"**Daily Language Lesson**\n\n"
            f"**Word:** {lesson['word']}\n"
            f"**Definition:** {lesson['definition']}\n"
            f"**Usage:** {lesson['usage']}\n"
            f"**Pronunciation Audio:** {lesson['pronunciation_url']}\n\n"
            f"**Quiz:** {lesson['quiz_question']}\n"
            f"Options: {', '.join(lesson['quiz_options'])}\n"
            f"Reply with your answer."
        ),
        "username": "Language Learning Assistant"
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(webhook_url, json=message)
        response.raise_for_status()

# The /tick endpoint that triggers the lesson delivery
@app.post("/tick")
async def tick(settings: Settings, background_tasks: BackgroundTasks):
    # Use a specific timezone (adjust as needed)
    user_tz = pytz.timezone("America/New_York")
    current_time = datetime.now(user_tz).strftime("%H:%M")
    if current_time == settings.lesson_time:
        lesson = await fetch_daily_lesson(settings.language)
        if lesson is None:
            return {"status": "No lesson available for the specified language."}
        background_tasks.add_task(send_lesson, settings.channel_webhook_url, lesson)
        return {"status": "Lesson scheduled for delivery"}
    else:
        return {"status": "It's not time for the lesson yet."}

# Optional: A simple root endpoint for health checks
@app.get("/")
async def read_root():
    return {"message": "Language Learning Assistant API is running."}
