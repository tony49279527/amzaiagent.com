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
        
    xml += '</urlset>'
    
    with open('sitemap.xml', 'w', encoding='utf-8') as f:
        f.write(xml)
    
    print(f"sitemap.xml generated with {len(files)} URLs.")

if __name__ == "__main__":
    generate_sitemap()
