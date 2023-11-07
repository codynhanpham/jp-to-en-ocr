import asyncio
import json
from json.decoder import JSONDecodeError
from PIL import ImageGrab
import pyperclip
import os, sys
import html
from langdetect import detect
from dotenv import dotenv_values
import requests
config = dotenv_values(".env")

try:
    import websockets
except ImportError:
    print("Websockets package not found. Make sure it's installed.")

URI = config["AI_HOST_WS_URL"]
OPENAI_COMPATIBLE_URI = 'http://127.0.0.1:5000/v1/chat/completions'

from manga_ocr import MangaOcr
manga_ocr = MangaOcr()

print("\nLoading translation models...")

from argostranslate import package, translate
from sentence_transformers import SentenceTransformer
language_model = SentenceTransformer('distilbert-base-nli-mean-tokens')
import torch.nn

if config["USE_AI"] == "false":
    # Use CUDA only if not using AI, as it's better to prioritize the AI over simple OCR
    ARGOS_DEVICE_TYPE = "CUDA" # Also, comment this out if you don't have a GPU

    # In the case you really want to have CUDA for this script
    # You might have to uninstall the current torch and torchvision, then install the torch's CUDA version
    # https://pytorch.org/get-started/locally/#start-locally
    # 
    # You might also need to have the correct CUDA version installed
    # https://developer.nvidia.com/cuda-toolkit-archive

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

request = {
    'max_new_tokens': 500,
    'auto_max_new_tokens': False,
    'max_tokens_second': 0,
    'mode': 'chat-instruct',
    'character': 'Assistant',
    'regenerate': False,
    '_continue': False,
    'chat_instruct_command': 'Enter translator mode. You are a professional Japanese translator. You must do your best to translate the text provided into English as detailed and accurate as possible. You can sometimes sacrifice accuracy over natural-sounding English. Use the machine translations as a reference to improve your own. Do not come up with something entirely new yourself. If the machine translation does not make sense, say "(Cannot translate)". You must always honor the translation notes.\n\n<|prompt|>',

    'preset': 'None',
    'do_sample': True,
    'temperature': 0.65,
    'top_p': 0.2,
    'typical_p': 1,
    'epsilon_cutoff': 0,  # In units of 1e-4
    'eta_cutoff': 0,  # In units of 1e-4
    'tfs': 1,
    'top_a': 0,
    'repetition_penalty': 1.16,
    'presence_penalty': 0,
    'frequency_penalty': 0,
    'repetition_penalty_range': 0,
    'top_k': 40,
    'min_length': 0,
    'no_repeat_ngram_size': 0,
    'num_beams': 1,
    'penalty_alpha': 0,
    'length_penalty': 1,
    'early_stopping': False,
    'mirostat_mode': 0,
    'mirostat_tau': 5,
    'mirostat_eta': 0.1,
    'grammar_string': '',
    'guidance_scale': 1,
    'negative_prompt': '',

    'seed': -1,
    'add_bos_token': True,
    'truncation_length': 2048,
    'ban_eos_token': False,
    'custom_token_bans': '',
    'skip_special_tokens': True,
    'stopping_strings': []
}

async def run(user_input, history):
    data = request.copy()
    data['user_input'] = user_input
    data['history'] = history

    async with websockets.connect(URI, ping_interval=None) as websocket:
        await websocket.send(json.dumps(data))

        while True:
            incoming_data = await websocket.recv()
            incoming_data = json.loads(incoming_data)

            match incoming_data['event']:
                case 'text_stream':
                    yield incoming_data['history']
                case 'stream_end':
                    return


async def print_response_stream(user_input, history) -> str:
    cur_len = 0
    new_history = None
    async for new_history in run(user_input, history):
        cur_message = new_history['visible'][-1][1][cur_len:]
        cur_len += len(cur_message)
        print(html.unescape(cur_message), end='')
        sys.stdout.flush()  # If we don't flush, we won't see tokens in realtime.

        new_history = new_history

    return new_history


# compatible with the openai api
def openai_run(user_input, history):
    openai_base_history = []
    for i in range(len(history['internal'])):
        openai_base_history.append({"role": "user", "content": history['internal'][i][0]})
        openai_base_history.append({"role": "assistant", "content": history['internal'][i][1]})

    openai_base_history.append({"role": "user", "content": user_input})

    data = request.copy()
    data['messages'] = openai_base_history
    data['stream'] = True
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    message_collected = ""

    response = requests.post(OPENAI_COMPATIBLE_URI, headers=headers, json=data, stream=True)
    
    # Initialize an empty string to accumulate the response chunks
    chunk = ''
    for line in response.iter_lines(decode_unicode=True):
        if not line:
            continue

        chunk += line

        if not line.startswith("data: "):
            continue

        # Indicates the end of a chunk
        try:
            # Extract and parse the JSON data
            data_chunk = chunk[len("data: "):]
            data_json = json.loads(data_chunk)

            message_collected += data_json['choices'][0]['message']['content']
            print(data_json['choices'][0]['message']['content'], end='')

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
        chunk = ''  # Reset the chunk for the next iteration

    print()

    # construct the new history
    history['internal'].append([user_input, message_collected])

    return history



def passed_similarity_score(sentences: list, mode: str) -> bool:
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


allTranslators = booleanInput("\nUse online translators (need internet connection)? (y/n): ")

if allTranslators:
    import translators as ts
    import translators.server as tss

dictionary = useDictionary()

print(f'\n\nReady!\nUsing {dictionary["dictionary_file"] if (dictionary and dictionary["dictionary"]) else "no"} dictionary\nand\n{"All" if allTranslators else "Offline"} translators.')
print("\nOK! Waiting for new screen snip...")


base_history = {'internal': [], 'visible': []}
# try to use the ./base_history.json if it exists to replace the history variable
try:
    with open('ai_translate/base_history.json', 'r', encoding='utf-8') as f:
        base_history = json.load(f)
except:
    pass


def main():
    totalCharsCount = 0
    while True:
        try:
            text = newClipboardImageToText(allow_ja_text=True)

            if (text == ""):
                continue


            history = {}
            if config["ROLLING_CONTEXT"] == "true":
                # try open translationHistory.json and read it, if file doesn't exist, use the base_history instead
                try:
                    with open('translationHistory.json', 'r', encoding='utf-8') as f:
                        history = json.load(f)
                except FileNotFoundError:
                    history = base_history
            else:
                history = base_history
            

            AIInput = f"{text}\nMachine Translations:\n"
            # Count the number of characters in the text and add it to the total
            charsCount = len(text)
            totalCharsCount += charsCount
            print("ORIGINAL:     \t" +"\x1b[33m" + text + "\x1b[0m")

            # First, pre-process the text by replacing kana/terms for the actual official translations
            trans_note = "Translation Note: " # add key = value here if key exists in text, otherwise None
            used_pairs = [] # keep track of used key-value pairs
            if not dictionary or not dictionary["dictionary"]:
                trans_note += "None"
            else:
                # Keep track of which key = value pairs are used
                for key in dictionary["dictionary"]:
                    if key in text:
                        text = text.replace(key, dictionary["dictionary"][key])
                        used_pairs.append(f"{key} = {dictionary['dictionary'][key]}")
                if used_pairs:
                    trans_note += ", ".join(used_pairs)
                else:
                    trans_note += "None"


            # Then, machine translate the text
            trans00 = model0.translate(text).strip()
            AIInput += "- " + trans00 + "\n"
            if config["USE_AI"] == "false" or config["SHOW_ML"] == "true":
                print("\x1b[1m" + "TRANSLATION 0.0:  " + "\x1b[32m" + trans00 + "\x1b[0m")

            if config["USE_AI"] == "false" or config["SHOW_ML"] == "true":
                trans01 = model1.translate(text, source_lang="ja", target_lang="en", beam_size=15, max_length=250).strip()
                print("\x1b[1m" + "TRANSLATION 0.1:  " + "\x1b[32m" + trans01 + "\x1b[0m")

            # if config["USE_AI"] == "false" or config["SHOW_ML"] == "true":
            #     trans02 = model2.translate(text, source_lang="ja", target_lang="en", beam_size=15, max_length=250)
            #     print("\x1b[1m" + "TRANSLATION 0.2:  " + "\x1b[32m" + trans02 + "\x1b[0m")

            if allTranslators:
                trans1 = tss.bing(text, from_language="ja", to_language="en").strip()
                AIInput += "- " + trans1 + "\n"
                trans2 = tss.google(text, from_language="ja", to_language="en").strip()
                AIInput += "- " + trans2 + "\n"
                if config["USE_AI"] == "false" or config["SHOW_ML"] == "true":
                    print("\x1b[1m" + "TRANSLATION 1:    " + "\x1b[32m" + trans1 + "\x1b[0m")
                    print("\x1b[1m" + "TRANSLATION 2:    " + "\x1b[32m" + trans2 + "\x1b[0m")

            AIInput += trans_note


            # If AI is enabled, use the AI to translate the text
            if config["USE_AI"] == "true":
                print("\x1b[1mAI TRANSLATION: \x1b[32m", end=" ", flush=True)
                # history = asyncio.run(print_response_stream(AIInput, history)) # legacy oobabooga API: https://github.com/oobabooga/text-generation-webui/blob/6086768309f49be88fce3c0c5e7e6a7a0b3fb735/api-examples/api-example-chat-stream.py
                history = openai_run(AIInput, history)
                print("\x1b[0m\n")

                # trans1 and trans2 might not exist, so if this is the case, check and only pass the ones that exist
                passed_sim = passed_similarity_score([history['internal'][-1][1], trans00] + ([trans1] if allTranslators else []) + ([trans2] if allTranslators else []), "mean")
                    

                if not passed_sim:
                    print("\x1b[31m(Possibly bad AI result! Check the Machine Translations below.)\x1b[0m\n")

                    print("\x1b[2m")
                    print(history['internal'][-1][0])
                    print("\n\x1b[0m")

                if config["ROLLING_CONTEXT"] == "true":
                    # Use the history variable to write to translationHistory.json. Only the ["internal"] part is needed, so set the ["visible"] part to []
                    # if not passed_sim, though, pop the last item from history['internal']
                    if not passed_sim:
                        history['internal'].pop()

                    new_history = { "internal": history['internal'], "visible": [] }
                    with open('translationHistory.json', 'w', encoding='utf-8') as f:
                        json.dump(new_history, f, indent=4, ensure_ascii=False)

            # print(f"Characters translated: {charsCount}")
            # print(f"(Total: {totalCharsCount})")
            print("\n")

        except KeyboardInterrupt:
            break

    print("\n\nExiting...")
    try:
        exit(0)
    except SystemExit:
        os._exit(0)

if __name__ == "__main__":
    main()