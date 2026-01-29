
import os
import json
import time
import feedparser
from datetime import datetime, timedelta
from openai import OpenAI
from supabase import create_client, Client
import re
from bs4 import BeautifulSoup

# ==========================================
# 🔧 用户控制面板 (USER CONTROL PANEL)
# ==========================================

# 1. RSS 订阅列表 (已更新为用户精选列表)
RSS_FEEDS = [
    "https://aws.amazon.com/blogs/aws/feed/", 
    "https://www.amazon.science/index.xml",
    "https://www.marketplacepulse.com/articles/recent.atom",
    "http://www.ecommercebytes.com/feed/",
    "https://www.helium10.com/blog/feed/",
    "https://www.junglescout.com/feed/",
    "https://www.sellerlabs.com/blog/feed/",
    "https://www.ecomengine.com/blog/rss.xml",
    "https://tamebay.com/feed",
    "https://retaildive.com/feeds/news/",
]

# 2. 只有最近 N 天的新闻才会被采用 (防止写出旧闻)
NEWS_MAX_AGE_DAYS = 7

# 3. 每天发布文章数量限制
LIMIT_POSTS_PER_RUN = 1

# 4. AI 模型选择
AI_MODEL_NAME = "anthropic/claude-3.5-sonnet"

# ==========================================
# ⚙️ 系统配置 (System Config) - 勿动
# ==========================================

# Initialize Clients
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
site_url = "https://amzaiagent.com"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=openrouter_api_key,
    default_headers={
        "HTTP-Referer": site_url,
        "X-Title": "Amz AI Agent Bot",
    },
)

try:
    if supabase_url and supabase_key:
        supabase: Client = create_client(supabase_url, supabase_key)
    else:
        print("Warning: Supabase credentials missing. DB save will be skipped.")
        supabase = None
except Exception as e:
    print(f"Supabase init warning: {e}")
    supabase = None

def clean_html(raw_html):
    CLEANR = re.compile('<.*?>') 
    cleantext = re.sub(CLEANR, '', raw_html)
    return cleantext

def extract_image_from_entry(entry):
    """
    Attempt to extract the best image URL from an RSS entry.
    Priority:
    1. Media Content / Enclosures (Standard RSS)
    2. Parsing <img src> from description/summary (BeautifulSoup)
    3. None (Bot will use topic-based fallback later)
    """
    # 1. Check media_content or enclosures
    if hasattr(entry, 'media_content'):
        for media in entry.media_content:
            if media.get('type', '').startswith('image') or 'medium' in media:
                return media.get('url')
                
    if hasattr(entry, 'media_thumbnail'):
        for media in entry.media_thumbnail:
            return media.get('url')
            
    if hasattr(entry, 'enclosures'):
        for enclosure in entry.enclosures:
            if enclosure.get('type', '').startswith('image'):
                return enclosure.get('href')

    # 2. Parse HTML content for <img> tags
    content_html = ""
    if hasattr(entry, 'content'):
        content_html = entry.content[0].value
    elif hasattr(entry, 'summary'):
        content_html = entry.summary
    elif hasattr(entry, 'description'):
        content_html = entry.description
        
    if content_html:
        try:
            soup = BeautifulSoup(content_html, 'lxml')
            img_tag = soup.find('img')
            if img_tag and img_tag.get('src'):
                return img_tag.get('src')
        except Exception:
            pass
            
    return None

def fetch_and_filter_candidates():
    """
    Fetch news from ALL feeds and filter by date.
    Returns a list of valid candidate items.
    """
    print("Fetching RSS feeds from all sources...")
    candidates = []
    
    cutoff_date = datetime.now() - timedelta(days=NEWS_MAX_AGE_DAYS)
    
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            print(f"Checking {feed_url} - Found {len(feed.entries)} entries")
            
            for entry in feed.entries[:5]: 
                # Check date
                published_time = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_time = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    published_time = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
                
                if not published_time:
                    continue
                
                # Filter by age
                if published_time > cutoff_date:
                    # Extract Image
                    img_url = extract_image_from_entry(entry)
                    
                    candidates.append({
                        "source": feed.feed.get('title', 'Unknown Source'),
                        "title": entry.title,
                        "link": entry.link,
                        "summary": clean_html(getattr(entry, 'summary', '') or getattr(entry, 'description', ''))[:300],
                        "published": published_time.strftime("%Y-%m-%d"),
                        "image_url": img_url # Can be None
                    })
        except Exception as e:
            print(f"Error parsing {feed_url}: {e}")
            continue
            
    print(f"Total valid candidates found (last {NEWS_MAX_AGE_DAYS} days): {len(candidates)}")
    return candidates

def select_best_article(candidates):
    """
    Uses LLM to pick the best article from the list.
    """
    if not candidates:
        return None
        
    print("Asking AI to select the best topic...")
    
    candidates_list_str = ""
    for idx, item in enumerate(candidates):
        has_img = "✅" if item['image_url'] else "❌"
        candidates_list_str += f"[{idx}] Source: {item['source']} | Title: {item['title']} | Date: {item['published']} | Image: {has_img}\n"
        
    prompt = f"""
    You are an expert editor for "Amz AI Agent". Select the ONE most impactful news story for Amazon Sellers.
    
    Criteria:
    1. Relevance: Must impact Amazon FBA Sellers directly.
    2. Visuals: Prefer stories that have an Image (✅) if the quality/relevance is equal.
    3. Value: Strategic value over gossip.
    
    Candidate List:
    {candidates_list_str}
    
    Return ONLY JSON:
    {{
        "best_index": 0,
        "reason": "Explain why"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model=AI_MODEL_NAME, 
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
            
        selection = json.loads(content.strip())
        best_idx = selection.get("best_index", 0)
        
        return candidates[best_idx]
        
    except Exception as e:
        print(f"AI Selection failed: {e}. Defaulting to first candidate.")
        return candidates[0]

def generate_cover_image(title, slug):
    """
    Generate a cover image using OpenRouter's gpt-5-image model.
    Returns the relative path to the saved image.
    """
    print(f"Generating AI cover image for: {title}...")
    
    # Create a prompt for the image
    image_prompt = f"""Create a professional, modern blog cover image for an Amazon FBA seller blog article titled: "{title}". 
    
    Style requirements:
    - Clean, professional business/e-commerce aesthetic
    - Modern gradient background (blue/purple tones)
    - Abstract geometric shapes or subtle icons related to e-commerce
    - No text in the image
    - High contrast, suitable for web thumbnail
    - 16:9 aspect ratio
    - Minimalist design suitable for a tech/business blog
    """
    
    
    # Try Pollinations.ai (Free, fast, URL-based)
    # Try Pollinations.ai (Free, fast, URL-based)
    try:
        # 1. FIXED STYLE PROMPT (The "System" Prompt)
        # Defines the consistent look and feel
        style_prompt = "isometric 3d illustration, soft studio lighting, amazon aws brand colors (dark blue and orange), clean minimalist background, high quality 3d render, unreal engine 5, 4k"
        
        # 2. CONTENT PROMPT (The "User" Prompt)
        # Extracts the core subject from the title
        subject = title.lower()
        subject = subject.replace("amazon", "").replace("fba", "").replace("2026", "").replace("update", "")
        # Remove non-alphanumeric chars
        import re
        subject = re.sub(r'[^\w\s]', '', subject).strip()
        
        # Combine them
        final_prompt = f"{subject}, {style_prompt}"
        
        import urllib.parse
        encoded_prompt = urllib.parse.quote(final_prompt)
        # Add random seed and no-logo param
        import random
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={random.randint(0, 10000)}&width=800&height=450&nologo=true"
        
        print(f"Generating image via Pollinations.ai: {image_url}")
        
        image_filename = f"{slug}.png"
        image_path = f"assets/images/blog_thumbs/{image_filename}"
        
        os.makedirs("assets/images/blog_thumbs", exist_ok=True)
        
        # Download with a timeout
        import requests
        resp = requests.get(image_url, timeout=60)
        if resp.status_code == 200:
            with open(image_path, 'wb') as f:
                f.write(resp.content)
            print(f"Pollinations Image saved to: {image_path}")
            return image_path
            
    except Exception as e:
        print(f"Pollinations generation failed: {e}")
    
    # Fallback to existing images if AI generation fails
    print("Falling back to default images...")
    t = title.lower()
    
    # More specific keyword matching (order matters - check specific terms first)
    if "algorithm" in t or "cosmo" in t or "rufus" in t or "ranking" in t or "a9" in t or "a10" in t:
        return "assets/images/blog_thumbs/algo.png"
    if "seo" in t or "keyword" in t or "search" in t or "intent" in t:
        return "assets/images/blog_thumbs/seo_intent.png"
    if "image" in t or "visual" in t or "photo" in t or "listing optimization" in t:
        return "assets/images/blog_thumbs/visual_opt.png"
    if "package" in t or "shipping" in t or "logistic" in t or "fulfillment" in t:
        return "assets/images/blog_thumbs/packaging.png"
    if "efficiency" in t or "cost" in t or "time" in t or "save" in t or "profit" in t:
        return "assets/images/blog_thumbs/efficiency.png"
    if "sop" in t or "team" in t or "process" in t or "operation" in t or "workflow" in t:
        return "assets/images/blog_thumbs/sop.png"
    if "blue ocean" in t or "niche" in t or "opportunity" in t or "case study" in t:
        return "assets/images/blog_thumbs/blue_ocean.png"
    if "ai" in t or "automation" in t or "agentic" in t or "agent" in t:
        return "assets/images/blog_thumbs/agentic.png"
    if "return" in t or "refund" in t or "policy" in t:
        return "assets/images/blog_thumbs/sop.png"
    if "seller" in t or "registration" in t or "account" in t:
        return "assets/images/blog_thumbs/efficiency.png"
    
    # Random selection from all available images as final fallback
    import random
    fallback_images = [
        "assets/images/blog_thumbs/agentic.png",
        "assets/images/blog_thumbs/algo.png",
        "assets/images/blog_thumbs/blue_ocean.png",
        "assets/images/blog_thumbs/efficiency.png",
        "assets/images/blog_thumbs/seo_intent.png",
        "assets/images/blog_thumbs/sop.png",
        "assets/images/blog_thumbs/visual_opt.png",
    ]
    return random.choice(fallback_images)


def generate_blog_post(news_item):
    """Uses LLM to write a blog post based on the selected news."""
    print(f"Generating content for: {news_item['title']}...")
    
    prompt = f"""
    You are an expert Amazon FBA consultant and SEO Strategist (E-E-A-T compliant). 
    Your goal is to write a world-class blog post that ranks #1 on Google.
    
    Source Material:
    - Title: {news_item['title']}
    - Summary: {news_item['summary']}
    - Link: {news_item['link']}
    
    ==================================================
    MANDATORY SEO REQUIREMENTS (Strict Enforcement)
    ==================================================
    
    1. 🔍 **Keyword Strategy**:
       - Primary Keyword: Identify the most searchable term related to this news (e.g., "Amazon FBA Fee Change 2026").
       - Placement: Must appear in the **First H1 Title**, **First Paragraph (first 100 words)**, and **at least one H2**.
    
    2. 🔗 **Internal Linking Strategy**:
       - You MUST contextually link to at least 2 internal pages if relevant:
         - <a href="/index.html">Amz AI Agent Home</a> (for general tools)
         - <a href="/faq.html">FBA FAQ</a> (for questions)
         - <a href="/about.html">About Us</a>
       - Do NOT force them; weave them naturally into the text (e.g., "Use tools like <a href='/index.html'>Amz AI Agent</a> to monitor these changes...").
    
    3. 🖼️ **Image Optimization**:
       - If you insert the image, the `<img>` tag MUST have a descriptive `alt` attribute containing the Primary Keyword.
       - Syntax: <img src="{news_item['image_url'] or 'PLACEHOLDER'}" alt="[Primary Keyword] - Descriptive Text" class="rounded-lg my-4 w-full object-cover">
    
    4. 🧩 **Structure & Readability**:
       - **H1**: High-impact title.
       - **Intro**: Hook the reader immediately. State the "What" and "Why".
       - **H2**: Deep dive into the details.
       - **H2**: Impact on Sellers (The "So What?").
       - **H2**: 3 Actionable Steps (Bulleted list).
       - **H2**: Frequently Asked Questions (FAQ) - **Crucial for SEO Snippets**.
         - Write 3 Q&A pairs related to the news.
       - **Conclusion**: Brief summary + Call to Action (CTA).
    
    5. 📣 **Engagement**:
       - End with a question to encourage comments.
    
    Output JSON format ONLY:
    {{
        "title": "Optimized Title Here",
        "slug": "optimized-url-slug-contain-keywords",
        "excerpt": "SEO Meta Description (Max 160 chars) - Must be click-worthy.",
        "content_html": "<div>...full html content...</div>",
        "tags": ["Tag1", "Tag2", "SEO Keyword"]
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model=AI_MODEL_NAME, 
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content.strip()
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        content = content.strip()
        content = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', content)
        
        data = json.loads(content)
        
        # Generate AI cover image (with fallback built-in)
        final_image = generate_cover_image(data['title'], data['slug'])
            
        # Inject Image into HTML if bot didn't (or replace placeholder)
        if 'PLACEHOLDER' in data['content_html']:
             data['content_html'] = data['content_html'].replace('PLACEHOLDER', final_image)
        
        # Make sure we have the cover image field for the JSON listing
        data['cover_image'] = final_image
        
        return data
        
    except Exception as e:
        print(f"Generation failed: {e}")
        return None

def save_to_supabase(post_data, source_link):
    if not supabase: return
    
    print("Saving to Supabase...")
    db_record = {
        "title": post_data["title"],
        "slug": post_data["slug"],
        "summary": post_data["excerpt"],
        "content": post_data["content_html"],
        "author": "Amz AI Agent",
        "tags": post_data["tags"],
        "status": "published",
        "published_at": datetime.now().isoformat(),
        "cover_image": post_data.get('cover_image', "images/blog_thumbs/default_news.png"),
        "source_url": source_link
    }
    
    try:
        supabase.table("blog_posts").insert(db_record).execute()
        print("Saved to DB.")
    except Exception as e:
        print(f"DB Error (ignored): {e}")

def save_to_json(post_data, source_link):
    """
    Save the new post to blog_posts.js (JavaScript module format).
    This is the file that blog.html actually reads from.
    """
    print("Saving to blog_posts.js...")
    js_path = "data/blog/blog_posts.js"
    
    new_entry = {
        "id": post_data["slug"],
        "title": post_data["title"],
        "date": datetime.now().strftime("%B %d, %Y"),  # Human-readable format like existing posts
        "author": "Amz AI Agent",
        "cover_image": post_data.get('cover_image', "assets/images/blog_thumbs/default_news.png"),
        "tags": post_data["tags"],
        "content": post_data["content_html"],
    }

    try:
        # Read existing JS file and extract the JSON array
        existing_posts = []
        if os.path.exists(js_path):
            with open(js_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract the blogPostsEN array
                match = re.search(r'window\.blogPostsEN\s*=\s*(\[[\s\S]*?\]);', content)
                if match:
                    existing_posts = json.loads(match.group(1))
        
        # Check for duplicates
        if any(d.get('id') == new_entry['id'] for d in existing_posts):
            print("Duplicate slug detected. Skipping save.")
            return

        # Insert new post at the beginning
        existing_posts.insert(0, new_entry)
        
        # Write back as JavaScript module
        js_content = f"""
window.blogPostsCN = [];
window.blogPostsEN = {json.dumps(existing_posts, indent=2, ensure_ascii=False)};
"""
        with open(js_path, 'w', encoding='utf-8') as f:
            f.write(js_content)
        print("Success: blog_posts.js updated.")
        
    except Exception as e:
        print(f"JS Save Error: {e}")

def main():
    candidates = fetch_and_filter_candidates()
    
    if not candidates:
        print("No recent news found (last 48 hours). Resting today.")
        return

    best_news = select_best_article(candidates)
    if not best_news:
        return

    blog_post = generate_blog_post(best_news)
    
    if blog_post:
        save_to_supabase(blog_post, best_news['link'])
        save_to_json(blog_post, best_news['link'])

if __name__ == "__main__":
    main()
