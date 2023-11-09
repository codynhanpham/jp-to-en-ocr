from dotenv import dotenv_values
config = dotenv_values(".env")
import json
import os

HOST = config["AI_API_SERVER"]

print("\nLoading trained models...\n")

import utils
from argostranslate import package, translate
from sentence_transformers import SentenceTransformer
language_model = SentenceTransformer('distilbert-base-nli-mean-tokens')

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
# model2 = EasyNMT("m2m_100_1.2B", cache_folder= "", max_loaded_models=1) # Really big model, very slow if not on GPU, not really worth the tradeoff

# Warm up the models
model0.translate("だけど")
model1.translate("だけど", source_lang="ja", target_lang="en", beam_size=15, max_length=500)
# model2.translate("だけど", source_lang="ja", target_lang="en", beam_size=15, max_length=500)

print("\nTrained models loaded!\n")



# ----------------- Doing actual work -----------------

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
    'truncation_length': 1600, # shorter context size for faster response
    'ban_eos_token': False,
    'custom_token_bans': '',
    'skip_special_tokens': True,
    'stopping_strings': []
}

allTranslators = utils.booleanInput("\nUse online translators (need internet connection)? (y/n): ")

if allTranslators:
    import translators as ts
    import translators.server as tss

dictionary = utils.useDictionary()

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
            text = utils.newClipboardImageToText(allow_ja_text=True)

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
                history = utils.openai_run(AIInput, history, request, HOST)
                print("\x1b[0m\n")

                # trans1 and trans2 might not exist, so if this is the case, check and only pass the ones that exist
                passed_sim = utils.passed_similarity_score([history['internal'][-1][1], trans00] + ([trans1] if allTranslators else []) + ([trans2] if allTranslators else []), "mean", language_model)
                    

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