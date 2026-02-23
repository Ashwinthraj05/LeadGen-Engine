import re

# =====================================
# PHONE CLEANING & NORMALIZATION
# =====================================


def clean_phone_number(num: str):
    digits = re.sub(r"\D", "", num)

    # valid global length
    if not (9 <= len(digits) <= 15):
        return None

    # reject date-like patterns (1999, 2023 etc)
    if digits.startswith(("19", "20")) and len(digits) >= 10:
        return None

    # reject repeating digits (0000000000)
    if len(set(digits)) == 1:
        return None

    # reject obvious fake endings
    if digits.endswith(("0000", "1111", "2222", "1234")):
        return None

    # =============================
    # 🇮🇳 INDIA MOBILE (HIGH PRIORITY)
    # =============================
    # formats:
    # 9876543210
    # +919876543210
    # 0919876543210

    if digits.startswith("91") and len(digits) == 12:
        return digits

    if len(digits) == 10 and digits[0] in "6789":
        return "91" + digits

    # =============================
    # 🇺🇸 US NUMBERS
    # =============================
    if digits.startswith("1") and len(digits) == 11:
        return digits

    if len(digits) == 10:
        return "1" + digits

    # =============================
    # 🌍 INTERNATIONAL SUPPORT
    # =============================
    # keep valid international numbers
    if 11 <= len(digits) <= 15:
        return digits

    return None


def extract_phones(text: str):
    """
    Extract and clean phone numbers from text.
    """

    if not text:
        return []

    # includes tel: links & WhatsApp links
    raw_phones = re.findall(
        r"(?:tel:|\+?\d[\d\-\s\(\)]{7,}\d)",
        text
    )

    phones = set()

    for phone in raw_phones:
        cleaned = clean_phone_number(phone)
        if cleaned:
            phones.add(cleaned)

    return list(phones)


# =====================================
# EMAIL EXTRACTION & FILTERING
# =====================================

EMAIL_REGEX = re.compile(
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    re.IGNORECASE
)

INVALID_EMAIL_PARTS = (
    ".png", ".jpg", ".jpeg", ".webp", ".svg",
    "example.com", "domain.com", "email.com",
    "@2x", "sample@", "test@", "yourname@"
)


def extract_emails(text: str):
    """
    Extract unique & clean emails from text.
    """

    if not text:
        return []

    matches = EMAIL_REGEX.findall(text)

    cleaned = set()

    for email in matches:
        e = email.lower().strip()

        # remove image filenames & fake placeholders
        if any(x in e for x in INVALID_EMAIL_PARTS):
            continue

        # remove extremely long junk emails
        if len(e) > 60:
            continue

        cleaned.add(e)

    return list(cleaned)
