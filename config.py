# ====================================
# API KEYS
# ====================================
SERP_API_KEY = "d3254bd5eaf71f77af07014a1758c5e65e76a21276bad70028b32b381dcc29ff"

# ====================================
# REQUEST HEADERS
# ====================================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml",
    "Connection": "keep-alive",
}


# ====================================
# STEALTH / ANTI-BLOCK SETTINGS
# ====================================

REQUEST_DELAY_MIN = 1.5   # seconds
REQUEST_DELAY_MAX = 4.5

ROTATE_USER_AGENTS = True

# ====================================
# GLOBAL SCALING CONFIG
# ====================================

COUNTRIES = {
    "USA": [
        "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Dallas",
        "Austin", "San Diego", "San Jose", "Seattle", "Denver", "Atlanta",
        "Miami", "Boston", "San Francisco", "Las Vegas", "Orlando", "Tampa",
        "Charlotte", "Nashville", "Detroit", "Minneapolis", "Portland",
        "Salt Lake City", "Indianapolis", "Columbus", "Kansas City",
        "Raleigh", "Pittsburgh", "Cleveland"
    ],

    "UK": [
        "London", "Manchester", "Birmingham", "Leeds", "Glasgow", "Liverpool",
        "Bristol", "Sheffield", "Edinburgh", "Nottingham", "Leicester",
        "Newcastle", "Cardiff", "Belfast", "Reading"
    ],

    "Canada": [
        "Toronto", "Vancouver", "Montreal", "Calgary", "Ottawa", "Edmonton",
        "Winnipeg", "Quebec City", "Hamilton", "Victoria", "Kitchener",
        "Halifax", "London Ontario", "Saskatoon", "Regina"
    ],

    "Australia": [
        "Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Gold Coast",
        "Canberra", "Newcastle", "Hobart", "Darwin", "Townsville",
        "Geelong", "Cairns", "Toowoomba", "Ballarat"
    ],

    "India": [
        "Chennai", "Bangalore", "Hyderabad", "Mumbai", "Pune", "Delhi",
        "Noida", "Gurgaon", "Kolkata", "Ahmedabad", "Coimbatore",
        "Trichy", "Madurai", "Kochi", "Vizag"
    ]
}

# ====================================
# TARGET INDUSTRIES
# ====================================

DEFAULT_CATEGORIES = [

    # BPO & OUTSOURCING
    "bpo company",
    "call center services",
    "outsourcing services",
    "customer support outsourcing",
    "back office outsourcing",

    # RCM & MEDICAL BILLING
    "medical billing company",
    "revenue cycle management",
    "medical coding services",
    "dental billing services",

    # IT & SOFTWARE
    "IT services company",
    "software development company",
    "web development company",
    "cloud services provider",
    "cybersecurity services",

    # HIGH-CONVERSION SERVICES
    "outsourced accounting services",
    "HR outsourcing services",
    "digital marketing agency"
]

# ====================================
# PAGINATION BOOST
# ====================================

GOOGLE_PAGES = 15
GOOGLE_SEARCH_PAGES = 15
JUSTDIAL_PAGES = 15

# ====================================
# SCALE CONTROL
# ====================================

MAX_WEBSITES = 20000
