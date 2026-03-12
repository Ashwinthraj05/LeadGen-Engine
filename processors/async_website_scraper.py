"""
processors/async_website_scraper.py
FIXED:
  1. BIG BUG: old code returned immediately on first email found per page
     — now collects from ALL contact pages before returning
  2. Cloudflare email decoder kept and improved
  3. Concurrency raised from 60 to 80
  4. Returns data even when only phone/LinkedIn found (not just email)
  5. Timeout increased to 18s for slow sites
  6. Collects ALL emails then ranks them (not first-found)
"""

import asyncio
import random
import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from utils.contact_finder import find_contact_page
from utils.headers import get_headers
from processors.contact_extractor import extract_phones, extract_emails
from processors.validator import filter_emails, clean_email

CONTACT_PATHS = [
    "/contact", "/contact-us", "/contact_us",
    "/about", "/about-us", "/about_us",
    "/support", "/help", "/team",
    "/company", "/reach-us", "/get-in-touch",
    "/enquiry", "/inquiry", "/connect",
    "/info", "/write-to-us", "/privacy-policy",
]

BLOCKED_WORDS = ["access denied", "forbidden",
                 "blocked", "captcha", "not found"]


# ── Cloudflare email decoder ──────────────────────────────────────────────────

def decode_cfemail(encoded: str) -> str:
    try:
        r = int(encoded[:2], 16)
        return "".join(
            chr(int(encoded[i:i+2], 16) ^ r)
            for i in range(2, len(encoded), 2)
        )
    except Exception:
        return ""


# ── Email confidence ranking ──────────────────────────────────────────────────

def email_confidence(email: str, domain: str) -> int:
    email = email.lower()
    domain = domain.replace("www.", "")
    if domain and domain in email:
        return 100
    if any(email.startswith(p) for p in ["info@", "contact@", "sales@", "hello@"]):
        return 90
    if any(email.startswith(p) for p in ["support@", "admin@", "office@", "enquiry@"]):
        return 75
    return 50


# ── Phone cleaner ─────────────────────────────────────────────────────────────

def clean_phone(phone: str):
    digits = re.sub(r"\D", "", phone)
    return digits if len(digits) >= 8 else None


# ── Async fetch ───────────────────────────────────────────────────────────────

async def fetch(client: httpx.AsyncClient, url: str) -> str:
    try:
        r = await client.get(url, timeout=18, follow_redirects=True)
        if r.status_code != 200 or not r.text:
            return ""
        text = r.text.lower()
        if any(w in text for w in BLOCKED_WORDS):
            return ""
        await asyncio.sleep(random.uniform(0.3, 0.9))
        return r.text
    except Exception:
        return ""


# ── Parse one page ────────────────────────────────────────────────────────────

def parse_page(html: str, domain: str) -> tuple:
    """Returns (emails_set, phones_set, linkedin_set)"""
    emails = set()
    phones = set()
    linkedin = set()

    if not html:
        return emails, phones, linkedin

    soup = BeautifulSoup(html, "html.parser")

    # standard extraction
    for e in extract_emails(html):
        emails.add(e.lower())

    for p in extract_phones(html):
        cleaned = clean_phone(str(p))
        if cleaned:
            phones.add(cleaned)

    # Cloudflare protected emails
    for tag in soup.select("[data-cfemail]"):
        decoded = decode_cfemail(tag.get("data-cfemail", ""))
        if decoded and "@" in decoded:
            emails.add(decoded.lower())

    # footer (high success area)
    footer = soup.find("footer")
    if footer:
        for e in extract_emails(str(footer)):
            emails.add(e.lower())

    # links: LinkedIn + WhatsApp
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        if "linkedin.com/company" in href:
            linkedin.add(href.split("?")[0])
        if "wa.me" in href or "api.whatsapp.com" in href:
            digits = re.sub(r"\D", "", href)
            if digits:
                phones.add(digits)

    return emails, phones, linkedin


# ── Scrape one site ───────────────────────────────────────────────────────────

async def scrape_site(url: str) -> dict:
    if not url:
        return {}

    if not url.startswith("http"):
        url = "https://" + url

    parsed = urlparse(url)
    domain = parsed.netloc
    root = f"{parsed.scheme}://{parsed.netloc}"

    all_emails:   set = set()
    all_phones:   set = set()
    all_linkedin: set = set()
    visited:      set = set()

    async with httpx.AsyncClient(
        headers=get_headers(),
        timeout=httpx.Timeout(18),
        limits=httpx.Limits(max_connections=50, max_keepalive_connections=25),
        verify=False,
    ) as client:

        # ── Main page ─────────────────────────────────────────────────────
        html = await fetch(client, url)
        if not html:
            return {}

        e, p, li = parse_page(html, domain)
        all_emails |= e
        all_phones |= p
        all_linkedin |= li
        visited.add(url)

        # ── Discover contact links from main page ─────────────────────────
        contact_links: set = set()
        try:
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"].lower()
                if href.startswith("#"):
                    continue
                if any(k in href for k in (
                    "contact", "about", "support", "team",
                    "reach", "enquiry", "inquiry", "connect"
                )):
                    full = urljoin(url, a["href"])
                    if root in full:
                        contact_links.add(full)
        except Exception:
            pass

        # ── Visit contact pages + standard paths ──────────────────────────
        # FIX: collect from ALL pages, not just return on first email found
        all_urls_to_visit = list(contact_links)[:6]
        for path in CONTACT_PATHS:
            all_urls_to_visit.append(urljoin(root, path))

        for link in all_urls_to_visit[:15]:
            if link in visited:
                continue
            visited.add(link)

            html2 = await fetch(client, link)
            if html2:
                e, p, li = parse_page(html2, domain)
                all_emails |= e
                all_phones |= p
                all_linkedin |= li

        # ── Google-discovered contact page ────────────────────────────────
        try:
            contact_page = find_contact_page(domain)
            if contact_page and contact_page not in visited:
                html3 = await fetch(client, contact_page)
                if html3:
                    e, p, li = parse_page(html3, domain)
                    all_emails |= e
                    all_phones |= p
                    all_linkedin |= li
        except Exception:
            pass

    # ── Nothing found at all ──────────────────────────────────────────────
    if not all_emails and not all_phones and not all_linkedin:
        return {}

    # ── Rank and filter emails ────────────────────────────────────────────
    validated = filter_emails(list(all_emails), website=url, limit=5)
    if not validated and all_emails:
        # keep any email rather than returning empty
        validated = [clean_email(e) for e in list(all_emails)[:3] if "@" in e]

    ranked_emails = sorted(
        validated,
        key=lambda e: email_confidence(e, domain),
        reverse=True
    )

    return {
        "Email":    ranked_emails,
        "Phone":    list(all_phones)[:4],
        "LinkedIn": list(all_linkedin)[:2],
    }


# ── Bulk async runner ─────────────────────────────────────────────────────────

async def _scrape_async(urls: list, concurrency: int = 80) -> dict:
    sem = asyncio.Semaphore(concurrency)

    async def bounded(url: str):
        async with sem:
            return url, await scrape_site(url)

    tasks = [bounded(u) for u in urls if u]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    output = {}
    for result in results:
        if isinstance(result, tuple):
            url, data = result
            if data:
                output[url] = data

    return output


def scrape_websites_bulk(urls: list) -> dict:
    """Entry point: runs async scraper in a new event loop."""
    if not urls:
        return {}
    return asyncio.run(_scrape_async(urls))
