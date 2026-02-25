from bs4 import BeautifulSoup
import requests
import time
import re

from utils.helpers import create_business
from config import HEADERS


def slugify(text):
    """Convert category to Justdial slug format"""
    return (
        text.lower()
        .replace("&", "and")
        .replace(",", "")
        .replace("  ", " ")
        .strip()
        .replace(" ", "-")
    )


def scrape_justdial(city, category, pages=3):
    """
    Scrape Justdial listings for any city & category
    """

    results = []

    city_slug = city.lower().replace(" ", "-")
    category_slug = slugify(category)

    session = requests.Session()
    session.headers.update(HEADERS)

    for page in range(1, pages + 1):

        url = f"https://www.justdial.com/{city_slug}/{category_slug}/page-{page}"

        print(f"📒 Justdial → {url}")

        try:
            res = session.get(url, timeout=20)
        except Exception:
            continue

        if res.status_code != 200:
            print("⚠ Blocked:", res.status_code)
            continue

        soup = BeautifulSoup(res.text, "html.parser")

        # NEW layout cards
        cards = soup.select("li.cntanr")

        # fallback older layout
        if not cards:
            cards = soup.select("div.resultbox")

        if not cards:
            print("⚠ No results (layout/block)")
            continue

        for card in cards:

            # ----------------------
            # BUSINESS NAME
            # ----------------------
            name = ""

            tag = card.select_one(
                "h2, .lng_cont_name, .resultbox_title_anchor")
            if tag:
                name = tag.get_text(strip=True)

            if not name:
                continue

            # ----------------------
            # PHONE
            # ----------------------
            phone = ""

            phone_tag = card.select_one(
                ".contact-info span, .callcontent, .mobilesv")
            if phone_tag:
                phone = re.sub(r"\D+", "", phone_tag.get_text())

            # ----------------------
            # ADDRESS
            # ----------------------
            address = ""

            addr_tag = card.select_one(".cont_fl_addr, .address, .mrehover")
            if addr_tag:
                address = addr_tag.get_text(" ", strip=True)

            results.append(
                create_business(
                    name=name,
                    phone=phone,
                    address=address,
                    website="",
                    email="",
                    city=city,
                    category=category,
                    source="Justdial"
                )
            )

        time.sleep(1.5)

    return results
