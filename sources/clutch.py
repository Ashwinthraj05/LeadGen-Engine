import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from utils.headers import get_headers
from utils.helpers import create_business
from utils.stealth import human_delay


def scrape_clutch(city, keyword, pages=2):
    """
    Scrape Clutch company listings
    Works globally for services like:
    BPO, IT Services, Medical Billing, RCM, Outsourcing
    """

    results = []
    session = requests.Session()
    session.headers.update(get_headers())

    keyword_slug = keyword.replace(" ", "-").lower()

    for page in range(1, pages + 1):

        url = f"https://clutch.co/search?query={keyword_slug}&page={page}"

        print(f"🔵 Clutch → {url}")

        try:
            res = session.get(url, timeout=20)
        except Exception:
            continue

        if res.status_code != 200:
            print("⚠ Blocked:", res.status_code)
            continue

        soup = BeautifulSoup(res.text, "html.parser")

        companies = soup.select(
            ".provider-row, .directory-list div.provider"
        )

        if not companies:
            print("⚠ No companies found")
            continue

        for comp in companies:

            # -----------------
            # NAME
            # -----------------
            name_tag = comp.select_one(
                ".company-name, .provider__title a"
            )

            if not name_tag:
                continue

            name = name_tag.get_text(strip=True)

            # -----------------
            # WEBSITE
            # -----------------
            website = ""

            website_tag = comp.select_one(
                "a.website-link__item, a[data-type='website']"
            )

            if website_tag:
                website = website_tag.get("href", "")
                if website.startswith("/"):
                    website = urljoin("https://clutch.co", website)

            # skip if no website (optional)
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
                    source="Clutch"
                )
            )

        human_delay()

    return results
