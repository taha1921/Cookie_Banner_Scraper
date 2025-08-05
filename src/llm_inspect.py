import asyncio
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from langchain.llms import Ollama
import re

def get_page_html(url, wait_time=5):
    """Launches browser, gets HTML content of the given URL"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_timeout(wait_time * 1000)
        html = page.content()
        browser.close()
        return html

def extract_cookie_snippets(html, max_snippets=5, max_chars=5000):
    soup = BeautifulSoup(html, 'html.parser')

    for tag_name in ['script', 'style', 'noscript', 'iframe', 'template', 'svg']:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    cookie_keywords = ['cookie', 'consent', 'gdpr', 'privacy', 'data usage', 'accept all']

    def keyword_count(text):
        return sum(1 for kw in cookie_keywords if kw in text)

    candidates = []
    for tag in soup.find_all(True):
        if tag.name in ['html', 'head', 'body']:
            continue
        text = tag.get_text(" ", strip=True).lower()
        attrs = " ".join([str(val).lower() for val in tag.attrs.values()])
        combined = text + " " + attrs
        score = keyword_count(combined)

        # Include tags with decent keyword presence and visible text
        if score >= 1 and len(text) > 40:
            candidates.append((score, tag))

    # Sort candidates: higher score first, longer text preferred
    candidates.sort(key=lambda x: (-x[0], -len(x[1].get_text(strip=True))))

    snippets = []
    seen = set()

    for score, tag in candidates:
        outer_html = str(tag)
        if outer_html in seen:
            continue
        seen.add(outer_html)
        if len(outer_html) <= max_chars:
            snippets.append(outer_html)
        else:
            snippets.append(outer_html[:max_chars])
        if len(snippets) >= max_snippets:
            break

    return snippets if snippets else None

def ask_llm_to_choose(snippets, model_name="llama3.1:8b"):
    llm = Ollama(model=model_name)

    formatted = "\n\n".join([f"Snippet {i+1}:\n{snippet}" for i, snippet in enumerate(snippets)])

    prompt = f"""

Task: Identify and reconstruct the full HTML element corresponding to the cookie consent banner on a webpage.

Context:
> You will be provided with several possibly overlapping HTML snippets from a webpage.
> These snippets were selected using keyword matching and may contain parts of the cookie banner.
> Your job is to stitch together one coherent HTML element that fully represents the cookie consent banner.

Instructions:
> From the snippets, extract and combine relevant parts into one complete HTML structure representing the cookie banner.
> The final element should include:
    >> Text related to cookies, consent, privacy, tracking, or vendors.
    >> Buttons or links that allow users to accept or reject cookies.

Example input snippets:

<!-- Snippet 1 -->
<body>
  <div id="main page">
    <div id="footer">
      <div id="cookie-banner-container">
        <div id="cookie-text">
          <p>We use cookies to improve your experience.</p>
        </div>

<!-- Snippet 2 -->
<div id="cookie-buttons">
  <button id="accept">Accept</button>
  <button id="reject">Reject</button>
</div>

Expected output:
<div id="cookie-banner-container">
  <div id="cookie-text">
    <p>We use cookies to improve your experience.</p>
  </div>
  <div id="cookie-buttons">
    <button id="accept">Accept</button>
    <button id="reject">Reject</button>
  </div>
</div>

Important rules:
> Return only one complete HTML element, even if it's repeated or partially found in multiple snippets.
> If you can't confidently identify such an element, return: None
> Do not return any explanations, comments, or additional text—just the final HTML.

{formatted}
"""
    return llm(prompt).strip()

def main():
    url = input("Enter a URL: ").strip()
    print("Fetching page...")
    raw_html = get_page_html(url)

    print("Extracting candidate elements...")
    candidates = extract_cookie_snippets(raw_html)

    print(f"Found {len(candidates)} candidates.")

    for c in candidates:
        print(len(c))


    best_snippet = ask_llm_to_choose(candidates)

    # print("Best-matching cookie banner HTML:\n")

    with open("best_snippet.html", "w", encoding="utf-8") as f:
        f.write(best_snippet)
        # for c in range(len(candidates)):
        #     f.write(f"snippet {c+1}: {candidates[c]} + \n\n")
    
 

if __name__ == "__main__":
    main()