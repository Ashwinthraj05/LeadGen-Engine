import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from utils.headers import get_headers
from utils.helpers import create_business
from utils.stealth import human_delay


def scrape_manta(city, keyword, pages=2):
    """
    Scrape Manta business listings
    Works for US & global service companies
    """

    results = []
    session = requests.Session()
    session.headers.update(get_headers())

    city_slug = city.replace(" ", "-").lower()
    keyword_slug = keyword.replace(" ", "+")

    for page in range(1, pages + 1):

        url = (
            f"https://www.manta.com/search?"
            f"search={keyword_slug}&location={city_slug}&pg={page}"
        )

        print(f"🟢 Manta → {url}")

        try:
            res = session.get(url, timeout=20)
        except Exception:
            continue

        if res.status_code != 200:
            print("⚠ Blocked:", res.status_code)
            continue

        soup = BeautifulSoup(res.text, "html.parser")

        listings = soup.select(
            "div.SearchResults__Result, div.search-result"
        )

        if not listings:
            print("⚠ No listings found")
            continue

        for item in listings:

            # -----------------
            # BUSINESS NAME
            # -----------------
            name_tag = item.select_one(
                "a.SearchResult__TitleLink, a[data-testid='title']"
            )

            if not name_tag:
                continue

            name = name_tag.get_text(strip=True)

            # -----------------
            # WEBSITE LINK
            # -----------------
            website = ""

            site_tag = item.select_one(
                "a[href^='http'], a[data-testid='website']"
            )

            if site_tag:
                website = site_tag.get("href", "").strip()

                # handle relative links
                if website.startswith("/"):
                    website = urljoin("https://www.manta.com", website)

            if not website:
                continue

            results.append(
                create_business(
                    name=name,
                    phone="",
                    address="",
                    website=website,
                    email="",
                    city=city,
                    category=keyword,
                    source="Manta"
                )
            )

        human_delay()

    return results
