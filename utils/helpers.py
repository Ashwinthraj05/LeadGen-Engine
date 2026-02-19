import requests
import time
import random
from urllib.parse import urlparse
from utils.headers import get_headers as rotating_headers  # ✅ use rotating headers


# =========================================================
# SAFE HTTP REQUEST
# =========================================================
def safe_request(url, headers=None, retries=3, timeout=20, delay=2):
    """
    Human-like safe request handler
    prevents blocking & handles retries
    """

    for attempt in range(retries):
        try:
            # human-like delay
            time.sleep(random.uniform(1.5, 3.5))

            response = requests.get(
                url,
                headers=headers or rotating_headers(),
                timeout=timeout,
                allow_redirects=True
            )

            if response.status_code == 200:
                return response

            # Blocked or rate limited
            if response.status_code in [403, 429, 503]:
                print(f"⚠ Blocked ({response.status_code}) → retrying...")
                time.sleep(delay * (attempt + 2))

        except requests.exceptions.SSLError:
            print("⚠ SSL error → retrying without verification...")
            try:
                response = requests.get(
                    url,
                    headers=headers or rotating_headers(),
                    timeout=timeout,
                    verify=False
                )
                if response.status_code == 200:
                    return response
            except:
                pass

        except requests.exceptions.RequestException:
            print("⚠ Request failed → retrying...")

        time.sleep(delay * (attempt + 1))

    return None


# =========================================================
# CLEAN TEXT
# =========================================================
def clean_text(value):
    if not value:
        return ""
    return str(value).strip()


# =========================================================
# NORMALIZE WEBSITE
# =========================================================
def normalize_website(url):
    if not url:
        return ""

    url = url.strip()

    if not url.startswith("http"):
        url = "https://" + url

    parsed = urlparse(url)

    if not parsed.netloc:
        return ""

    return f"{parsed.scheme}://{parsed.netloc}"


# =========================================================
# CREATE BUSINESS OBJECT + FILTER JUNK SITES
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

    BAD_DOMAINS = [
        "wikipedia.org",
        "youtube.com",
        "glassdoor",
        "ambitionbox",
        "justdial.com",
        "sulekha.com",
        "clutch.co",
        "goodfirms.co",
        "builtin.com",
        "interviewbit.com",
        "wellfound.com",
        "designrush.com",
        "scribd.com",
        "housing.com",
        "internshala.com",
        "mygate.com",
        "nobroker.in",
        "topsoftwarecompanies.co",
        "selectedfirms.co",
        "facebook.com",
        "linkedin.com",
        "instagram.com"
    ]

    website = normalize_website(website)

    if website:
        for bad in BAD_DOMAINS:
            if bad in website.lower():
                return None

    business = {
        "Name": clean_text(name),
        "Phone": clean_text(phone),
        "Address": clean_text(address),
        "Website": website,
        "Email": clean_text(email),
        "City": clean_text(city),
        "Category": clean_text(category),
        "Source": clean_text(source)
    }

    return business
