def normalize_website(url: str) -> str:
    if not url:
        return ""

    url = url.strip().lower()

    url = url.replace("https://", "")
    url = url.replace("http://", "")
    url = url.replace("www.", "")

    return url.rstrip("/")


def dedupe_businesses(businesses):
    seen = set()
    unique = []

    for b in businesses:
        name = b.get("Name", "").strip().lower()
        website = normalize_website(b.get("Website", ""))

        key = (name, website)

        if key not in seen:
            seen.add(key)
            b["Website"] = website
            unique.append(b)

    return unique
