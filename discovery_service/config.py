"""
Configuration for Product Discovery Service
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys (all loaded from environment variables)
SCRAPINGBEE_API_KEY = os.getenv("SCRAPINGBEE_API_KEY", "")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = "real-time-amazon-data.p.rapidapi.com"

# Google Custom Search API (Official)
GOOGLE_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY", "")
GOOGLE_CX = os.getenv("GOOGLE_SEARCH_CX", "")

# OpenRouter API (for LLM)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Model Configuration
DEFAULT_MODEL_FREE = "anthropic/claude-3.5-sonnet"  # Free users
DEFAULT_MODEL_PRO = "anthropic/claude-sonnet-4.5"  # Pro users default

# Available Pro Models (must match frontend select options)
PRO_MODELS = [
    "anthropic/claude-sonnet-4.5",
    "google/gemini-3-pro-preview",
    "openai/gpt-5.2-pro",
    "openai/gpt-5.2-chat",
    "qwen/qwen3-v1-235b-a22b-thinking",
    "deepseek/deepseek-v3.2-speciale",
]

# Free tier source limits
FREE_WEB_SOURCES_COUNT = 3
FREE_YOUTUBE_SOURCES_COUNT = 3

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

# Polar.sh Payment Settings
POLAR_ACCESS_TOKEN = os.getenv("POLAR_ACCESS_TOKEN", "")
POLAR_ORGANIZATION_ID = os.getenv("POLAR_ORGANIZATION_ID", "")
POLAR_PRODUCT_ID = os.getenv("POLAR_PRODUCT_ID", "dc5fea6e-0719-4bbd-9138-da29b495e242")
POLAR_CHECKOUT_SUCCESS_URL = "https://amz-ai-replica-550177383294.us-central1.run.app/processing.html?taskId={CHECKOUT_ID}"
