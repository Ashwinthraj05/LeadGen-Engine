"""
sources/bbb.py
FIXED:
  1. Visits company profile page to extract real website URL
  2. Better selectors for current BBB layout
  3. Stealth headers + random delays
  4. pages default raised to 3
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
    "Accept-Language": "en-US,en;q=0.9",
    "Referer":         "https://www.bbb.org/",
    "DNT":             "1",
}

BBB_BASE = "https://www.bbb.org"


def _get_website_from_profile(session, profile_url):
    if not profile_url:
        return ""
    try:
        r = session.get(profile_url, timeout=15)
        if r.status_code != 200:
            return ""
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.select("a[href]"):
            href = a.get("href", "")
            text = a.get_text(strip=True).lower()
            if ("visit website" in text or "website" in text) and \
               href.startswith("http") and "bbb.org" not in href:
                return href.split("?")[0]
        for a in soup.select("a[href^='http']"):
            href = a["href"]
            if "bbb.org" not in href and len(href) > 10:
                return href.split("?")[0]
    except Exception:
        pass
    return ""


def scrape_bbb(city, keyword, pages=3):
    results = []
    session = requests.Session()
    session.headers.update(STEALTH_HEADERS)

    city_slug = quote_plus(city)
    keyword_slug = quote_plus(keyword)

    for page in range(1, pages + 1):
        url = (
            f"{BBB_BASE}/search?"
            f"find_country=USA&find_text={keyword_slug}"
            f"&find_loc={city_slug}&page={page}"
        )
        print(f"🟩 BBB → {url}")

        try:
            res = session.get(url, timeout=25)
        except Exception as e:
            print(f"  ⚠ {e}")
            continue

        if res.status_code != 200:
            print(f"  ⚠ Status {res.status_code}")
            continue

        soup = BeautifulSoup(res.text, "html.parser")

        listings = (
            soup.select("div.result-item")
            or soup.select(".MuiCard-root")
            or soup.select("div[class*='result']")
            or soup.select("li[class*='result']")
        )

        if not listings:
            print(f"  ⚠ No listings page {page}")
            continue

        print(f"  ✅ {len(listings)} listings")

        for item in listings:
            name = ""
            profile_url = ""

            for sel in ["a.result-business-name", "a[href*='/profile/']",
                        "h3 a", "h2 a"]:
                tag = item.select_one(sel)
                if tag:
                    name = tag.get_text(strip=True)
                    href = tag.get("href", "")
                    profile_url = href if href.startswith(
                        "http") else urljoin(BBB_BASE, href)
                    break

            if not name:
                continue

            phone = ""
            for sel in [".phone", "[class*='phone']", "p.bds-body"]:
                tag = item.select_one(sel)
                if tag:
                    raw = re.sub(r"\D", "", tag.get_text())
                    if len(raw) >= 7:
                        phone = raw
                        break

            address = ""
            for sel in [".address", "[class*='address']", "address"]:
                tag = item.select_one(sel)
                if tag:
                    address = tag.get_text(" ", strip=True)
                    break

            website = ""
            for a in item.select("a[href^='http']"):
                href = a["href"]
                if "bbb.org" not in href:
                    website = href.split("?")[0]
                    break

            if not website and profile_url:
                time.sleep(random.uniform(0.5, 1.2))
                website = _get_website_from_profile(session, profile_url)

            results.append(create_business(
                name=name, phone=phone, address=address,
                website=website, email="", city=city,
                category=keyword, source="BBB"
            ))

        time.sleep(random.uniform(2.0, 4.0))

    return results
