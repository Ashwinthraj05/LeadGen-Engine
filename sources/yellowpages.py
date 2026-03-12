"""
sources/yellowpages.py
FIXED:
  1. Stealth headers — YP aggressively blocks default UA
  2. Updated CSS selectors for current YP layout
  3. Proper website redirect extraction
  4. Email extraction from listing cards (YP sometimes shows them)
  5. pages default raised to 5
  6. Random delays + session reuse
"""

import re
import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import parse_qs, urlparse, urljoin, quote_plus

from utils.helpers import create_business

STEALTH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer":         "https://www.yellowpages.com/",
    "DNT":             "1",
    "Connection":      "keep-alive",
}

YP_BASE = "https://www.yellowpages.com"

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")


def extract_real_website(raw_url: str) -> str:
    """Strip YP tracking redirects to get the real domain."""
    if not raw_url:
        return ""
    try:
        parsed = urlparse(raw_url)
        # YP redirect: /biz_redir?url=https%3A%2F%2F...
        if "biz_redir" in parsed.path or "redirect" in parsed.path:
            qs = parse_qs(parsed.query)
            for key in ("url", "website", "u"):
                if key in qs:
                    return qs[key][0].split("?")[0]
        if raw_url.startswith("http") and "yellowpages" not in raw_url:
            return raw_url.split("?")[0]
    except Exception:
        pass
    return ""


def scrape_yellowpages(city: str, category: str, pages: int = 5) -> list:
    """
    FIXED YellowPages scraper with stealth headers, updated selectors,
    website redirect extraction, and email extraction from cards.
    """

    results = []
    seen = set()

    cat_slug = quote_plus(category)
    city_slug = quote_plus(city)

    session = requests.Session()
    session.headers.update(STEALTH_HEADERS)

    for page in range(1, pages + 1):

        url = (
            f"{YP_BASE}/search?"
            f"search_terms={cat_slug}&"
            f"geo_location_terms={city_slug}&"
            f"page={page}"
        )
        print(f"🟡 YellowPages → {url}")

        try:
            res = session.get(url, timeout=25)
        except Exception as e:
            print(f"  ⚠ Request error: {e}")
            continue

        if res.status_code == 403:
            print("  🚫 Blocked — waiting...")
            time.sleep(random.uniform(10, 18))
            try:
                res = session.get(url, timeout=25)
            except Exception:
                continue

        if res.status_code != 200:
            print(f"  ⚠ Status {res.status_code}")
            continue

        soup = BeautifulSoup(res.text, "html.parser")

        # ── Try multiple listing selectors ─────────────────────────────────
        listings = (
            soup.select("div.result")               # current layout
            or soup.select("div.v-card")
            or soup.select("article.srp-listing")
            or soup.select("div[class*='listing']")
            or soup.select("li.result")
        )

        if not listings:
            print(f"  ⚠ No listings page {page}")
            print("  HTML preview:", res.text[200:500])
            continue

        print(f"  ✅ {len(listings)} listings on page {page}")

        for listing in listings:

            # ── Name ──────────────────────────────────────────────────────
            name = ""
            for sel in [
                "a.business-name span", "a.business-name",
                "h2.n a", ".listing-name", "h2 a", ".business a"
            ]:
                tag = listing.select_one(sel)
                if tag:
                    name = tag.get_text(strip=True)
                    break

            if not name:
                continue

            unique_key = name.lower()
            if unique_key in seen:
                continue
            seen.add(unique_key)

            # ── Website ───────────────────────────────────────────────────
            website = ""
            for sel in [
                "a.track-visit-website",
                "a.visit-business",
                "a[class*='website']",
                "a[href*='biz_redir']",
            ]:
                tag = listing.select_one(sel)
                if tag:
                    website = extract_real_website(tag.get("href", ""))
                    if website:
                        break

            # ── Phone ─────────────────────────────────────────────────────
            phone = ""
            for sel in [".phones", ".phone", "[class*='phone']",
                        "p.phone", ".contact-phone"]:
                tag = listing.select_one(sel)
                if tag:
                    phone = tag.get_text(strip=True)
                    break

            # ── Address ───────────────────────────────────────────────────
            address = ""
            parts = []
            street = listing.select_one(".street-address, .adr .street")
            locality = listing.select_one(".locality, .city")
            if street:
                parts.append(street.get_text(strip=True))
            if locality:
                parts.append(locality.get_text(strip=True))
            address = ", ".join(parts)

            # ── Email (sometimes in card) ─────────────────────────────────
            email = ""
            card_text = listing.get_text(" ")
            found = EMAIL_RE.findall(card_text)
            if found:
                email = found[0].lower()

            results.append(create_business(
                name=name,
                phone=phone,
                address=address,
                website=website,
                email=email,
                city=city,
                category=category,
                source="YellowPages"
            ))

        time.sleep(random.uniform(2.0, 4.5))

    return results
