from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import httpx
from datetime import datetime
import pytz
import random
import os
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# Add CORS middleware to allow requests from all origins for testing.
# You can restrict origins as needed (e.g., to ["https://app.telex.im"]).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with specific origins if needed.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Replace these with your actual API credentials
OXFORD_APP_ID = os.getenv("OXFORD_APP_ID")
OXFORD_APP_KEY = os.getenv("OXFORD_APP_KEY")
FORVO_API_KEY = "your_forvo_api_key"

# Integration settings model
class Settings(BaseModel):
    channel_webhook_url: str
    language: str = "Spanish"
    lesson_time: str = "08:00"

async def fetch_word_data(word: str) -> (str, str):
    """
    Asynchronously fetches word definition and an example sentence from the Oxford Dictionaries API.
    """
    language_code = "en-us"  # Adjust if needed
    url = f"https://od-api-sandbox.oxforddictionaries.com/api/v2/entries/{language_code}/{word.lower()}"
    headers = {"app_id": OXFORD_APP_ID, "app_key": OXFORD_APP_KEY}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
    
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

async def fetch_pronunciation(word: str) -> str:
    """
    Asynchronously fetches the pronunciation audio URL for the word from the Forvo API.
    """
    url = f"https://apifree.forvo.com/key/{FORVO_API_KEY}/format/json/action/word-pronunciations/word/{word}/language/en"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    
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
    It selects a random word from a predefined list and fetches its definition, usage example, and pronunciation.
    """
    word_list = {
        "Spanish": ["hola", "gracias", "amigo", "libro"],
        "French": ["bonjour", "merci", "ami", "livre"],
        "German": ["hallo", "danke", "freund", "buch"],
        "Mandarin": ["你好", "谢谢", "朋友", "书"],
        "Japanese": ["こんにちは", "ありがとう", "友達", "本"]
    }
    
    words = word_list.get(language, ["hello"])
    word = random.choice(words)
    
    definition, example = await fetch_word_data(word)
    pronunciation_url = await fetch_pronunciation(word)
    
    # Create a dummy quiz for demonstration purposes
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
    Sends the constructed lesson to the provided webhook URL.
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
    lesson = await fetch_daily_lesson(settings.language)
    if lesson is None:
        return {"status": "No lesson available for the specified language."}
    background_tasks.add_task(send_lesson, settings.channel_webhook_url, lesson)
    return {"status": "Lesson scheduled for delivery", "lesson": lesson}

@app.get("/")
async def read_root():
    return {"message": "Language Learning Assistant API is running."}

# Render deployment adjustment: run on host 0.0.0.0 and port from environment variable.
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
