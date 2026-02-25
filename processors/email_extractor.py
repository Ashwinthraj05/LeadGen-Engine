import re
import urllib3
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils.helpers import safe_request
from processors.validator import filter_emails

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --------------------------------------------------
# EMAIL PATTERN (improved accuracy)
# --------------------------------------------------

EMAIL_REGEX = r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"

COMMON_CONTACT_PATHS = [
    "/contact", "/contact-us", "/about", "/about-us",
    "/support", "/team", "/company", "/connect"
]

# Skip only true government & education domains
SKIP_DOMAINS = (".gov", ".edu")

# Block directories & social platforms
BLOCKED_DOMAINS = [
    "linkedin", "facebook", "instagram", "twitter",
    "youtube", "quora", "reddit", "indeed", "naukri",
    "glassdoor", "justdial", "yellowpages",
    "clutch.co", "goodfirms", "semrush", "f6s.com"
]

# junk & fake emails
JUNK_EMAIL_PATTERNS = [
    "example.com", "test.com", "domain.com",
    "error-tracking", "noreply", "no-reply",
    "donotreply", "webmaster", "admin@localhost"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# --------------------------------------------------


def normalize(url):
    if not url.startswith("http"):
        url = "https://" + url
    return url.rstrip("/")


def skip_domain(url):
    """Avoid skipping valid company domains accidentally"""
    domain = urlparse(url).netloc.lower()

    if domain.endswith(SKIP_DOMAINS):
        return True

    return any(b in domain for b in BLOCKED_DOMAINS)


def valid(email):
    email = email.lower()
    return not any(j in email for j in JUNK_EMAIL_PATTERNS)

# --------------------------------------------------
# EMAIL EXTRACTION
# --------------------------------------------------


def extract(html):
    """Extract emails from HTML"""

    emails = set()

    # regex scan
    for e in re.findall(EMAIL_REGEX, html, re.I):
        if valid(e):
            emails.add(e.lower())

    soup = BeautifulSoup(html, "html.parser")

    # mailto links
    for a in soup.find_all("a", href=True):
        if "mailto:" in a["href"]:
            e = a["href"].split("mailto:")[1].split("?")[0]
            if valid(e):
                emails.add(e.lower())

    # decode obfuscated emails
    text = soup.get_text(" ")

    replacements = {
        "[at]": "@", "(at)": "@", " at ": "@",
        "[dot]": ".", "(dot)": ".", " dot ": "."
    }

    for k, v in replacements.items():
        text = text.replace(k, v)

    for e in re.findall(EMAIL_REGEX, text, re.I):
        if valid(e):
            emails.add(e.lower())

    return emails

# --------------------------------------------------
# SAFE FETCH
# --------------------------------------------------


def fetch(url, timeout=12):
    """Safe request with retry protection"""
    try:
        res = safe_request(url, timeout=timeout, headers=HEADERS)
        return res
    except:
        return None

# --------------------------------------------------
# WEBSITE SCRAPER
# --------------------------------------------------


def extract_emails_from_website(url):
    """
    ⚡ High accuracy email extraction
    """

    if not url:
        return []

    try:
        url = normalize(url)

        if skip_domain(url):
            return []

        raw_emails = set()

        # ===== 1️⃣ MAIN PAGE =====
        res = fetch(url)

        # try www fallback
        if not res:
            parsed = urlparse(url)
            www_url = f"{parsed.scheme}://www.{parsed.netloc}"
            res = fetch(www_url)

        if not res or not res.text:
            return []

        html = res.text[:500000]  # safety limit for huge pages
        raw_emails.update(extract(html))

        soup = BeautifulSoup(html, "html.parser")

        # ===== 2️⃣ FIND CONTACT LINKS =====
        links = set()

        for a in soup.find_all("a", href=True):
            href = a["href"]

            if href.startswith("#"):
                continue

            if any(k in href.lower() for k in ("contact", "about", "support", "team", "connect")):
                links.add(urljoin(url, href))

        # visit top contact pages
        for link in list(links)[:5]:
            time.sleep(0.3)
            res = fetch(link, timeout=10)
            if res and res.text:
                raw_emails.update(extract(res.text[:200000]))

        # ===== 3️⃣ COMMON CONTACT PATHS =====
        parsed = urlparse(url)
        root = f"{parsed.scheme}://{parsed.netloc}"

        for path in COMMON_CONTACT_PATHS:
            time.sleep(0.3)
            res = fetch(urljoin(root, path), timeout=10)
            if res and res.text:
                raw_emails.update(extract(res.text[:200000]))

        if not raw_emails:
            return []

        # ===== 4️⃣ FILTER & PRIORITIZE =====
        return filter_emails(list(raw_emails), website=url)

    except Exception:
        return []

# --------------------------------------------------
# 🚀 BULK PARALLEL EXTRACTION
# --------------------------------------------------


def extract_emails_bulk(urls, workers=20):
    """
    Parallel email extraction
    """

    results = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(extract_emails_from_website, u): u
            for u in urls if u
        }

        for future in as_completed(futures):
            try:
                emails = future.result()
                if emails:
                    results.extend(emails)
            except:
                pass

    return list(set(results))
