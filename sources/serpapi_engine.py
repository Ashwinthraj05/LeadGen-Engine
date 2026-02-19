from serpapi import GoogleSearch
from config import SERP_API_KEY


def scrape_serpapi(city, keyword, pages=3):

    all_results = []

    for page in range(pages):

        params = {
            "engine": "google",
            "q": f"{keyword} in {city}",
            "api_key": SERP_API_KEY,
            "start": page * 10
        }

        search = GoogleSearch(params)
        results = search.get_dict()

        organic = results.get("organic_results", [])

        for item in organic:

            website = item.get("link")
            title = item.get("title")

            if website:
                all_results.append({
                    "Name": title,
                    "Website": website,
                    "Phone": "",
                    "Email": ""
                })

    return all_results
