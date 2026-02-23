from config import SERP_API_KEY
from utils.helpers import create_business, safe_request
import time


def scrape_google_maps(city, category, pages=3):
    """
    Scrape local businesses using SerpAPI Google Maps engine.
    """

    results = []
    seen = set()

    query = f"{category} in {city}"
    url = "https://serpapi.com/search"

    for page in range(pages):
        params = {
            "engine": "google_maps",
            "q": query,
            "api_key": SERP_API_KEY,
            "start": page * 20,
            "hl": "en",
            "gl": "in"
        }

        response = safe_request(url, params=params)

        if not response:
            continue

        try:
            data = response.json()
        except Exception:
            continue

        local_results = data.get("local_results", [])

        # stop early if no more results
        if not local_results:
            break

        for r in local_results:
            name = r.get("title", "").strip()
            website = r.get("website", "").strip()

            # skip empty names
            if not name:
                continue

            # avoid duplicates
            unique_key = (name.lower(), website.lower())
            if unique_key in seen:
                continue
            seen.add(unique_key)

            results.append(
                create_business(
                    name=name,
                    phone=r.get("phone", ""),
                    address=r.get("address", ""),
                    website=website,
                    email="",
                    city=city,
                    category=category,
                    source="Google Maps"
                )
            )

        # avoid throttling
        time.sleep(0.5)

    return results
