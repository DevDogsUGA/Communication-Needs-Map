"""Gemini for scripts. The key comes from GEMINI_API_KEY in .env (see .env.example)."""

from dotenv import load_dotenv
from google import genai

# Model list: https://ai.google.dev/gemini-api/docs/models
MODEL = "gemini-3.8-flash"


def client() -> genai.Client:
    load_dotenv()
    return genai.Client()  # reads GEMINI_API_KEY from the environment
