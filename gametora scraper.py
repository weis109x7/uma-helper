import re
import json
import time
import configparser
import os
import sys

from playwright.sync_api import sync_playwright

global event_data
global uma_event_data
global campaignEvents
event_data = {}
uma_event_data = {}
campaignEvents={"ExhilaratingWhataScoop","ATrainersKnowledge","BestFootForward"}

def get_base_path():
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller exe
        return os.path.dirname(sys.executable)
    else:
        # Running as normal python script
        return os.path.dirname(os.path.abspath(__file__))
    
def addEventToEventJson(page,id):
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

def addEventToUmaJson(page,id):
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
            print("DUPLICATE UMA EVENT????" + header + " id is "+id)
        if header not in uma_event_data[id]:
            uma_event_data[id][header] = {}
        for j in range(min(left_count, right_count)):
            label = left_cells.nth(j).text_content().strip()
            label = re.sub(r'[^a-zA-Z]', '', label)
            value_lines = right_cells.nth(j).locator("div").all_text_contents()
            value = "\n".join(line.strip() for line in value_lines) if value_lines else right_cells.nth(j).text_content().strip()
            uma_event_data[id][header][label] = value
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
        page.click("[class*='filters_settings_button__']")
        page.check("#allAtOnceCheckbox")
        page.check("#expandEventsCheckbox")
        page.check("#onlyChoicesCheckbox")
        page.click("[class*='filters_confirm_button__']")
        
        campaign = "URA Finals"
        # set campaign
        page.click("#boxScenario")
        page.click(f'xpath=//div[contains(@class, "tooltips_tooltip_striped__")]//div[.//span[text()="{campaign}"]]')

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