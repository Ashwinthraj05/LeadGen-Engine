import requests
import time
import random
import re
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor
from utils.headers import get_headers as rotating_headers

session = requests.Session()

# =========================================================
# BUSINESS OBJECT CREATOR  ⭐ REQUIRED
# =========================================================


def create_business(
    name="",
    phone="",
    address="",
    website="",
    email="",
    city="",
    category="",
    source=""
):
    """
    Standard business structure used across the engine.
    """

    return {
        "Name": name or "",
        "Phone": phone or "",
        "Address": address or "",
        "Website": website or "",
        "Email": email or "",
        "UndeliverableEmails": "",   # ⭐ dashboard metric
        "City": city or "",
        "Category": category or "",
        "Source": source or ""
    }

# =========================================================
# SAFE REQUEST
# =========================================================


def safe_request(url, params=None, timeout=15, headers=None, retries=2):
    for _ in range(retries + 1):
        try:
            r = session.get(
                url,
                params=params,
                timeout=timeout,
                headers=headers or rotating_headers(),
                verify=False
            )
            if r.status_code == 200 and r.text:
                return r
        except requests.RequestException:
            time.sleep(random.uniform(0.4, 1.2))
    return None


# =========================================================
# FILTER DIRECTORY / JUNK DOMAINS
# =========================================================
BAD_DOMAINS = [
    "semrush", "f6s", "clutch", "designrush", "goodfirms",
    "justdial", "sulekha", "yellowpages", "manta", "indiamart",
    "reddit", "quora", "wikipedia", "glassdoor", "ambitionbox",
    "facebook.com", "instagram.com", "linkedin.com"
]


def is_valid_business_site(url):
    if not url:
        return False
    return not any(bad in url.lower() for bad in BAD_DOMAINS)


# =========================================================
# EMAIL EXTRACTION
# =========================================================
EMAIL_REGEX = re.compile(
    r'[A-Za-z0-9._%+-]+\s*@\s*[A-Za-z0-9.-]+\.[A-Za-z]{2,}')

BLOCKED_WORDS = [
    "example", "test", "noreply", "no-reply",
    "donotreply", ".png", ".jpg", ".jpeg", ".svg"
]


def clean_email(email):
    return email.replace(" ", "").strip().lower()


def is_deliverable(email):
    if not email:
        return False
    email = clean_email(email)
    if any(b in email for b in BLOCKED_WORDS):
        return False
    if "@" not in email:
        return False
    return True


def extract_emails(text):
    found = set()
    if not text:
        return found

    found.update(e.replace(" ", "") for e in EMAIL_REGEX.findall(text))

    for m in re.findall(r"mailto:([^\?\"'>]+)", text, re.I):
        found.add(m.strip())

    cleaned = text.lower().replace("[at]", "@").replace("(at)", "@")
    cleaned = cleaned.replace("[dot]", ".").replace("(dot)", ".")
    found.update(e.replace(" ", "") for e in EMAIL_REGEX.findall(cleaned))

    return found


# =========================================================
# PHONE EXTRACTION
# =========================================================
PHONE_REGEX = re.compile(r'\+?\d[\d\s\-\(\)]{7,}\d')


def extract_phones(text):
    phones = set()
    if not text:
        return phones

    for match in PHONE_REGEX.findall(text):
        digits = re.sub(r"\D", "", match)
        if 9 <= len(digits) <= 15:
            phones.add(digits)

    return phones


# =========================================================
# CONTACT PAGE DISCOVERY
# =========================================================
CONTACT_KEYWORDS = [
    "contact", "contact-us", "about", "about-us",
    "reach", "support", "get-in-touch"
]


def find_contact_pages(base_url, html):
    pages = set()
    for link in re.findall(r'href=["\'](.*?)["\']', html):
        full = urljoin(base_url, link)
        for keyword in CONTACT_KEYWORDS:
            if keyword in full.lower():
                pages.add(full)
    return list(pages)

# =========================================================
# WEBSITE SCRAPER
# =========================================================


def scrape_website_data(url):
    """
    Returns valid & rejected emails for dashboard metrics
    """

    if not is_valid_business_site(url):
        return None

    if not url.startswith("http"):
        url = "https://" + url

    response = safe_request(url)
    if not response:
        return None

    html = response.text

    emails_found = set()
    phones = set()

    emails_found.update(extract_emails(html))
    phones.update(extract_phones(html))

    contact_pages = find_contact_pages(url, html)

    def scan(link):
        resp = safe_request(link)
        if resp:
            page_html = resp.text
            emails_found.update(extract_emails(page_html))

    with ThreadPoolExecutor(max_workers=5) as ex:
        ex.map(scan, contact_pages[:6])

    valid = []
    rejected = []

    for e in emails_found:
        e = clean_email(e)
        if is_deliverable(e):
            valid.append(e)
        else:
            rejected.append(e)

    return {
        "Email": valid[:5],
        "UndeliverableEmails": ", ".join(rejected[:10]),
        "Phone": list(phones)[:3]
    }
