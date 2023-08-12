print("\nOCR required manga_ocr (https://github.com/kha-white/manga-ocr) installed and run in the background.")

import json
from json.decoder import JSONDecodeError
from PIL import ImageGrab
import pyperclip
import os

from manga_ocr import MangaOcr
manga_ocr = MangaOcr()

from argostranslate import package, translate
print("\nLoading translation models...")
ARGOS_DEVICE_TYPE="cuda"
package.install_from_path('translate-ja_en-1_1.argosmodel')
installed_languages = translate.get_installed_languages()
# for lang in installed_languages:
#     print(lang)
model0 = installed_languages[1].get_translation(installed_languages[0])

from easynmt import EasyNMT
model1 = EasyNMT('opus-mt', cache_folder= "", max_loaded_models=1)
model2 = EasyNMT('m2m_100_1.2B', cache_folder= "", max_loaded_models=1)

# Warm up the models
model0.translate("だけど")
model1.translate("だけど", source_lang='ja', target_lang='en', beam_size=15, max_length=250)
model2.translate("だけど", source_lang='ja', target_lang='en', beam_size=15, max_length=250)

print("Offline models loaded!")

def booleanInput(prompt):
    while True:
        try:
            return {"true": True, "false": False, "yes": True, "y": True, "no": False, "n": False}[input(prompt).lower()]
        except KeyError:
            print("Invalid input. Please enter 'yes' or 'no'.")
            continue

def newClipboardImageToText():
    while True:
        try:
            img = ImageGrab.grabclipboard()
            if img:
                break
        except:
            pass
    text = manga_ocr(img)
    pyperclip.copy("")
    return text

def useDictionary(dictionary = None):
    useDictionary = booleanInput("\nUse custom dictionary? (y/n): ")
    if useDictionary == False:
        return None
    
    path = os.getcwd()
    dictionaryList = os.listdir(path + "/custom-dictionary")
    dictionaryList = [f for f in dictionaryList if os.path.isfile(path + "/custom-dictionary" + "/" + f)]

    if len(dictionaryList) == 0:
        print("\nNo dictionaries found. Skipped.")
        return None

    print("\nAvailable dictionaries:")
    for i in range(len(dictionaryList)):
        print(f"[{i+1}] {dictionaryList[i]}")

    if len(dictionaryList) == 1:
        dictionary = dictionaryList[0]
        print(f"\nUsing dictionary: {dictionary}")
    else:
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

    with open(path + "/custom-dictionary" + "/" + dictionary, encoding='utf-8') as f:
        if f == None or f == "":
            print("Invalid dictionary file. Skipped.")
            return None
        try:
            dictionary = json.load(f)
        except JSONDecodeError:
            print("Invalid JSON file. Skipped.")
            dictionary = None
    
    return dictionary

allTranslators = booleanInput("\nUse online translators (slower)? (y/n): ")

if allTranslators:
    import translators as ts
    import translators.server as tss

dictionary = useDictionary()

print(f"\n\nReady! Using {dictionary if dictionary else 'no'} dictionary and {'all' if allTranslators else 'offline'} translators.")
print("Waiting for new text to be copied to clipboard...")

totalCharsCount = 0
while True:
    text = newClipboardImageToText()
    # Count the number of characters in the text and add it to the total
    charsCount = len(text)
    totalCharsCount += charsCount

    if (text != ""):
        print("ORIGINAL:     \t" +"\x1b[33m" + text + "\x1b[0m")

        # First, pre-process the text by replacing kana/terms for the actual official translations
        if dictionary:
            for key in dictionary:
                text = text.replace(key, dictionary[key])

        # Then, translate the text
        
        trans00 = model0.translate(text)
        print("\x1b[1m" + "TRANSLATION 0.0:  " + "\x1b[32m" + trans00 + "\x1b[0m")

        trans01 = model1.translate(text, source_lang='ja', target_lang='en', beam_size=15, max_length=250)
        print("\x1b[1m" + "TRANSLATION 0.1:  " + "\x1b[32m" + trans01 + "\x1b[0m")

        trans02 = model2.translate(text, source_lang='ja', target_lang='en', beam_size=15, max_length=250)
        print("\x1b[1m" + "TRANSLATION 0.2:  " + "\x1b[32m" + trans02 + "\x1b[0m")

        if allTranslators:
            trans1 = tss.bing(text, from_language='ja', to_language='en')
            trans2 = tss.google(text, from_language='ja', to_language='en')
            print("\x1b[1m" + "TRANSLATION 1:    " + "\x1b[32m" + trans1 + "\x1b[0m")
            print("\x1b[1m" + "TRANSLATION 2:    " + "\x1b[32m" + trans2 + "\x1b[0m")

            trans3 = tss.reverso(text, from_language='ja', to_language='en')
            print("\x1b[1m" + "TRANSLATION 3:    " + "\x1b[32m" + trans3 + "\x1b[0m")
            # trans4 = html.unescape(tss.deepl(text, from_language='ja', to_language='en'))
            # print("\x1b[1m" + "TRANSLATION 4:    " + "\x1b[32m" + trans4 + "\x1b[0m")

        print(f"Characters translated: {charsCount}")
        print(f"(Total: {totalCharsCount})")
        print("")