"""
Enhanced Amazon Client with better data extraction
"""
import httpx
from typing import Optional, List
from ..config import RAPIDAPI_KEY, RAPIDAPI_HOST
from ..models import AmazonProduct


class AmazonClient:
    """Enhanced client for Amazon data via Rapid API"""
    
    def __init__(self, api_key: str = RAPIDAPI_KEY):
        self.api_key = api_key
        self.host = RAPIDAPI_HOST
        self.base_url = f"https://{self.host}"
        self.headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": self.host
        }
    
    async def get_product_details(self, asin: str, marketplace: str = "US") -> Optional[AmazonProduct]:
        """
        Get product details with enhanced field extraction
        """
        url = f"{self.base_url}/product-details"
        
        params = {
            "asin": asin,
            "country": marketplace
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:  # Increased timeout
                response = await client.get(url, headers=self.headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    product_data = data.get("data", {})
                    
                    # Enhanced field extraction - try multiple field names
                    features = (
                        product_data.get("feature_bullets") or
                        product_data.get("features") or
                        product_data.get("product_features") or
                        product_data.get("bullet_points") or
                        []
                    )
                    
                    # Extract price from multiple possible fields
                    price = (
                        product_data.get("product_price") or
                        product_data.get("price") or
                        product_data.get("product_original_price")
                    )
                    
                    # Extract rating
                    rating = (
                        product_data.get("product_star_rating") or
                        product_data.get("rating") or
                        product_data.get("star_rating")
                    )
                    
                    # Extract review count
                    review_count = (
                        product_data.get("product_num_ratings") or
                        product_data.get("review_count") or
                        product_data.get("ratings_total")
                    )
                    
                    return AmazonProduct(
                        asin=asin,
                        title=product_data.get("product_title", ""),
                        price=price,
                        rating=rating,
                        review_count=review_count,
                        features=features
                    )
                else:
                    print(f"[Amazon API] Error {response.status_code} for ASIN {asin}")
                    return None
                    
        except Exception as e:
            print(f"[Amazon API] Exception for {asin}: {str(e)}")
            return None
    
    async def get_product_reviews(
        self, 
        asin: str, 
        marketplace: str = "US", 
        max_reviews: int = 100  # Increased default
    ) -> List[dict]:
        """
        Get product reviews with pagination support
        """
        all_reviews = []
        page = 1
        max_pages = 5  # Get up to 5 pages to reach ~100 reviews
        
        while len(all_reviews) < max_reviews and page <= max_pages:
            url = f"{self.base_url}/product-reviews"
            
            params = {
                "asin": asin,
                "country": marketplace,
                "page": str(page)
            }
            
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.get(url, headers=self.headers, params=params)
                    
                    if response.status_code == 200:
                        data = response.json()
                        reviews_data = data.get("data", {}).get("reviews", [])
                        
                        if not reviews_data:
                            break  # No more reviews
                        
                        # Standardize review format
                        for review in reviews_data:
                            all_reviews.append({
                                "rating": review.get("review_star_rating"),
                                "title": review.get("review_title"),
                                "text": review.get("review_comment"),
                                "verified": review.get("is_verified_purchase", False),
                                "date": review.get("review_date"),
                                "helpful_count": review.get("helpful_vote_count", 0)
                            })
                        
                        page += 1
                        
                        if len(all_reviews) >= max_reviews:
                            break
                    else:
                        print(f"[Reviews] Error {response.status_code} for ASIN {asin} page {page}")
                        break
                        
            except Exception as e:
                print(f"[Reviews] Exception for {asin} page {page}: {str(e)}")
                break
        
        print(f"[Reviews] Fetched {len(all_reviews)} reviews for {asin}")
        return all_reviews[:max_reviews]
    
    async def get_full_product_data(self, asin: str, marketplace: str = "US") -> Optional[AmazonProduct]:
        """
        Get complete product data including reviews
        """
        import asyncio
        
        # Fetch product details and reviews concurrently
        product_task = self.get_product_details(asin, marketplace)
        reviews_task = self.get_product_reviews(asin, marketplace, max_reviews=100)
        
        product, reviews = await asyncio.gather(product_task, reviews_task)
        
        if product:
            product.reviews = reviews
        
        return product
    
    async def get_multiple_products(self, asins: List[str], marketplace: str = "US") -> List[AmazonProduct]:
        """
        Get data for multiple ASINs concurrently
        """
        import asyncio
        
        tasks = [self.get_full_product_data(asin, marketplace) for asin in asins]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None and exceptions
        products = []
        for result in results:
            if isinstance(result, AmazonProduct):
                products.append(result)
        
        return products
    async def search_products(self, query: str, country: str = "US", limit: int = 10) -> List[str]:
        """
        Search for products and return list of ASINs
        """
        url = f"{self.base_url}/search"
        params = {
            "query": query,
            "country": country,
            "sort_by": "RELEVANCE",
            "page": "1"
        }
        
        print(f"[Amazon Search] Searching for '{query}' in {country}...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self.headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    products = data.get("data", {}).get("products", [])
                    
                    asins = []
                    for p in products:
                        if p.get("asin"):
                            asins.append(p.get("asin"))
                            
                    print(f"[Amazon Search] Found {len(asins)} ASINs")
                    return asins[:limit]
                else:
                    print(f"[Amazon Search] Error {response.status_code}: {response.text}")
                    return []
                    
        except Exception as e:
            print(f"[Amazon Search] Exception: {str(e)}")
            return []
