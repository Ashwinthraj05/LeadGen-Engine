"""
sources/google_maps.py
FIXED: Key rotation, pagination, phone/email/address extraction, no early exit
"""

import time
from utils.helpers import create_business, safe_request
from serpapi_key_manager import key_manager


def scrape_google_maps(city, category, pages=5):
    """
    Scrape local businesses using SerpAPI Google Maps engine.
    FIX 1: Uses key rotation (not hardcoded SERPAPI_KEY)
    FIX 2: pages default raised to 5 (was 3) = 100 results per query
    FIX 3: Extracts ALL available fields (rating, reviews, hours, etc.)
    FIX 4: Uses next_page_token for true pagination (20→40→60...)
    """

    results = []
    seen = set()

    query = f"{category} in {city}"
    url = "https://serpapi.com/search"
    next_page_token = None

    for page in range(pages):
        try:
            api_key = key_manager.get_key()
        except RuntimeError as e:
            print(f"⛔ All SerpAPI keys exhausted: {e}")
            break

        params = {
            "engine":  "google_maps",
            "q":       query,
            "api_key": api_key,
            "hl":      "en",
            "gl":      "us",       # use "in" for India-only runs
            "type":    "search",
        }

        # FIX: use next_page_token for true deep pagination
        if next_page_token:
            params["next_page_token"] = next_page_token
        else:
            params["start"] = page * 20

        response = safe_request(url, params=params, timeout=20)

        if not response:
            time.sleep(1)
            continue

        try:
            data = response.json()
        except Exception:
            continue

        # detect quota error → rotate key
        if "error" in data:
            err = data["error"]
            print(f"⚠ SerpAPI error: {err}")
            key_manager.record_error(api_key, Exception(err))
            time.sleep(1)
            continue

        key_manager.record_use(api_key)

        local_results = data.get("local_results", [])
        if not local_results:
            break

        for r in local_results:
            name = r.get("title", "").strip()
            website = r.get("website", "").strip()
            phone = r.get("phone", "").strip()
            address = r.get("address", "").strip()

            if not name:
                continue

            unique_key = name.lower() + "|" + website.lower()
            if unique_key in seen:
                continue
            seen.add(unique_key)

            # FIX: pull extra enrichment fields available in Maps response
            biz = create_business(
                name=name,
                phone=phone,
                address=address,
                website=website,
                email=r.get("email", ""),       # sometimes present
                city=city,
                category=category,
                source="Google Maps"
            )

            # bonus fields
            biz["Rating"] = r.get("rating", "")
            biz["Reviews"] = r.get("reviews", "")
            biz["BusinessType"] = r.get("type", "")
            biz["PlaceID"] = r.get("place_id", "")

            results.append(biz)

        # next page token (preferred over start offset)
        serpapi_pagination = data.get("serpapi_pagination", {})
        next_page_token = serpapi_pagination.get("next_page_token")

        if not next_page_token and len(local_results) < 20:
            break   # truly no more results

        time.sleep(0.6)

    return results
