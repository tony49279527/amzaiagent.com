
import os
import json
import time
import feedparser
from datetime import datetime, timedelta
from openai import OpenAI
from supabase import create_client, Client
import re

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
    # 补充备选源
    "https://tamebay.com/feed",
    "https://retaildive.com/feeds/news/",
]

# 2. 只有最近 N 天的新闻才会被采用 (防止写出旧闻)
NEWS_MAX_AGE_DAYS = 2

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

# 配置 OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=openrouter_api_key,
    default_headers={
        "HTTP-Referer": site_url,
        "X-Title": "Amz AI Agent Bot",
    },
)

# 配置 Supabase client (即使 key 缺失也不报错，方便本地无环境测试)
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

def fetch_and_filter_candidates():
    """
    Fetch news from ALL feeds and filter by date.
    Returns a list of valid candidate items.
    """
    print("Fetching RSS feeds from all sources...")
    candidates = []
    
    # Calculate cutoff time
    cutoff_date = datetime.now() - timedelta(days=NEWS_MAX_AGE_DAYS)
    
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            print(f"Checking {feed_url} - Found {len(feed.entries)} entries")
            
            for entry in feed.entries[:5]: # Only check top 5 from each feed to save time
                # Check date
                published_time = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_time = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    published_time = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
                
                # If no date found, skip to be safe (or assume new if critical, but skipping is safer)
                if not published_time:
                    continue
                
                # Filter by age
                if published_time > cutoff_date:
                    candidates.append({
                        "source": feed.feed.get('title', 'Unknown Source'),
                        "title": entry.title,
                        "link": entry.link,
                        "summary": clean_html(getattr(entry, 'summary', '') or getattr(entry, 'description', ''))[:300], # Limit summary len
                        "published": published_time.strftime("%Y-%m-%d")
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
    
    # Prepare list for prompt
    candidates_list_str = ""
    for idx, item in enumerate(candidates):
        candidates_list_str += f"[{idx}] Source: {item['source']} | Title: {item['title']} | Date: {item['published']}\n"
        
    prompt = f"""
    You are an expert editor for "Amz AI Agent", a blog for Amazon FBA Sellers.
    Your goal is to select the ONE most important and valuable news story from the list below to write a blog post about.
    
    Criteria for selection:
    1. Relevance: Must directly impact Amazon Sellers (FBAfees, Policies, Algorithms, Tools).
    2. Freshness: Breaking news is better.
    3. Value: "How-to" or "Strategic" potential is better than generic corporate news.
    
    Candidate List:
    {candidates_list_str}
    
    Return ONLY a JSON object with the index of the best article.
    {{
        "best_index": 0,
        "reason": "Explain why you picked this"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model=AI_MODEL_NAME, 
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        # Parse response
        content = response.choices[0].message.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
            
        selection = json.loads(content.strip())
        best_idx = selection.get("best_index", 0)
        
        print(f"AI Selection: {candidates[best_idx]['title']}")
        print(f"Reason: {selection.get('reason')}")
        
        return candidates[best_idx]
        
    except Exception as e:
        print(f"AI Selection failed: {e}. Defaulting to first candidate.")
        return candidates[0]

def check_if_exists(slug):
    # Check local JSON first (faster/easier)
    json_path = "data/blog/posts_en.json"
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for post in data:
                    if post.get('slug') == slug or post.get('id') == slug:
                        return True
        except:
            pass
    return False

def generate_blog_post(news_item):
    """Uses LLM to write a blog post based on the selected news."""
    print(f"Generating content for: {news_item['title']}...")
    
    prompt = f"""
    You are an expert Amazon FBA consultant. Write a high-quality blog post based on this news.
    
    Source: {news_item['source']}
    Title: {news_item['title']}
    Link: {news_item['link']}
    Summary: {news_item['summary']}
    
    Requirements:
    1. Title: Catchy, SEO-optimized, focusing on benefit/impact for Sellers.
    2. Structure:
       - What is the update? (Clear facts)
       - The Hidden Impact (What Amazon isn't saying)
       - 3 Action Steps for Sellers (What to do NOW)
    3. Tone: Professional, authoritative, "Old Pro".
    4. Length: 800+ words. Depth is key.
    5. No generic intros like "In the ever-evolving world of e-commerce..." - Start strong.
    
    Output JSON format:
    {{
        "title": "The generated title",
        "slug": "seo-friendly-url-slug-2026",
        "excerpt": "Compelling meta description (150 chars)",
        "content_html": "Full HTML content (use h2, h3, p, ul, table if needed). No html/body tags.",
        "tags": ["Tag1", "Tag2"]
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model=AI_MODEL_NAME, 
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content.strip()
        
        # Robust Clean
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        content = content.strip()
        # Remove control characters
        content = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', content)
        
        return json.loads(content)
        
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
        "cover_image": "images/blog_thumbs/default_news.png",
        "source_url": source_link
    }
    
    try:
        supabase.table("blog_posts").insert(db_record).execute()
        print("Saved to DB.")
    except Exception as e:
        print(f"DB Error (ignored): {e}")

def save_to_json(post_data, source_link):
    print("Saving to local JSON...")
    json_path = "data/blog/posts_en.json"
    
    new_entry = {
        "id": post_data["slug"],
        "slug": post_data["slug"],
        "title": post_data["title"],
        "date": datetime.now().strftime("%Y-%m-%d"), # Publish date is NOW, not news date
        "author": "Amz AI Agent",
        "excerpt": post_data["excerpt"],
        "content": post_data["content_html"],
        "cover_image": "images/blog_thumbs/default_news.png", # Ideally AI generates this too, but future step
        "tags": post_data["tags"],
        "source_link": source_link
    }

    try:
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = []
        
        # Avoid duplicate slugs
        if any(d['slug'] == new_entry['slug'] for d in data):
            print("Duplicate slug detected. Skipping JSON save.")
            return

        data.insert(0, new_entry)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print("Success: JSON updated.")
        
    except Exception as e:
        print(f"JSON Error: {e}")

def main():
    # 1. Gather Candidates
    candidates = fetch_and_filter_candidates()
    
    if not candidates:
        print("No recent news found (last 48 hours). Resting today.")
        return

    # 2. Select the Best One
    best_news = select_best_article(candidates)
    if not best_news:
        return

    # 3. Check Duplicates
    # We construct a theoretical slug to check, OR check by title logic used before.
    # But since we generate slug later, let's check title similiarity or source link?
    # Checking source link is safest.
    # For now, we proceed to generate, and save_to_json handles slug collision.
    
    # 4. Generate Content
    blog_post = generate_blog_post(best_news)
    
    if blog_post:
        # 5. Save
        save_to_supabase(blog_post, best_news['link'])
        save_to_json(blog_post, best_news['link'])

if __name__ == "__main__":
    main()
