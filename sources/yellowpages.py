import requests
import time
from bs4 import BeautifulSoup
from urllib.parse import parse_qs, urlparse

from utils.helpers import create_business
from utils.headers import get_headers


def extract_real_website(url):
    """Extract actual website from YellowPages redirect"""
    try:
        parsed = urlparse(url)
        if "biz_redir" in parsed.path:
            return parse_qs(parsed.query).get("url", [""])[0]
        return url
    except:
        return ""


def scrape_yellowpages(city, category, pages=3):
    """
    Scrape YellowPages business listings
    Works globally for multiple cities & categories
    """

    results = []

    session = requests.Session()
    session.headers.update(get_headers())

    for page in range(1, pages + 1):

        url = (
            "https://www.yellowpages.com/search?"
            f"search_terms={category}&"
            f"geo_location_terms={city}&"
            f"page={page}"
        )

        print(f"🟡 YellowPages → {url}")

        try:
            res = session.get(url, timeout=20)
        except Exception:
            continue

        if res.status_code != 200:
            print("⚠ Blocked:", res.status_code)
            continue

        soup = BeautifulSoup(res.text, "html.parser")
        listings = soup.select("div.result")

        if not listings:
            print("⚠ No listings found")
            continue

        for listing in listings:

            # -----------------
            # BUSINESS NAME
            # -----------------
            name_tag = listing.select_one("a.business-name")
            if not name_tag:
                continue

            name = name_tag.get_text(strip=True)

            # -----------------
            # WEBSITE
            # -----------------
            website = ""
            website_tag = listing.select_one(
                "a.track-visit-website, a.visit-business"
            )

            if website_tag:
                raw_url = website_tag.get("href")
                website = extract_real_website(raw_url)

            # -----------------
            # PHONE
            # -----------------
            phone = ""
            phone_tag = listing.select_one(".phones")
            if phone_tag:
                phone = phone_tag.get_text(strip=True)

            # -----------------
            # ADDRESS
            # -----------------
            address = ""
            addr_tag = listing.select_one(".street-address")
            if addr_tag:
                address = addr_tag.get_text(" ", strip=True)

            results.append(
                create_business(
                    name=name,
                    phone=phone,
                    address=address,
                    website=website,
                    email="",
                    city=city,
                    category=category,
                    source="YellowPages"
                )
            )

        time.sleep(2)  # avoid blocking

    return results
