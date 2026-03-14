import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

BLOG_JS_PATH = Path("data/blog/blog_posts.js")

TOPIC_RULES: List[Tuple[str, str]] = [
    ("topic-ad-fee-outage", r"((ad fee|advertising fees?|ad charges?).*(outage|system failure|system outage|platform outage))|(outage.*(ad fee|advertising fees?|ad charges?))"),
    ("topic-ai-analytics", r"ai sales analytics tool|ai analytics tool"),
    ("topic-spring-sale", r"spring deal days|big spring sale"),
    ("topic-inventory-forecasting", r"inventory forecasting"),
    ("topic-safe-t-window", r"safe t claims window"),
    ("topic-bsa-compliance", r"bsa compliance|seller tool compliance|bsa rules?"),
    ("topic-gmv-growth", r"gmv growth"),
    ("topic-seller-registration-drop", r"seller registrations? drop|seller registration drop"),
    ("topic-dd7-disbursement", r"dd 7|disbursement policy change"),
    ("topic-shipping-costs", r"fba shipping cost"),
    ("topic-elite-seller-share", r"elite 1 6|control half of marketplace sales|marketplace revenue"),
]

PREFERRED_CANONICAL_BY_TOPIC: Dict[str, str] = {
    "topic-ad-fee-outage": "amazon-fba-ad-fee-crisis-2026-outage-charges",
    "topic-ai-analytics": "amazon-ai-sales-analytics-tool-guide-fba-sellers",
    "topic-spring-sale": "amazon-big-spring-sale-2026-dates-deals-guide",
    "topic-inventory-forecasting": "ai-inventory-forecasting-amazon-fba-guide",
    "topic-safe-t-window": "amazon-safe-t-claims-window-30-days-2026-update",
    "topic-bsa-compliance": "amazon-seller-tool-compliance-2024-bsa-rules",
    "topic-gmv-growth": "amazon-gmv-growth-2025-milestone",
    "topic-seller-registration-drop": "amazon-seller-registration-drop-2025-fba-impact",
    "topic-dd7-disbursement": "amazon-disbursement-policy-changes-dd7-2024",
    "topic-shipping-costs": "amazon-fba-shipping-cost-increases-2026-protect-margins",
    "topic-elite-seller-share": "amazon-fba-elite-sellers-marketplace-revenue-2024",
}

EXPLICIT_REDIRECTS: Dict[str, str] = {
    "amazon-bsa-compliance-2024-seller-tools-ai": "amazon-seller-tool-compliance-2024-bsa-rules",
    "amazon-bsa-compliance-2024-seller-tools-deadline": "amazon-seller-tool-compliance-2024-bsa-rules",
    "amazon-bsa-compliance-update-2024-fba-sellers": "amazon-seller-tool-compliance-2024-bsa-rules",
    "amazon-safe-t-claims-window-30-days-2026": "amazon-safe-t-claims-window-30-days-2026-update",
    "amazon-safe-t-claims-window-change-2026": "amazon-safe-t-claims-window-30-days-2026-update",
    "amazon-safe-t-claims-window-changes-2026": "amazon-safe-t-claims-window-30-days-2026-update",
    "amazon-safe-t-claims-window-reduction-2026": "amazon-safe-t-claims-window-30-days-2026-update",
    "amazon-gmv-growth-2025-record-milestone": "amazon-gmv-growth-2025-milestone",
    "amazon-gmv-growth-2025-sales-impact-fba-sellers": "amazon-gmv-growth-2025-milestone",
    "amazon-gmv-growth-2025-seller-impact": "amazon-gmv-growth-2025-milestone",
    "amazon-fba-shipping-costs-2026-protect-profit-margins": "amazon-fba-shipping-cost-increases-2026-protect-margins",
    "amazon-seller-registrations-2025-drop-fba-impact": "amazon-seller-registration-drop-2025-fba-impact",
    "ai-inventory-forecasting-amazon-fba-stockouts-overstock": "ai-inventory-forecasting-amazon-fba-guide",
    "amazon-fba-ad-fee-charges-system-outage-2026": "amazon-fba-ad-fee-crisis-2026-outage-charges",
    "amazon-fba-outage-2026-seller-ad-charges": "amazon-fba-ad-fee-crisis-2026-outage-charges",
    "amazon-seller-ad-fees-outage-2026-fba-impact": "amazon-fba-ad-fee-crisis-2026-outage-charges",
    "amazon-fba-ad-fee-outage-2026-seller-impact": "amazon-fba-ad-fee-crisis-2026-outage-charges",
    "amazon-fba-ai-analytics-tool-2024-sales-insights": "amazon-ai-sales-analytics-tool-guide-fba-sellers",
    "amazon-fba-ai-analytics-tool-2024": "amazon-ai-sales-analytics-tool-guide-fba-sellers",
    "amazon-spring-deal-days-2026-seller-guide": "amazon-big-spring-sale-2026-dates-deals-guide",
    "amazon-top-seller-statistics-2024": "amazon-fba-elite-sellers-marketplace-revenue-2024",
}


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (title or "").lower()).strip()


def parse_human_date(date_str: str) -> datetime:
    try:
        return datetime.strptime((date_str or "").strip(), "%B %d, %Y")
    except Exception:
        return datetime.min


def topic_key(post: dict) -> str:
    normalized = normalize_title(post.get("title", ""))
    for key, pattern in TOPIC_RULES:
        if re.search(pattern, normalized):
            return key
    return f"post-{post.get('id') or 'untitled'}"


def sort_posts(posts: List[dict]) -> List[dict]:
    return sorted(posts, key=lambda p: parse_human_date(p.get("date", "")), reverse=True)


def build_redirect_map(posts: List[dict]) -> Dict[str, str]:
    sorted_posts = sort_posts(posts)
    redirect_map = dict(EXPLICIT_REDIRECTS)
    grouped: Dict[str, List[dict]] = {}

    for post in sorted_posts:
        pid = post.get("id")
        if not pid:
            continue
        grouped.setdefault(topic_key(post), []).append(post)

    for key, group in grouped.items():
        ids = {post.get("id") for post in group if post.get("id")}
        preferred = PREFERRED_CANONICAL_BY_TOPIC.get(key)
        canonical_id = preferred if preferred in ids else group[0].get("id")
        if not canonical_id:
            continue
        for post in group:
            pid = post.get("id")
            if pid and pid != canonical_id:
                redirect_map[pid] = canonical_id

    return redirect_map


def curate_posts(posts: List[dict]) -> List[dict]:
    sorted_posts = sort_posts(posts)
    redirect_map = build_redirect_map(sorted_posts)
    curated: List[dict] = []
    seen_titles = set()

    for post in sorted_posts:
        pid = post.get("id")
        if not pid:
            continue
        if redirect_map.get(pid, pid) != pid:
            continue

        title_key = normalize_title(post.get("title", ""))
        if title_key and title_key in seen_titles:
            continue
        seen_titles.add(title_key)
        curated.append(post)

    return curated


def extract_posts_from_blog_js(path: Path = BLOG_JS_PATH) -> List[dict]:
    content = path.read_text(encoding="utf-8")
    match = re.search(r"window\.blogPostsEN\s*=\s*(\[\s*.*?\]);", content, re.S)
    if not match:
        raise RuntimeError("Could not find blogPostsEN array in blog_posts.js")
    return json.loads(match.group(1))


def write_blog_js(posts: List[dict], path: Path = BLOG_JS_PATH) -> None:
    js_content = (
        "\nwindow.blogPostsCN = [];\n"
        f"window.blogPostsEN = {json.dumps(posts, indent=2, ensure_ascii=False)};\n"
    )
    path.write_text(js_content, encoding="utf-8")
