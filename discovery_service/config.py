"""
Configuration for Product Discovery Service
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
SCRAPINGBEE_API_KEY = "FZRSC69J3MPE5OO5FYJKEZFGI2XWG65IQA2V86EFJWKF9ARVGV0AIPMTSJ74XL0FV3EZIL95B7ZQI1XR"

RAPIDAPI_KEY = "35d443d327msh77164428609687ep1ee4b4jsn763b388ea69a"
RAPIDAPI_HOST = "real-time-amazon-data.p.rapidapi.com"

# OpenRouter API (for LLM)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")  # You'll need to set this

# Model Configuration
DEFAULT_MODEL_FREE = "google/gemini-3.0-flash"  # Free users - Gemini 3 Flash
DEFAULT_MODEL_PRO = "anthropic/claude-3.5-sonnet"  # Pro users - Claude 3.5 Sonnet

# Free Tier Source Limits (must successfully scrape this many)
FREE_WEB_SOURCES_COUNT = 3
FREE_YOUTUBE_SOURCES_COUNT = 3

# Available Pro Models
PRO_MODELS = [
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-4-turbo",
    "google/gemini-pro-1.5",
    "meta-llama/llama-3.1-405b"
]

# ScrapingBee Settings
SCRAPINGBEE_BASE_URL = "https://app.scrapingbee.com/api/v1/"

# Email Settings (for sending reports)
# Support both SMTP_HOST and SMTP_SERVER env var names for compatibility
SMTP_HOST = os.getenv("SMTP_HOST") or os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").replace(" ", "")

# Report Settings
MAX_SEARCH_RESULTS = 10  # Max websites/videos to scrape
MAX_REVIEWS_PER_ASIN = 100  # Max reviews to analyze per product (increased)
