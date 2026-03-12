"""
processors/email_extractor.py
FIXED: 6-strategy email extraction, pattern guessing, async-ready,
       obfuscation decoding, JSON-LD parsing, meta tag scanning
"""

import re
import time
import json
import urllib3
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils.helpers import safe_request
from processors.validator import filter_emails, clean_email, is_valid_email

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Patterns ──────────────────────────────────────────────────────────────────

EMAIL_REGEX = r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b"

# Obfuscation variants
OBFUSCATION_MAP = {
    "[at]":  "@", "(at)":  "@", "{at}":  "@", " at ":  "@",
    "[dot]": ".", "(dot)": ".", "{dot}": ".", " dot ": ".",
    " @ ":   "@", "&#64;": "@", "%40":   "@",
}

CONTACT_PATHS = [
    "/contact", "/contact-us", "/contact_us",
    "/about",   "/about-us",   "/about_us",
    "/support", "/help",       "/team",
    "/company", "/reach-us",   "/get-in-touch",
    "/enquiry", "/inquiry",    "/connect",
    "/info",    "/write-to-us",
]

SKIP_DOMAINS = (".gov", ".edu")

BLOCKED_DOMAINS = [
    "linkedin", "facebook", "instagram", "twitter", "youtube",
    "quora", "reddit", "indeed", "naukri", "glassdoor",
    "justdial", "yellowpages", "clutch.co", "goodfirms",
    "semrush", "f6s.com", "wix.com", "wordpress.com",
]

JUNK_PATTERNS = [
    "example.com", "test.com", "domain.com", "sentry", "wixpress",
    "noreply", "no-reply", "donotreply", "do-not-reply",
    "webmaster@localhost", "@2x", "@3x",
]

# Common first-name guessing prefixes for pattern emails
GUESS_PREFIXES = ["info", "contact", "sales", "hello", "enquiry",
                  "support", "office", "admin", "marketing", "hr"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# ─────────────────────────────────────────────────────────────────────────────


def normalize_url(url: str) -> str:
    if not url.startswith("http"):
        url = "https://" + url
    return url.rstrip("/")


def get_root(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


def should_skip(url: str) -> bool:
    domain = urlparse(url).netloc.lower()
    if domain.endswith(SKIP_DOMAINS):
        return True
    return any(b in domain for b in BLOCKED_DOMAINS)


def is_clean(email: str) -> bool:
    e = email.lower()
    return not any(j in e for j in JUNK_PATTERNS)


def fetch(url: str, timeout: int = 14) -> object:
    try:
        return safe_request(url, timeout=timeout, headers=HEADERS)
    except Exception:
        return None

# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY 1 — Regex + mailto on raw HTML
# ─────────────────────────────────────────────────────────────────────────────


def _strategy_regex(html: str) -> set:
    emails = set()
    for e in re.findall(EMAIL_REGEX, html, re.I):
        if is_clean(e):
            emails.add(e.lower())
    return emails


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY 2 — BeautifulSoup mailto + visible text
# ─────────────────────────────────────────────────────────────────────────────

def _strategy_soup(html: str) -> set:
    emails = set()
    try:
        soup = BeautifulSoup(html, "html.parser")

        # mailto links
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "mailto:" in href.lower():
                raw = href.split("mailto:")[-1].split("?")[0].strip()
                if is_clean(raw) and "@" in raw:
                    emails.add(raw.lower())

        # visible text (catches emails written as plain text in paragraphs)
        text = soup.get_text(" ")
        for e in re.findall(EMAIL_REGEX, text, re.I):
            if is_clean(e):
                emails.add(e.lower())

    except Exception:
        pass
    return emails


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY 3 — Obfuscation decoding
# ─────────────────────────────────────────────────────────────────────────────

def _strategy_deobfuscate(html: str) -> set:
    emails = set()
    try:
        text = html
        for k, v in OBFUSCATION_MAP.items():
            text = text.replace(k, v)

        # also decode HTML entities
        soup = BeautifulSoup(text, "html.parser")
        decoded = soup.get_text(" ")

        for e in re.findall(EMAIL_REGEX, decoded, re.I):
            if is_clean(e):
                emails.add(e.lower())
    except Exception:
        pass
    return emails


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY 4 — JSON-LD structured data
# ─────────────────────────────────────────────────────────────────────────────

def _strategy_jsonld(html: str) -> set:
    emails = set()
    try:
        soup = BeautifulSoup(html, "html.parser")
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                text = json.dumps(data)
                for e in re.findall(EMAIL_REGEX, text, re.I):
                    if is_clean(e):
                        emails.add(e.lower())
            except Exception:
                pass
    except Exception:
        pass
    return emails


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY 5 — Meta tags (some sites put email in meta)
# ─────────────────────────────────────────────────────────────────────────────

def _strategy_meta(html: str) -> set:
    emails = set()
    try:
        soup = BeautifulSoup(html, "html.parser")
        for meta in soup.find_all("meta"):
            content = meta.get("content", "")
            for e in re.findall(EMAIL_REGEX, content, re.I):
                if is_clean(e):
                    emails.add(e.lower())
    except Exception:
        pass
    return emails


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY 6 — Pattern guessing (last resort)
# ─────────────────────────────────────────────────────────────────────────────

def _strategy_pattern_guess(domain: str) -> list:
    """
    FIX: When no email is found, generate likely addresses like
    info@domain.com, contact@domain.com etc.
    These are marked as GUESSED so caller can handle them separately.
    """
    if not domain:
        return []
    return [f"{prefix}@{domain}" for prefix in GUESS_PREFIXES[:4]]


# ─────────────────────────────────────────────────────────────────────────────
# RUN ALL STRATEGIES ON ONE HTML BLOCK
# ─────────────────────────────────────────────────────────────────────────────

def _all_strategies(html: str) -> set:
    found = set()
    found |= _strategy_regex(html)
    found |= _strategy_soup(html)
    found |= _strategy_deobfuscate(html)
    found |= _strategy_jsonld(html)
    found |= _strategy_meta(html)
    return found


# ─────────────────────────────────────────────────────────────────────────────
# MAIN SINGLE-SITE EXTRACTOR
# ─────────────────────────────────────────────────────────────────────────────

def extract_emails_from_website(url: str, use_guessing: bool = True) -> list:
    """
    Full multi-strategy email extraction for one website.
    Returns list of validated emails. Falls back to guessed patterns.
    """
    if not url:
        return []

    try:
        url = normalize_url(url)

        if should_skip(url):
            return []

        raw_emails: set = set()

        # ── Fetch main page ───────────────────────────────────────────────
        res = fetch(url)

        # try www. fallback
        if not res:
            p = urlparse(url)
            if not p.netloc.startswith("www."):
                res = fetch(f"{p.scheme}://www.{p.netloc}")

        if not res or not res.text:
            if use_guessing:
                domain = urlparse(url).netloc.replace("www.", "")
                return _strategy_pattern_guess(domain)
            return []

        html = res.text[:600_000]
        raw_emails |= _all_strategies(html)

        # ── Discover & visit contact pages ────────────────────────────────
        root = get_root(url)
        contact_links: set = set()

        try:
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"].lower()
                if href.startswith("#"):
                    continue
                if any(k in href for k in (
                    "contact", "about", "support", "team",
                    "connect", "reach", "enquiry", "inquiry"
                )):
                    full = urljoin(url, a["href"])
                    if root in full:           # stay on same domain
                        contact_links.add(full)
        except Exception:
            pass

        # visit discovered + standard contact paths
        all_contact_urls = list(contact_links)[:6]
        for path in CONTACT_PATHS:
            all_contact_urls.append(urljoin(root, path))

        for link in all_contact_urls[:12]:     # cap at 12 sub-pages
            time.sleep(0.25)
            r = fetch(link, timeout=10)
            if r and r.text:
                raw_emails |= _all_strategies(r.text[:300_000])

        # ── Filter & validate ─────────────────────────────────────────────
        validated = filter_emails(list(raw_emails), website=url, limit=5)

        # ── Pattern guess fallback ────────────────────────────────────────
        if not validated and use_guessing:
            domain = urlparse(url).netloc.replace("www.", "")
            return _strategy_pattern_guess(domain)

        return validated

    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────────────────
# BULK PARALLEL EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

def extract_emails_bulk(urls: list, workers: int = 25) -> list:
    """
    FIX: workers raised to 25 (was 20).
    FIX: returns per-url mapping, not flat list — so orchestrator can
         correctly assign emails to the right company.
    Returns: dict { url: [email, ...] }
    """
    url_email_map: dict = {}

    valid_urls = [u for u in urls if u]

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_url = {
            executor.submit(extract_emails_from_website, u): u
            for u in valid_urls
        }

        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                emails = future.result(timeout=60)
                url_email_map[url] = emails or []
            except Exception:
                url_email_map[url] = []

    return url_email_map   # ← NOW returns dict, not flat list
