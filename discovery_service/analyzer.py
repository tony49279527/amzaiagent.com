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
        return self._get_default_sources(category, keywords)
    
    def _get_default_sources(self, category: str, keywords: str) -> List[dict]:
        """
        Use DuckDuckGo to find real, relevant URLs for analysis.
        This replaces the hallucinated or hardcoded approach.
        """
        from duckduckgo_search import DDGS
        
        search_query = f"{keywords} reviews reddit blog forum"
        print(f"Searching web for: {search_query}...")
        
        results_data = []
        
        # 1. Try DuckDuckGo
        try:
            with DDGS() as ddgs:
                # DDGS returns: {'title', 'href', 'body'}
                results = list(ddgs.text(search_query, max_results=25))
                
                if not results:
                    print("No results via standard DDGS, trying safesearch off...")
                    results = list(ddgs.text(search_query, max_results=25, safesearch="off"))
                
                if results:
                    for r in results:
                        u = r['href']
                        if any(x in u for x in ["reddit.com", "youtube.com", "tomshardware", "cnet", "nytimes", "consumer", "pet"]):
                            results_data.append({
                                "url": u,
                                "title": r.get('title', 'Web Search Result'),
                                "body": r.get('body', "")
                            })
                    
                    # If filtering left too few, take non-filtered
                    if len(results_data) < 3:
                        for r in results[:5]:
                            if not any(d['url'] == r['href'] for d in results_data):
                                results_data.append({
                                    "url": r['href'],
                                    "title": r.get('title', 'Web Search Result'),
                                    "body": r.get('body', "")
                                })
                    
                    print(f"Found {len(results_data)} relevant URLs via DuckDuckGo.")
        except Exception as e:
            print(f"DuckDuckGo search failed: {e}")

        # 2. Fallback to Google Search if DDGS failed or found nothing
        if not results_data:
            print("Result list empty. Trying Google Search fallback...")
            try:
                from googlesearch import search
                # googlesearch-python returns list of URLs
                g_results = list(search(search_query, num_results=15, advanced=True))
                
                for r in g_results:
                    # advanced=True returns objects with .url, .title, .description in some versions,
                    # but check if it returns string or object.
                    # safe usage: check type or attributes.
                    # actually googlesearch-python 'advanced=True' returns objects. 
                    # standard 'search' returns strings. Let's use standard to be safe if version varies, 
                    # OR try advanced and catch error.
                    # Let's use simple string search first to be robust.
                    pass
                
                # Re-doing with standard search for maximum compatibility
                g_urls = list(search(search_query, num_results=15))
                
                for u in g_urls:
                    if any(x in u for x in ["reddit.com", "youtube.com", "tomshardware", "cnet", "nytimes", "consumer", "pet"]):
                        results_data.append({
                            "url": u,
                            "title": "Google Search Result",
                            "body": "" # No snippet avail
                        })
                
                if len(results_data) < 3 and g_urls:
                    for u in g_urls[:5]:
                        if not any(d['url'] == u for d in results_data):
                            results_data.append({
                                "url": u,
                                "title": "Google Search Result", 
                                "body": ""
                            })
                            
                print(f"Found {len(results_data)} via Google Search")
            except Exception as e:
                print(f"Google Search failed: {e}")

        # 3. Last Resort: Generate dynamic fallback URLs based on keywords
        if not results_data:
            print("All search methods failed. Using dynamic fallback URLs.")
            safe_keywords = keywords.replace(' ', '+')
            safe_keywords_dash = keywords.replace(' ', '-')
            
            # Generate multiple fallback sources that are likely to exist
            fallback_sources = [
                {
                    "url": f"https://old.reddit.com/search/?q={safe_keywords}&sort=relevance&t=year",
                    "title": f"Reddit: {keywords} discussions",
                    "body": f"User discussions and reviews about {keywords} on Reddit. Includes pros, cons, and real user experiences."
                },
                {
                    "url": f"https://www.reddit.com/r/BuyItForLife/search/?q={safe_keywords}&restrict_sr=1",
                    "title": f"r/BuyItForLife: {keywords}",
                    "body": f"Quality-focused discussions about {keywords} from users who value durability and long-term value."
                },
                {
                    "url": f"https://www.reddit.com/r/Frugal/search/?q={safe_keywords}&restrict_sr=1",
                    "title": f"r/Frugal: {keywords} recommendations",
                    "body": f"Budget-conscious recommendations for {keywords}."
                },
                {
                    "url": f"https://www.nytimes.com/wirecutter/search/?s={safe_keywords}",
                    "title": f"Wirecutter: {keywords} reviews",
                    "body": f"Professional product testing and recommendations for {keywords}."
                },
                {
                    "url": f"https://www.consumerreports.org/search/?query={safe_keywords}",
                    "title": f"Consumer Reports: {keywords}",
                    "body": f"Independent product testing and ratings for {keywords}."
                },
                {
                    "url": f"https://www.cnet.com/search/?query={safe_keywords}",
                    "title": f"CNET: {keywords} reviews",
                    "body": f"Tech reviews and buying guides for {keywords}."
                },
                {
                    "url": f"https://www.tomsguide.com/search?searchTerm={safe_keywords}",
                    "title": f"Tom's Guide: {keywords}",
                    "body": f"Expert reviews and comparisons for {keywords}."
                },
                {
                    "url": f"https://www.techradar.com/search?searchTerm={safe_keywords}",
                    "title": f"TechRadar: {keywords} reviews",
                    "body": f"In-depth tech product reviews for {keywords}."
                },
            ]
            
            return fallback_sources[:10]  # Return up to 10 sources
            
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
        
        report = await self.ai_client.generate_with_retry(prompt, model=model)
        
        if not report:
            raise Exception("Failed to generate report after retries")
        
        return report
    
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
        
        youtube_sources = await self.fetch_youtube_sources(request.keywords)
        
        await emit("YouTube Research", f"Got {len(youtube_sources)} video transcripts.", 45, {
            "log": f"Scraped captions from {len(youtube_sources)} YouTube videos."
        })
        
        # Combine web and YouTube sources
        all_sources = web_sources + youtube_sources
        print(f"Total sources for analysis: {len(all_sources)} ({len(web_sources)} web + {len(youtube_sources)} YouTube)")
        
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
