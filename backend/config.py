"""Configuration for AI Peer Review."""

import os
from dotenv import load_dotenv

load_dotenv()

# API Keys for different providers
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Council members - list of model identifiers from multiple providers
# Prefix convention:
#   - "gemini/" for Google Gemini models (e.g., "gemini/gemini-2.5-flash")
#   - "github/" for GitHub Models (e.g., "github/openai/gpt-4o-mini")
#   - No prefix for OpenRouter models (e.g., "openai/gpt-oss-120b:free")
COUNCIL_MODELS = [
    "openai/gpt-oss-120b:free",                  # OpenRouter (free)
    "gemini/gemini-2.5-flash",                   # Google Gemini (free tier)
    "github/openai/gpt-4o-mini",                 # GitHub Models (free)
]

# Chairman model - synthesizes final response
CHAIRMAN_MODEL = "github/openai/gpt-4o"

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Data directory for conversation storage
DATA_DIR = "data/conversations"
