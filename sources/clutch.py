import requests
from bs4 import BeautifulSoup
from utils.headers import get_headers
from utils.stealth import human_delay


def scrape_clutch(keyword, pages=2):

    results = []
    keyword_slug = keyword.replace(" ", "-").lower()

    for page in range(1, pages + 1):

        url = f"https://clutch.co/search?query={keyword_slug}&page={page}"

        print(f"🔵 Clutch → {url}")

        try:
            res = requests.get(url, headers=get_headers(), timeout=20)

            if res.status_code != 200:
                continue

            soup = BeautifulSoup(res.text, "html.parser")
            companies = soup.select(".provider-row")

            for comp in companies:

                name_tag = comp.select_one(".company-name")
                website_tag = comp.select_one("a.website-link__item")

                if not name_tag or not website_tag:
                    continue

                name = name_tag.get_text(strip=True)
                website = website_tag.get("href")

                results.append({
                    "Name": name,
                    "Website": website,
                    "Phone": ""
                })

            human_delay()

        except Exception as e:
            print("Clutch error:", e)

    return results
