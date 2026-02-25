import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from utils.headers import get_headers
from utils.helpers import create_business
from utils.stealth import human_delay


def scrape_bbb(city, keyword, pages=2):
    """
    Scrape Better Business Bureau listings
    Works best for US companies & outsourcing firms
    """

    results = []
    session = requests.Session()
    session.headers.update(get_headers())

    city_slug = city.replace(" ", "-")
    keyword_slug = keyword.replace(" ", "+")

    for page in range(1, pages + 1):

        url = (
            "https://www.bbb.org/search?"
            f"find_country=USA&"
            f"find_text={keyword_slug}&"
            f"find_loc={city_slug}&"
            f"page={page}"
        )

        print(f"🟩 BBB → {url}")

        try:
            res = session.get(url, timeout=20)
        except Exception:
            continue

        if res.status_code != 200:
            print("⚠ Blocked:", res.status_code)
            continue

        soup = BeautifulSoup(res.text, "html.parser")

        listings = soup.select(
            ".result-item, .MuiCard-root"
        )

        if not listings:
            print("⚠ No results found")
            continue

        for item in listings:

            # -----------------
            # BUSINESS NAME
            # -----------------
            name_tag = item.select_one(
                "a.result-business-name, a[href*='/profile/']"
            )

            if not name_tag:
                continue

            name = name_tag.get_text(strip=True)

            # -----------------
            # WEBSITE
            # -----------------
            website = ""

            site_tag = item.select_one(
                "a[href^='http'][rel='noopener'], a[href*='http']"
            )

            if site_tag:
                website = site_tag.get("href", "").strip()

            if not website:
                continue

            # -----------------
            # PHONE (optional)
            # -----------------
            phone = ""
            phone_tag = item.select_one(".bds-body")
            if phone_tag:
                phone = phone_tag.get_text(strip=True)

            results.append(
                create_business(
                    name=name,
                    phone=phone,
                    address="",
                    website=website,
                    email="",
                    city=city,
                    category=keyword,
                    source="BBB"
                )
            )

        human_delay()

    return results
