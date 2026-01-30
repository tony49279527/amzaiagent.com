import asyncio
import os
from dotenv import load_dotenv

# Load env from discovery_service/.env
load_dotenv("discovery_service/.env")

from discovery_service.scrapers.amazon_client import AmazonClient

async def main():
    client = AmazonClient()
    asin = "B07ZPKBL9V" # User provided ASIN
    print(f"Fetching details for ASIN: {asin}...")
    
    product = await client.get_product_details(asin)
    
    if product:
        print(f"Success! Found: {product.title}")
        print(f"Price: {product.price}")
    else:
        print("❌ Failed to fetch product details.")

if __name__ == "__main__":
    asyncio.run(main())
