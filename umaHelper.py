import os
import re
import sys
import time
import pytesseract
import pyautogui
import cv2
import numpy as np
from rapidfuzz import fuzz
import json

def get_base_path():
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller exe
        return os.path.dirname(sys.executable)
    else:
        # Running as normal python script
        return os.path.dirname(os.path.abspath(__file__))
    

base_path = get_base_path()
uma_events_filepath = os.path.join(base_path, 'resources', 'uma_events.json')
card_events_filepath = os.path.join(base_path, 'resources', 'card_events.json')

with open(uma_events_filepath, "r", encoding="utf-8") as f:
    uma_events_data = json.load(f)
with open(card_events_filepath, "r", encoding="utf-8") as f:
    card_events_data = json.load(f)

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

pytesseract.pytesseract.tesseract_cmd = r"Tesseract-OCR\tesseract.exe"  # point to tesseract folder

threshold = 0.8
nameMatchThreshold=50

uma_id_path = os.path.join(base_path, 'resources', 'umas')
uma_template = map_filenames_to_paths(uma_id_path)


charaRegion = (205, 214, 329-205, 350-214)  # Adjust this to your desired screen area
eventTextRegion = (325, 266, 807-325, 322-266)  # Adjust this to your desired screen area

prevEventName=""
currentEventName=""
prevCharaId=""
currentCharaId=""

print(uma_template)
print(uma_events_data)
print(card_events_data)
time.sleep(5)
os.system('cls' if os.name == 'nt' else 'clear')

print("umas event helper started\n\n\n")

lines=0
while True:
    charScreenshot = pyautogui.screenshot(region=charaRegion)
    charScreenshot = np.array(charScreenshot)
    char_grey_source = cv2.cvtColor(charScreenshot, cv2.COLOR_BGR2GRAY)

    charaId=False
    for name, path in uma_template.items():
        template = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        res = cv2.matchTemplate(char_grey_source, template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        if len(loc[0]) > 0:
            currentCharaId = name
            break
        else:
            currentCharaId=""
    # print("Detected charaId:", charaId)

    eventScreenshot = pyautogui.screenshot(region=eventTextRegion)
    currentEventName = pytesseract.image_to_string(eventScreenshot).strip()
    currentEventName = re.sub(r'[^a-zA-Z]', '', currentEventName)

    # print("event name:", currentEventName)


    if ((currentEventName!=prevEventName) or (currentCharaId!=prevCharaId)):
        highscore=0
        mostLikelyEventName=""
        if currentCharaId in uma_events_data:
            for eventName, options in uma_events_data[currentCharaId].items():
                _, score = is_similar(eventName, currentEventName)
                if (score > highscore):
                    highscore=score
                    mostLikelyEventName=eventName
            clearLines(lines)
            if (highscore>nameMatchThreshold):
                print("OCR eventName: " +currentEventName)
                print("actual eventName: "+mostLikelyEventName)
                lines=2
                for key, value in uma_events_data[currentCharaId][mostLikelyEventName].items():
                    print(f"{key}:")
                    lines+=1
                    for line in value.split('\n'):
                        print(f"  - {line}")
                        lines+=1
            else:
                print("detected: "+currentEventName)
                lines=1
                pass
        else:
            for eventName, options in card_events_data.items():
                _, score = is_similar(eventName, currentEventName)
                if (score > highscore):
                    highscore=score
                    mostLikelyEventName=eventName

            clearLines(lines)
            if (highscore>nameMatchThreshold):
                print("OCR eventName: " +currentEventName)
                print("actual eventName: "+mostLikelyEventName)
                lines=2
                for key, value in card_events_data[mostLikelyEventName].items():
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
    prevCharaId=currentCharaId