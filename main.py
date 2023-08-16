import asyncio
import json
from json.decoder import JSONDecodeError
from PIL import ImageGrab
import pyperclip
import os, sys
from langdetect import detect
from dotenv import dotenv_values
config = dotenv_values(".env")

from ai_translate.ai_translate import ai_translate_stream, format_prompt

from manga_ocr import MangaOcr
manga_ocr = MangaOcr()

from argostranslate import package, translate
print("\nLoading translation models...")
# ARGOS_DEVICE_TYPE="CUDA" # Comment this out if you don't have a GPU
package.install_from_path("translate-ja_en-1_1.argosmodel")
installed_languages = translate.get_installed_languages()
# for lang in installed_languages:
#     print(lang)
model0 = installed_languages[1].get_translation(installed_languages[0])

from easynmt import EasyNMT
model1 = EasyNMT("opus-mt", cache_folder= "", max_loaded_models=1)
# model2 = EasyNMT("m2m_100_1.2B", cache_folder= "", max_loaded_models=1)

# Warm up the models
model0.translate("だけど")
model1.translate("だけど", source_lang="ja", target_lang="en", beam_size=15, max_length=250)
# model2.translate("だけど", source_lang="ja", target_lang="en", beam_size=15, max_length=250)

print("Offline models loaded!")

def booleanInput(prompt):
    while True:
        try:
            return {"true": True, "false": False, "yes": True, "y": True, "no": False, "n": False}[input(prompt).lower()]
        except KeyError:
            print('Invalid input. Please enter "yes" or "no".')
            continue

def newClipboardImageToText(allow_ja_text = False):
    text = ""
    while True:
        try:
            img = ImageGrab.grabclipboard()
            if img:
                break
            elif detect(pyperclip.paste()) == "ja" and allow_ja_text:
                text = pyperclip.paste()
                break
        except KeyboardInterrupt:
            try:
                exit(0)
            except SystemExit:
                os._exit(0)
        except:
            pass # No image in clipboard
            
    if not text:
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

    with open(path + "/custom-dictionary" + "/" + dictionary, encoding="utf-8") as f:
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

print(f'\n\nReady!\nUsing {dictionary if dictionary else "no"} dictionary\n\nand\n{"All" if allTranslators else "Offline"} translators.')
print("\nOK! Waiting for new screen snip...")


def main():
    f = open('ai_translate/translationHistoryBase.txt', 'r', encoding="utf8")
    base_prompt = f.read()
    f.close()
    f = open('ai_translate/system.txt', 'r', encoding="utf8")
    system = f.read()
    f.close()

    totalCharsCount = 0
    # Without AI
    while True:
        try:
            text = newClipboardImageToText(allow_ja_text=True)

            if (text != ""):
                AIInput = f"USER: Japanese: {text}\nMachine Translations:\n"
                # Count the number of characters in the text and add it to the total
                charsCount = len(text)
                totalCharsCount += charsCount
                print("ORIGINAL:     \t" +"\x1b[33m" + text + "\x1b[0m")

                # First, pre-process the text by replacing kana/terms for the actual official translations
                trans_note = "Translation Note: " # add key = value here if key exists in text, otherwise None
                used_pairs = [] # keep track of used key-value pairs
                if not dictionary:
                    trans_note += "None"
                else:
                    # Keep track of which key = value pairs are used
                    for key in dictionary:
                        if key in text:
                            text = text.replace(key, dictionary[key])
                            used_pairs.append(f"{key} = {dictionary[key]}")
                    if used_pairs:
                        trans_note += ", ".join(used_pairs)
                    else:
                        trans_note += "None"

                # Then, machine translate the text
                
                trans00 = model0.translate(text)
                AIInput += "- " + trans00 + "\n"
                if config["USE_AI"] == "false" or config["SHOW_ML"] == "true":
                    print("\x1b[1m" + "TRANSLATION 0.0:  " + "\x1b[32m" + trans00 + "\x1b[0m")

                if config["USE_AI"] == "false" or config["SHOW_ML"] == "true":
                    trans01 = model1.translate(text, source_lang="ja", target_lang="en", beam_size=15, max_length=250)
                    print("\x1b[1m" + "TRANSLATION 0.1:  " + "\x1b[32m" + trans01 + "\x1b[0m")

                # if config["USE_AI"] == "false" or config["SHOW_ML"] == "true":
                #     trans02 = model2.translate(text, source_lang="ja", target_lang="en", beam_size=15, max_length=250)
                #     print("\x1b[1m" + "TRANSLATION 0.2:  " + "\x1b[32m" + trans02 + "\x1b[0m")

                if allTranslators:
                    trans1 = tss.bing(text, from_language="ja", to_language="en")
                    AIInput += "- " + trans1 + "\n"
                    trans2 = tss.google(text, from_language="ja", to_language="en")
                    AIInput += "- " + trans2 + "\n"
                    if config["USE_AI"] == "false" or config["SHOW_ML"] == "true":
                        print("\x1b[1m" + "TRANSLATION 1:    " + "\x1b[32m" + trans1 + "\x1b[0m")
                        print("\x1b[1m" + "TRANSLATION 2:    " + "\x1b[32m" + trans2 + "\x1b[0m")

                AIInput += trans_note + "\nASSISTANT: English: "

                # If AI is enabled, use the AI to translate the text
                if config["USE_AI"] == "true":
                    prompt_f = format_prompt(AIInput, base_prompt, system)
                    
                    # Write and keep overwriting the prompt to the file latest_prompt.txt
                    with open("latest_prompt.txt", "w", encoding="utf-8") as f:
                        f.write(prompt_f["prompt"])

                    print("\x1b[1mAI TRANSLATION: \x1b[32m", end=" ", flush=True)
                    response = asyncio.run(ai_translate_stream(prompt_f["prompt"]))
                    print("\x1b[0m\n")

                    # Check if response["response_full"] is empty, if so, use the the last ML translation as the log
                    if response["response_full"] == "":
                        response["response_full"] = response["machine_translations"][-1]

                    # base_prompt = prompt_f["base_prompt"] + response["response_full"]


                # print(f"Characters translated: {charsCount}")
                # print(f"(Total: {totalCharsCount})")
                print("")

        except KeyboardInterrupt:
            break

    print("\n\nExiting...")
    try:
        exit(0)
    except SystemExit:
        os._exit(0)

if __name__ == "__main__":
    main()