import os
from datetime import datetime

BASE_URL = "https://amzaiagent.com"
# Exclude system/utility pages or pages not meant for public indexing
EXCLUDE_FILES = ['create_old.html', 'logo_preview.html', 'failed.html', 'success.html', '404.html', 'order.html', 'processing.html', 'discovery_report.html']

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
        xml += f'    <lastmod>{today}</lastmod>\n'
        xml += f'    <changefreq>{freq}</changefreq>\n'
        xml += f'    <priority>{priority}</priority>\n'
        xml += '  </url>\n'
        urls_added += 1

    # Add dynamic Blog Posts
    print("Fetching blog posts...")
    blog_posts_file = 'data/blog/blog_posts.js'
    if os.path.exists(blog_posts_file):
        with open(blog_posts_file, 'r', encoding='utf-8') as bpf:
            content = bpf.read()
            # Crude extraction of IDs from JS file
            import re
            post_ids = re.findall(r'"id":\s*"([^"]+)"', content)
            unique_ids = sorted(list(set(post_ids)))
            print(f"Adding {len(unique_ids)} blog posts to sitemap...")
            for pid in unique_ids:
                xml += '  <url>\n'
                xml += f'    <loc>{BASE_URL}/blog-post.html?id={pid}</loc>\n'
                xml += f'    <lastmod>{today}</lastmod>\n'
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
            unique_rids = sorted(list(set(report_ids)))
            print(f"Adding {len(unique_rids)} case reports to sitemap...")
            for rid in unique_rids:
                xml += '  <url>\n'
                xml += f'    <loc>{BASE_URL}/report.html?id={rid}</loc>\n'
                xml += f'    <lastmod>{today}</lastmod>\n'
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
