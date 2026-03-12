"""
utils/headers.py
FIXED: Added more recent Chrome versions, Accept-Encoding header,
       sec-ch-ua headers that modern browsers send (helps bypass bot detection)
"""

import random

USER_AGENTS = [
    # Chrome 124 Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",

    # Chrome 124 Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",

    # Chrome 123 Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",

    # Firefox 125 Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) "
    "Gecko/20100101 Firefox/125.0",

    # Firefox 124 Linux
    "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) "
    "Gecko/20100101 Firefox/124.0",

    # Edge 124 Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",

    # Mobile Chrome Android
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",

    # Mobile Safari iPhone
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 "
    "Mobile/15E148 Safari/604.1",
]

REFERRERS = [
    "https://www.google.com/",
    "https://www.bing.com/",
    "https://duckduckgo.com/",
    "https://www.google.co.in/",
    "https://www.google.co.uk/",
]


def get_headers(include_sec_ch: bool = False) -> dict:
    """
    Generate realistic rotating browser headers.
    set include_sec_ch=True for sites that check Chrome client hints.
    """
    ua = random.choice(USER_AGENTS)

    headers = {
        "User-Agent":                ua,
        "Accept":                    "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language":           "en-US,en;q=0.9",
        "Accept-Encoding":           "gzip, deflate, br",
        "Referer":                   random.choice(REFERRERS),
        "Connection":                "keep-alive",
        "DNT":                       "1",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control":             "max-age=0",
    }

    if include_sec_ch and "Chrome" in ua:
        headers.update({
            "sec-ch-ua":          '"Chromium";v="124", "Google Chrome";v="124"',
            "sec-ch-ua-mobile":   "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Sec-Fetch-Dest":     "document",
            "Sec-Fetch-Mode":     "navigate",
            "Sec-Fetch-Site":     "none",
            "Sec-Fetch-User":     "?1",
        })

    return headers
