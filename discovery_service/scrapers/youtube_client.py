"""
YouTube Caption Scraper using ScrapingBee
Searches for product-related YouTube videos and extracts captions
"""
import re
import httpx
from typing import List, Optional
from dataclasses import dataclass
from ..config import SCRAPINGBEE_API_KEY

@dataclass
class YouTubeSource:
    video_id: str
    title: str
    url: str
    captions: str
    source_type: str = "youtube"

class YouTubeClient:
    """Client for searching YouTube and extracting captions via ScrapingBee"""
    
    def __init__(self):
        self.api_key = SCRAPINGBEE_API_KEY
        self.base_url = "https://app.scrapingbee.com/api/v1/"
        
    async def search_and_get_captions(
        self, 
        keywords: str, 
        required_count: int = 3,
        max_search: int = 10
    ) -> List[YouTubeSource]:
        """
        Search YouTube for videos and extract captions.
        Returns up to `required_count` videos that have successfully extracted captions.
        """
        print(f"[YouTube] Searching for videos about: {keywords}")
        
        # Step 1: Search YouTube for videos
        video_urls = await self._search_youtube(keywords, max_search)
        print(f"[YouTube] Found {len(video_urls)} video URLs")
        
        # Step 2: Try to get captions for each, stop when we have enough
        successful_sources = []
        for url, title in video_urls:
            if len(successful_sources) >= required_count:
                break
                
            captions = await self._get_captions(url)
            if captions and len(captions) > 100:  # Minimum caption length
                video_id = self._extract_video_id(url)
                successful_sources.append(YouTubeSource(
                    video_id=video_id,
                    title=title,
                    url=url,
                    captions=captions[:5000]  # Limit caption length
                ))
                print(f"[YouTube] ✓ Got captions for: {title[:50]}...")
            else:
                print(f"[YouTube] ✗ No captions for: {title[:50]}...")
                
        print(f"[YouTube] Successfully scraped {len(successful_sources)}/{required_count} videos")
        return successful_sources
    
    async def _search_youtube(self, keywords: str, max_results: int) -> List[tuple]:
        """
        Search YouTube and return list of (url, title) tuples.
        Uses ScrapingBee to scrape YouTube search results page.
        """
        search_query = f"{keywords} review"
        search_url = f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    self.base_url,
                    params={
                        "api_key": self.api_key,
                        "url": search_url,
                        "render_js": "true",
                        "wait": "3000"
                    }
                )
                
                if response.status_code != 200:
                    print(f"[YouTube] Search failed: {response.status_code}")
                    return []
                    
                html = response.text
                
                # Extract video IDs and titles from YouTube search results
                # Pattern matches: /watch?v=VIDEO_ID
                video_pattern = r'/watch\?v=([a-zA-Z0-9_-]{11})'
                title_pattern = r'"title":\{"runs":\[\{"text":"([^"]+)"\}\]'
                
                video_ids = re.findall(video_pattern, html)
                titles = re.findall(title_pattern, html)
                
                # Deduplicate while preserving order
                seen = set()
                results = []
                for vid in video_ids[:max_results * 2]:  # Get more to account for duplicates
                    if vid not in seen:
                        seen.add(vid)
                        url = f"https://www.youtube.com/watch?v={vid}"
                        # Try to find matching title
                        title = titles[len(results)] if len(results) < len(titles) else f"Video {vid}"
                        results.append((url, title))
                        if len(results) >= max_results:
                            break
                            
                return results
                
        except Exception as e:
            print(f"[YouTube] Search error: {e}")
            return []
    
    async def _get_captions(self, video_url: str) -> Optional[str]:
        """
        Get captions/transcript for a YouTube video using ScrapingBee.
        Scrapes the video page and extracts available captions.
        """
        try:
            # Try to get captions via a transcript service or direct scrape
            # YouTube stores captions in a specific format
            transcript_url = video_url  # ScrapingBee will render JS
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    self.base_url,
                    params={
                        "api_key": self.api_key,
                        "url": transcript_url,
                        "render_js": "true",
                        "wait": "2000",
                        "extract_rules": '{"captions": "script"}'  # Try to get script content
                    }
                )
                
                if response.status_code != 200:
                    return None
                    
                html = response.text
                
                # Try to extract caption data from YouTube's embedded JSON
                # YouTube embeds caption tracks in the page source
                caption_pattern = r'"captionTracks":\[.*?"baseUrl":"([^"]+)"'
                matches = re.findall(caption_pattern, html)
                
                if matches:
                    # Found caption URL, fetch it
                    caption_url = matches[0].replace('\\u0026', '&')
                    caption_response = await client.get(
                        self.base_url,
                        params={
                            "api_key": self.api_key,
                            "url": caption_url
                        }
                    )
                    
                    if caption_response.status_code == 200:
                        # Parse caption XML/text
                        caption_text = caption_response.text
                        # Remove XML tags if present
                        clean_text = re.sub(r'<[^>]+>', ' ', caption_text)
                        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                        return clean_text
                
                # Fallback: try to extract any text content from description
                desc_pattern = r'"description":\{"simpleText":"([^"]+)"\}'
                desc_matches = re.findall(desc_pattern, html)
                if desc_matches:
                    return desc_matches[0][:2000]
                    
                return None
                
        except Exception as e:
            print(f"[YouTube] Caption extraction error: {e}")
            return None
    
    def _extract_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL"""
        match = re.search(r'v=([a-zA-Z0-9_-]{11})', url)
        return match.group(1) if match else ""
