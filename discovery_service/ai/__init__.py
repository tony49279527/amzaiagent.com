"""AI package"""
from .openrouter_client import OpenRouterClient
from .prompts import (
    get_source_finder_prompt,
    get_free_tier_prompt,
    get_pro_tier_prompt,
    get_quick_summary_prompt
)

__all__ = [
    "OpenRouterClient",
    "get_source_finder_prompt",
    "get_discovery_analysis_prompt",
    "get_quick_summary_prompt"
]
