import re


def estimate_company_size(text: str) -> str:
    """
    Estimate company size from website/about text.

    Returns:
        "1-10"
        "11-50"
        "51-200"
        "201-500"
        "501-1000"
        "1000+"
        "unknown"
    """

    if not text:
        return "unknown"

    text = text.lower()

    # --------------------------
    # DIRECT NUMBER DETECTION
    # --------------------------
    patterns = [
        (r"(\d{4,})\+?\s*(employees|people|staff)", "1000+"),
        (r"(\d{3})\+?\s*(employees|people|staff)", "501-1000"),
        (r"(\d{3})\s*(employees|people|staff)", "201-500"),
        (r"(\d{2,3})\s*(employees|people|staff)", "51-200"),
        (r"(\d{2})\s*(employees|people|staff)", "11-50"),
    ]

    for pattern, size in patterns:
        if re.search(pattern, text):
            return size

    # --------------------------
    # KEYWORD HEURISTICS
    # --------------------------

    enterprise_keywords = [
        "enterprise",
        "fortune 500",
        "multinational",
        "global leader",
        "worldwide offices",
        "international presence"
    ]

    medium_keywords = [
        "growing team",
        "fast growing",
        "expanding team",
        "mid-sized",
        "scale-up"
    ]

    small_keywords = [
        "startup",
        "small team",
        "boutique agency",
        "small business",
        "early stage"
    ]

    if any(k in text for k in enterprise_keywords):
        return "1000+"

    if any(k in text for k in medium_keywords):
        return "51-200"

    if any(k in text for k in small_keywords):
        return "1-10"

    return "unknown"
