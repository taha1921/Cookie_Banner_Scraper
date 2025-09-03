import pandas as pd
from playwright.async_api import async_playwright
import asyncio
import json
import logging
from datetime import datetime

# data = pd.read_excel('Thesis_Data_2.xlsx', sheet_name='Data')
# explicit_domains = data[data['Implicit vs Explicit'] == 'Explicit']
# CMP_domains = explicit_domains[explicit_domains['CMPTYPE'].isin(['GCMP', 'NOT_GCMP', 'UNKNOWN', 'google_ump'])]

# train, test = train_test_split(CMP_domains, test_size=0.4, random_state=42)
# val, test = train_test_split(test, test_size=0.5, random_state=42)

# print(f"Train set size: {len(train)}")
# print(f"Validation set size: {len(val)}")
# print(f"Test set size: {len(test)}")


"""
Takes as input the button elements inside a banner from Playwright and assesses whether there is a reject button on the first layer of the banner.
"""
async def check_for_reject_button(banner, selector, css_selectors, playwright_selectors):
    # First we check if the specific selector for this selector can be found in the banner
    reject_button = selector['reject_button']
    # count_main = await banner.locator(reject_button).count()
    # count_alt = await banner.locator(','.join(reject_button_values)).count()

    if(await banner.locator(reject_button).count() > 0):
        logging.info(f"Found reject button with the designated selector: {reject_button}")
        return 1
    elif(await banner.locator(','.join(css_selectors)).count() > 0):
        logging.info(f"Found reject button with an alternative selector from the the list")
        return 1
    else:
        if('preferences_button' in selector):
            try:
                await banner.locator(selector['preferences_button']).first.click()
                logging.info(f"Clicked preferences button with selector: {selector['preferences_button']}")
                try:
                    await banner.locator(reject_button).wait_for(state='attached', timeout=10000)
                    logging.info(f"Found reject button with the designated selector on layer 2: {reject_button}")
                    return 2
                except:
                    try:
                        await banner.locator(','.join(css_selectors)).wait_for(state='attached', timeout=10000)
                        logging.info(f"Found reject button with an alternative selector from the the list on layer 2")
                        return 2
                    except:
                        logging.debug(f"No reject button found with selector: {reject_button}")
                        return 0
            except Exception as e:
                logging.error(f"Could not find preferences button or reject button: {e}")
                return 0
        else:
            logging.debug(f"No reject button found with selector: {reject_button}")
            return 0

"""
Takes an individual selector and searches the page for it. If the selector is found then we return the locator object 
and the selector.
"""
async def locate_cookie_banner(page, selector):
    try:
        banner = page.locator(selector)
        await banner.wait_for(state='attached', timeout=10000)
        if banner:
            logging.info(f"Found banner with selector: {selector}")
            return banner, selector
    except Exception as e:
        return None
    
"""
Takes a list of selectors and launches parallel tasks to search for each selector on the page. The first selector to
return a result will be the one that we use. If no selector is found then we return None. 
"""
async def check_selectors(page, selectors):
    tasks = [asyncio.create_task(locate_cookie_banner(page, sel)) for sel in selectors.keys()]
    try:
        for task in asyncio.as_completed(tasks):
            result = await task
            if result:
                for t in tasks:
                    if not t.done():
                        t.cancel()
                return result
    except Exception as e:
        logging.error("Error in task interruption:", e)
    return None

"""
Runs our simulator which takes a list of domains and a list of CMP selectors to try and find the cookie banner on the page.
"""
async def simulator(domain_list, selectors, css_selectors, playwright_selectors, progress_callback=None):
    
    reject_all_presence = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        total = len(domain_list)
        for i, sample_domain in enumerate(domain_list, start=1):
            page = await browser.new_page()
            try:
                await page.goto(sample_domain)
                logging.info(f"Visiting domain: {sample_domain}")
            except:
                logging.error(f"Could not load domain: {sample_domain}")
                await page.close()
                reject_all_presence.append(-2)

                if progress_callback:
                    progress_callback(i, total)
                continue

            await page.mouse.move(100, 200)
            await page.mouse.wheel(0, 300)

            try:
                result = await check_selectors(page, selectors)
                    
                if result:
                    banner, selector = result
                    selector_properties = selectors[selector]
                    res = await check_for_reject_button(banner, selector_properties, css_selectors, playwright_selectors)
                    if(res == 0):
                        await page.screenshot(path=f'../output/screenshots/{sample_domain.replace("https://", "").replace("http://", "").replace(".", "_")}_no_reject.png')
                    elif(res == -2):
                        await page.screenshot(path=f'../output/screenshots/{sample_domain.replace("https://", "").replace("http://", "").replace(".", "_")}.png')
                    reject_all_presence.append(res)

                else:
                    logging.warning(f"No banner found for domain {sample_domain}")
                    await page.screenshot(path=f'../output/screenshots/{sample_domain.replace("https://", "").replace("http://", "").replace(".", "_")}.png')
                    reject_all_presence.append(-1)
                    
            except Exception as e:
                logging.error(f"Error or timeout for domain {sample_domain}: {e}")
                reject_all_presence.append(-2)

            if progress_callback:
                progress_callback(i, total)

            await page.close()
        await browser.close()
    return reject_all_presence


async def process_domains(domain_list, progress_callback=None):
    # Start Logging
    logging.basicConfig(
    filename = f"../output/logs/val_run_{datetime.now():%Y-%m-%d_%H-%M-%S}.log",
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Load Domains
    logging.info(f"Number of domains to process: {len(domain_list)}")

    # Load Selectors
    with open('../SELECTORS.json', 'r') as file:
        selectors = json.load(file)
    
    reject_button_selectors = [selectors[key]['reject_button'] for key in selectors.keys() if 'reject_button' in selectors[key]]
    reject_button_selectors = ",".join(reject_button_selectors).split(',')
    reject_button_selectors = list(set(reject_button_selectors))

    css_selectors = []
    playwright_selectors = []
    
    for selector in reject_button_selectors:
        if(">>" in selector):
            playwright_selectors.append(selector)
        else:
            css_selectors.append(selector)
    
    # Run Simulator
    reject_all_presence = await simulator(domain_list, selectors, css_selectors, playwright_selectors, progress_callback)
  
    # Summarize Results
    total_found = sum(1 for res in reject_all_presence if res in [1,2])
    total_not_found = sum(1 for res in reject_all_presence if res == 0)
    total_no_banner = sum(1 for res in reject_all_presence if res == -1)
    total_error = sum(1 for res in reject_all_presence if res == -2)
    logging.info(f"Total Correct Results: {total_found}")
    logging.info(f"Total Incorrect Results: {total_not_found}")
    logging.info(f"Total Not Found Results: {total_no_banner}")
    logging.info(f"Total Error Results: {total_error}")
    
