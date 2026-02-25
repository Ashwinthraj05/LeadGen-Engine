def normalize_city(city):
    mapping = {
        "bangalore": "bengaluru",
        "delhi": "new-delhi"
    }
    return mapping.get(city.lower(), city.lower())


def normalize_category(category):
    mapping = {
        "bpo": "bpo",
        "call center": "call-centers",
        "rcm": "revenue-cycle-management",
        "it services": "it-services"
    }
    return mapping.get(category.lower(), category.lower())
