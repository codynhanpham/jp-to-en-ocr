print("\nOCR required manga_ocr (https://github.com/kha-white/manga-ocr) installed and run in the background.")

import pyperclip
import translators as ts
import translators.server as tss
import json
from json.decoder import JSONDecodeError
import html
import os

def booleanInput(prompt):
    while True:
        try:
            return {"true": True, "false": False, "yes": True, "y": True, "no": False, "n": False}[input(prompt).lower()]
        except KeyError:
            print("Invalid input. Please enter 'yes' or 'no'.")
            continue

dictionary = None
useDictionary = booleanInput("\n\nUse custom dictionary? (y/n): ")

if useDictionary:
    path = os.getcwd()
    dictionaryList = os.listdir(path + "/custom-dictionary")
    dictionaryList = [f for f in dictionaryList if os.path.isfile(path + "/custom-dictionary" + "/" + f)]

    if len(dictionaryList) == 0:
        print("\nNo dictionaries found. Skipped.")
    else:
        print("\nAvailable dictionaries:")
        # List of dictionaries, numbered from [1]
        for i in range(len(dictionaryList)):
            print(f"[{i+1}] {dictionaryList[i]}")

        # If there is only one dictionary, use it
        if len(dictionaryList) == 1:
            dictionary = dictionaryList[0]
            print(f"\nUsing dictionary: {dictionary}")
        else:
            # If there are multiple dictionaries, ask the user to choose one
            while True:
                try:
                    dictionary = dictionaryList[int(input("Choose dictionary: "))-1]
                    break
                except ValueError:
                    print("Invalid input. Please enter a number.")
                    continue
                except IndexError:
                    print("Invalid input. Please enter a number from the list.")
                    continue

        # Load the dictionary
        with open(path + "/custom-dictionary" + "/" + dictionary, encoding='utf-8') as f:
            try:
                Dictionary = json.load(f)
            except JSONDecodeError:
                print("Invalid JSON file. Skipped.")
                Dictionary = None

allTranslators = booleanInput("\nUse all 4 translators (slower)? (y/n): ")

print(f"\n\nReady! Using {dictionary if dictionary else 'no'} dictionary and {'4' if allTranslators else '2'} translators.")
print("Waiting for new text to be copied to clipboard...")
while True:
    text = pyperclip.waitForNewPaste()

    if (text != ""):
        print("ORIGINAL:     \t" +"\x1b[33m" + text + "\x1b[0m")

        # First, pre-process the text by replacing katakana/terms for the actual official translations
        if Dictionary:
            for key in Dictionary:
                text = text.replace(key, Dictionary[key])

        # Then, translate the text
        trans1 = tss.bing(text, from_language='ja', to_language='en')
        trans2 = tss.google(text, from_language='ja', to_language='en')
        print("\x1b[1m" + "TRANSLATION 1:\t" + "\x1b[32m" + trans1 + "\x1b[0m")
        print("\x1b[1m" + "TRANSLATION 2:\t" + "\x1b[32m" + trans2 + "\x1b[0m")

        if allTranslators:
            trans3 = tss.reverso(text, from_language='ja', to_language='en')
            print("\x1b[1m" + "TRANSLATION 3:\t" + "\x1b[32m" + trans3 + "\x1b[0m")
            trans4 = html.unescape(tss.alibaba(text, from_language='ja', to_language='en'))
            print("\x1b[1m" + "TRANSLATION 4:\t" + "\x1b[32m" + trans4 + "\x1b[0m")

        print("")