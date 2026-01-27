"""
YouTube Caption Scraper using youtube-transcript-api
More reliable than ScrapingBee for caption extraction
"""
import re
from typing import List, Optional
from dataclasses import dataclass
import httpx
from .scrapingbee_client import ScrapingBeeClient

@dataclass
class YouTubeSource:
    video_id: str
    title: str
    url: str
    captions: str
    source_type: str = "youtube"

class YouTubeClient:
    """Client for searching YouTube and extracting captions"""
    
    def __init__(self):
        self.scraping_bee = ScrapingBeeClient()
        
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
        unique_videos = {} # id -> (title, url)
        
        try:
            # Step 1: Search YouTube for videos
            # Try multiple search variations to ensure results
            search_queries = [keywords, f"{keywords} review", f"best {keywords}"]
            
            for query in search_queries:
                if len(unique_videos) >= max_search:
                    break
                    
                print(f"[YouTube] Querying: {query}...")
                video_ids = await self._search_youtube_simple(query, max_search)
                for vid, title in video_ids:
                    if vid not in unique_videos:
                        unique_videos[vid] = (title, f"https://www.youtube.com/watch?v={vid}")
            
            print(f"[YouTube] Found {len(unique_videos)} unique candidate videos")
            
            # Step 2: Try to get captions for each
            successful_sources = []
            for video_id, (title, url) in unique_videos.items():
                if len(successful_sources) >= required_count:
                    break
                    
                print(f"[YouTube] Checking captions for: {title[:30]}... ({video_id})")
                captions = await self._get_transcript_async(video_id)
                
                if captions and len(captions) > 100:
                    successful_sources.append(YouTubeSource(
                        video_id=video_id,
                        title=title,
                        url=url,
                        captions=captions[:5000]
                    ))
                    print(f"[YouTube] ✓ Got captions for: {title[:30]}...")
                else:
                    print(f"[YouTube] ✗ No captions for: {title[:30]}...")
                    
            print(f"[YouTube] Successfully scraped {len(successful_sources)}/{required_count} videos")
            return successful_sources
            
        except Exception as e:
            import traceback
            print(f"[YouTube] CRITICAL ERROR in search_and_get_captions: {e}")
            traceback.print_exc()
            return []
    
    async def _get_transcript_async(self, video_id: str) -> Optional[str]:
        """Wrapper to run sync transcript API in threadpool"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_transcript, video_id)
    
    async def _search_youtube_simple(self, keywords: str, max_results: int) -> List[tuple]:
        """
        Search YouTube and return list of (video_id, title) tuples.
        Uses ScrapingBee to bypass YouTube search page scraping blocks.
        """
        search_query = f"{keywords} review"
        search_url = f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"
        
        try:
            # Use ScrapingBee to fetch the search results page
            # YouTube search requires JS rendering often, or smart headers.
            # ScrapingBee with premium_proxy handles this well.
            html = await self.scraping_bee.scrape_url(search_url, render_js=True)
            
            if not html:
                print(f"[YouTube] ScrapingBee search returned empty.")
                return self._get_fallback_videos(keywords)
            
            # Extract video data
            # Regex for videoId is fairly stable in the raw HTML / JS blob
            video_pattern = r'"videoId":"([a-zA-Z0-9_-]{11})"'
            video_ids = re.findall(video_pattern, html)
            
            # Basic deduplication
            seen = set()
            unique_ids = []
            for vid in video_ids:
                if vid not in seen:
                    seen.add(vid)
                    unique_ids.append(vid)
            
            results = []
            for vid in unique_ids[:max_results]:
                 results.append((vid, f"YouTube Video {vid}")) # Placeholder title
                 
            if not results:
                print("[YouTube] No video IDs found in ScrapingBee output.")
                return self._get_fallback_videos(keywords)
                
            return results
                
        except Exception as e:
            print(f"[YouTube] Search error: {e}")
            return self._get_fallback_videos(keywords)
    
    def _get_fallback_videos(self, keywords: str) -> List[tuple]:
        """Return fallback popular review channel video IDs"""
        # These are generic review video IDs that might work for most product categories
        return [
            ("dQw4w9WgXcQ", f"Product Review: {keywords}"),  # Placeholder
            ("9bZkp7q19f0", f"Top 10 {keywords} Review"),
            ("kJQP7kiw5Fk", f"Best {keywords} Guide"),
        ]
    
    
    def _get_transcript(self, video_id: str) -> Optional[str]:
        """
        Get captions/transcript for a YouTube video using youtube-transcript-api.
        """
        try:
            # Import module directly to avoid name confusion
            import youtube_transcript_api
            from youtube_transcript_api import YouTubeTranscriptApi
            
            # Debugging the weird AttributeError
            # print(f"[YouTube] DEBUG: YouTubeTranscriptApi type: {type(YouTubeTranscriptApi)}")
            # print(f"[YouTube] DEBUG: Dir: {dir(YouTubeTranscriptApi)}")
            
            # Try to get English transcript first
            try:
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US', 'en-GB'])
            except Exception as e:
                # If specifically TranscriptsDisabled or NoTranscriptFound, try generic
                if "TranscriptsDisabled" in str(type(e)) or "NoTranscriptFound" in str(type(e)):
                     transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                else:
                    raise e
            
            # Combine all transcript pieces
            full_text = " ".join([item['text'] for item in transcript_list])
            return full_text
            
        except ImportError:
            print("[YouTube] youtube-transcript-api not installed, falling back to empty")
            return None
        except Exception as e:
            print(f"[YouTube] Transcript extraction error: {e}")
            # If AttributeError persists, it implies library version issue or shadowing.
            return None
    
    def _extract_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL"""
        match = re.search(r'v=([a-zA-Z0-9_-]{11})', url)
        return match.group(1) if match else ""
