import requests
import time
from bs4 import BeautifulSoup
from urllib.parse import parse_qs, urlparse
from config import HEADERS
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


def scrape_yellowpages(city, keyword, pages=3):

    results = []

    city_slug = city.replace(" ", "-").lower()

    for page in range(1, pages + 1):

        url = (
            f"https://www.yellowpages.com/search?"
            f"search_terms={keyword}&"
            f"geo_location_terms={city_slug}&"
            f"page={page}"
        )

        print(f"🟡 YellowPages → {url}")

        try:
            response = requests.get(url, headers=get_headers(), timeout=15)

            if response.status_code != 200:
                print("⚠ Blocked or failed")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            listings = soup.select("div.result")

            for listing in listings:

                name_tag = listing.select_one("a.business-name")
                if not name_tag:
                    continue

                name = name_tag.get_text(strip=True)

                website = ""
                website_tag = listing.select_one("a.track-visit-website")

                if website_tag:
                    raw_url = website_tag.get("href")
                    website = extract_real_website(raw_url)

                # skip listings without websites (optional but recommended)
                if not website:
                    continue

                phone = ""
                phone_tag = listing.select_one("div.phones")
                if phone_tag:
                    phone = phone_tag.get_text(strip=True)

                results.append({
                    "Name": name,
                    "Website": website,
                    "Phone": phone
                })

            time.sleep(2)  # prevent blocking

        except Exception as e:
            print("YellowPages error:", e)

    return results
