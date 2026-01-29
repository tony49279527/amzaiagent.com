"""
Core Product Discovery Analyzer
Orchestrates the entire analysis workflow
"""
import json
import asyncio
from datetime import datetime
from typing import List, Optional
import uuid

from .models import (
    DiscoveryRequest,
    AnalysisReport,
    WebSource,
    AmazonProduct,
    UserTier
)
from .scrapers import ScrapingBeeClient, AmazonClient
from .scrapers.youtube_client import YouTubeClient, YouTubeSource
from .ai import (
    OpenRouterClient,
    get_source_finder_prompt,
    get_free_tier_prompt,
    get_pro_tier_prompt,
    get_quick_summary_prompt
)
from .config import DEFAULT_MODEL_FREE, DEFAULT_MODEL_PRO, FREE_WEB_SOURCES_COUNT, FREE_YOUTUBE_SOURCES_COUNT


class ProductDiscoveryAnalyzer:
    """Main analyzer for product discovery"""
    
    def __init__(self):
        self.scraping_bee = ScrapingBeeClient()
        self.amazon_client = AmazonClient()
        self.ai_client = OpenRouterClient()
        self.youtube_client = YouTubeClient()
    
    async def find_research_sources(
        self,
        category: str,
        keywords: str,
        marketplace: str
    ) -> List[dict]:
        """
        Use AI to find relevant URLs to scrape
        
        Returns:
            List of dicts with url, title, body/reason
        """
        # For now, bypass LLM and go straight to DuckDuckGo for reliability
        return await self._get_default_sources(category, keywords)
    
    async def _get_default_sources(self, category: str, keywords: str) -> List[dict]:
        """
        Use Google Custom Search API (Official) to find real, relevant URLs.
        """
        from .config import GOOGLE_API_KEY, GOOGLE_CX
        import httpx
        
        search_query = f"{keywords} reviews reddit blog forum"
        print(f"[Search] Searching Google (Official API) for: {search_query}...")
        
        results_data = []
        
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": GOOGLE_API_KEY,
                "cx": GOOGLE_CX,
                "q": search_query,
                "num": 10
            }
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, params=params)
                
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                print(f"[Search] API returned {len(items)} raw results.")
                
                for item in items:
                    u = item.get("link")
                    title = item.get("title", "Google Result")
                    snippet = item.get("snippet", "")
                    
                    if not u: continue
                    
                    # Filter out irrelevant domains
                    if "google.com" in u: continue
                    
                    results_data.append({
                        "url": u,
                        "title": title,
                        "body": snippet
                    })
                    
                print(f"[Search] Found {len(results_data)} relevant URLs via Google API.")
            else:
                print(f"[Search] Google API Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"[Search] Google API Exception: {e}")

        # If API fails, return empty list (and let fallback logic handle it)
        if not results_data:
             print("[Search] Warning: No sources found via Google API.")
             return []
             
        return results_data
            
        return results_data[:20]
    
    async def scrape_web_sources(
        self, 
        search_results: List[dict], 
        required_count: int = FREE_WEB_SOURCES_COUNT
    ) -> List[WebSource]:
        """
        Scrape URLs until we have `required_count` successful sources with real content.
        Uses fallback to snippets only if scraping fails completely.
        """
        print(f"[Web] Attempting to scrape {len(search_results)} URLs, need {required_count} with content...")
        
        successful_sources = []
        
        for i, result in enumerate(search_results):
            if len(successful_sources) >= required_count:
                print(f"[Web] Got {required_count} successful sources, stopping.")
                break
            
            url = result["url"]
            print(f"[Scraping] Starting {i+1}/{len(search_results)}: {url[:60]}...")
            
            # Try to scrape this single URL
            scraped = await self.scraping_bee.scrape_url(url)
            
            if scraped and scraped.content and len(scraped.content) > 500:
                print(f"[Web] ✓ Got content for: {url[:50]}... ({len(scraped.content)} chars)")
                successful_sources.append(scraped)
            else:
                # Try snippet as last resort for this URL
                snippet = result.get("body", "")
                if snippet and len(snippet) > 100:
                    print(f"[Web] ~ Using snippet for: {url[:50]}...")
                    successful_sources.append(WebSource(
                        url=url,
                        title=result.get("title", "Search Result"),
                        content=f"[SEARCH SNIPPET] {snippet}",
                        source_type="search_snippet"
                    ))
                else:
                    print(f"[Web] ✗ No content for: {url[:50]}...")
        
        print(f"[Web] Finalized {len(successful_sources)} sources with content")
        return successful_sources
    
    async def fetch_youtube_sources(
        self,
        keywords: str,
        required_count: int = FREE_YOUTUBE_SOURCES_COUNT
    ) -> List[WebSource]:
        """
        Search YouTube and get captions for videos.
        Returns WebSource objects for compatibility with existing logic.
        """
        print(f"[YouTube] Searching for videos about: {keywords}")
        youtube_sources = await self.youtube_client.search_and_get_captions(
            keywords, 
            required_count=required_count
        )
        
        # Convert YouTubeSource to WebSource for unified handling
        web_sources = []
        for yt in youtube_sources:
            web_sources.append(WebSource(
                url=yt.url,
                title=f"[YouTube] {yt.title}",
                content=yt.captions,
                source_type="youtube"
            ))
        
        return web_sources
    
    async def fetch_amazon_data(
        self,
        asins: List[str],
        marketplace: str
    ) -> List[AmazonProduct]:
        """
        Fetch Amazon product data
        
        Args:
            asins: List of ASINs
            marketplace: Marketplace code
            
        Returns:
            List of AmazonProduct objects
        """
        if not asins:
            return []
        
        print(f"Fetching Amazon data for {len(asins)} ASINs...")
        products = await self.amazon_client.get_multiple_products(asins, marketplace)
        print(f"Successfully fetched {len(products)} products")
        return products
    
    async def generate_report(
        self,
        category: str,
        keywords: str,
        marketplace: str,
        web_sources: List[WebSource],
        amazon_products: List[AmazonProduct],
        model: str = DEFAULT_MODEL_PRO,
        user_tier: UserTier = UserTier.FREE,
        custom_prompt: Optional[str] = None
    ) -> str:
        """
        Generate the final analysis report
        """
        print(f"Generating report with {model} (Tier: {user_tier})...")
        print(f"Report Input Stats: {len(web_sources)} sources, {len(amazon_products)} products")
        
        if user_tier == UserTier.PRO:
            prompt = get_pro_tier_prompt(
                category,
                keywords,
                marketplace,
                web_sources,
                amazon_products,
                custom_focus=custom_prompt
            )
        else:
            prompt = get_free_tier_prompt(
                category,
                keywords,
                marketplace,
                web_sources,
                amazon_products
            )
        
        try:
            report = await self.ai_client.generate_with_retry(prompt, model=model)
            
            if not report:
                error_msg = f"Failed to generate report using model {model} after retries. sources={len(web_sources)} web, {len(amazon_products)} products."
                print(f"[Error] {error_msg}")
                raise Exception(error_msg)
            
            return report
        except Exception as e:
            print(f"[Error] Exception in generate_report: {str(e)}")
            raise
    
    async def analyze(self, request: DiscoveryRequest, task_id: str = None) -> AnalysisReport:
        """
        Main analysis workflow
        
        Args:
            request: Discovery request
            task_id: Optional ID for WebSocket progress tracking
            
        Returns:
            Analysis report
        """
        from .progress import progress_manager

        async def emit(step: str, status: str, progress: int, details: dict = None):
            if task_id:
                try:
                    await progress_manager.emit(task_id, step, status, progress, details)
                except Exception as e:
                    print(f"WS Emit Error: {e}")

        print(f"\n=== Starting Product Discovery Analysis ===")
        print(f"Category: {request.category}")
        print(f"Keywords: {request.keywords}")
        
        await emit("Initialization", "Starting analysis workflow...", 5, {
            "log": f"Target: {request.keywords} ({request.marketplace.value})",
            "tier": request.user_tier
        })
        
        # Step 1: Find research sources (Dicts with snippets)
        print("\n[1/5] Finding research sources...")
        await emit("Web Research", "Searching DuckDuckGo for signals...", 10)
        
        search_results = await self.find_research_sources(
            request.category,
            request.keywords,
            request.marketplace.value
        )
        
        await emit("Web Research", f"Found {len(search_results)} potential sources", 15, {
            "log": f"Top Source: {search_results[0]['title'] if search_results else 'None'}",
            "sources_preview": [s['title'] for s in search_results[:5]]
        })
        
        # Step 2: Scrape web sources (get first 3 successful)
        print("\n[2/5] Scraping web sources...")
        await emit("Web Research", "Scraping content from URL list...", 20)
        
        web_sources = await self.scrape_web_sources(search_results)
        
        await emit("Web Research", f"Scraped {len(web_sources)} pages successfully.", 30, {
            "log": f"Got {len(web_sources)} web sources with content."
        })
        
        # Step 3: Fetch YouTube sources (get first 3 with captions)
        print("\n[3/5] Fetching YouTube sources...")
        await emit("YouTube Research", "Searching YouTube for reviews...", 35)
        
        youtube_sources = []
        try:
            youtube_sources = await self.fetch_youtube_sources(request.keywords)
        except Exception as e:
            import traceback
            print(f"Error fetching YouTube sources: {e}")
            traceback.print_exc()
        
        await emit("YouTube Research", f"Got {len(youtube_sources)} video transcripts.", 45, {
            "log": f"Scraped captions from {len(youtube_sources)} YouTube videos."
        })
        
        # Combine web and YouTube sources
        all_sources = web_sources + youtube_sources
        print(f"Total sources for analysis: {len(all_sources)} ({len(web_sources)} web + {len(youtube_sources)} YouTube)")

        # ROBUSTNESS FIX: If no sources found (e.g. scraping blocked), inject synthetic source
        if not all_sources:
            print("[Analyzer] 0 sources found. Injecting Fallback Knowledge Source.")
            await emit("Web Research", "No live data found. Using internal knowledge base...", 50)
            all_sources.append(WebSource(
                url="internal://knowledge-base",
                title="AI Internal Market Knowledge",
                content=f"The live scraping for '{request.keywords}' did not yield accessible results (likely due to site protections or niche volume). The analysis will proceed using the AI's internal extensive database for the '{request.category}' category. The insights below are based on general market patterns for this product type.",
                source_type="internal_knowledge"
            ))
        
        # Step 4: Fetch Amazon data (if ASINs provided)
        print("\n[4/5] Fetching Amazon product data...")
        await emit("Amazon Data", "Fetching real-time product data...", 55)
        
        amazon_products = []
        if request.reference_asins:
            amazon_products = await self.fetch_amazon_data(
                request.reference_asins,
                request.marketplace.value
            )
            await emit("Amazon Data", f"Retrieved {len(amazon_products)} products", 65, {
                "products": [{"title": p.title[:30]+"...", "rating": p.rating, "reviews": p.review_count} for p in amazon_products]
            })
        
        # Step 5: Generate report
        print("\n[5/5] Generating analysis report...")
        
        # Determine which model to use
        if request.user_tier == UserTier.PRO and request.selected_model:
            model = request.selected_model
        elif request.user_tier == UserTier.PRO:
            model = DEFAULT_MODEL_PRO
        else:
            model = DEFAULT_MODEL_FREE
            
        await emit("AI Analysis", f"Thinking with {model}...", 75, {
             "log": f"Sending {len(all_sources)} sources + {len(amazon_products)} products to LLM."
        })
        
        report_markdown = await self.generate_report(
            request.category,
            request.keywords,
            request.marketplace.value,
            all_sources,  # Use combined web + YouTube sources
            amazon_products,
            model,
            request.user_tier,
            None # TODO: Add custom_prompt to DiscoveryRequest model
        )
        
        await emit("AI Analysis", "Report generation complete!", 95)
        
        # Convert Markdown to HTML (simple conversion)
        import markdown
        report_html = markdown.markdown(
            report_markdown,
            extensions=['tables', 'fenced_code']
        )
        
        # Create report object
        report = AnalysisReport(
            report_id=str(uuid.uuid4()),
            user_email=request.user_email,
            category=request.category,
            keywords=request.keywords,
            marketplace=request.marketplace.value,
            report_markdown=report_markdown,
            report_html=report_html,
            generated_at=datetime.utcnow().isoformat(),
            model_used=model,
            sources_count=len(all_sources),  # Count all sources
            asins_analyzed=len(amazon_products)
        )
        
        print(f"\n=== Analysis Complete ===")
        await emit("Complete", "Analysis finished successfully.", 100, {
            "report_id": report.report_id,
            "report_preview": report_markdown[:200]
        })
        
        return report
