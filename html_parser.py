from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import pandas as pd

def get_page_html(url, wait_time=5):
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

def has_keyword(tag):

    cookie_keywords = r"cookie|consent|privacy|cmp|didomi|qc-|ot-|cc-"

    attrs = [
        tag.get("id", ""),
        tag.get("data-test-id", ""),
        tag.get("aria-label", ""),
        " ".join(tag.get("class", [])) if isinstance(tag.get("class"), list) else tag.get("class", "")
    ]
    return any(re.search(cookie_keywords, attr, re.I) for attr in attrs)

def filter_html(html, max_depth=5):
    soup = BeautifulSoup(html, "lxml")
        
    candidates = soup.find_all(
        lambda tag: tag.name in ["div", "section", "aside"] and has_keyword(tag)
    )
 
    # fixed_candidates = soup.find_all(
    #     lambda tag: tag.name in ["div", "section", "aside"] and (
    #         "position:fixed" in tag.get("style", "").replace(" ", "").lower()
    #     )
    # )
    
    text_regex = re.compile(r"cookie|consent|privacy|accept|we use cookies|policy|marketing|purpose|vendors|tracking|partners", re.I)
    text_matches = soup.find_all(lambda tag: text_regex.search(tag.get_text(" ", strip=True)))
    text_candidates = set()

    # print(f"Found {len(text_matches)} text matches.")

    interactive_tags = {"button"}
    for tag in text_matches:
        parent = tag
        depth = 0
        while parent and depth < max_depth:
            if any(parent.find(itag) for itag in interactive_tags):
                text_candidates.add(parent)
                # break
            parent = parent.parent
            depth += 1

    all_candidates = set(candidates) | text_candidates

    all_candidates = [
        tag for tag in all_candidates
        if tag.name not in {"body", "html"} and len(tag.get_text(strip=True)) < 5000
    ]

    text_keywords = re.compile(r"cookie|consent|privacy|accept|we use cookies|policy|marketing|purpose|vendors|tracking|partners", re.I)

    def is_interactive(tag):
        return any(tag.find(itag) for itag in interactive_tags)

    def count_text_matches(tag):
        text = tag.get_text(" ", strip=True)
        return len(text_keywords.findall(text))

    def html_length(tag):
        return len(str(tag))

    # Check to see if the candidate has interactive elements like buttons
    interactive_candidates = [tag for tag in all_candidates if is_interactive(tag)]

    # Scoring: first criteria: High number of keyword matches, second criteria: length of HTML should be small
    def score(tag):
        return (-count_text_matches(tag), html_length(tag))

    # Final sorted list
    ranked = sorted(interactive_candidates, key=score)
    return ranked[0] if ranked else None

def main():
    data = pd.read_excel('train.xlsx')
    urls = ["https://"+ url if "http" not in url else url for url in data['Domain']]
    # urls = ["https://genius.com"]
    lengths = []
    for url in urls:
        print("Fetching page: ", url)
        raw_html = get_page_html(url)
    # print(f"Length of raw html: {len(raw_html)}")
        filtered_html = filter_html(raw_html)
        # with open('filtered.html', 'w', encoding='utf-8') as f:
        #     f.write(str(filtered_html) if filtered_html else "")

        lengths.append({"domain": url, "raw_length": len(raw_html), "filtered_length": len(str(filtered_html)) if filtered_html else 0})
    
    pd.DataFrame(lengths).to_excel('filtered_lengths.xlsx', index=False)
    # print(f"Length of filtered html: {len(str(filtered_html))}")

if __name__ == "__main__":
    main()

