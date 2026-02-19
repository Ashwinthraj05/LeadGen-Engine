from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time


def scrape_playwright(city, keyword, pages=3):

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for i in range(pages):

            start = i * 10
            url = f"https://www.google.com/search?q={keyword} in {city}&start={start}"

            print(f"Playwright → {url}")

            page.goto(url)
            time.sleep(3)

            html = page.content()
            soup = BeautifulSoup(html, "html.parser")

            for result in soup.select("div.tF2Cxc"):
                link_tag = result.find("a")
                title_tag = result.find("h3")

                if link_tag and title_tag:
                    results.append({
                        "Name": title_tag.text,
                        "Website": link_tag["href"],
                        "Phone": "",
                        "Email": ""
                    })

        browser.close()

    return results
