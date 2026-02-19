import re
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from utils.helpers import safe_request


EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

COMMON_CONTACT_PATHS = [
    "/contact",
    "/contact-us",
    "/contactus",
    "/about",
    "/about-us",
    "/aboutus",
    "/support",
    "/reach-us",
    "/team",
    "/staff",
    "/company",
    "/who-we-are",
    "/get-in-touch"
]

# Skip slow / blocked enterprise domains
SLOW_KEYWORDS = [
    "hospital",
    "health",
    "network",
    ".edu",
    "government"
]


# ✅ browser-like headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9",
}


def normalize_url(url):
    if not url.startswith("http"):
        url = "https://" + url
    return url.rstrip("/")


def is_slow_domain(url):
    return any(word in url.lower() for word in SLOW_KEYWORDS)


def fetch_url(url, retries=2):
    """Safe fetch with retry & anti-block"""
    for _ in range(retries):
        try:
            res = safe_request(url, headers=HEADERS)

            if res is None:
                continue

            if res.status_code == 200:
                return res

            # blocked → retry
            if res.status_code in [403, 429]:
                time.sleep(2)

        except:
            time.sleep(1)

    return None


def extract_from_html(html):
    emails = set()

    # ✅ regex scan
    found = re.findall(EMAIL_REGEX, html, re.I)
    for email in found:
        emails.add(email.lower())

    soup = BeautifulSoup(html, "html.parser")

    # ✅ mailto links
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "mailto:" in href:
            email = href.split("mailto:")[1].split("?")[0]
            emails.add(email.lower())

    # ✅ footer scan (high success rate)
    footer = soup.find("footer")
    if footer:
        footer_text = footer.get_text(" ")
        emails.update(re.findall(EMAIL_REGEX, footer_text, re.I))

    return emails


def find_contact_links(soup, base_url):
    """Discover contact-related links dynamically"""
    links = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].lower()

        if any(word in href for word in ["contact", "support", "about", "reach"]):
            full_url = urljoin(base_url, href)
            links.add(full_url)

    return links


def extract_emails_from_website(url):
    """
    Advanced Email Extraction Engine

    ✔ homepage scan
    ✔ footer scan
    ✔ dynamic contact links
    ✔ contact pages
    ✔ mailto detection
    ✔ anti-block retries
    ✔ safe fail (never breaks pipeline)
    """

    if not url:
        return []

    try:
        base_url = normalize_url(url)

        if is_slow_domain(base_url):
            return []

        emails = set()

        # =========================
        # 1️⃣ HOMEPAGE
        # =========================
        response = fetch_url(base_url)

        if not response:
            return []

        emails.update(extract_from_html(response.text))

        soup = BeautifulSoup(response.text, "html.parser")

        # discover contact links
        contact_links = find_contact_links(soup, base_url)

        if emails:
            return list(emails)

        time.sleep(1)

        # =========================
        # 2️⃣ DYNAMIC CONTACT LINKS
        # =========================
        for link in contact_links:
            res = fetch_url(link)
            if res:
                emails.update(extract_from_html(res.text))
                if emails:
                    return list(emails)
            time.sleep(1)

        # =========================
        # 3️⃣ COMMON CONTACT PATHS
        # =========================
        parsed = urlparse(base_url)
        root = f"{parsed.scheme}://{parsed.netloc}"

        for path in COMMON_CONTACT_PATHS:
            contact_url = urljoin(root, path)
            res = fetch_url(contact_url)

            if res:
                emails.update(extract_from_html(res.text))
                if emails:
                    return list(emails)

            time.sleep(1)

    except Exception:
        return []

    return list(emails)
