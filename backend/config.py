"""Configuration for AI Peer Review."""

import os
from dotenv import load_dotenv

load_dotenv()

# API Keys for different providers
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Council members - list of model identifiers from multiple providers
# Prefix convention:
#   - "perplexity/" for Perplexity models (e.g., "perplexity/sonar")
#   - "gemini/" for Google Gemini models (e.g., "gemini/gemini-2.0-flash")
#   - No prefix or other format for OpenRouter models (e.g., "x-ai/grok-4.1-fast:free")
COUNCIL_MODELS = [
    "x-ai/grok-4.1-fast:free",      # OpenRouter (free)
    "perplexity/sonar",              # Perplexity direct API
    "gemini/gemini-2.0-flash",       # Google Gemini direct API
]

# Chairman model - synthesizes final response
CHAIRMAN_MODEL = "perplexity/sonar"

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Data directory for conversation storage
DATA_DIR = "data/conversations"
