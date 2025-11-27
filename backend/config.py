"""Configuration for AI Peer Review."""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Council members - list of OpenRouter model identifiers (free tier)
COUNCIL_MODELS = [
    "x-ai/grok-4.1-fast:free",
    "google/gemma-3-27b-it:free",
    "openai/gpt-oss-20b:free",

]

# Chairman model - synthesizes final response
CHAIRMAN_MODEL = "x-ai/grok-4.1-fast:free"

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Data directory for conversation storage
DATA_DIR = "data/conversations"
