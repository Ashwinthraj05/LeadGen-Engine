from bs4 import BeautifulSoup
import requests
import time

from utils.helpers import create_business
from config import HEADERS


def slugify(text):
    return (
        text.lower()
        .replace("&", "and")
        .replace(",", "")
        .strip()
        .replace(" ", "-")
    )


def scrape_sulekha(city, category, pages=2):
    """
    Scrape Sulekha listings for any city & category
    """

    results = []

    city_slug = city.lower().replace(" ", "-")
    category_slug = slugify(category)

    session = requests.Session()
    session.headers.update(HEADERS)

    for page in range(1, pages + 1):

        url = f"https://www.sulekha.com/{category_slug}-services/{city_slug}?page={page}"

        print(f"📒 Sulekha → {url}")

        try:
            res = session.get(url, timeout=20)
        except Exception:
            continue

        if res.status_code != 200:
            print("⚠ Blocked:", res.status_code)
            continue

        soup = BeautifulSoup(res.text, "html.parser")

        # NEW layout
        cards = soup.select("div.listing-card")

        # fallback layout
        if not cards:
            cards = soup.select(".business-listing")

        if not cards:
            print("⚠ No results / layout changed")
            continue

        for card in cards:

            # -------------------
            # NAME
            # -------------------
            name = ""
            tag = card.select_one("h3, h2, .title")
            if tag:
                name = tag.get_text(strip=True)

            if not name:
                continue

            # -------------------
            # ADDRESS
            # -------------------
            address = ""
            addr = card.select_one(".address, .addr, .location")
            if addr:
                address = addr.get_text(" ", strip=True)

            # -------------------
            # PHONE (rarely visible)
            # -------------------
            phone = ""
            phone_tag = card.select_one(".contact, .phone")
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
                    source="Sulekha"
                )
            )

        time.sleep(1.5)

    return results
