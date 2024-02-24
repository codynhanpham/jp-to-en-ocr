from dotenv import dotenv_values
config = dotenv_values(".env")

import json
from json.decoder import JSONDecodeError
from PIL import ImageGrab
import pyperclip
import os
import requests
import sseclient
from langdetect import detect
import torch.nn
from manga_ocr import MangaOcr
manga_ocr = MangaOcr()

# compatible with the openai api
def openai_run(user_input, history, params, HOST):
    OPENAI_COMPATIBLE_URI = HOST.rstrip("/") + "/v1/chat/completions"

    openai_base_history = []
    for i in range(len(history['internal'])):
        openai_base_history.append({"role": "user", "content": history['internal'][i][0]})
        openai_base_history.append({"role": "assistant", "content": history['internal'][i][1]})

    openai_base_history.append({"role": "user", "content": user_input})

    data = params.copy()
    data['messages'] = openai_base_history
    data['stream'] = True
    headers = { "Content-Type": "application/json" }
    message_collected = ""

    response = requests.post(OPENAI_COMPATIBLE_URI, headers=headers, json=data, verify=False, stream=True)
    client = sseclient.SSEClient(response)

    for event in client.events():
        try:
            payload = json.loads(event.data)
            # chunk = payload['choices'][0]['message']['content'] # does not seems to work anymore...
            chunk = payload['choices'][0]['delta']['content']
            message_collected += chunk
            print(chunk, end='')

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")

    # construct the new history
    history['internal'].append([user_input, message_collected])

    return history


def passed_similarity_score(sentences: list, mode: str, language_model) -> bool:
    threshold = 0.785
    sentence_embeddings = language_model.encode(sentences)
    cos = torch.nn.CosineSimilarity(dim=0, eps=1e-6)
    b = torch.from_numpy(sentence_embeddings)
    max_similarity = max([cos(b[0], b[i]) for i in range(1, len(b))])
    mean_similarity = sum([cos(b[0], b[i]) for i in range(1, len(b))]) / (len(b) - 1)

    if mode == "max":
        print(f"Similarity (max): {max_similarity.item()}")
        return max_similarity.item() > threshold
    elif mode == "mean":
        print(f"Similarity (mean): {mean_similarity.item()}")
        return mean_similarity.item() > threshold
    
    return False


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
    return text.strip()


def useDictionary(dictionary_file = None):
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
        dictionary_file = dictionaryList[0]
        dictionary = None
        with open(path + "/custom-dictionary" + "/" + dictionary_file, encoding="utf-8") as f:
            if f == None or f == "":
                print("Invalid dictionary file. Skipped.")
                return None
            try:
                dictionary = json.load(f)
            except JSONDecodeError:
                print("Invalid JSON file. Skipped.")
                dictionary = None
    else:
        while True:
            try:
                dictionary_file = dictionaryList[int(input("Choose dictionary: "))-1]
                break
            except ValueError:
                print("Invalid input. Please enter a number.")
                continue
            except IndexError:
                print("Invalid input. Please enter a number from the list.")
                continue

    dictionary = None
    with open(path + "/custom-dictionary" + "/" + dictionary_file, encoding="utf-8") as f:
        if f == None or f == "":
            print("Invalid dictionary file. Skipped.")
            return None
        try:
            dictionary = json.load(f)
        except JSONDecodeError:
            print("Invalid JSON file. Skipped.")
            dictionary = None
    
    return {
        "dictionary_file": dictionary_file,
        "dictionary": dictionary
    }