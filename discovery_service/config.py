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
DEFAULT_MODEL_FREE = "anthropic/claude-3.5-sonnet"  # Free users - High quality magnet
DEFAULT_MODEL_PRO = "anthropic/claude-sonnet-4"  # Pro users - Claude 4 Sonnet

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
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").replace(" ", "")

# Report Settings
MAX_SEARCH_RESULTS = 10  # Max websites/videos to scrape
MAX_REVIEWS_PER_ASIN = 100  # Max reviews to analyze per product (increased)
