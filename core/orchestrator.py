import os
from datetime import datetime
from urllib.parse import urlparse

from config import (
    COUNTRIES,
    DEFAULT_CATEGORIES,
    GOOGLE_PAGES,
    MAX_WEBSITES
)

from sources.google_maps import scrape_google_maps
from sources.serpapi_engine import scrape_serpapi
from sources.playwright_engine import scrape_playwright
from sources.justdial import scrape_justdial
from sources.sulekha import scrape_sulekha

from sources.yellowpages import scrape_yellowpages
from sources.manta import scrape_manta
from sources.bbb import scrape_bbb
from sources.clutch import scrape_clutch

from processors.email_extractor import extract_emails_from_website
from processors.validator import is_valid_email, clean_email
from processors.deduper import dedupe_businesses

from storage.csv_writer import save_to_csv
from utils.keyword_expander import expand_keyword
from utils.stealth import human_delay
from utils.parallel_executor import run_parallel

from processors.company_enricher import extract_company_details
from processors.company_size import estimate_company_size
from processors.email_score import score_email
from processors.lead_score import score_lead


BLOCKED_DOMAINS = [
    "justdial.com", "yellowpages.com", "google.com",
    "facebook.com", "instagram.com", "linkedin.com", "yelp.com"
]


def get_domain(url):
    try:
        return urlparse(url).netloc.replace("www.", "")
    except:
        return ""


# =========================================================
# 🔥 MAIN SCRAPER ENGINE (UI SAFE VERSION)
# =========================================================
def run_global_scraper(
        cities=None,
        categories=None,
        progress_callback=None,
        stop_flag=None):

    def update_progress(message):
        print(message)
        if progress_callback:
            progress_callback(message)

        if stop_flag and stop_flag():
            raise Exception("⛔ Scraping stopped by user")

    update_progress("🌍 Engine Started")

    if not cities:
        cities = []
        for c in COUNTRIES.values():
            cities.extend(c)

    if not categories:
        categories = DEFAULT_CATEGORIES

    all_leads = []

    try:
        for city in cities:
            update_progress(f"📍 City: {city}")

            for category in categories:
                update_progress(f"🏷 Category: {category}")

                keywords = expand_keyword(category)

                for keyword in keywords:
                    update_progress(f"🔎 Searching: {keyword}")

                    # GOOGLE MAPS
                    try:
                        leads = scrape_google_maps(city, keyword, GOOGLE_PAGES)
                        all_leads.extend(leads)
                        update_progress(f"Maps → {len(leads)}")
                    except Exception as e:
                        update_progress(f"Maps error: {e}")

                    human_delay()

                    # GOOGLE SEARCH
                    try:
                        leads = scrape_serpapi(city, keyword, GOOGLE_PAGES)
                        if not leads:
                            raise Exception()
                    except:
                        update_progress("Fallback → Playwright")
                        try:
                            leads = scrape_playwright(
                                city, keyword, GOOGLE_PAGES)
                        except Exception as e:
                            update_progress(f"Playwright failed")
                            leads = []

                    all_leads.extend(leads)
                    update_progress(f"Search → {len(leads)}")
                    human_delay()

                    # DIRECTORIES
                    try:
                        tasks = [
                            lambda: scrape_yellowpages(city, keyword, 1),
                            lambda: scrape_manta(city, keyword, 1),
                            lambda: scrape_bbb(city, keyword, 1),
                            lambda: scrape_clutch(keyword, 1),
                        ]

                        results = run_parallel(tasks, max_workers=4)

                        for r in results:
                            if r:
                                all_leads.extend(r)

                    except Exception:
                        pass

                    # INDIA DIRECTORIES
                    try:
                        jd = scrape_justdial(city, keyword, 1)
                        all_leads.extend(jd)
                        update_progress(f"Justdial → {len(jd)}")
                    except:
                        pass

                    try:
                        sk = scrape_sulekha(city, keyword, 1)
                        all_leads.extend(sk)
                        update_progress(f"Sulekha → {len(sk)}")
                    except:
                        pass

                    human_delay()

    except Exception as stop_msg:
        update_progress(str(stop_msg))
        return []

    update_progress(f"📊 Raw Leads: {len(all_leads)}")

    if not all_leads:
        return []

    # ================= CLEAN =================
    cleaned = []

    for lead in all_leads:
        name = lead.get("Name") or lead.get("title") or "Unknown"
        website = lead.get("Website") or lead.get("url") or ""
        phone = lead.get("Phone") or ""

        if any(b in website.lower() for b in BLOCKED_DOMAINS):
            continue

        cleaned.append({
            "Name": name.strip(),
            "Website": website.strip(),
            "Phone": phone.strip(),
            "Email": ""
        })

    unique = dedupe_businesses(cleaned)
    unique = unique[:MAX_WEBSITES]

    update_progress(f"✅ Unique Leads: {len(unique)}")

    # ================= EMAIL EXTRACTION =================
    update_progress("📧 Extracting Emails...")

    for lead in unique:
        if stop_flag and stop_flag():
            update_progress("⛔ Stopped")
            return []

        site = lead["Website"]
        if not site:
            continue

        try:
            emails = extract_emails_from_website(site) or []
            for email in emails:
                email = clean_email(email)
                if is_valid_email(email):
                    lead["Email"] = email
                    break
        except:
            pass

    final = unique

    # ================= ENRICH =================
    update_progress("🧠 Enriching Leads...")

    for lead in final:
        if stop_flag and stop_flag():
            update_progress("⛔ Stopped")
            return []

        try:
            details = extract_company_details(lead["Website"])

            lead["LinkedIn"] = details["linkedin"]
            lead["About"] = details["about"]
            lead["CompanySize"] = estimate_company_size(details["about"])
            lead["EmailScore"] = score_email(lead["Email"], lead["Website"])
            lead["LeadScore"] = score_lead(lead)
        except:
            pass

    # ================= EXPORT =================
    os.makedirs("data", exist_ok=True)

    filename = f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = os.path.join("data", filename)

    save_to_csv(final, filepath)

    update_progress("🎉 Completed")

    return final


# =========================================================
# ✅ DASHBOARD WRAPPER
# =========================================================
def run_pipeline(city, keyword, progress_callback=None, stop_flag=None):
    return run_global_scraper(
        cities=[city],
        categories=[keyword],
        progress_callback=progress_callback,
        stop_flag=stop_flag
    )
