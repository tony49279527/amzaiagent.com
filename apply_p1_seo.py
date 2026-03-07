import os
import re
import json
from datetime import datetime

# 1. Generate feed.xml
with open('data/blog/blog_posts.js', 'r', encoding='utf-8') as f:
    content = f.read()

match = re.search(r"window\.blogPostsEN\s*=\s*(\[\s*.*?\]);", content, re.S)
if match:
    posts = json.loads(match.group(1))
    
    # Sort posts
    def parse_date(date_str):
        try:
            return datetime.strptime(date_str.strip(), "%B %d, %Y")
        except:
            return datetime.fromtimestamp(0)
            
    sorted_posts = sorted(posts, key=lambda x: parse_date(x.get('date', '')), reverse=True)
    
    now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    atom = f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
    <title>Amz AI Agent Blog</title>
    <subtitle>Amazon seller insights, FBA strategies, and AI-powered market analysis.</subtitle>
    <link href="https://amzaiagent.com/feed.xml" rel="self"/>
    <link href="https://amzaiagent.com/blog.html"/>
    <updated>{now}</updated>
    <id>https://amzaiagent.com/blog.html</id>
    <author>
        <name>Amz AI Agent</name>
        <email>contact@amzaiagent.com</email>
    </author>
"""
    for post in sorted_posts[:20]: # top 20
        pid = post['id']
        url = f"https://amzaiagent.com/blog/{pid}.html"
        title = post['title']
        date_obj = parse_date(post['date'])
        date_iso = date_obj.strftime('%Y-%m-%dT00:00:00Z')
        text = re.sub('<[^<]+?>', '', post['content'])[:200]
        
        atom += f"""
    <entry>
        <title>{title}</title>
        <link href="{url}"/>
        <id>{url}</id>
        <updated>{date_iso}</updated>
        <summary>{text}...</summary>
    </entry>"""
        
    atom += "\n</feed>"
    
    with open('feed.xml', 'w', encoding='utf-8') as f:
        f.write(atom)
    print("Generated feed.xml")


# 2. Inject Twitter/OG Tags
HTML_FILES = ['index.html', 'create.html', 'discovery.html', 'pricing.html', 'cases.html', 'blog.html', 'contact.html', 'about.html', 'faq.html', 'privacy.html', 'terms.html']

for f in HTML_FILES:
    if not os.path.exists(f): continue
    with open(f, 'r', encoding='utf-8') as file:
        html = file.read()
        
    url_path = '/' if f == 'index.html' else f'/{f}'
    full_url = f'https://amzaiagent.com{url_path}'
    
    # Extract title and description
    title_match = re.search(r'<title>(.*?)</title>', html)
    desc_match = re.search(r'<meta name="description" content="(.*?)">', html)
    
    title = title_match.group(1) if title_match else "Amz AI Agent"
    desc = desc_match.group(1) if desc_match else ""
    
    tags_to_add = []
    
    if '<meta name="twitter:card"' not in html:
        # Check for property="twitter:card" error (P1-7 Note)
        if '<meta property="twitter:card"' in html:
            html = html.replace('<meta property="twitter:card"', '<meta name="twitter:card"')
        else:
            tags_to_add.append('<meta name="twitter:card" content="summary_large_image">')
            tags_to_add.append(f'<meta name="twitter:title" content="{title}">')
            tags_to_add.append(f'<meta name="twitter:description" content="{desc}">')
            tags_to_add.append('<meta name="twitter:image" content="https://amzaiagent.com/images/about_hero.webp">')

    if '<meta property="og:title"' not in html:
        tags_to_add.append(f'<meta property="og:title" content="{title}">')
        tags_to_add.append(f'<meta property="og:description" content="{desc}">')
        tags_to_add.append(f'<meta property="og:url" content="{full_url}">')
        tags_to_add.append('<meta property="og:type" content="website">')
        tags_to_add.append('<meta property="og:image" content="https://amzaiagent.com/images/about_hero.webp">')
    
    if tags_to_add:
        tag_string = "\n    ".join(tags_to_add) + "\n"
        if '</head>' in html:
            html = html.replace('</head>', f'    {tag_string}</head>')
            with open(f, 'w', encoding='utf-8') as file:
                file.write(html)
            print(f"Added OG/Twitter tags to {f}")
