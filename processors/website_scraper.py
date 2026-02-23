# processors/website_scraper.py

import re
from urllib import response
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils.helpers import safe_request
from utils.headers import get_headers

# ==========================
# REGEX PATTERNS
# ==========================

EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_REGEX = r"(?:\+91[\s-]?|0)?[6-9]\d{9}"
LINKEDIN_REGEX = re.compile(r"https?://(www\.)?linkedin\.com/[A-Za-z0-9/_\-]+")

CONTACT_HINTS = [
    "contact",
    "contact-us",
    "get-in-touch",
    "reach-us",
    "connect",
    "support",
    "about"
]

# ==========================
# FIND CONTACT PAGE
# ==========================


def find_contact_page(base_url, html):
    html_lower = html.lower()

    for hint in CONTACT_HINTS:
        if f'href="/{hint}' in html_lower:
            return urljoin(base_url, f"/{hint}")
        if f'href="{hint}' in html_lower:
            return urljoin(base_url, hint)

    return None

# ==========================
# EXTRACT DATA FROM HTML
# ==========================


def extract_data(html):
    emails = set(EMAIL_REGEX.findall(html))
    phones = set(PHONE_REGEX.findall(html))
    linkedin = set(LINKEDIN_REGEX.findall(html))

    return emails, phones, linkedin

# ==========================
# SCRAPE SINGLE WEBSITE
# ==========================


def scrape_website_data(url):
    if not url:
        return None

    if not url.startswith("http"):
        url = "https://" + url

    headers = get_headers()

    try:
        response = safe_request(url, headers=headers)
        if not response:
            return None

        html = response.text

        # 🚀 Skip slow / blocked pages
        if "timeout" in html.lower():
            return None

        emails, phones, linkedin = extract_data(html)

        # 🔎 find contact page
        contact_page = find_contact_page(url, html)

        if contact_page:
            response2 = safe_request(contact_page, headers=headers)
            if response2:
                e2, p2, l2 = extract_data(response2.text)
                emails.update(e2)
                phones.update(p2)
                linkedin.update(l2)

        return {
            "Email": list(emails)[:5],
            "Phone": list(phones)[:3],
            "LinkedIn": list(linkedin)[:2]
        }

    except Exception:
        return None

# ==========================
# ⚡ BULK THREADED SCRAPER
# ==========================


def scrape_websites_bulk(websites, workers=20):
    """
    ⚡ FAST threaded scraping
    Default workers = 20 (balanced speed & stability)
    """
    results = {}

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(scrape_website_data, site): site
            for site in websites if site
        }

        for future in as_completed(futures):
            site = futures[future]
            try:
                data = future.result()
                if data:
                    results[site] = data
            except Exception:
                pass

    return results
