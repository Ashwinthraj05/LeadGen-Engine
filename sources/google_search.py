import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from config import HEADERS


BLOCKED_DOMAINS = [
    "google.com",
    "youtube.com",
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "justdial.com",
    "yellowpages.com",
    "yelp.com"
]


def scrape_google_search(city, keyword, pages=3):

    results = []

    query = f"{keyword} in {city}"

    for page in range(pages):

        start = page * 10
        url = (
            f"https://www.google.com/search?q={query}"
            f"&start={start}"
        )

        print(f"🌐 Google Search → {url}")

        try:
            response = requests.get(url, headers=HEADERS, timeout=15)

            if response.status_code != 200:
                print("Google blocked request")
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            for g in soup.select("div.yuRUbf > a"):

                link = g.get("href")

                if not link:
                    continue

                domain = urlparse(link).netloc.lower()

                if any(blocked in domain for blocked in BLOCKED_DOMAINS):
                    continue

                results.append({
                    "Name": domain,
                    "Website": link,
                    "Phone": ""
                })

        except Exception as e:
            print("Google Search error:", e)

    return results
