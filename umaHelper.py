import configparser
import os
import re
import sys
import time
import pytesseract
import pyautogui
from rapidfuzz import fuzz
import json
import questionary

def get_base_path():
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller exe
        return os.path.dirname(sys.executable)
    else:
        # Running as normal python script
        return os.path.dirname(os.path.abspath(__file__))

def clearLines(lines):
    for _ in range(lines):
        sys.stdout.write("\033[F")  # Move cursor up
        sys.stdout.write("\033[K")  # Clear line

def map_filenames_to_paths(folder_path):
    file_dict = {}
    for filename in os.listdir(folder_path):
        full_path = os.path.join(folder_path, filename)
        if os.path.isfile(full_path):
            key, _ = os.path.splitext(filename)
            file_dict[key] = full_path
    return file_dict

def is_similar(a, b, threshold=0):
    score = fuzz.ratio(a, b)  # Score is 0–100
    return score >= threshold, score

def main():
    # Create parser
    config = configparser.ConfigParser()
    # Read the ini file
    config.read("config.ini")
    # Access values
    card_events_filepath = os.path.join(get_base_path(), config["app"]["cardEventsPath"]) 
    uma_events_filepath = os.path.join(get_base_path(), config["app"]["umaEventsPath"])
    ocrPath = os.path.join(get_base_path(), config["app"]["ocrPath"])

    with open(uma_events_filepath, "r", encoding="utf-8") as f:
        uma_events_data = json.load(f)
    with open(card_events_filepath, "r", encoding="utf-8") as f:
        card_events_data = json.load(f)
        
    pytesseract.pytesseract.tesseract_cmd = ocrPath+"/tesseract.exe"  # point to tesseract folder

    nameMatchThreshold=50 #match when event name is similar

    print(uma_events_data)
    print(card_events_data)
    time.sleep(1)
    os.system('cls' if os.name == 'nt' else 'clear')

    print("umas event helper started")
    
    selected_uma = ""
    choices = list(uma_events_data.keys())
    while (selected_uma not in choices):
        selected_uma = questionary.autocomplete("Select uma:",choices=choices).ask()

    try:
        # Attempt to read coordinates from INI
        x1 = config['app'].getint('x1')
        y1 = config['app'].getint('y1')
        x2 = config['app'].getint('x2')
        y2 = config['app'].getint('y2')
       
        if None in (x1,y1,x2,y2):
            raise ValueError("Coordinate is None")
    except (configparser.NoOptionError, configparser.NoSectionError, ValueError):
        # If any value is missing or invalid, ask user
        print("Coordinates not found or invalid, asking for input...")

        print("Move your mouse to the TOP-LEFT corner and press Enter...")
        input()
        x1, y1 = pyautogui.position()

        print("Move your mouse to the BOTTOM-RIGHT corner and press Enter...")
        input()
        x2, y2 = pyautogui.position()

        # Save the coordinates back to the INI
        if not config.has_section('app'):
            config.add_section('app')
        config.set('app', 'x1', str(x1))
        config.set('app', 'y1', str(y1))
        config.set('app', 'x2', str(x2))
        config.set('app', 'y2', str(y2))

        with open("config.ini", 'w') as f:
            config.write(f)
        print("Coordinates saved to INI.")

    eventTextRegion = (x1, y1, x2 - x1, y2 - y1)

    combined_events_data = uma_events_data[selected_uma] | card_events_data

    lines=0
    prevEventName=""
    currentEventName=""

    os.system('cls' if os.name == 'nt' else 'clear')
    print("training:", selected_uma)

    while True:

        eventScreenshot = pyautogui.screenshot(region=eventTextRegion)
        currentEventName = pytesseract.image_to_string(eventScreenshot).strip()
        currentEventName = re.sub(r'[^a-zA-Z]', '', currentEventName)

        if (currentEventName!=prevEventName):
            highscore=0
            mostLikelyEventName=""
            for eventName, _ in combined_events_data.items():
                _, score = is_similar(eventName, currentEventName)
                if (score > highscore):
                    highscore=score
                    mostLikelyEventName=eventName

            clearLines(lines)
            if (highscore>nameMatchThreshold):
                print("OCR eventName: " +currentEventName)
                print("actual eventName: "+mostLikelyEventName)
                lines=2
                for key, value in combined_events_data[mostLikelyEventName].items():
                    print(f"{key}:")
                    lines+=1
                    for line in value.split('\n'):
                        print(f"  - {line}")
                        lines+=1
            else:
                print("detected: "+currentEventName)
                lines=1
                pass
        prevEventName=currentEventName


if __name__ == "__main__":
    main()