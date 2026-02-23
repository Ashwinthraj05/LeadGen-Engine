import asyncio
import random
import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from utils.contact_finder import find_contact_page
from utils.headers import get_headers
from processors.contact_extractor import extract_phones, extract_emails


CONTACT_PATHS = [
    "/contact", "/contact-us", "/about",
    "/support", "/team", "/company",
    "/privacy-policy", "/privacy",
    "/terms", "/legal", "/disclaimer"
]

BLOCKED_WORDS = ["access denied", "forbidden", "blocked", "captcha"]


# =========================
# CLOUDFLARE EMAIL DECODER
# =========================

def decode_cfemail(encoded):
    try:
        r = int(encoded[:2], 16)
        return ''.join(
            chr(int(encoded[i:i+2], 16) ^ r)
            for i in range(2, len(encoded), 2)
        )
    except Exception:
        return ""


# =========================
# EMAIL CONFIDENCE SCORE
# =========================

def email_confidence(email, domain):
    email = email.lower()
    domain = domain.replace("www.", "")

    if domain in email:
        return 100
    if any(x in email for x in ["info@", "contact@", "sales@", "hello@"]):
        return 85
    if any(x in email for x in ["support@", "admin@", "office@"]):
        return 70
    return 50


# =========================
# CLEAN PHONE NUMBERS
# =========================

def clean_phone(phone):
    phone = re.sub(r"\D", "", phone)
    if len(phone) >= 8:
        return phone
    return None


# =========================
# STEALTH REQUEST
# =========================

async def fetch(client, url):
    try:
        r = await client.get(url, timeout=12, follow_redirects=True)

        if r.status_code != 200 or not r.text:
            return None

        text = r.text.lower()
        if any(word in text for word in BLOCKED_WORDS):
            return None

        await asyncio.sleep(random.uniform(0.4, 1.1))
        return r.text

    except Exception:
        return None


# =========================
# PARSE PAGE
# =========================

def parse(html, domain):
    linkedin = set()
    phones = set()
    emails = set()

    soup = BeautifulSoup(html, "html.parser")

    # extract emails & phones
    emails |= set(extract_emails(html))
    phones |= set(extract_phones(html))

    # decode Cloudflare protected emails
    for tag in soup.select("[data-cfemail]"):
        decoded = decode_cfemail(tag.get("data-cfemail", ""))
        if decoded:
            emails.add(decoded)

    # footer extraction (high success area)
    footer = soup.find("footer")
    if footer:
        emails |= set(extract_emails(str(footer)))

    # extract links
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()

        if "linkedin.com/company" in href:
            linkedin.add(href.split("?")[0])

        if "wa.me" in href or "api.whatsapp.com" in href:
            number = re.sub(r"\D", "", href)
            if number:
                phones.add(number)

    # clean phones
    phones = {clean_phone(p) for p in phones if clean_phone(p)}

    # rank emails
    ranked = sorted(
        emails,
        key=lambda e: email_confidence(e, domain),
        reverse=True
    )

    return ranked[:3], list(phones), list(linkedin)


# =========================
# SCRAPE SINGLE SITE
# =========================

async def scrape_site(url):
    if not url:
        return None

    if not url.startswith("http"):
        url = "https://" + url

    parsed = urlparse(url)
    domain = parsed.netloc
    visited = set()

    async with httpx.AsyncClient(
        headers=get_headers(),
        timeout=httpx.Timeout(15),
        limits=httpx.Limits(max_connections=40, max_keepalive_connections=20),
    ) as client:

        html = await fetch(client, url)
        if not html:
            return None

        emails, phones, linkedin = parse(html, domain)
        if emails:
            return {"Email": emails, "Phone": phones, "LinkedIn": linkedin}

        soup = BeautifulSoup(html, "html.parser")

        # discover contact links
        for a in soup.find_all("a", href=True):
            href = a["href"].lower()

            if any(x in href for x in ["contact", "about", "support", "team"]):
                link = urljoin(url, href)

                if link in visited:
                    continue
                visited.add(link)

                html2 = await fetch(client, link)
                if html2:
                    emails, phones, linkedin = parse(html2, domain)
                    if emails:
                        return {"Email": emails, "Phone": phones, "LinkedIn": linkedin}

        # try common paths
        for path in CONTACT_PATHS:
            link = urljoin(url, path)

            if link in visited:
                continue

            html2 = await fetch(client, link)
            if html2:
                emails, phones, linkedin = parse(html2, domain)
                if emails:
                    return {"Email": emails, "Phone": phones, "LinkedIn": linkedin}

        # Google-discovered contact page
        contact_page = find_contact_page(domain)
        if contact_page:
            html3 = await fetch(client, contact_page)
            if html3:
                emails, phones, linkedin = parse(html3, domain)
                if emails:
                    return {"Email": emails, "Phone": phones, "LinkedIn": linkedin}

    return None


# =========================
# BULK ASYNC SCRAPER
# =========================

async def scrape_async(urls, concurrency=60):
    sem = asyncio.Semaphore(concurrency)

    async def bound(url):
        async with sem:
            return url, await scrape_site(url)

    tasks = [bound(u) for u in urls if u]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    output = {}
    for result in results:
        if isinstance(result, tuple):
            url, data = result
            if data:
                output[url] = data

    return output


def scrape_websites_bulk(urls):
    return asyncio.run(scrape_async(urls))
