from urllib.parse import urlparse
from datetime import datetime
import os

from processors.lead_score import score_lead
from processors.email_score import score_email, choose_best_email
from processors.company_size import estimate_company_size
from processors.company_enricher import extract_company_details
from processors.deduper import dedupe_businesses
from processors.validator import is_valid_email, clean_email
from processors.email_extractor import extract_emails_bulk
from processors.async_website_scraper import scrape_websites_bulk

from utils.stealth import human_delay
from utils.keyword_expander import expand_keyword
from storage.csv_writer import save_to_csv

from sources.google_maps import scrape_google_maps
from sources.serpapi_engine import scrape_serpapi
from sources.playwright_engine import scrape_playwright

# ⭐ NEW SOURCES (SAFE)
from sources.bbb import scrape_bbb
from sources.indiamart import scrape_indiamart
from sources.justdial import scrape_justdial

from config import COUNTRIES, DEFAULT_CATEGORIES, GOOGLE_PAGES, MAX_WEBSITES


# --------------------------------------------------
# FILTER RULES
# --------------------------------------------------

BLOCKED_DOMAINS = [
    "justdial.com", "yellowpages.com", "google.com",
    "facebook.com", "instagram.com", "linkedin.com",
    "yelp.com", "sulekha.com", "clutch.co",
    "indeed", "glassdoor", "monster", "shine", "wikipedia"
]

SKIP_EMAIL_DOMAINS = [".gov", ".edu"]
SPAM_TRAPS = ["example.com", "domain.com", "email.com"]
FALLBACK_PREFIXES = ["sales", "info", "contact", "hello"]


def bad_domain(url):
    return any(d in url.lower() for d in SKIP_EMAIL_DOMAINS)


def get_domain(site):
    try:
        return urlparse(site).netloc.replace("www.", "")
    except:
        return ""


def domain_match(email_domain, site):
    try:
        return email_domain in urlparse(site).netloc
    except:
        return False


def generate_fallback_email(site):
    domain = get_domain(site)
    if not domain:
        return ""
    return f"{FALLBACK_PREFIXES[0]}@{domain}"


# --------------------------------------------------

def run_global_scraper(cities=None, categories=None,
                       progress_callback=None, stop_flag=None):

    def update_progress(msg):
        print(msg)
        if progress_callback:
            progress_callback(msg)

    update_progress("🌍 Engine Started")

    if not cities:
        cities = []
        for c in COUNTRIES.values():
            cities.extend(c)

    if not categories:
        categories = DEFAULT_CATEGORIES

    all_leads = []

    # =================================================
    # 🔎 SCRAPE LISTINGS
    # =================================================
    for city in cities:

        if stop_flag and stop_flag():
            update_progress("🛑 Stop requested")
            return []

        update_progress(f"📍 City: {city}")

        for category in categories:

            update_progress(f"🏷 Category: {category}")

            keywords = expand_keyword(category) + [
                f"top {category}",
                f"best {category}",
                f"{category} companies",
                f"{category} services",
                f"{category} providers",
            ]

            for keyword in keywords:

                if stop_flag and stop_flag():
                    update_progress("🛑 Stop requested")
                    return []

                update_progress(f"🔎 Searching: {keyword}")

                # Google Maps
                try:
                    all_leads += scrape_google_maps(city,
                                                    keyword, GOOGLE_PAGES)
                except Exception as e:
                    update_progress(f"Maps error: {e}")

                # Google search engines
                try:
                    leads = scrape_serpapi(city, keyword, GOOGLE_PAGES)
                    if not leads:
                        raise Exception("empty")
                except:
                    leads = scrape_playwright(city, keyword, GOOGLE_PAGES)

                all_leads += leads

                # ⭐ EXTRA SOURCES (HUGE BOOST)
                for source in (
                    scrape_bbb,
                    scrape_indiamart,
                    scrape_justdial,
                ):
                    try:
                        all_leads += source(city, keyword)
                    except:
                        pass

                human_delay()

        update_progress(f"📊 Raw Leads: {len(all_leads)}")

    # =================================================
    # CLEAN & DEDUPE
    # =================================================
    cleaned = []

    for lead in all_leads:
        website = lead.get("Website") or lead.get("url") or ""

        if any(b in website.lower() for b in BLOCKED_DOMAINS):
            continue

        if any(spam in website.lower() for spam in SPAM_TRAPS):
            continue

        cleaned.append({
            "Name": lead.get("Name", ""),
            "Website": website,
            "Phone": lead.get("Phone", ""),
            "Email": "",
            "UndeliverableEmails": [],
            "LinkedIn": ""
        })

    unique = dedupe_businesses(cleaned)[:MAX_WEBSITES]

    update_progress(f"✅ Unique Leads: {len(unique)}")

    # =================================================
    # EMAIL EXTRACTION
    # =================================================
    update_progress("📧 Extracting emails...")

    websites = list({
        lead["Website"]
        for lead in unique
        if lead["Website"] and not bad_domain(lead["Website"])
    })

    email_results = extract_emails_bulk(websites)

    email_map = {}

    for email in email_results:
        domain = email.split("@")[-1]
        for site in websites:
            if domain_match(domain, site):
                email_map.setdefault(site, []).append(email)

    for lead in unique:
        site = lead["Website"]
        valid, invalid = [], []

        if site in email_map:
            for e in email_map[site]:
                e = clean_email(e)
                if is_valid_email(e):
                    valid.append(e)
                else:
                    invalid.append(e)

        if valid:
            lead["Email"] = choose_best_email(valid, site)

        if invalid:
            lead["UndeliverableEmails"] = list(set(invalid))

        if not lead["Email"]:
            fallback = generate_fallback_email(site)
            if fallback:
                lead["Email"] = fallback

    # =================================================
    # DEEP WEBSITE CRAWL
    # =================================================
    update_progress("🌐 Deep crawling websites...")

    website_data = scrape_websites_bulk(websites) or {}

    for lead in unique:
        site = lead["Website"]
        if site in website_data:
            data = website_data[site]

            if data.get("Email") and not lead["Email"]:
                lead["Email"] = choose_best_email(data["Email"], site)

            if data.get("Phone"):
                lead["Phone"] = ", ".join(data["Phone"][:2])

            if data.get("LinkedIn") and not lead["LinkedIn"]:
                lead["LinkedIn"] = data["LinkedIn"][0]

    # =================================================
    # ENRICH + SCORE
    # =================================================
    update_progress("🏢 Enriching & scoring leads...")

    for lead in unique:
        try:
            details = extract_company_details(lead["Website"])
            lead["Company"] = details["company_name"]
            lead["About"] = details["about"]
            lead["CompanySize"] = estimate_company_size(details["about"])
            lead["EmailScore"] = score_email(lead["Email"], lead["Website"])
            lead["LeadScore"] = score_lead(lead)
        except:
            pass

    # =================================================
    # SAVE
    # =================================================
    os.makedirs("data", exist_ok=True)

    filename = f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = os.path.join("data", filename)

    save_to_csv(unique, filepath)

    update_progress("🎉 Completed")

    return unique
