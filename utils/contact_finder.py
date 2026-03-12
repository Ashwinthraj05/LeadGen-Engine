"""
utils/contact_finder.py
FIXED:
  1. Old version used Google directly — instantly gets blocked/CAPTCHA
  2. Now uses DuckDuckGo HTML search (no bot detection)
  3. Tries multiple contact page patterns
  4. Returns None gracefully instead of crashing
"""

import re
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

CONTACT_KEYWORDS = ["contact", "about", "support", "reach", "enquiry"]


def find_contact_page(domain: str) -> str:
    """
    Find a contact page for a domain using DuckDuckGo site search.
    Falls back to common paths if search fails.
    FIX: uses DuckDuckGo instead of Google (no CAPTCHA).
    """

    if not domain:
        return ""

    domain = domain.replace("www.", "").strip()

    # ── Strategy 1: DuckDuckGo site search ───────────────────────────────
    try:
        query = f"site:{domain} contact email"
        url = f"https://html.duckduckgo.com/html/?q={query}"

        res = requests.get(url, headers=HEADERS, timeout=10)

        if res.status_code == 200:
            links = re.findall(r"https?://[^\s\"'<>]+", res.text)
            for link in links:
                if domain in link:
                    link_lower = link.lower()
                    if any(kw in link_lower for kw in CONTACT_KEYWORDS):
                        return link.split("?")[0]
    except Exception:
        pass

    # ── Strategy 2: Common path guessing ─────────────────────────────────
    base = f"https://{domain}"
    common_paths = [
        "/contact", "/contact-us", "/about", "/about-us",
        "/support", "/reach-us", "/get-in-touch",
    ]

    for path in common_paths:
        try:
            full = base + path
            r = requests.head(full, headers=HEADERS, timeout=6,
                              allow_redirects=True)
            if r.status_code == 200:
                return full
        except Exception:
            continue

    return ""
