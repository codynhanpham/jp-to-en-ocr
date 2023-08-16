import asyncio
import json
import sys
import json
from dotenv import dotenv_values
config = dotenv_values(".env")

try:
    import websockets
except ImportError:
    print("Websockets package not found. Make sure it's installed.")

async def run(context):
    # Note: the selected defaults change from time to time.
    request = {
        'prompt': context,
    }
    options = open('ai_translate/configs.json')
    options = json.load(options)
    request.update(options)

    async with websockets.connect(config["AI_HOST_WS_URL"], ping_interval=None) as websocket:
        await websocket.send(json.dumps(request))

        while True:
            incoming_data = await websocket.recv()
            incoming_data = json.loads(incoming_data)

            match incoming_data['event']:
                case 'text_stream':
                    yield incoming_data['text']
                case 'stream_end':
                    return


async def ai_translate_stream(prompt):
    response_full = ""
    machine_translations = []
    async for response in run(prompt):
        print(response.rstrip(), end='')
        sys.stdout.flush()  # If we don't flush, we won't see tokens in realtime.
        response_full += response

    # if there is no AI output, trim for the last turn at "Machine Translations:", remove anything after "Translation Note:" so that the output is just the Machine Translations.
    last_turn_split = prompt.split("Machine Translations:")[-1]
    last_turn_split = last_turn_split.split("Translation Note:")[0]
    machine_translations = last_turn_split.split("\n- ")
    machine_translations.pop(0)

    response_full = response_full.strip()
    # print(len(response_full))
    if len(response_full) <= 1 and not response_full.isalnum():
        response_full = ""
        print(machine_translations[-1])
    return {
        "response_full": response_full,
        "machine_translations": machine_translations
    }


def format_prompt(last_turn, base_prompt, system):
    # may change in the future, not sure yet...

    # add the last turn to the base prompt
    prompt = base_prompt +"\n<!eop>\n" + last_turn

    prompt_length = 700
    # split by <!eop> into turns. Check the if the total word count of all turns is greater than 1650, if so, remove the turns from top until it is less than 1650
    turns = prompt.split("<!eop>")
    total_word_count = 0
    for turn in turns:
        total_word_count += len(turn.split(" "))
    while total_word_count > prompt_length:
        turns.pop(0)
        total_word_count = 0
        for turn in turns:
            total_word_count += len(turn.split(" "))
    prompt = "<!eop>".join(turns)

    # save the base prompt for the next turn
    base_prompt = prompt

    # prompt = prompt.replace("\nUSER: ", " USER: ")
    # prompt = prompt.replace("\nASSISTANT: ", " ASSISTANT: ")
    # replace "\n<!eop>" with "" to make the turns into simple paragraphs
    prompt = prompt.replace("\n<!eop>", "\n")
    prompt = system + "" + prompt

    return {
        "prompt": prompt,
        "base_prompt": base_prompt
    }