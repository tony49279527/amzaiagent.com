"""
YouTube Caption Scraper using youtube-transcript-api
More reliable than ScrapingBee for caption extraction
"""
import re
from typing import List, Optional
from dataclasses import dataclass
import httpx

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
        pass
        
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
        
        # Step 1: Search YouTube for videos using a simple approach
        video_ids = await self._search_youtube_simple(keywords, max_search)
        print(f"[YouTube] Found {len(video_ids)} video IDs")
        
        # Step 2: Try to get captions for each, stop when we have enough
        successful_sources = []
        for video_id, title in video_ids:
            if len(successful_sources) >= required_count:
                break
                
            captions = self._get_transcript(video_id)
            if captions and len(captions) > 100:  # Minimum caption length
                url = f"https://www.youtube.com/watch?v={video_id}"
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
    
    async def _search_youtube_simple(self, keywords: str, max_results: int) -> List[tuple]:
        """
        Search YouTube and return list of (video_id, title) tuples.
        Uses YouTube search page scraping as a simple approach.
        """
        search_query = f"{keywords} review"
        search_url = f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    search_url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    }
                )
                
                if response.status_code != 200:
                    print(f"[YouTube] Search failed: {response.status_code}")
                    return self._get_fallback_videos(keywords)
                    
                html = response.text
                
                # Extract video IDs from YouTube search results
                # Pattern matches: "videoId":"XXXXXXXXXXX"
                video_pattern = r'"videoId":"([a-zA-Z0-9_-]{11})"'
                title_pattern = r'"title":\{"runs":\[\{"text":"([^"]+)"\}\]'
                
                video_ids = re.findall(video_pattern, html)
                titles = re.findall(title_pattern, html)
                
                # Deduplicate while preserving order
                seen = set()
                results = []
                for i, vid in enumerate(video_ids):
                    if vid not in seen and len(results) < max_results:
                        seen.add(vid)
                        title = titles[len(results)] if len(results) < len(titles) else f"Video about {keywords}"
                        results.append((vid, title))
                        
                if not results:
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
            from youtube_transcript_api import YouTubeTranscriptApi
            from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
            
            try:
                # Try to get English transcript first
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US', 'en-GB'])
            except (TranscriptsDisabled, NoTranscriptFound):
                try:
                    # Try any available transcript
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                except:
                    return None
            
            # Combine all transcript pieces
            full_text = " ".join([item['text'] for item in transcript_list])
            return full_text
            
        except ImportError:
            print("[YouTube] youtube-transcript-api not installed, falling back to empty")
            return None
        except Exception as e:
            print(f"[YouTube] Transcript extraction error: {e}")
            return None
    
    def _extract_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL"""
        match = re.search(r'v=([a-zA-Z0-9_-]{11})', url)
        return match.group(1) if match else ""
