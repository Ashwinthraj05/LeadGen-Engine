import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9"
}

SOCIAL_PLATFORMS = {
    "linkedin": "linkedin.com/company",
    "twitter": "twitter.com",
    "facebook": "facebook.com",
    "instagram": "instagram.com",
    "youtube": "youtube.com"
}


# --------------------------------------------------
# DOMAIN NORMALIZATION
# --------------------------------------------------

def normalize_domain(url: str) -> str:
    if not url:
        return ""

    parsed = urlparse(url)
    domain = parsed.netloc if parsed.netloc else parsed.path

    return domain.replace("www.", "").strip().lower()


# --------------------------------------------------
# COMPANY NAME EXTRACTION
# --------------------------------------------------

def extract_company_name(soup, domain):
    """
    Detect company name using multiple signals
    """

    # 1️⃣ og:site_name (most accurate)
    tag = soup.find("meta", property="og:site_name")
    if tag and tag.get("content"):
        return tag["content"].strip()

    # 2️⃣ application-name meta
    tag = soup.find("meta", attrs={"name": "application-name"})
    if tag and tag.get("content"):
        return tag["content"].strip()

    # 3️⃣ title tag cleanup
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

        for separator in ["|", "-", "•", "–"]:
            if separator in title:
                title = title.split(separator)[0].strip()

        if 2 <= len(title) <= 60:
            return title

    # 4️⃣ logo alt text
    logo = soup.find("img", alt=True)
    if logo and len(logo["alt"]) < 60:
        return logo["alt"].strip()

    # 5️⃣ fallback to domain
    return domain.split(".")[0].capitalize()


# --------------------------------------------------
# ABOUT / DESCRIPTION
# --------------------------------------------------

def extract_about_text(soup):
    """
    Extract meaningful company description
    """

    # meta description (best signal)
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        return meta["content"].strip()[:300]

    # og:description
    og = soup.find("meta", property="og:description")
    if og and og.get("content"):
        return og["content"].strip()[:300]

    # longest paragraph fallback
    paragraphs = soup.find_all("p")
    best = ""

    for p in paragraphs:
        text = p.get_text(" ", strip=True)

        # ignore cookie/privacy junk
        if len(text) < 40:
            continue
        if any(x in text.lower() for x in ["cookie", "privacy", "terms"]):
            continue

        if len(text) > len(best):
            best = text

    return best[:300]


# --------------------------------------------------
# SOCIAL LINKS
# --------------------------------------------------

def extract_social_links(soup, base_url):
    socials = {}

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if href.startswith("/"):
            href = urljoin(base_url, href)

        for name, keyword in SOCIAL_PLATFORMS.items():
            if keyword in href.lower() and name not in socials:
                socials[name] = href

    return socials


# --------------------------------------------------
# MAIN EXTRACTION FUNCTION
# --------------------------------------------------

def extract_company_details(url):
    """
    Extract company intelligence from website

    Returns:
    {
        company_name,
        domain,
        linkedin,
        about,
        socials
    }
    """

    result = {
        "company_name": "",
        "domain": "",
        "linkedin": "",
        "about": "",
        "socials": {}
    }

    if not url:
        return result

    try:
        if not url.startswith("http"):
            url = "https://" + url

        res = requests.get(
            url,
            timeout=10,
            verify=False,
            headers=HEADERS
        )

        if res.status_code != 200 or not res.text:
            return result

        soup = BeautifulSoup(res.text, "html.parser")

        domain = normalize_domain(url)

        result["domain"] = domain
        result["company_name"] = extract_company_name(soup, domain)
        result["about"] = extract_about_text(soup)
        result["socials"] = extract_social_links(soup, url)
        result["linkedin"] = result["socials"].get("linkedin", "")

    except Exception:
        pass

    return result
