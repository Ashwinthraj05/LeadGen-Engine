def estimate_company_size(text):

    text = text.lower()

    if "enterprise" in text or "global" in text:
        return "1000+"

    if "team of" in text or "employees" in text:
        return "50-200"

    if "startup" in text or "small team" in text:
        return "1-10"

    return "unknown"
