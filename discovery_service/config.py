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

# ScrapingBee Settings
SCRAPINGBEE_BASE_URL = "https://app.scrapingbee.com/api/v1/"

# Email Settings (for sending reports)
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").replace(" ", "")

# Report Settings
MAX_SEARCH_RESULTS = 10  # Max websites/videos to scrape
MAX_REVIEWS_PER_ASIN = 100  # Max reviews to analyze per product (increased)
