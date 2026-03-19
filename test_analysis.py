#!/usr/bin/env python3
"""
Test script for Competitor Analysis flow.
Usage: python test_analysis.py [--base-url URL]
Default base URL: http://127.0.0.1:8000 (local) or set BASE_URL env
"""
import json
import sys
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"  # Use --url https://amzaiagent.com for production

payload = {
    "order_id": "ORD-TEST-" + str(__import__("time").time())[:10],
    "user_name": "Tony",
    "user_email": "leetony4927@gmail.com",
    "industry": "General",
    "main_asins": ["B07BGV23GK", "B0DP1X5RD7", "B0CRHJ2FP9"],
    "competitor_asins": ["B0DJ4Z4RDL", "B0BM6YWTS1", "B095NX3BFY", "B0C1RSH46Z"],
    "productSite": "US",
    "language": "en",
    "llm_model": "gpt-4o-mini",
    "custom_prompt": "",
    "reference_website_count": 5,
    "reference_youtube_count": 5,
    "version": "v1_pro_verified",
    "payment_status": "free",
    "amount_paid": 0,
}

def main():
    base = BASE_URL
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a in ("--url", "-u") and i + 1 < len(args):
            base = args[i + 1]
            break
        elif a.startswith("http"):
            base = a
            break
    url = base.rstrip("/") + "/api/proxy/free-analysis"
    print(f"POST {url}")
    print(f"Payload: main_asins={payload['main_asins']}, competitor_asins={payload['competitor_asins']}, email={payload['user_email']}")
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read().decode()
            print(f"Status: {r.status}")
            try:
                data = json.loads(body)
                print(f"Response: {json.dumps(data, indent=2)}")
                if data.get("taskId") or data.get("report_id"):
                    print("\n✅ Analysis started. Check email leetony4927@gmail.com for report.")
            except json.JSONDecodeError:
                print(f"Response (raw): {body}")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        print(e.read().decode())
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")
        sys.exit(1)

if __name__ == "__main__":
    main()
