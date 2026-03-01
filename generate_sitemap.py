import os
import re
import json
from datetime import datetime
from typing import Optional

BASE_URL = "https://amzaiagent.com"
# Exclude system/utility pages or pages not meant for public indexing
EXCLUDE_FILES = [
    'create_old.html',
    'logo_preview.html',
    'logo_redesign_preview.html',
    'failed.html',
    'success.html',
    '404.html',
    'order.html',
    'processing.html',
    'discovery_report.html',
    'dashboard.html',
    'blog-post.html',
    'temp_live_index.html',
    'temp_local_index.html'
]

def _file_lastmod(path: str, fallback: str) -> str:
    try:
        ts = os.path.getmtime(path)
        return datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    except Exception:
        return fallback

def _parse_date(date_str: str) -> Optional[str]:
    """
    Convert human-readable date like 'February 18, 2026' to '2026-02-18'.
    Returns None if parsing fails.
    """
    try:
        return datetime.strptime(date_str.strip(), "%B %d, %Y").strftime('%Y-%m-%d')
    except Exception:
        return None


def _extract_blog_posts(path: str):
    with open(path, 'r', encoding='utf-8') as bpf:
        content = bpf.read()
    match = re.search(r"window\.blogPostsEN\s*=\s*(\[\s*.*?\]);", content, re.S)
    if not match:
        return []
    try:
        return json.loads(match.group(1))
    except Exception:
        return []


def _normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (title or "").lower()).strip()


def _blog_topic_key(post: dict) -> str:
    normalized = _normalize_title(post.get("title") or "")
    rules = [
        ("topic-safe-t-window", r"safe t claims window"),
        ("topic-bsa-compliance", r"bsa compliance|seller tool compliance|bsa rules?"),
        ("topic-gmv-growth", r"gmv growth"),
        ("topic-seller-registration-drop", r"seller registrations? drop"),
        ("topic-dd7-disbursement", r"dd 7|disbursement policy change"),
    ]
    for key, pattern in rules:
        if re.search(pattern, normalized):
            return key
    return f"post-{post.get('id') or 'untitled'}"


def _curate_blog_posts(posts: list) -> list:
    def _date_key(post):
        parsed = _parse_date(post.get("date", ""))
        return parsed or "1970-01-01"

    sorted_posts = sorted(posts, key=_date_key, reverse=True)
    seen = set()
    curated = []
    for post in sorted_posts:
        key = _blog_topic_key(post)
        if key in seen:
            continue
        seen.add(key)
        curated.append(post)
    return curated

def generate_sitemap():
    # List all HTML files in current directory
    files = [f for f in os.listdir('.') if f.endswith('.html') and f not in EXCLUDE_FILES]
    files.sort() # Sort for consistent output
    
    # Start XML content
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Priority mapping for core pages
    priority_map = {
        'index.html': '1.0',
        'create.html': '0.9',
        'pricing.html': '0.9',
        'discovery.html': '0.9',
        'cases.html': '0.8',
        'blog.html': '0.8',
        'reports.html': '0.8',
        'contact.html': '0.7',
        'about.html': '0.7',
        'faq.html': '0.7'
    }
    
    # Always put index first
    if 'index.html' in files:
        files.remove('index.html')
        files.insert(0, 'index.html')
    
    urls_added = 0
    for f in files:
        # Determine URL
        if f == 'index.html':
            url = BASE_URL + "/" # Clean URL for home
        else:
            url = f"{BASE_URL}/{f}"
            
        priority = priority_map.get(f, '0.6') # Default lower priority for others
        
        # Determine changfreq
        if priority >= '0.9':
            freq = 'daily'
        elif priority >= '0.8':
            freq = 'weekly'
        else:
            freq = 'monthly'
        
        xml += '  <url>\n'
        xml += f'    <loc>{url}</loc>\n'
        lastmod = _file_lastmod(f, today)
        xml += f'    <lastmod>{lastmod}</lastmod>\n'
        xml += f'    <changefreq>{freq}</changefreq>\n'
        xml += f'    <priority>{priority}</priority>\n'
        xml += '  </url>\n'
        urls_added += 1

    # Add dynamic Blog Posts
    print("Fetching blog posts...")
    blog_posts_file = 'data/blog/blog_posts.js'
    if os.path.exists(blog_posts_file):
        posts = _extract_blog_posts(blog_posts_file)
        curated_posts = _curate_blog_posts(posts)
        print(f"Adding {len(curated_posts)} curated blog posts to sitemap...")
        for post in curated_posts:
            pid = post.get("id")
            if not pid:
                continue
            parsed_date = _parse_date(post.get("date", "")) or today
            xml += '  <url>\n'
            xml += f'    <loc>{BASE_URL}/blog-post.html?id={pid}</loc>\n'
            xml += f'    <lastmod>{parsed_date}</lastmod>\n'
            xml += f'    <changefreq>monthly</changefreq>\n'
            xml += f'    <priority>0.6</priority>\n'
            xml += '  </url>\n'
            urls_added += 1

    # Add dynamic Reports/Cases
    print("Fetching reports...")
    reports_file = 'data/reports/reports.js'
    if os.path.exists(reports_file):
        with open(reports_file, 'r', encoding='utf-8') as rf:
            content = rf.read()
            report_ids = re.findall(r'"id":\s*"([^"]+)"', content)
            report_dates = dict(re.findall(r'"id":\s*"([^"]+)"[\\s\\S]*?"created_at":\s*"([^"]+)"', content))
            unique_rids = sorted(list(set(report_ids)))
            print(f"Adding {len(unique_rids)} case reports to sitemap...")
            for rid in unique_rids:
                rid_date = report_dates.get(rid, "")
                parsed_date = _parse_date(rid_date) or rid_date[:10] or today
                xml += '  <url>\n'
                xml += f'    <loc>{BASE_URL}/report.html?id={rid}</loc>\n'
                xml += f'    <lastmod>{parsed_date}</lastmod>\n'
                xml += f'    <changefreq>monthly</changefreq>\n'
                xml += f'    <priority>0.5</priority>\n'
                xml += '  </url>\n'
                urls_added += 1
    
    xml += '</urlset>'
    
    with open('sitemap.xml', 'w', encoding='utf-8') as f:
        f.write(xml)
    
    print(f"sitemap.xml generated with {len(files)} URLs.")

if __name__ == "__main__":
    generate_sitemap()
