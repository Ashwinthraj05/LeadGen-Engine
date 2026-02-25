from bs4 import BeautifulSoup
import requests
import time

from utils.helpers import create_business
from config import HEADERS


def scrape_indiamart(city, category, pages=2):
    """
    Scrapes IndiaMART supplier listings
    Works for all cities & categories
    """

    results = []

    query = f"{category} {city}".replace(" ", "+")

    session = requests.Session()
    session.headers.update(HEADERS)

    for page in range(1, pages + 1):

        url = f"https://www.indiamart.com/search.mp?ss={query}&page={page}"

        print(f"📒 IndiaMART → {url}")

        try:
            res = session.get(url, timeout=20)
        except Exception:
            continue

        if res.status_code != 200:
            print("⚠ Blocked:", res.status_code)
            continue

        soup = BeautifulSoup(res.text, "html.parser")

        # updated listing cards
        cards = soup.select(".cardbody, .f-div")

        if not cards:
            print("⚠ No results / layout changed")
            continue

        for card in cards:

            # ------------------
            # COMPANY NAME
            # ------------------
            name = ""
            name_tag = card.select_one("a.compname, .company-name, .pn")
            if name_tag:
                name = name_tag.get_text(strip=True)

            if not name:
                continue

            # ------------------
            # ADDRESS
            # ------------------
            address = ""
            addr_tag = card.select_one(".address, .city, .loc")
            if addr_tag:
                address = addr_tag.get_text(" ", strip=True)

            # ------------------
            # PHONE
            # ------------------
            phone = ""
            phone_tag = card.select_one(".mobile, .contact-number")
            if phone_tag:
                phone = phone_tag.get_text(strip=True)

            results.append(
                create_business(
                    name=name,
                    phone=phone,
                    address=address,
                    website="",
                    email="",
                    city=city,
                    category=category,
                    source="IndiaMART"
                )
            )

        time.sleep(1.5)

    return results
