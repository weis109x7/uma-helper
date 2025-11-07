import re
import json
import time
import configparser
import os
import sys

from playwright.sync_api import sync_playwright

global event_data
global uma_event_data

eventWrapperClass=""
event_data = {}
uma_event_data = {}

def get_base_path():
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller exe
        return os.path.dirname(sys.executable)
    else:
        # Running as normal python script
        return os.path.dirname(os.path.abspath(__file__))
    
def addEventToEventJson(page,id):
    global eventWrapperClass

    if not eventWrapperClass:
        container = page.locator("div[class*='eventhelper_listgrid_item__']")
        eventTypeContainer = container.locator('> div')
        chainEvent = eventTypeContainer.nth(2)
        eventWrapper = chainEvent.locator('> div').nth(0)
        eventWrapperClass = eventWrapper.get_attribute("class")

    eventWrappers = page.locator(f"div[class*='{eventWrapperClass}']")
    count = eventWrappers.count()

    # Example: get text content of each
    for i in range(count):
        wrapper = eventWrappers.nth(i)

        # Get header
        header = wrapper.locator('> div').nth(0).inner_text()
        header = header.strip() if header else "Unknown Header"
        header = re.sub(r'[^a-zA-Z]', '', header)
        # get cells
        cells = wrapper.locator('> div').nth(2)
        topBotOptions = cells.locator('> div')
        optionCount = topBotOptions.count()
        for i in range(optionCount):
            eachOption = topBotOptions.nth(i)

            eachOptionLabel = eachOption.locator('> div').nth(0).inner_text()
            eachOptionResult = eachOption.locator('> div').nth(1).inner_text()

            if header not in event_data:
                event_data[header] = {}
            event_data[header][eachOptionLabel] = eachOptionResult
    return

def addEventToUmaJson(page,id):
    eventWrappers = page.locator(f"div[class*='{eventWrapperClass}']")
    count = eventWrappers.count()

    # Example: get text content of each
    for i in range(count):
        wrapper = eventWrappers.nth(i)

        # Get header
        header = wrapper.locator('> div').nth(0).inner_text()
        header = header.strip() if header else "Unknown Header"
        header = re.sub(r'[^a-zA-Z]', '', header)
        # get cells
        cells = wrapper.locator('> div').nth(2)
        topBotOptions = cells.locator('> div')
        optionCount = topBotOptions.count()
        for i in range(optionCount):
            eachOption = topBotOptions.nth(i)

            if eachOption.locator('> div').count()>1:
                eachOptionLabel = eachOption.locator('> div').nth(0).inner_text()
                eachOptionResult = eachOption.locator('> div').nth(1).inner_text()
            else:
                continue
            if header not in uma_event_data[id]:
                uma_event_data[id][header] = {}
            uma_event_data[id][header][eachOptionLabel] = eachOptionResult
    return





def loadCfg():
    # Create parser
    config = configparser.ConfigParser()

    # Read the ini file
    config.read("config.ini")

    # Access values
    
    global cardEventsPath
    cardEventsPath = os.path.join(get_base_path(), config["app"]["cardEventsPath"]) 
    global umaEventsPath
    umaEventsPath = os.path.join(get_base_path(), config["app"]["umaEventsPath"])

    print(cardEventsPath, umaEventsPath)

def main():
    loadCfg()
    # Output dictionary

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # You can use firefox or webkit too
        page = browser.new_page()
        page.goto("https://gametora.com/umamusume/training-event-helper")

        # set settings
        page.click('[id$="settings-open"]')
        page.check("#allAtOnceCheckbox")
        page.check("#expandEventsCheckbox")
        page.check("#onlyChoicesCheckbox")
        page.click("[class*='filters_confirm_button__']")
        
        # campaign = "URA Finals"
        # set campaign
        page.click("#boxScenario")
        scenarioLocator = page.locator('[class^="tooltips_tooltip_striped__"] img[src^="/images/umamusume/scenarios/"]')
        scenarioLocator.first.wait_for(state="attached")
        scenarios = scenarioLocator.all()
        # print(scenarios)
        # scenarios[1].click()
        # page.click(f'xpath=//div[contains(@class, "tooltips_tooltip_striped__")]//div[.//span[text()="{campaign}"]]')

        # Find the parent that contains ONLY one div with img src="/images/ui/remove.png"
        only_img_parent = page.locator("div:has(> span > img[src='/images/ui/remove.png']):not(:has(div:has-text('Remove')))")
        cardClass = "div."+only_img_parent.first.get_attribute("class").replace(" ",".")
        # Select all <div> elements with the exact class
        divs = page.query_selector_all(cardClass)
        # Collect their IDs
        cardIds = [div.get_attribute("id") for div in divs]
        cardIds = [item for item in cardIds if item is not None]

        # Find the parent that contains one div with img src="/images/ui/remove.png" and remove text
        remove_text_parent = page.locator("div:has(> span > img[src='/images/ui/remove.png']):has(div:has-text('Remove'))")
        umaClass = "div."+remove_text_parent.first.get_attribute("class").replace(" ",".")
        # # Select all <div> elements with the exact class
        divs = page.query_selector_all(umaClass)
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

            addEventToEventJson(page,id)

            page.click("button:has-text('Delete')")
            page.click("button:has-text('Yes')")


        page.click("#boxSupport1")
        page.click(f'xpath=//*[@id="{id}"]')
        page.click("#boxScenario")
        for scenario in scenarios:
            scenario.click()
            addEventToEventJson(page,id)

        page.click("button:has-text('Delete')")
        page.click("button:has-text('Yes')")
        
        for id in umaIds:
            
            page.click("#boxChar")
            uma = page.locator(f'xpath=//*[@id="{id}"]')
            name = uma.locator("xpath=./div[2]").inner_text()
            uma.click()

            if id not in uma_event_data:
                uma_event_data[name] = {}

            addEventToUmaJson(page,name)

            page.click("button:has-text('Delete')")
            page.click("button:has-text('Yes')")

        # time.sleep(9999)
        browser.close()

    print(event_data)
    print(uma_event_data)

    # Save to file
    with open(cardEventsPath, "w", encoding="utf-8") as f:
        json.dump(event_data, f, indent=4)
        
    # Save to file
    with open(umaEventsPath, "w", encoding="utf-8") as f:
        json.dump(uma_event_data, f, indent=4)

if __name__ == "__main__":
    main()