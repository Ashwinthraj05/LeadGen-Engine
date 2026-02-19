import requests
from bs4 import BeautifulSoup
from utils.headers import get_headers
from utils.stealth import human_delay


def scrape_manta(city, keyword, pages=2):

    results = []
    city_slug = city.replace(" ", "-").lower()

    for page in range(1, pages + 1):

        url = f"https://www.manta.com/search?search={keyword}&location={city_slug}&pg={page}"

        print(f"🟢 Manta → {url}")

        try:
            res = requests.get(url, headers=get_headers(), timeout=20)

            if res.status_code != 200:
                continue

            soup = BeautifulSoup(res.text, "html.parser")
            listings = soup.select("div.SearchResults__Result")

            for item in listings:
                name_tag = item.select_one("a.SearchResult__TitleLink")
                if not name_tag:
                    continue

                name = name_tag.get_text(strip=True)

                website = ""
                site_tag = item.select_one("a[href^='http']")
                if site_tag:
                    website = site_tag.get("href")

                if not website:
                    continue

                results.append({
                    "Name": name,
                    "Website": website,
                    "Phone": ""
                })

            human_delay()

        except Exception as e:
            print("Manta error:", e)

    return results
