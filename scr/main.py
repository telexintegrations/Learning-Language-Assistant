from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import httpx
import requests
from datetime import datetime
import pytz
import random

app = FastAPI()

# Configuration for external APIs (Replace with your actual keys)
OXFORD_APP_ID = "your_oxford_app_id"
OXFORD_APP_KEY = "your_oxford_app_key"
FORVO_API_KEY = "your_forvo_api_key"

# Integration settings model
class Settings(BaseModel):
    channel_webhook_url: str
    language: str = "Spanish"
    lesson_time: str = "08:00"

def fetch_word_data(word: str) -> (str, str):
    """
    Fetches word definition and an example sentence from the Oxford Dictionaries API.
    """
    language = "en-us"  # Adjust based on target language if needed
    url = f"https://od-api.oxforddictionaries.com/api/v2/entries/{language}/{word.lower()}"
    headers = {"app_id": OXFORD_APP_ID, "app_key": OXFORD_APP_KEY}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        try:
            senses = data["results"][0]["lexicalEntries"][0]["entries"][0]["senses"][0]
            definition = senses["definitions"][0]
            example = senses.get("examples", [{"text": "No example available."}])[0]["text"]
            return definition, example
        except (IndexError, KeyError):
            return "Definition not found.", "Example not found."
    else:
        return "Definition not found.", "Example not found."

def fetch_pronunciation(word: str) -> str:
    """
    Fetches the pronunciation audio URL for the word from the Forvo API.
    """
    url = f"https://apifree.forvo.com/key/{FORVO_API_KEY}/format/json/action/word-pronunciations/word/{word}/language/en"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        if items:
            return items[0].get("pathmp3", "")
        else:
            return ""
    else:
        return ""

async def fetch_daily_lesson(language: str) -> dict:
    """
    Constructs a lesson for the given language.
    For demonstration, selects a random word from a predefined list and augments it with external API data.
    """
    # In production, you might have a language-specific word list or database.
    word_list = {
        "Spanish": ["hola", "gracias", "amigo", "libro"],
        "French": ["bonjour", "merci", "ami", "livre"],
        "German": ["hallo", "danke", "freund", "buch"],
        "Mandarin": ["你好", "谢谢", "朋友", "书"],
        "Japanese": ["こんにちは", "ありがとう", "友達", "本"]
    }
    
    words = word_list.get(language, ["hello"])
    word = random.choice(words)
    
    definition, example = fetch_word_data(word)
    pronunciation_url = fetch_pronunciation(word)
    
    # Construct a dummy quiz (In production, create meaningful quiz data)
    quiz_question = f"What is the meaning of '{word}'?"
    quiz_options = [definition, "Option B", "Option C", "Option D"]
    correct_answer = definition
    
    return {
        "word": word,
        "definition": definition,
        "usage": example,
        "pronunciation_url": pronunciation_url,
        "quiz_question": quiz_question,
        "quiz_options": quiz_options,
        "correct_answer": correct_answer
    }

async def send_lesson(webhook_url: str, lesson: dict):
    """
    Sends the lesson to the provided webhook URL.
    """
    message = {
        "text": (
            f"**Daily Language Lesson**\n\n"
            f"**Word:** {lesson['word']}\n"
            f"**Definition:** {lesson['definition']}\n"
            f"**Usage:** {lesson['usage']}\n"
            f"**Pronunciation Audio:** [Listen Here]({lesson['pronunciation_url']})\n\n"
            f"**Quiz:** {lesson['quiz_question']}\n"
            f"Options: {', '.join(lesson['quiz_options'])}\n"
            f"Reply with your answer."
        ),
        "username": "Language Learning Assistant"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(webhook_url, json=message)
        resp.raise_for_status()

@app.post("/tick")
async def tick(settings: Settings, background_tasks: BackgroundTasks):
    """
    The /tick endpoint that Telex calls at the scheduled time.
    It checks the current time against the lesson_time setting and sends the lesson if they match.
    """
    # Adjust timezone as needed. For this example, we use "America/New_York"
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

@app.get("/")
async def read_root():
    return {"message": "Language Learning Assistant API is running."}
