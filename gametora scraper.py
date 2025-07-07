import re
import json

from playwright.sync_api import sync_playwright


# Output dictionary
event_data = {}
uma_event_data = {}


campaignEvents={"ExhilaratingWhataScoop","ATrainersKnowledge","BestFootForward"}

def addEventToEventJson(page):
    divs = page.locator("div[class*='eventhelper_ewrapper__']")
    count = divs.count()
    print(f"Found {count} matching divs")
    # Example: get text content of each
    for i in range(count):
        wrapper = divs.nth(i)

        # Get header
        header = wrapper.locator("[class*='tooltips_ttable_heading__']").text_content()
        header = header.strip() if header else "Unknown Header"
        header = re.sub(r'[^a-zA-Z]', '', header)
        # Get all left and right cells
        left_cells = wrapper.locator("div[class*='eventhelper_leftcell__']")
        right_cells = wrapper.locator("div[class*='eventhelper_ecell__']:not([class*='leftcell'])")

        left_count = left_cells.count()
        right_count = right_cells.count()

        # Prepare entry in dict
        if header in event_data:
            if header not in campaignEvents:
                print(id)
                print("DUPLICATE EVENT?????" + header)
        if header not in event_data:
            event_data[header] = {}
        for j in range(min(left_count, right_count)):
            label = left_cells.nth(j).text_content().strip()
            label = re.sub(r'[^a-zA-Z]', '', label)
            value_lines = right_cells.nth(j).locator("div").all_text_contents()
            value = "\n".join(line.strip() for line in value_lines) if value_lines else right_cells.nth(j).text_content().strip()
            event_data[header][label] = value
    return


def addEventToUmaJson(page):
    divs = page.locator("div[class*='eventhelper_ewrapper__']")
    count = divs.count()
    print(f"Found {count} matching divs")
    # Example: get text content of each
    for i in range(count):
        wrapper = divs.nth(i)

        # Get header
        header = wrapper.locator("[class*='tooltips_ttable_heading__']").text_content()
        header = header.strip() if header else "Unknown Header"
        header = re.sub(r'[^a-zA-Z]', '', header)
        # Get all left and right cells
        left_cells = wrapper.locator("div[class*='eventhelper_leftcell__']")
        right_cells = wrapper.locator("div[class*='eventhelper_ecell__']:not([class*='leftcell'])")

        left_count = left_cells.count()
        right_count = right_cells.count()

        # Prepare entry in dict
        if header in uma_event_data[id]:
            print("DUPLICATE UMA?????" + header + " id is "+id)
        if header not in uma_event_data[id]:
            uma_event_data[id][header] = {}
        for j in range(min(left_count, right_count)):
            label = left_cells.nth(j).text_content().strip()
            label = re.sub(r'[^a-zA-Z]', '', label)
            value_lines = right_cells.nth(j).locator("div").all_text_contents()
            value = "\n".join(line.strip() for line in value_lines) if value_lines else right_cells.nth(j).text_content().strip()
            uma_event_data[id][header][label] = value
    return

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # You can use firefox or webkit too
    page = browser.new_page()
    page.goto("https://gametora.com/umamusume/training-event-helper")

    # set settings
    page.click("[class*='filters_settings_button__']")
    page.check("#allAtOnceCheckbox")
    page.check("#expandEventsCheckbox")
    page.check("#onlyChoicesCheckbox")
    page.click("[class*='filters_confirm_button__']")
    
    campaign = "URA Finals"
    # set campaign
    page.click("#boxScenario")
    page.click(f'xpath=//div[contains(@class, "tooltips_tooltip_striped__")]//div[.//span[text()="{campaign}"]]')


    # Select all <div> elements with the exact class
    divs = page.query_selector_all("div.sc-919c8f5e-1.KHdsc") #prolly need to change div class

    # Collect their IDs
    cardIds = [div.get_attribute("id") for div in divs]
    cardIds = [item for item in cardIds if item is not None]

    # # Select all <div> elements with the exact class
    divs = page.query_selector_all("div.sc-8ad9342f-1.eqOYiX") #prolly need to change div class

    # Collect their IDs
    umaIds = [div.get_attribute("id") for div in divs]
    umaIds = [item for item in umaIds if item is not None]

    print("cardid")
    print(cardIds)
    print("umaid")
    print(umaIds)

    for id in cardIds:
        page.click("#boxSupport1")
        page.click(f'xpath=//*[@id="{id}"]')

        addEventToEventJson(page)

        page.click("button:has-text('Delete')")
        page.click("button:has-text('Yes')")


    for id in umaIds:
        
        page.click("#boxChar")
        page.click(f'xpath=//*[@id="{id}"]')

        if id not in uma_event_data:
            uma_event_data[id] = {}

        addEventToUmaJson(page)

        page.click("button:has-text('Delete')")
        page.click("button:has-text('Yes')")

    browser.close()

print(event_data)
print(uma_event_data)

# Save to file
with open(".\\resources\\card_events.json", "w", encoding="utf-8") as f:
    json.dump(event_data, f, indent=4)
    
# Save to file
with open(".\\resources\\uma_events.json", "w", encoding="utf-8") as f:
    json.dump(uma_event_data, f, indent=4)