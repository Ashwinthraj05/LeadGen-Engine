import sys
import asyncio
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
import random

# ✅ FIX: Required for Windows + Streamlit subprocess support
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


def scrape_playwright(city, keyword, pages=3):
    """
    Scrapes Google search results using Playwright.
    Returns list of business websites.
    """

    results = []
    seen = set()

    search_query = quote_plus(f"{keyword} in {city}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
            locale="en-US"
        )

        page = context.new_page()

        for i in range(pages):
            start = i * 10
            url = f"https://www.google.com/search?q={search_query}&start={start}"

            print(f"Playwright → {url}")

            try:
                page.goto(url, timeout=60000)
                page.wait_for_load_state("domcontentloaded")
                time.sleep(random.uniform(2, 4))

                html = page.content()

                # detect CAPTCHA / block
                if "captcha" in html.lower():
                    print("⚠ Google CAPTCHA detected — stopping")
                    break

                soup = BeautifulSoup(html, "html.parser")

                for result in soup.select("div.tF2Cxc"):
                    link_tag = result.select_one("a")
                    title_tag = result.select_one("h3")

                    if not link_tag or not title_tag:
                        continue

                    website = link_tag.get("href")

                    if not website or website in seen:
                        continue

                    seen.add(website)

                    results.append({
                        "Name": title_tag.get_text(strip=True),
                        "Website": website,
                        "Phone": "",
                        "Email": ""
                    })

            except Exception as e:
                print(f"Playwright error: {e}")

            time.sleep(random.uniform(2, 5))

        browser.close()

    return results
