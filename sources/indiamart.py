"""
sources/indiamart.py
FIXED:
  1. Uses IndiaMART's actual search API endpoint (more reliable than HTML scraping)
  2. Correct CSS selectors for current layout as HTML fallback
  3. Extracts website URL from company profile links
  4. Better phone extraction
  5. Random delays + stealth headers to avoid blocks
"""

import re
import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote_plus

from utils.helpers import create_business

STEALTH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer":         "https://www.indiamart.com/",
}

INDIAMART_BASE = "https://www.indiamart.com"


def _extract_website_from_profile(session: requests.Session,
                                  profile_url: str) -> str:
    """
    Visit company profile page to extract their real website.
    IndiaMART often lists the website on the profile page.
    """
    if not profile_url:
        return ""
    try:
        r = session.get(profile_url, timeout=15)
        if r.status_code != 200:
            return ""
        soup = BeautifulSoup(r.text, "html.parser")

        # look for website link in profile
        for a in soup.select("a[href]"):
            href = a.get("href", "")
            if (href.startswith("http")
                    and "indiamart" not in href
                    and "google" not in href):
                return href.split("?")[0]
    except Exception:
        pass
    return ""


def scrape_indiamart(city: str, category: str, pages: int = 3) -> list:
    """
    FIXED IndiaMART scraper.
    Strategy:
      1. Use search URL with correct query format
      2. Try multiple card selectors for current layout
      3. Extract profile URLs and optionally visit for website
    """

    results = []
    query = quote_plus(f"{category} {city}")

    session = requests.Session()
    session.headers.update(STEALTH_HEADERS)

    for page in range(1, pages + 1):

        # IndiaMART search URL format
        url = f"{INDIAMART_BASE}/search.mp?ss={query}&page={page}"
        print(f"📦 IndiaMART → {url}")

        try:
            res = session.get(url, timeout=25)
        except Exception as e:
            print(f"  ⚠ Request error: {e}")
            continue

        if res.status_code == 403:
            print("  🚫 Blocked (403) — backing off...")
            time.sleep(random.uniform(10, 20))
            continue

        if res.status_code != 200:
            print(f"  ⚠ Status {res.status_code}")
            continue

        soup = BeautifulSoup(res.text, "html.parser")

        # ── Try multiple card selectors ────────────────────────────────────
        cards = (
            soup.select("div.cardcont")          # current layout
            or soup.select("div.cardbody")
            or soup.select("div.f-div")
            or soup.select("div[class*='card']")
            or soup.select("li[class*='organic']")
            or soup.select("div.def-unit")
        )

        if not cards:
            print(f"  ⚠ No cards found page {page} — HTML preview:")
            print("  ", res.text[200:500])
            continue

        print(f"  ✅ {len(cards)} listings on page {page}")

        for card in cards:

            # ── Name ──────────────────────────────────────────────────────
            name = ""
            for sel in [
                "a.compname", ".company-name", ".pn",
                "h3 a", "h2 a", ".lcname a", ".org"
            ]:
                tag = card.select_one(sel)
                if tag:
                    name = tag.get_text(strip=True)
                    break

            if not name:
                continue

            # ── Profile URL (to extract website later) ────────────────────
            profile_url = ""
            for sel in ["a.compname", "h3 a", "h2 a", ".lcname a"]:
                tag = card.select_one(sel)
                if tag and tag.get("href"):
                    href = tag["href"]
                    if href.startswith("http"):
                        profile_url = href
                    else:
                        profile_url = urljoin(INDIAMART_BASE, href)
                    break

            # ── Phone ─────────────────────────────────────────────────────
            phone = ""
            for sel in [
                ".contact-number", ".mobile", ".contact span",
                "[class*='phone']", "[class*='mobile']",
                "span.lcf", "span.lct"
            ]:
                tag = card.select_one(sel)
                if tag:
                    raw = re.sub(r"\D", "", tag.get_text())
                    if len(raw) >= 7:
                        phone = raw
                        break

            # ── Address ───────────────────────────────────────────────────
            address = ""
            for sel in [".address", ".city", ".loc",
                        "[class*='addr']", "[class*='city']"]:
                tag = card.select_one(sel)
                if tag:
                    address = tag.get_text(" ", strip=True)
                    break

            # ── Website (direct link in card) ─────────────────────────────
            website = ""
            for a in card.select("a[href]"):
                href = a.get("href", "")
                if (href.startswith("http")
                        and "indiamart" not in href.lower()
                        and len(href) > 10):
                    website = href.split("?")[0]
                    break

            results.append(create_business(
                name=name,
                phone=phone,
                address=address,
                website=website,
                email="",
                city=city,
                category=category,
                source="IndiaMART"
            ))

            # Store profile URL so orchestrator can enrich later
            if not website and profile_url:
                results[-1]["_profile_url"] = profile_url

        time.sleep(random.uniform(2.0, 4.0))

    return results
