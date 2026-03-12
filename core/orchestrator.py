"""
core/orchestrator.py
FIXED:
  1. BIG FIX: JustDial, IndiaMART, BBB called ONCE per city+category only.
     Calling them with expanded keywords like "seo-agency-in-bangalore" causes
     404s and wastes time. SerpAPI/Google/Playwright handle the keyword variants.
  2. Website finder now logs results properly
  3. SerpAPI None key_manager handled — returns [] gracefully
  4. All type checks in place
"""

import os
import logging
import re
import requests
from urllib.parse import urlparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from processors.lead_score import score_lead
from processors.email_score import score_email, choose_best_email
from processors.deduper import dedupe_businesses
from processors.validator import is_valid_email, clean_email
from processors.email_extractor import extract_emails_bulk
from processors.async_website_scraper import scrape_websites_bulk

from utils.stealth import human_delay
from utils.keyword_expander import expand_keyword
from utils.headers import get_headers
from storage.csv_writer import save_to_csv

from sources.google_maps import scrape_google_maps
from sources.serpapi_engine import scrape_serpapi
from sources.playwright_engine import scrape_playwright
from sources.bbb import scrape_bbb
from sources.indiamart import scrape_indiamart
from sources.justdial import scrape_justdial

from config import COUNTRIES, DEFAULT_CATEGORIES, GOOGLE_PAGES

logger = logging.getLogger(__name__)

MAX_WEBSITES = 500

BLOCKED_DOMAINS = [
    "justdial.com", "yellowpages.com", "google.com",
    "facebook.com", "instagram.com", "linkedin.com",
    "yelp.com", "sulekha.com", "clutch.co",
    "indeed", "glassdoor", "monster", "shine", "wikipedia",
]
SPAM_TRAPS = ["example.com", "domain.com", "email.com"]
SKIP_EMAIL_DOMAINS = [".gov", ".edu"]

SKIP_IN_WEBSITE = [
    "justdial", "facebook", "linkedin", "instagram",
    "twitter", "youtube", "sulekha", "indiamart",
    "duckduckgo", "google", "bing",
]


def bad_domain(url: str) -> bool:
    return any(s in url.lower() for s in SKIP_EMAIL_DOMAINS)


def get_domain(site: str) -> str:
    try:
        return urlparse(site).netloc.replace("www.", "")
    except Exception:
        return ""


# ─────────────────────────────────────────────────────────────────────────────
# WEBSITE FINDER
# ─────────────────────────────────────────────────────────────────────────────

def find_website_via_search(name: str, city: str) -> str:
    """Find a company's website via DuckDuckGo when scraper didn't get one."""
    if not name:
        return ""
    try:
        from urllib.parse import quote_plus
        q = quote_plus(f"{name} {city} official website")
        url = f"https://html.duckduckgo.com/html/?q={q}"
        r = requests.get(url, headers=get_headers(), timeout=10)
        if r.status_code != 200:
            return ""
        links = re.findall(r'href="(https?://[^"]+)"', r.text)
        for link in links:
            if not any(s in link.lower() for s in SKIP_IN_WEBSITE):
                return link.split("?")[0]
    except Exception:
        pass
    return ""


def _find_website_worker(args):
    idx, lead = args
    if not lead.get("Website"):
        site = find_website_via_search(
            lead.get("Name", ""), lead.get("City", ""))
        if site:
            lead["Website"] = site
            return idx, site
    return idx, ""


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE SCRAPERS
# ─────────────────────────────────────────────────────────────────────────────

def _safe_scrape(fn, *args, **kwargs):
    try:
        result = fn(*args, **kwargs)
        return result if isinstance(result, list) else []
    except Exception as e:
        logger.warning(f"Source error [{fn.__name__}]: {e}")
        return []


def scrape_keyword_sources(city: str, keyword: str, pages: int) -> list:
    """
    Sources that work well with keyword variants: SerpAPI + Google Maps + Playwright.
    These handle "seo agency in bangalore", "top seo agency", etc.
    """
    results = []

    # Run SerpAPI and Google Maps in parallel
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {
            ex.submit(_safe_scrape, scrape_serpapi,    city, keyword, pages): "SerpAPI",
            ex.submit(_safe_scrape, scrape_google_maps, city, keyword, pages): "GoogleMaps",
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                data = future.result(timeout=120)
                if data:
                    results.extend(data)
            except Exception as e:
                logger.warning(f"{name} timeout/error: {e}")

    # Playwright fallback if both above returned nothing
    if not results:
        results.extend(_safe_scrape(scrape_playwright, city, keyword, pages))

    return results


def scrape_directory_sources(city: str, category: str) -> list:
    """
    Directory sources (JustDial, IndiaMART, BBB) called ONCE per city+category.
    These don't work with keyword variants — they use URL slugs.
    """
    results = []

    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {
            ex.submit(_safe_scrape, scrape_justdial,  city, category): "JustDial",
            ex.submit(_safe_scrape, scrape_indiamart, city, category): "IndiaMART",
            ex.submit(_safe_scrape, scrape_bbb,       city, category): "BBB",
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                data = future.result(timeout=300)
                if data:
                    results.extend(data)
                    logger.info(f"  ✅ {name}: {len(data)} leads")
            except Exception as e:
                logger.warning(f"  ⚠ {name} timeout/error: {e}")

    return results


# ─────────────────────────────────────────────────────────────────────────────
# ENRICH
# ─────────────────────────────────────────────────────────────────────────────

def _enrich_lead(lead: dict) -> dict:
    try:
        from processors.company_enricher import extract_company_details
        from processors.company_size import estimate_company_size
        details = extract_company_details(lead.get("Website", ""))
        if details.get("company_name"):
            lead["Company"] = details["company_name"]
        lead["About"] = details.get("about", "")
        lead["CompanySize"] = estimate_company_size(details.get("about", ""))
        lead["LinkedIn"] = lead.get("LinkedIn") or details.get("linkedin", "")
    except Exception as e:
        logger.debug(f"Enrich error: {e}")

    try:
        lead["EmailScore"] = score_email(
            lead.get("Email", ""), lead.get("Website", ""))
        lead["LeadScore"] = score_lead(lead)
    except Exception:
        pass

    return lead


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def run_global_scraper(cities=None, categories=None,
                       progress_callback=None, stop_flag=None):

    def log(msg: str):
        logger.info(msg)
        print(msg)
        if progress_callback:
            try:
                progress_callback(msg)
            except Exception:
                pass

    log("🌍 Engine Started")

    if not cities:
        cities = [c for lst in COUNTRIES.values() for c in lst]
    if not categories:
        categories = DEFAULT_CATEGORIES

    all_leads = []

    # ─── PHASE 1: SCRAPE LISTINGS ─────────────────────────────────────────
    for city in cities:
        if stop_flag and stop_flag():
            log("🛑 Stop requested")
            return [], []

        log(f"\n📍 City: {city}")

        for category in categories:
            if stop_flag and stop_flag():
                log("🛑 Stop requested")
                return [], []

            log(f"  🏷 Category: {category}")

            # ── 1a. Directories: called ONCE with raw category ─────────────
            log(f"    📂 Scraping directories...")
            dir_leads = scrape_directory_sources(city, category)
            all_leads.extend(dir_leads)
            log(f"    📂 Directories: {len(dir_leads)} leads")

            # ── 1b. Search engines: called with keyword variants ───────────
            keywords = [category] + expand_keyword(category)
            keywords += [f"top {category}", f"best {category}"]

            # deduplicate keywords
            seen_kw, unique_kw = set(), []
            for kw in keywords:
                if kw.lower() not in seen_kw:
                    seen_kw.add(kw.lower())
                    unique_kw.append(kw)

            for keyword in unique_kw:
                if stop_flag and stop_flag():
                    log("🛑 Stop requested")
                    return [], []

                log(f"    🔎 {keyword}")
                batch = scrape_keyword_sources(city, keyword, GOOGLE_PAGES)
                all_leads.extend(batch)
                log(f"    📦 Batch: {len(batch)} | Total raw: {len(all_leads)}")
                human_delay()

        log(f"📊 Raw after {city}: {len(all_leads)}")

    raw_leads = list(all_leads)

    # ─── PHASE 2: CLEAN & DEDUPE ──────────────────────────────────────────
    log("🧹 Cleaning & deduplicating...")

    cleaned = []
    for lead in all_leads:
        website = str(lead.get("Website") or lead.get("url") or "").strip()
        name = str(lead.get("Name", "") or "").strip()
        if not name:
            continue
        if website and any(b in website.lower() for b in BLOCKED_DOMAINS):
            website = ""
        if website and any(s in website.lower() for s in SPAM_TRAPS):
            website = ""
        cleaned.append({
            "Name":                name,
            "Website":             website,
            "Phone":               str(lead.get("Phone",   "") or "").strip(),
            "Email":               str(lead.get("Email",   "") or "").strip(),
            "UndeliverableEmails": [],
            "LinkedIn":            "",
            "City":                str(lead.get("City",     city) or city).strip(),
            "Category":            str(lead.get("Category", category) or category).strip(),
            "Source":              str(lead.get("Source",   "") or "").strip(),
            "Address":             str(lead.get("Address",  "") or "").strip(),
        })

    unique = dedupe_businesses(cleaned)[:MAX_WEBSITES]
    log(f"✅ Unique leads after dedup: {len(unique)}")

    # ─── PHASE 3: WEBSITE FINDER ──────────────────────────────────────────
    no_website_leads = [(i, l)
                        for i, l in enumerate(unique) if not l.get("Website")]
    log(f"🔍 Finding websites for {len(no_website_leads)} leads without one...")

    if no_website_leads:
        found_count = 0
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = {executor.submit(_find_website_worker, args): args[0]
                       for args in no_website_leads}
            for future in as_completed(futures):
                try:
                    idx, site = future.result(timeout=20)
                    if site:
                        unique[idx]["Website"] = site
                        found_count += 1
                except Exception:
                    pass
        log(f"  ✅ Found {found_count} additional websites via search")

    with_website_total = sum(1 for l in unique if l.get("Website"))
    log(f"  📊 Total leads with website: {with_website_total}")

    # ─── PHASE 4: EMAIL EXTRACTION ────────────────────────────────────────
    log("📧 Extracting emails (parallel, 6 strategies)...")

    sites_needing_email = list({
        lead["Website"]
        for lead in unique
        if lead.get("Website")
        and not lead.get("Email")
        and not bad_domain(lead["Website"])
    })

    log(f"  🔍 Scraping emails for {len(sites_needing_email)} websites...")

    email_map: dict = extract_emails_bulk(sites_needing_email, workers=30)

    for lead in unique:
        site = lead.get("Website", "")
        if not site or lead.get("Email"):
            continue
        emails = email_map.get(site, [])
        if isinstance(emails, str):
            emails = [emails]
        valid = [clean_email(e)
                 for e in emails if is_valid_email(clean_email(e))]
        invalid = [clean_email(e)
                   for e in emails if not is_valid_email(clean_email(e))]
        if valid:
            lead["Email"] = choose_best_email(valid, site)
        if invalid:
            lead["UndeliverableEmails"] = list(set(invalid))

    # ─── PHASE 5: DEEP CRAWL ──────────────────────────────────────────────
    log("🌐 Deep crawling websites for phone/LinkedIn...")

    all_websites = list({l["Website"] for l in unique if l.get("Website")})
    website_data = scrape_websites_bulk(all_websites) or {}

    for lead in unique:
        site = lead.get("Website", "")
        data = website_data.get(site) if isinstance(
            website_data, dict) else None
        if not data or not isinstance(data, dict):
            continue

        if not lead.get("Email"):
            emails = data.get("Email", [])
            if isinstance(emails, str):
                emails = [emails]
            valid = [e for e in emails if is_valid_email(clean_email(str(e)))]
            if valid:
                lead["Email"] = choose_best_email(valid, site)

        if not lead.get("Phone"):
            phones = data.get("Phone", [])
            if isinstance(phones, str):
                phones = [phones]
            if phones:
                lead["Phone"] = ", ".join(str(p) for p in phones[:2])

        if not lead.get("LinkedIn"):
            li = data.get("LinkedIn", "")
            lead["LinkedIn"] = li[0] if isinstance(
                li, list) and li else str(li or "")

    # ─── PHASE 6: ENRICH + SCORE ──────────────────────────────────────────
    log("🏢 Enriching & scoring leads (parallel)...")

    enriched = list(unique)
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(_enrich_lead, lead): i
                   for i, lead in enumerate(unique)}
        for future in as_completed(futures):
            idx = futures[future]
            try:
                enriched[idx] = future.result()
            except Exception:
                pass

    unique = [l for l in enriched if l is not None]

    # ─── STATS ────────────────────────────────────────────────────────────
    total = len(unique)
    with_email = sum(1 for l in unique if l.get("Email"))
    with_phone = sum(1 for l in unique if l.get("Phone"))
    with_website = sum(1 for l in unique if l.get("Website"))

    log(f"\n📊 FINAL STATS")
    log(f"  Total leads    : {total}")
    log(f"  With website   : {with_website}")
    log(f"  With email     : {with_email} ({100*with_email//max(total,1)}%)")
    log(f"  With phone     : {with_phone}")

    # ─── SAVE ─────────────────────────────────────────────────────────────
    os.makedirs("data", exist_ok=True)
    filename = f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    save_to_csv(unique, os.path.join("data", filename))
    log(f"💾 Saved → data/{filename}")
    log("🎉 Completed!")

    return unique, raw_leads
