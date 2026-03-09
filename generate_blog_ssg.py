import os
import re
import json
import shutil
from datetime import datetime

os.makedirs('blog', exist_ok=True)

def strip_html(html):
    # Simple regex to strip HTML for meta description
    text = re.sub('<[^<]+?>', '', html)
    text = text.replace('\n', ' ').strip()
    return text[:155] + '...' if len(text) > 155 else text

# 1. Read blog posts
with open('data/blog/blog_posts.js', 'r', encoding='utf-8') as f:
    content = f.read()

match = re.search(r"window\.blogPostsEN\s*=\s*(\[\s*.*?\]);", content, re.S)
if not match:
    print("Could not find blogPostsEN")
    exit(1)

posts = json.loads(match.group(1))

# 2. Read template
with open('blog-post.html', 'r', encoding='utf-8') as f:
    template = f.read()

def rewrite_root_relative_links(html: str) -> str:
    replacements = {
        'href="styles.css"': 'href="/styles.css"',
        "src='js/components.js'": "src='/js/components.js'",
        'src="js/components.js"': 'src="/js/components.js"',
        'href="index.html"': 'href="/index.html"',
        'href="blog.html"': 'href="/blog.html"',
        'href="create.html"': 'href="/create.html"',
        'href="discovery.html"': 'href="/discovery.html"',
        'href="cases.html"': 'href="/cases.html"',
        'href="pricing.html"': 'href="/pricing.html"',
        'href="faq.html"': 'href="/faq.html"',
        'href="about.html"': 'href="/about.html"',
        'href="contact.html"': 'href="/contact.html"',
        'href="privacy.html"': 'href="/privacy.html"',
        'href="terms.html"': 'href="/terms.html"',
    }
    for source, target in replacements.items():
        html = html.replace(source, target)
    return html

# 3. Fix relative paths in template so it works from /blog/ dir
template = rewrite_root_relative_links(template)

# 4. Process each post
for post in posts:
    pid = post['id']
    title = post['title']
    safe_title = title.replace('"', '&quot;')
    desc = strip_html(post['content'])
    url = f"https://amzaiagent.com/blog/{pid}.html"
    cover = f"https://amzaiagent.com/{post.get('cover_image', '')}"
    
    # Render OG Tags
    og_tags = f"""
    <meta property="og:title" content="{safe_title} | Amz AI Agent Blog">
    <meta property="og:description" content="{desc}">
    <meta property="og:url" content="{url}">
    <meta property="og:type" content="article">
    <meta property="og:image" content="{cover}">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{safe_title}">
    <meta name="twitter:description" content="{desc}">
    <meta name="twitter:image" content="{cover}">
"""

    # Schema JSON-LD
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "image": [cover],
        "datePublished": post.get('date', ''),
        "author": [{
            "@type": "Organization",
            "name": "Amz AI Agent",
            "url": "https://amzaiagent.com"
        }]
    }
    schema_script = f'<script type="application/ld+json">\n{json.dumps(schema, indent=2)}\n</script>'
    
    html = template
    
    # Replace SEO tags
    html = re.sub(r'<title.*?>.*?</title>', f'<title>{safe_title} | Amz AI Agent Blog</title>', html, flags=re.S)
    html = re.sub(r'<meta name="description" id="meta-description"\s+content="[^"]*">', f'<meta name="description" content="{desc}">', html, flags=re.S)
    html = re.sub(r'<link rel="canonical" id="canonical-link" href="[^"]*">', f'<link rel="canonical" href="{url}">', html, flags=re.S)
    
    # Insert OG tags and Schema before </head>
    html = html.replace('</head>', f'{og_tags}\n{schema_script}\n</head>')
    
    # Inject static content
    # We must fix image src and root links inside post content.
    post_content = post['content'].replace('src="assets/', 'src="/assets/')
    post_content = post_content.replace("src='assets/", "src='/assets/")
    post_content = rewrite_root_relative_links(post_content)
    
    static_content = f"""
    <div class="article-header">
        <h1 class="article-title">{title}</h1>
    </div>
    <div class="article-content">
        {post_content}
    </div>
    """
    
    # Replace loading div with static content
    html = re.sub(r'<div id="article-content">.*?</div>\s*</main>', f'<div id="article-content">\n{static_content}\n</div>\n</main>', html, flags=re.S)
    
    # Update breadcrumb title
    html = re.sub(r'<li class="current" id="breadcrumb-title">.*?</li>', f'<li class="current" id="breadcrumb-title">{title}</li>', html, flags=re.S)
    
    # Disable the dynamic JS fetch so it doesn't overwrite our static content, but keep back button logic
    # Find the script tag and just remove the data fetching part
    html = re.sub(r'const urlParams = new URLSearchParams.*?(?=// Smart back button logic)', '', html, flags=re.S)
    # Actually, we can just replace the whole inline script with a simple one for the back button
    simple_script = """
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const backBtn = document.getElementById('back-to-list');
            if (backBtn) {
                backBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    if (document.referrer && document.referrer.includes(window.location.host)) {
                        window.history.back();
                    } else {
                        window.location.href = '/blog.html';
                    }
                });
            }
        });
    </script>
    """
    html = re.sub(r'<!-- Load Data with Cache Busting -->.*?</body>', f'{simple_script}\n</body>', html, flags=re.S)
    
    with open(f"blog/{pid}.html", "w", encoding="utf-8") as f_out:
        f_out.write(html)

print(f"Successfully generated {len(posts)} static blog posts in /blog/ directory.")
