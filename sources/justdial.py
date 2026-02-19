from bs4 import BeautifulSoup
import requests
import time

from utils.helpers import create_business
from config import HEADERS


def scrape_justdial(city, category, pages=5):
    results = []

    category_slug = category.replace(" ", "-")

    session = requests.Session()
    session.headers.update(HEADERS)

    for page in range(1, pages + 1):
        url = f"https://www.justdial.com/{city}/{category_slug}?page={page}"
        print(f"📒 {url}")

        try:
            res = session.get(url, timeout=20)
        except:
            continue

        if res.status_code != 200:
            print("Blocked:", res.status_code)
            continue

        soup = BeautifulSoup(res.text, "html.parser")

        cards = soup.select("div.resultbox")

        if not cards:
            print("⚠ Layout changed or blocked")
            continue

        for card in cards:

            # BUSINESS NAME
            name_tag = card.select_one(".resultbox_title_anchor")
            name = name_tag.text.strip() if name_tag else ""

            if not name:
                continue

            # PHONE (visible numbers only)
            phone = ""
            phone_tag = card.select_one(".callcontent")
            if phone_tag:
                phone = phone_tag.text.strip()

            # ADDRESS
            address = ""
            addr_tag = card.select_one(".address")
            if addr_tag:
                address = addr_tag.text.strip()

            results.append(
                create_business(
                    name=name,
                    phone=phone,
                    address=address,
                    website="",   # website rarely available
                    email="",
                    city=city,
                    category=category,
                    source="Justdial"
                )
            )

        time.sleep(2)

    return results
