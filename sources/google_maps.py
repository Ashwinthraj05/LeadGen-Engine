from config import SERP_API_KEY
from utils.helpers import create_business, safe_request


def scrape_google_maps(city, category, pages=1):
    results = []

    query = f"{category} in {city}"
    url = "https://serpapi.com/search"

    for page in range(pages):
        params = {
            "engine": "google_maps",
            "q": query,
            "api_key": SERP_API_KEY,
            "start": page * 20
        }

        response = safe_request(url, headers=None)

        if not response:
            continue

        try:
            data = response.json()
        except Exception:
            continue

        local_results = data.get("local_results", [])

        for r in local_results:
            results.append(
                create_business(
                    name=r.get("title", ""),
                    phone=r.get("phone", ""),
                    address=r.get("address", ""),
                    website=r.get("website", ""),
                    email="",
                    city=city,
                    category=category,
                    source="Google Maps"
                )
            )

    return results
