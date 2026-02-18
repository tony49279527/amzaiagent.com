# Product Discovery Service

AI-powered Amazon product discovery and market analysis service.

## Setup

1. Install dependencies:
```bash
cd discovery_service
pip install -r requirements.txt
```

2. Set environment variables:
```bash
# Create .env file
OPENROUTER_API_KEY=your_key_here
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

3. Run the service:
```bash
python -m discovery_service.main
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.

## Quick Test

```python
import requests

response = requests.post("http://localhost:8000/api/discovery/analyze-sync", json={
    "category": "Kitchen & Dining",
    "keywords": "coffee maker",
    "marketplace": "US",
    "user_name": "Test User",
    "user_email": "test@example.com",
    "user_tier": "free"
})

print(response.json())
```

## Architecture

```
discovery_service/
├── main.py              # FastAPI application
├── analyzer.py          # Core analysis orchestrator
├── models.py            # Data models
├── config.py            # Configuration
├── scrapers/
│   ├── scrapingbee_client.py  # Web scraping
│   └── amazon_client.py       # Amazon data
└── ai/
    ├── openrouter_client.py   # LLM client
    └── prompts.py             # Prompt templates
```

## Features

- ✅ Automatic web source discovery
- ✅ Reddit & YouTube scraping
- ✅ Amazon product data fetching
- ✅ AI-powered analysis with multiple models
- ✅ Free & Pro tier support
- ✅ Background processing
- ✅ Email delivery (TODO)
- ✅ Report storage

## Next Steps

1. Add email sending functionality
2. Add database for report persistence
3. Add user authentication
4. Add rate limiting
5. Deploy to production
