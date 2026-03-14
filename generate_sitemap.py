import os
from datetime import datetime
from typing import Optional

from blog_curation import build_redirect_map, curate_posts, extract_posts_from_blog_js

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
    'report.html',
    'reports.html',
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
        posts = extract_posts_from_blog_js()
        curated_posts = curate_posts(posts)
        redirect_map = build_redirect_map(posts)
        print(f"Adding {len(curated_posts)} curated blog posts to sitemap...")
        for post in curated_posts:
            pid = post.get("id")
            if not pid or redirect_map.get(pid, pid) != pid:
                continue
            parsed_date = _parse_date(post.get("date", "")) or today
            xml += '  <url>\n'
            xml += f'    <loc>{BASE_URL}/blog/{pid}.html</loc>\n'
            xml += f'    <lastmod>{parsed_date}</lastmod>\n'
            xml += f'    <changefreq>monthly</changefreq>\n'
            xml += f'    <priority>0.6</priority>\n'
            xml += '  </url>\n'
            urls_added += 1

    # Add dynamic Reports/Cases is intentionally removed to avoid leaking private reports.
    
    xml += '</urlset>'
    
    with open('sitemap.xml', 'w', encoding='utf-8') as f:
        f.write(xml)
    
    print(f"sitemap.xml generated with {len(files)} URLs.")

if __name__ == "__main__":
    generate_sitemap()
