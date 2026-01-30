import asyncio
import os
from dotenv import load_dotenv

# Load env from discovery_service/.env
load_dotenv("discovery_service/.env")

from discovery_service.scrapers.amazon_client import AmazonClient

async def main():
    client = AmazonClient()
    query = "Ergonomic Office Chair"
    print(f"Searching for: {query}...")
    
    # Enable verbose logging in client if possible or just print result
    asins = await client.search_products(query)
    print(f"Found ASINs: {asins}")
    
    if not asins:
        print("Search failed. Check your API Key or Response format.")

if __name__ == "__main__":
    asyncio.run(main())
