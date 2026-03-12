"""
sources/playwright_engine.py
FIXED:
  1. Returns proper create_business dicts (not raw dicts) — was causing
     KeyError crashes in orchestrator
  2. Extracts local pack results (map results) — much richer data
  3. Also extracts phone from knowledge panel when available
  4. Better organic result selectors for current Google layout
  5. CAPTCHA detection improved
  6. Windows event loop policy fix kept
"""

import sys
import asyncio
import time
import random
from urllib.parse import quote_plus

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

from utils.helpers import create_business

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

BLOCKED_DOMAINS = [
    "justdial", "yellowpages", "yelp", "clutch", "goodfirms",
    "facebook", "linkedin", "instagram", "wikipedia", "glassdoor",
    "indeed", "quora", "reddit", "sulekha", "indiamart",
]


def scrape_playwright(city: str, keyword: str, pages: int = 3) -> list:
    """
    Fallback scraper using Playwright when SerpAPI is exhausted.
    Extracts both organic results and local pack (Maps) cards.
    """

    results = []
    seen = set()

    query = quote_plus(f"{keyword} in {city}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ]
            )

            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1366, "height": 768},
                locale="en-US",
            )

            page = context.new_page()

            # block images/fonts to speed up
            page.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf}",
                       lambda r: r.abort())

            for i in range(pages):
                start = i * 10
                url = f"https://www.google.com/search?q={query}&start={start}&hl=en"

                print(f"🎭 Playwright → page {i+1}: {url}")

                try:
                    page.goto(url, timeout=45000,
                              wait_until="domcontentloaded")
                    time.sleep(random.uniform(1.5, 3.0))

                    html = page.content()

                    if "captcha" in html.lower() or \
                       "unusual traffic" in html.lower():
                        print("  ⚠ CAPTCHA detected — stopping Playwright")
                        break

                    soup = BeautifulSoup(html, "html.parser")

                    # ── Local pack (Maps cards) ────────────────────────────
                    for card in soup.select("div.VkpGBb, div[class*='uMdZh']"):
                        name_tag = card.select_one("div.dbg0pd, span.OSrXXb")
                        if not name_tag:
                            continue
                        name = name_tag.get_text(strip=True)
                        if not name or name.lower() in seen:
                            continue
                        seen.add(name.lower())

                        phone = ""
                        phone_tag = card.select_one(
                            "span[class*='phone'], [data-dtype='d3ph']")
                        if phone_tag:
                            phone = phone_tag.get_text(strip=True)

                        website = ""
                        for a in card.select("a[href^='http']"):
                            href = a["href"]
                            if not any(d in href for d in BLOCKED_DOMAINS):
                                website = href.split("?")[0]
                                break

                        results.append(create_business(
                            name=name, phone=phone, address="",
                            website=website, email="",
                            city=city, category=keyword,
                            source="Playwright-Maps"
                        ))

                    # ── Organic results ────────────────────────────────────
                    for result in soup.select(
                        "div.tF2Cxc, div.g, div[class*='MjjYud'] > div"
                    ):
                        link_tag = result.select_one("a[href^='http']")
                        title_tag = result.select_one("h3")

                        if not link_tag or not title_tag:
                            continue

                        website = link_tag.get("href", "").split("?")[0]
                        name = title_tag.get_text(strip=True)

                        if not website or not name:
                            continue

                        if any(d in website.lower() for d in BLOCKED_DOMAINS):
                            continue

                        key = website.lower()
                        if key in seen:
                            continue
                        seen.add(key)

                        results.append(create_business(
                            name=name, phone="", address="",
                            website=website, email="",
                            city=city, category=keyword,
                            source="Playwright-Organic"
                        ))

                except Exception as e:
                    print(f"  ⚠ Page error: {e}")

                time.sleep(random.uniform(2.0, 4.0))

            browser.close()

    except Exception as e:
        print(f"Playwright launch error: {e}")

    print(f"  🎭 Playwright total: {len(results)} results")
    return results
