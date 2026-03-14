import re
from datetime import datetime, timezone
from typing import List, Dict

from blog_curation import curate_posts, extract_posts_from_blog_js

BASE_URL = "https://amzaiagent.com"
BLOG_FILE = "data/blog/blog_posts.js"
FEED_FILE = "feed.xml"
def parse_date(date_str: str) -> datetime:
    try:
        return datetime.strptime(date_str.strip(), "%B %d, %Y").replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)
def build_feed(posts: List[Dict]) -> str:
    now_iso = datetime.now(timezone.utc).isoformat()
    feed_items = []
    curated_posts = curate_posts(posts)
    for p in curated_posts[:50]:  # cap to avoid an overly large feed
        pid = p.get("id") or "untitled"
        title = p.get("title") or "Untitled"
        link = f"{BASE_URL}/blog/{pid}.html"
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
    posts = extract_posts_from_blog_js()
    feed = build_feed(posts)
    with open(FEED_FILE, "w", encoding="utf-8") as f:
        f.write(feed)
    print(f"Wrote {FEED_FILE} with {len(curate_posts(posts))} curated posts (capped to 50).")


if __name__ == "__main__":
    main()
