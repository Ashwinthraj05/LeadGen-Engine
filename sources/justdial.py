"""
sources/justdial.py
FIXED:
  1. BIG FIX: Only scrape base city+category — not keyword variants like
     "seo-agency-in-bangalore" which 404 every time. The orchestrator calls
     this once per category, not per expanded keyword.
  2. Website extracted by visiting individual company profile pages
  3. Phone decoded from JD CSS icon obfuscation
  4. Falls back to DuckDuckGo search if profile visit gets no website
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
    "Accept-Encoding": "gzip, deflate, br",
    "Referer":         "https://www.justdial.com/",
    "DNT":             "1",
    "Connection":      "keep-alive",
}

JD_BASE = "https://www.justdial.com"

JD_PHONE_MAP = {
    "icon-f1": "8", "icon-f2": "9", "icon-f3": "0",
    "icon-f4": "1", "icon-f5": "2", "icon-f6": "3",
    "icon-f7": "4", "icon-f8": "5", "icon-f9": "6",
    "icon-f0": "7",
}

SKIP_IN_WEBSITE = [
    "justdial", "facebook", "linkedin", "instagram",
    "twitter", "youtube", "sulekha", "indiamart",
]


def _slugify(text: str) -> str:
    """Convert text to JustDial URL slug."""
    return (
        text.lower()
        .strip()
        .replace("&", "and")
        .replace("/", "-")
        .replace(",", "")
        .replace("  ", " ")
        .replace(" ", "-")
    )


def _decode_phone(card) -> str:
    digits = []
    for span in card.select("span[class]"):
        for cls in span.get("class", []):
            if cls in JD_PHONE_MAP:
                digits.append(JD_PHONE_MAP[cls])
    return "".join(digits) if len(digits) >= 7 else ""


def _get_website_from_profile(session: requests.Session, profile_url: str) -> str:
    """Visit JD company page to extract their real external website."""
    if not profile_url:
        return ""
    try:
        r = session.get(profile_url, timeout=15)
        if r.status_code != 200:
            return ""
        soup = BeautifulSoup(r.text, "html.parser")

        for a in soup.select("a[href]"):
            href = str(a.get("href", ""))
            text = a.get_text(strip=True).lower()

            # direct clean external link labeled as website
            if href.startswith("http") and not any(s in href.lower() for s in SKIP_IN_WEBSITE):
                if any(kw in text for kw in ("website", "visit", "web", "homepage")):
                    return href.split("?")[0]

            # JD redirect: /redir?url=https://...
            if "redir" in href and "url=" in href:
                try:
                    from urllib.parse import parse_qs, urlparse as _up
                    qs = parse_qs(_up(href).query)
                    url = qs.get("url", [""])[0]
                    if url and not any(s in url.lower() for s in SKIP_IN_WEBSITE):
                        return url.split("?")[0]
                except Exception:
                    pass

        # fallback: first clean external link on the page
        for a in soup.select("a[href^='http']"):
            href = a["href"]
            if not any(s in href.lower() for s in SKIP_IN_WEBSITE) and len(href) > 12:
                return href.split("?")[0]

    except Exception:
        pass
    return ""


def _find_website_ddg(session: requests.Session, name: str, city: str) -> str:
    """DuckDuckGo fallback when profile page has no website."""
    try:
        q = quote_plus(f"{name} {city} official website")
        url = f"https://html.duckduckgo.com/html/?q={q}"
        r = session.get(url, headers=STEALTH_HEADERS, timeout=10)
        if r.status_code != 200:
            return ""
        links = re.findall(r'href="(https?://[^"]+)"', r.text)
        for link in links:
            if not any(s in link.lower() for s in SKIP_IN_WEBSITE + ["duckduckgo"]):
                return link.split("?")[0]
    except Exception:
        pass
    return ""


def scrape_justdial(city: str, category: str, pages: int = 4) -> list:
    """
    Scrape JustDial for a city + category.
    KEY FIX: Only uses the base category slug — not keyword variants.
    "seo-agency-in-bangalore" → 404 every time.
    "seo-agency" → works fine.
    """
    results = []
    city_slug = _slugify(city)
    # FIXED: only slugify the raw category, not expanded variants
    cat_slug = _slugify(category)
    session = requests.Session()
    session.headers.update(STEALTH_HEADERS)
    websites_found = 0

    for page in range(1, pages + 1):

        url = (
            f"{JD_BASE}/{city_slug}/{cat_slug}"
            if page == 1
            else f"{JD_BASE}/{city_slug}/{cat_slug}/page-{page}"
        )

        print(f"📒 Justdial → {url}")

        try:
            res = session.get(url, timeout=25)
        except Exception as e:
            print(f"  ⚠ Request error: {e}")
            break

        if res.status_code == 403:
            print("  🚫 Blocked — retrying after delay...")
            time.sleep(random.uniform(8, 14))
            try:
                res = session.get(url, timeout=25)
            except Exception:
                break

        if res.status_code == 404:
            print(f"  ⚠ 404 — stopping JD for this category")
            break

        if res.status_code != 200:
            print(f"  ⚠ Status {res.status_code}")
            break

        soup = BeautifulSoup(res.text, "html.parser")

        cards = (
            soup.select("li.cntanr")
            or soup.select("li.resultbox")
            or soup.select("div.resultbox_info")
            or soup.select("div[class*='resultbox']")
            or soup.select("li[class*='store']")
        )

        if not cards:
            print(f"  ⚠ No cards on page {page}")
            if page == 1:
                # page 1 empty → nothing for this category
                break
            continue

        print(f"  ✅ Found {len(cards)} listings page {page}")

        for card in cards:

            # ── Name + profile URL ─────────────────────────────────────────
            name = ""
            profile_url = ""

            for sel in ["h2.lng_cont_name a", ".lng_cont_name a",
                        ".resultbox_title_anchor", "h2 a", ".jd-heading a"]:
                tag = card.select_one(sel)
                if tag and tag.get_text(strip=True):
                    name = tag.get_text(strip=True)
                    href = tag.get("href", "")
                    profile_url = href if href.startswith("http") \
                        else urljoin(JD_BASE, href)
                    break

            if not name:
                continue

            # ── Phone ──────────────────────────────────────────────────────
            phone = _decode_phone(card)
            if not phone:
                for sel in [".contact-info", ".callcontent", ".mobilesv",
                            "[class*='phone']", "[class*='call']"]:
                    tag = card.select_one(sel)
                    if tag:
                        raw = re.sub(r"\D", "", tag.get_text())
                        if len(raw) >= 7:
                            phone = raw
                            break

            # ── Address ────────────────────────────────────────────────────
            address = ""
            for sel in [".cont_fl_addr", ".address-info",
                        ".mrehover", "[class*='addr']"]:
                tag = card.select_one(sel)
                if tag:
                    address = tag.get_text(" ", strip=True)
                    break

            # ── Website: card → profile → DDG ─────────────────────────────
            website = ""

            # 1. Any direct external link in the card
            for a in card.select("a[href^='http']"):
                href = a["href"]
                if not any(s in href.lower() for s in SKIP_IN_WEBSITE):
                    website = href.split("?")[0]
                    break

            # 2. Visit profile page (limit to avoid slowness)
            if not website and profile_url and websites_found < 80:
                time.sleep(random.uniform(0.3, 0.7))
                website = _get_website_from_profile(session, profile_url)

            # 3. DDG fallback for first 30 leads only
            if not website and len(results) < 30:
                time.sleep(random.uniform(0.5, 1.0))
                website = _find_website_ddg(session, name, city)

            if website:
                websites_found += 1

            results.append(create_business(
                name=name,
                phone=phone,
                address=address,
                website=website,
                email="",
                city=city,
                category=category,
                source="Justdial"
            ))

        time.sleep(random.uniform(1.5, 3.0))

    print(
        f"  📒 JustDial [{city}/{category}]: {len(results)} leads, {websites_found} websites")
    return results
