"""
Enhanced ScrapingBee client with retry and better parsing
"""
import httpx
from typing import List, Optional
import asyncio
from ..config import SCRAPINGBEE_API_KEY, SCRAPINGBEE_BASE_URL
from ..models import WebSource


class ScrapingBeeClient:
    """Enhanced client for ScrapingBee API with retry logic"""
    
    def __init__(self, api_key: str = SCRAPINGBEE_API_KEY):
        self.api_key = api_key
        self.base_url = SCRAPINGBEE_BASE_URL
    
    async def scrape_url(
        self, 
        url: str, 
        render_js: bool = True,
        retry_count: int = 3
    ) -> Optional[str]:
        """
        Scrape a single URL with retry logic
        """
        params = {
            "api_key": self.api_key,
            "url": url,
            "render_js": "true" if render_js else "false",
            "premium_proxy": "true",
            "country_code": "us",
            "wait": "5000",  # Wait 5 seconds for JS to load
            "wait_for": "networkidle",  # Wait for network to be idle
        }
        
        # Enable custom_google for Search Engine Result Pages (SERP)
        if "google.com/search" in url or "youtube.com/results" in url or "reddit.com/search" in url:
             params["custom_google"] = "true"
        
        for attempt in range(retry_count):
            try:
                async with httpx.AsyncClient(timeout=90.0) as client:
                    response = await client.get(self.base_url, params=params)
                    
                if response.status_code == 200:
                    return response.text
                elif response.status_code == 400:
                    print(f"[ScrapingBee] Bad Request (400) for {url}. Skipping.")
                    return None
                else:
                    print(f"[ScrapingBee] Attempt {attempt+1}/{retry_count} failed for {url}: {response.status_code}")
                    if attempt < retry_count - 1:
                        await asyncio.sleep(2 ** attempt)
                        
                        # Fallback: Try disabling premium proxy for subsequent attempts if it's a 500/timeout
                        if attempt == 1:
                            params["premium_proxy"] = "false"
                        
            except Exception as e:
                print(f"[ScrapingBee] Attempt {attempt+1}/{retry_count} exception for {url}: {str(e)}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(2 ** attempt)
        
        return None
    
    async def scrape_reddit_post(self, url: str) -> Optional[WebSource]:
        """Scrape a Reddit post with enhanced parsing"""
        html = await self.scrape_url(url, render_js=True)
        if not html:
            return None
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try multiple selectors for title
        title = None
        for selector in ['h1', '[data-test-id="post-content-title"]', '.title']:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                break
        
        title = title or "Reddit Post"
        
        # Get post content
        content_parts = []
        
        # Post body - try multiple selectors
        for selector in [
            '[data-test-id="post-content"]',
            '.usertext-body',
            '[data-click-id="text"]'
        ]:
            post_body = soup.select_one(selector)
            if post_body:
                content_parts.append(post_body.get_text(strip=True))
                break
        
        # Comments - try multiple selectors
        comment_selectors = [
            '[data-testid="comment"]',
            '.Comment',
            '[data-type="comment"]'
        ]
        
        comments = []
        for selector in comment_selectors:
            comments = soup.select(selector, limit=20)
            if comments:
                break
        
        for comment in comments[:20]:
            comment_text = comment.get_text(strip=True)
            if comment_text and len(comment_text) > 10:
                content_parts.append(f"Comment: {comment_text}")
        
        content = "\n\n".join(content_parts) if content_parts else "Could not extract content"
        
        return WebSource(
            url=url,
            title=title,
            content=content,
            source_type="reddit"
        )
    
    async def scrape_youtube_video(self, url: str) -> Optional[WebSource]:
        """
        Scrape YouTube video - get description and attempt transcript
        """
        html = await self.scrape_url(url, render_js=True)
        if not html:
            return None
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Get title
        title = soup.find('meta', {'name': 'title'})
        title_text = title.get('content') if title else "YouTube Video"
        
        # Get description
        description = soup.find('meta', {'name': 'description'})
        description_text = description.get('content') if description else ""
        
        # Try to get transcript from page (limited success)
        content_parts = [f"Video Description:\n{description_text}"]
        
        # Look for transcript in page
        transcript_elem = soup.find('div', {'id': 'transcript'})
        if transcript_elem:
            content_parts.append(f"\nTranscript:\n{transcript_elem.get_text(strip=True)}")
        
        return WebSource(
            url=url,
            title=title_text,
            content="\n\n".join(content_parts),
            source_type="youtube"
        )
    
    async def scrape_generic_page(self, url: str) -> Optional[WebSource]:
        """Scrape a generic web page with better content extraction"""
        html = await self.scrape_url(url, render_js=False)
        if not html:
            return None
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Get title
        title = soup.find('title')
        title_text = title.get_text(strip=True) if title else url
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
            element.decompose()
        
        # Try to find main content
        main_content = None
        for selector in ['main', 'article', '[role="main"]', '.content', '#content']:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        if not main_content:
            main_content = soup.find('body')
        
        # Get text content
        content = main_content.get_text(separator='\n', strip=True) if main_content else ""
        
        # Limit content length but keep more
        content = content[:10000]  # Increased from 5000
        
        return WebSource(
            url=url,
            title=title_text,
            content=content,
            source_type="web"
        )
    
    async def scrape_multiple(self, urls: List[str]) -> List[WebSource]:
        """
        Scrape multiple URLs with limited concurrency to avoid rate limiting
        """
        sources = []
        semaphore = asyncio.Semaphore(3)  # Limit to 3 concurrent requests
        
        async def scrape_with_semaphore(url: str, index: int):
            async with semaphore:
                print(f"[Scraping] Starting {index+1}/{len(urls)}: {url[:50]}...")
                try:
                    if "reddit.com" in url:
                        result = await self.scrape_reddit_post(url)
                    elif "youtube.com" in url or "youtu.be" in url:
                        result = await self.scrape_youtube_video(url)
                    else:
                        result = await self.scrape_generic_page(url)
                    
                    if result:
                        print(f"[Scraping] [OK] {index+1}/{len(urls)}: Success")
                        return result
                    else:
                        print(f"[Scraping] [FAIL] {index+1}/{len(urls)}: No content")
                        return None
                except Exception as e:
                    print(f"[Scraping] [ERROR] {index+1}/{len(urls)}: {str(e)[:50]}")
                    return None
        
        tasks = [scrape_with_semaphore(url, i) for i, url in enumerate(urls)]
        results = await asyncio.gather(*tasks)
        
        # Filter out None results
        sources = [r for r in results if r is not None]
        
        print(f"[Scraping] Total: {len(sources)}/{len(urls)} successful")
        return sources

