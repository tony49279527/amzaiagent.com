import os
import re

NAV_HTML = """
    <noscript>
        <nav aria-label="Main Navigation">
            <a href="/">Home</a>
            <a href="/create.html">Competitor Analysis</a>
            <a href="/discovery.html">Product Discovery</a>
            <a href="/cases.html">Cases</a>
            <a href="/blog.html">Blog</a>
            <a href="/pricing.html">Pricing</a>
        </nav>
    </noscript>
"""

HTML_FILES = ['index.html', 'create.html', 'discovery.html', 'pricing.html', 'cases.html', 'blog.html', 'contact.html', 'about.html', 'faq.html', 'privacy.html', 'terms.html', 'blog-post.html']

for f in HTML_FILES:
    if not os.path.exists(f): continue
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # 1. Inject static nav inside navbar-placeholder if empty
    if '<div id="navbar-placeholder"></div>' in content:
        content = content.replace('<div id="navbar-placeholder"></div>', f'<div id="navbar-placeholder">{NAV_HTML}</div>')
    
    # 2. Add cross-site canonical/hreflang if not present
    # We will let the SSG script handle blog-post.html specifically, but for others:
    if f != 'blog-post.html':
        if 'hreflang="en"' not in content:
            url_path = '/' if f == 'index.html' else f'/{f}'
            full_url = f'https://amzaiagent.com{url_path}'
            hreflang_tags = f'\n    <link rel="alternate" hreflang="en" href="{full_url}">\n    <link rel="alternate" hreflang="x-default" href="{full_url}">\n'
            # Insert after canonical or description
            if '<link rel="canonical"' in content:
                content = re.sub(r'(<link rel="canonical" href="[^"]+">)', r'\1' + hreflang_tags, content, 1)
            elif '<meta name="description"' in content:
                content = re.sub(r'(<meta name="description"[^>]+>)', r'\1' + hreflang_tags, content, 1)

    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)

print("Injected static nav and hreflang.")
