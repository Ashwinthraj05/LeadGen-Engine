import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlsplit
from config import HEADERS

# ----------------------------------
# BLOCKED DOMAINS (junk sources)
# ----------------------------------

BLOCKED_DOMAINS = {
    "google.com",
    "youtube.com",
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "twitter.com",
    "justdial.com",
    "sulekha.com",
    "indiamart.com",
    "yellowpages.com",
    "yelp.com",
    "clutch.co",
    "goodfirms.co",
    "trustpilot.com",
    "wikipedia.org",
}

# words that indicate blog/list articles
BLOCKED_URL_KEYWORDS = {
    "blog",
    "top",
    "best",
    "list",
    "directory",
    "agencies",
    "companies",
    "services",
    "reviews",
    "ratings",
}

# ----------------------------------
# CLEAN GOOGLE REDIRECT LINKS
# ----------------------------------


def extract_actual_url(google_url):
    """
    Google wraps URLs like:
    /url?q=https://example.com&sa=...
    """
    parsed = urlsplit(google_url)

    if parsed.path == "/url":
        real_url = parse_qs(parsed.query).get("q")
        if real_url:
            return real_url[0]

    return google_url

# ----------------------------------
# VALIDATE BUSINESS WEBSITE
# ----------------------------------


def is_valid_business_url(link):
    if not link:
        return False

    domain = urlparse(link).netloc.lower()

    # remove www
    domain = domain.replace("www.", "")

    # block junk domains
    if any(b in domain for b in BLOCKED_DOMAINS):
        return False

    # block blog/list pages
    if any(word in link.lower() for word in BLOCKED_URL_KEYWORDS):
        return False

    return True

# ----------------------------------
# GOOGLE SEARCH SCRAPER
# ----------------------------------


def scrape_google_search(city, keyword, pages=3):
    """
    ✔ Finds real company websites
    ✔ Removes directories & blog pages
    ✔ Removes duplicates
    ✔ Returns clean domains
    """

    results = []
    seen_domains = set()

    query = f"{keyword} in {city}"

    for page in range(pages):
        start = page * 10

        url = f"https://www.google.com/search?q={query}&start={start}"

        print(f"🌐 Google Search → {url}")

        try:
            response = requests.get(url, headers=HEADERS, timeout=15)

            if response.status_code != 200:
                print("Google blocked request")
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            for g in soup.select("div.yuRUbf > a"):
                raw_link = g.get("href")

                if not raw_link:
                    continue

                link = extract_actual_url(raw_link)

                if not is_valid_business_url(link):
                    continue

                domain = urlparse(link).netloc.lower().replace("www.", "")

                # remove duplicates
                if domain in seen_domains:
                    continue

                seen_domains.add(domain)

                results.append({
                    "Name": domain,
                    "Website": link,
                    "Phone": ""
                })

        except Exception as e:
            print("Google Search error:", e)

    return results
