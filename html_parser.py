from playwright.sync_api import sync_playwright
import asyncio
from bs4 import BeautifulSoup
import re
import pandas as pd

def get_page_html(url, wait_time=5):
    """Launches browser, gets HTML content of the given URL"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        try: 
            page.goto(url, timeout=60000)
            page.wait_for_timeout(wait_time * 1000)
            html = page.content()
        except:
            html = ""
        browser.close()
        return html

def filter_html(html):
    soup = BeautifulSoup(html, "lxml")    

    cookie_keywords = r"cookie|consent|privacy|cmp|didomi|qc-|ot-|cc-"

    candidates = soup.find_all(
        lambda tag: tag.name in ["div", "section", "aside"] and (
            any(re.search(cookie_keywords, attr, re.I) for attr in [
                tag.get("id", ""), 
                tag.get("data-test-id", ""), 
                tag.get("aria-label", ""),
                tag.get("class", "") if isinstance(tag.get("class"), str) else " ".join(tag.get("class", []))
                ])
        )
    )

    more_candidates = soup.find_all(
        lambda tag: tag.name in ["div", "section", "aside"] and (
            "position:fixed" in tag.get("style", "").replace(" ", "").lower()
        )
    )

    all_candidates = set(candidates + more_candidates)


    ranked = sorted(
        all_candidates,
        key=lambda tag: (
            bool(re.search(r"cookie|we\suse\s+cookies|accept|consent|privacy|reject|partners|measure|experience|withdraw|marketing", tag.get_text(), re.I)),
            len(tag.get_text(strip=True)),
        ),
        reverse=True
    )

    return ranked[0] if ranked else None

def main():
    data = pd.read_excel('train.xlsx')
    urls = ["https://"+ url if "http" not in url else url for url in data['Domain']]
    lengths = []
    for url in urls[0:5]:
        print("Fetching page: ", url)
        raw_html = get_page_html(url)
    # print(f"Length of raw html: {len(raw_html)}")
        filtered_html = filter_html(raw_html)
        lengths.append({"domain": url, "raw_length": len(raw_html), "filtered_length": len(str(filtered_html)) if filtered_html else 0})
    
    pd.DataFrame(lengths).to_excel('filtered_lengths.xlsx', index=False)
    # print(f"Length of filtered html: {len(str(filtered_html))}")

if __name__ == "__main__":
    main()

