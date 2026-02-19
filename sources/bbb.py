import requests
from bs4 import BeautifulSoup
from utils.headers import get_headers
from utils.stealth import human_delay


def scrape_bbb(city, keyword, pages=2):

    results = []
    city_slug = city.replace(" ", "-").lower()

    for page in range(1, pages + 1):

        url = f"https://www.bbb.org/search?find_country=USA&find_text={keyword}&find_loc={city_slug}&page={page}"

        print(f"🟩 BBB → {url}")

        try:
            res = requests.get(url, headers=get_headers(), timeout=20)

            if res.status_code != 200:
                continue

            soup = BeautifulSoup(res.text, "html.parser")
            listings = soup.select(".result-item")

            for item in listings:

                name_tag = item.select_one("a.result-business-name")
                website_tag = item.select_one("a[href^='http']")

                if not name_tag:
                    continue

                name = name_tag.get_text(strip=True)

                website = ""
                if website_tag:
                    website = website_tag.get("href")

                if not website:
                    continue

                results.append({
                    "Name": name,
                    "Website": website,
                    "Phone": ""
                })

            human_delay()

        except Exception as e:
            print("BBB error:", e)

    return results
