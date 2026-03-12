"""
sources/serpapi_engine.py
FIXED:
  1. key_manager=None → return [] immediately, no crash
  2. No .get() called on strings anywhere
  3. Proper isinstance checks on every API response field
"""

import logging
import time
import requests

logger = logging.getLogger(__name__)

SERPAPI_BASE = "https://serpapi.com/search"

try:
    from serpapi_key_manager import key_manager
except Exception as e:
    logger.warning(f"serpapi_key_manager import failed: {e}")
    key_manager = None

SKIP_DOMAINS = [
    "justdial", "yellowpages", "yelp", "clutch", "goodfirms",
    "facebook", "linkedin", "wikipedia", "sulekha", "indiamart",
    "glassdoor", "indeed", "quora", "reddit", "twitter",
]


def _safe_request(params: dict) -> dict:
    """Single SerpAPI request with key rotation. Returns {} on any failure."""
    if not key_manager:
        return {}

    for attempt in range(len(key_manager.keys)):
        try:
            key = key_manager.get_key()
        except RuntimeError as e:
            logger.warning(f"All SerpAPI keys exhausted: {e}")
            return {}

        params["api_key"] = key

        try:
            r = requests.get(SERPAPI_BASE, params=params, timeout=20)
            r.raise_for_status()
            data = r.json()

            if not isinstance(data, dict):
                return {}
            if "error" in data:
                raise ValueError(str(data["error"]))

            key_manager.record_use(key)
            return data

        except ValueError as e:
            key_manager.record_error(key, e)
            time.sleep(2)
        except requests.RequestException as e:
            logger.error(f"SerpAPI network error: {e}")
            return {}

    return {}


def scrape_serpapi(city: str, category: str, pages: int = 5) -> list:
    """
    Scrape via SerpAPI organic + Maps engines.
    Returns [] if no keys configured — caller handles gracefully.
    """
    from utils.helpers import create_business

    if not key_manager:
        return []

    results = []
    seen = set()
    query = f"{category} in {city}"

    # ── Organic search ─────────────────────────────────────────────────────
    for page in range(pages):
        data = _safe_request({
            "engine": "google",
            "q":      query,
            "hl":     "en",
            "gl":     "in",
            "num":    10,
            "start":  page * 10,
        })
        if not data:
            break

        # local pack inside organic
        for item in data.get("local_results", []):
            if not isinstance(item, dict):
                continue
            name = str(item.get("title",   "") or "").strip()
            website = str(item.get("website", "") or "").strip()
            phone = str(item.get("phone",   "") or "").strip()
            address = str(item.get("address", "") or "").strip()
            if not name:
                continue
            uid = (name.lower(), website.lower())
            if uid in seen:
                continue
            seen.add(uid)
            results.append(create_business(
                name=name, phone=phone, address=address,
                website=website, city=city, category=category,
                source="SerpAPI-Local"
            ))

        # organic results
        for item in data.get("organic_results", []):
            if not isinstance(item, dict):
                continue
            name = str(item.get("title", "") or "").strip()
            website = str(item.get("link",  "") or "").strip()
            if not name or not website:
                continue
            if any(d in website.lower() for d in SKIP_DOMAINS):
                continue
            if website.lower() in seen:
                continue
            seen.add(website.lower())
            results.append(create_business(
                name=name, phone="", address="",
                website=website, city=city, category=category,
                source="SerpAPI-Organic"
            ))

        organic = data.get("organic_results", [])
        if not isinstance(organic, list) or len(organic) < 10:
            break
        time.sleep(0.4)

    # ── Google Maps engine ─────────────────────────────────────────────────
    next_token = None
    for page in range(pages):
        params = {
            "engine": "google_maps",
            "q":      query,
            "type":   "search",
            "hl":     "en",
            "gl":     "in",
        }
        if next_token:
            params["next_page_token"] = next_token
        else:
            params["start"] = page * 20

        data = _safe_request(params)
        if not data:
            break

        local = data.get("local_results", [])
        if not isinstance(local, list) or not local:
            break

        for item in local:
            if not isinstance(item, dict):
                continue
            name = str(item.get("title",   "") or "").strip()
            website = str(item.get("website", "") or "").strip()
            phone = str(item.get("phone",   "") or "").strip()
            address = str(item.get("address", "") or "").strip()
            if not name:
                continue
            uid = (name.lower(), website.lower())
            if uid in seen:
                continue
            seen.add(uid)
            results.append(create_business(
                name=name, phone=phone, address=address,
                website=website, city=city, category=category,
                source="SerpAPI-Maps"
            ))

        pagination = data.get("serpapi_pagination", {})
        next_token = pagination.get("next_page_token") if isinstance(
            pagination, dict) else None
        if not next_token and len(local) < 20:
            break
        time.sleep(0.4)

    logger.info(f"SerpAPI [{city}/{category}]: {len(results)}")
    return results
