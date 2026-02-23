import requests
import re

HEADERS = {"User-Agent": "Mozilla/5.0"}


def find_contact_page(domain):
    """
    Find hidden contact pages indexed by Google
    """
    try:
        query = f"site:{domain} contact email"
        url = f"https://www.google.com/search?q={query}"

        res = requests.get(url, headers=HEADERS, timeout=8)

        links = re.findall(r"https://[^\"&]+", res.text)

        for link in links:
            if domain in link and "contact" in link:
                return link

    except:
        pass

    return None
