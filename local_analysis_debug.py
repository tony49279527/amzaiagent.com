
import asyncio
import os
import sys

# Ensure current dir is in path
sys.path.append(os.getcwd())

from dotenv import load_dotenv
from discovery_service.analyzer import ProductDiscoveryAnalyzer
from discovery_service.models import DiscoveryRequest, UserTier, MarketplaceEnum

# Load env variables (API keys etc)
load_dotenv()

async def run_test():
    print("=== Starting Local Analysis Debug ===")
    
    # Mock Request
    req = DiscoveryRequest(
        category="Pet Supplies",
        keywords="Smart Bird Feeder with Camera",
        marketplace=MarketplaceEnum.US,
        user_email="aurotony4927@gmail.com",
        user_name="Local Debug User",
        user_tier=UserTier.PRO,
        reference_asins=["B09XMCGR1C"] # Example Smart Bird Feeder ASIN
    )
    
    print(f"Target: {req.keywords}")
    print(f"Email: {req.user_email}")
    
    analyzer = ProductDiscoveryAnalyzer()
    
    try:
        # We pass a dummy task_id. The emit function in analyzer handles exceptions if ws fails.
        report = await analyzer.analyze(req, task_id="local-debug-run")
        
        print("\n" + "="*50)
        print("✅ ANALYSIS COMPLETED SUCCESSFULLY!")
        print("="*50)
        print(f"Report ID: {report.report_id}")
        print(f"Generated At: {report.generated_at}")
        print(f"Sources Used: {report.sources_count}")
        print(f"Report Length: {len(report.report_markdown)} chars")
        print("-" * 20)
        print("Preview:")
        print(report.report_markdown[:500] + "...")
        
    except Exception as e:
        print("\n" + "="*50)
        print(f"❌ ANALYSIS FAILED: {str(e)}")
        print("="*50)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_test())
