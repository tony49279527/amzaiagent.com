import re
import json
from datetime import datetime, timezone
from typing import List, Dict

BASE_URL = "https://amzaiagent.com"
BLOG_FILE = "data/blog/blog_posts.js"
FEED_FILE = "feed.xml"


def parse_posts() -> List[Dict]:
    with open(BLOG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r"window\.blogPostsEN\s*=\s*(\[\s*.*?\]);", content, re.S)
    if not match:
        raise RuntimeError("Could not find blogPostsEN array in blog_posts.js")
    json_blob = match.group(1)
    posts = json.loads(json_blob)
    return posts


def parse_date(date_str: str) -> datetime:
    try:
        return datetime.strptime(date_str.strip(), "%B %d, %Y").replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (title or "").lower()).strip()


def topic_key(post: Dict) -> str:
    normalized = normalize_title(post.get("title") or "")
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


def curate_posts(posts: List[Dict]) -> List[Dict]:
    sorted_posts = sorted(posts, key=lambda p: parse_date(p.get("date", "")), reverse=True)
    seen_keys = set()
    curated = []
    for post in sorted_posts:
        key = topic_key(post)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        curated.append(dict(post))
    return curated


def build_feed(posts: List[Dict]) -> str:
    now_iso = datetime.now(timezone.utc).isoformat()
    feed_items = []
    curated_posts = curate_posts(posts)
    for p in curated_posts[:50]:  # cap to avoid an overly large feed
        pid = p.get("id") or "untitled"
        title = p.get("title") or "Untitled"
        link = f"{BASE_URL}/blog-post.html?id={pid}"
        updated = parse_date(p.get("date", "")).isoformat()
        summary = ""
        raw_content = p.get("content") or ""
        # crude plain-text excerpt
        summary = re.sub("<[^>]+>", " ", raw_content)
        summary = " ".join(summary.split())[:300]
        cover = p.get("cover_image") or ""
        feed_items.append(f"""
  <entry>
    <title>{escape_xml(title)}</title>
    <link href="{link}"/>
    <id>{link}</id>
    <updated>{updated}</updated>
    <summary>{escape_xml(summary)}</summary>
    <author><name>{escape_xml(p.get("author") or "Amz AI Agent")}</name></author>
    {'<media:thumbnail xmlns:media="http://search.yahoo.com/mrss/" url="'+cover.replace('.png','.webp')+'"/>' if cover else ''}
  </entry>""")

    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Amz AI Agent Blog</title>
  <id>{BASE_URL}/feed.xml</id>
  <link href="{BASE_URL}/feed.xml" rel="self"/>
  <link href="{BASE_URL}/blog.html" />
  <updated>{now_iso}</updated>
  <author>
    <name>Amz AI Agent</name>
  </author>
{''.join(feed_items)}
</feed>
"""
    return feed


def escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def main():
    posts = parse_posts()
    feed = build_feed(posts)
    with open(FEED_FILE, "w", encoding="utf-8") as f:
        f.write(feed)
    print(f"Wrote {FEED_FILE} with {len(curate_posts(posts))} curated posts (capped to 50).")


if __name__ == "__main__":
    main()
