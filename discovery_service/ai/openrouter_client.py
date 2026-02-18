"""
OpenRouter AI Client for LLM analysis
"""
import httpx
from typing import Optional, List
from ..config import OPENROUTER_API_KEY, DEFAULT_MODEL_FREE, DEFAULT_MODEL_PRO


class OpenRouterClient:
    """Client for OpenRouter API"""
    
    def __init__(self, api_key: str = OPENROUTER_API_KEY):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
    
    async def generate_analysis(
        self,
        prompt: str,
        model: str = DEFAULT_MODEL_PRO,
        max_tokens: int = 8000,
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        Generate analysis using LLM
        
        Args:
            prompt: The analysis prompt
            model: Model to use
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            
        Returns:
            Generated text or None
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://amzaiagent.com",  # Optional but recommended
        }
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    print(f"OpenRouter API error: {response.status_code}")
                    print(f"Response: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"Error calling OpenRouter: {str(e)}")
            return None
    
    async def generate_with_retry(
        self,
        prompt: str,
        model: str = DEFAULT_MODEL_PRO,
        max_retries: int = 3
    ) -> Optional[str]:
        """
        Generate with automatic retry on failure
        
        Args:
            prompt: The analysis prompt
            model: Model to use
            max_retries: Maximum retry attempts
            
        Returns:
            Generated text or None
        """
        import asyncio
        
        for attempt in range(max_retries):
            result = await self.generate_analysis(prompt, model)
            
            if result:
                return result
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Retry attempt {attempt + 1} after {wait_time}s...")
                await asyncio.sleep(wait_time)
        
        return None
