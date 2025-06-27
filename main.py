import pandas as pd
from playwright.async_api import async_playwright
import asyncio
from sklearn.model_selection import train_test_split
import json


data = pd.read_excel('Thesis_Data_2.xlsx', sheet_name='Data')
explicit_domains = data[data['Implicit vs Explicit'] == 'Explicit']
CMP_domains = explicit_domains[explicit_domains['CMPTYPE'].isin(['GCMP', 'NOT_GCMP', 'UNKNOWN', 'google_ump'])]

train, test = train_test_split(CMP_domains, test_size=0.4, random_state=42)
val, test = train_test_split(test, test_size=0.5, random_state=42)

print(f"Train set size: {len(train)}")
print(f"Validation set size: {len(val)}")
print(f"Test set size: {len(test)}")


"""
Takes as input the button elements inside a banner from Playwright and assesses whether there is a reject button on the first layer of the banner.
"""
async def check_for_reject_button(buttons, selector):

    attribute = selector["attribute"]
    reject_button = selector['reject_button']

    btn_count = await buttons.count()
    # print(btn_count)
    for i in range(btn_count):
        btn = buttons.nth(i)
        btn_id = await btn.get_attribute(attribute)
        # print(btn_id)
        if(btn_id == reject_button):
            return 1
        # else:
        #     text_content = await btn.text_content()
        #     text = text_content.strip()
        #     if "reject" in text.lower():
        #         return 1

    return 0

"""
Takes an individual selector and searches the page for it. If the selector is found then we return the locator object 
and the selector.
"""
async def locate_cookie_banner(page, selector):

    try:
        banner = page.locator(selector)
        await banner.wait_for(state='attached', timeout=20000)
        if banner:
            return banner, selector
    except Exception as e:
        print(f"Error or Possible timeout when searching for banner: {e}")
        return None
    
"""
Takes a list of selectors and launches parallel tasks to search for each selector on the page. The first selector to
return a result will be the one that we use. If no selector is found then we return None. 
"""
async def check_selectors(page, selectors):

    tasks = [asyncio.create_task(locate_cookie_banner(page, sel)) for sel in selectors.keys()]
    # done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    try:
        for task in asyncio.as_completed(tasks):
            result = await task
            if result:
                for t in tasks:
                    if not t.done():
                        t.cancel()
                return result
    except Exception as e:
        print("Error:", e)
    return None

"""
Runs our simulator which takes a list of domains and a list of CMP selectors to try and find the cookie banner on the page.
"""
async def simulator(domain_list, selectors):
    reject_all_presence = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        for sample_domain in domain_list:
            page = await browser.new_page()
            await page.goto(sample_domain)
            await page.mouse.move(100, 200)
            await page.mouse.wheel(0, 300)

            try:
                result = await check_selectors(page, selectors)
                    
                if result:
                    banner, selector = result
                    selector_properties = selectors[selector]
                    # buttons = banner.locator(selector_properties['element'])
                    # print(buttons)
                    # print(banner)
                    buttons = banner.get_by_role('button')
                    res = await check_for_reject_button(buttons, selector_properties)
                    print(f"Reject all button presence for domain {sample_domain}: {res}")
                    reject_all_presence.append(res)
                    await page.close()

                else:
                    print(f"No banner not found for domain {sample_domain}")
                    reject_all_presence.append(-1)
            
            except Exception as e:
                print(f"Error or timeout for domain {sample_domain}: {e}")
                reject_all_presence.append(-2)

        await browser.close()
    return reject_all_presence


async def main():
    domains_of_interest = train[train['CMP'].isin(['onetrust'])][0:20]
    domain_list = domains_of_interest['Domain'].tolist()
    domain_list = ['https://www.'+domain if domain != 'support.clever.com' else 'https://support.clever.com/' for domain in domain_list ]
    print(len(domain_list))

    with open('SELECTORS.json', 'r') as file:
        selectors = json.load(file)

    reject_all_presence = await simulator(domain_list, selectors)
    print(reject_all_presence)
    domains_of_interest['Automated_Reject_All'] = reject_all_presence
    accuracy = len(domains_of_interest[((domains_of_interest['Automated_Reject_All'] == 1) & (domains_of_interest['Reject All Option'] == True) & (domains_of_interest['Number of Interactions to Reject'] == 1)) | 
                ((domains_of_interest['Automated_Reject_All'] == 0) & (domains_of_interest['Reject All Option'] == False))])
    print(f"Total Correct Results: {accuracy}")

    # domains_of_interest.to_csv('domains_reject_all.csv', index=False)

asyncio.run(main())