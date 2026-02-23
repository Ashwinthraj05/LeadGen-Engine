from serpapi.google_search import GoogleSearch
from config import SERP_API_KEY
from utils.helpers import create_business


def scrape_serpapi(city, keyword, pages=3):
    """
    Fetch businesses using SerpApi Google search results
    """

    if not SERP_API_KEY:
        print("❌ Missing SERP API Key")
        return []

    all_results = []
    seen_websites = set()

    for page in range(pages):
        try:
            params = {
                "engine": "google",
                "q": f"{keyword} in {city}",
                "api_key": SERP_API_KEY,
                "start": page * 10,
            }

            search = GoogleSearch(params)
            results = search.get_dict()

            organic = results.get("organic_results", [])

            for item in organic:
                website = item.get("link")
                title = item.get("title")

                if not website:
                    continue

                if website in seen_websites:
                    continue

                business = create_business(
                    name=title,
                    website=website,
                    city=city,
                    category=keyword,
                    source="SerpAPI"
                )

                if business:
                    all_results.append(business)
                    seen_websites.add(website)

        except Exception as e:
            print(f"⚠ SerpApi error: {e}")

    return all_results
