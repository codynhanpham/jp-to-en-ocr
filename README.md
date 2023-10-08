# jp-to-en-ocr
A scuff quality-of-life manga translator, using [manga_ocr](https://github.com/kha-white/manga-ocr), [argostranslate](https://github.com/argosopentech/argos-translate), and [translators](https://github.com/uliontse/translators) libraries.

## Demo

![](jp-en_manga-ocr_demo_15s.gif)

## Why?
- I'm ~not a weeb~
- Japanese is hard. I'm trying my best to learn this fascinating language.
- Even with [manga_ocr](https://github.com/kha-white/manga-ocr) doing the text extraction, pasting the text into Google Translate alone is already a super repetitive and tedious task.
- Google Translate is not enough. Japanese is context-heavy, and a single translator can easily mess up the translation. Outputting some additional translations helps with this, even just a tiny bit.
- You may want to add your own custom dictionary for the series you are reading. Katakana, or other made-up terms in manga and light novels can be translated quite differently from what the machine can understand. 

And because this script is literally under 160 lines of code.

## Shiny! ~
Why read a bunch of different machine translations when you can let AI do it for you?

Well, AI is not all that great yet, but if you just want to read some manga, this would improve your immersion somewhat ~

**YES! THAT'S RIGHT! This script can now use AI to translate your manga!** (See [step 5](#5-optional-install-oobaboogatext-generation-webui-for-ai-assisted-translations)). It will do all of the machine translations, and feed them into the AI model as references. The AI model will then generate a new translation based on these. More or less, it's combining the best of the translations into a coherent one.

And if you really want to live on the edge, you can even enable rolling context as well! Which will use the previous translations as references for the next translation.

## How?

***Note: I have only tested this code on a Windows machine with NVIDIA GPU. In theory, things should work the same on Mac and Linux.***

</br>

### 0. Install Python from the [official site](https://www.python.org/downloads/)
It has been tested to work on Python versions 3.9, 3.10, and 3.11.

</br>

***Then, Open the Terminal/Command Prompt in your desired location***

---
### 1. Download/Clone this repository
```
git clone https://github.com/codynhanpham/jp-to-en-ocr.git
```
**Also,** download and extract the ***content*** of `offline_models.zip` in the [releases section](https://github.com/codynhanpham/jp-to-en-ocr/releases/tag/offline-models-v0.1.0) into the same folder as the `main.py` file (the `Extract Here` option).

</br>

### 2. Start a virtual environment

Just so it does not mess with your other projects on your system.

#### *On Windows*

It is as simple as running the `venv-terminal.bat` file. You can also do it manually by running the following commands:
```bat
python -m venv venv
.\venv\Scripts\activate
```

#### *On Mac/Linux*

Open the terminal in the same folder as the `main.py` file (aka. `cd jp-to-en-ocr`), and run:
```bash
. venv-terminal.sh
```
Or, manually:
```bash
python3 -m venv venv
source venv/bin/activate
```

</br>

#### *From now on,*

You can just run the `venv-terminal.bat` file, or the `. venv-terminal.sh` command as above to start the virtual environment's terminal. **The instructions below will assume that you are in the virtual environment.**

</br>

### 3. Start with installing PyTorch

Here: https://pytorch.org/get-started/locally/#start-locally

>*If you don't have an NVIDIA GPU, you can skip this step.* Later on, the script will use the CPU version of PyTorch.

In any case, the PyTorch installation command should look *something* like this:
```bash
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```
Note that you do not need the `torchaudio` library.

#### *Futhermore,*

*If you come here **after** all of the installations because the script did not utilize CUDA but used the CPU instead...*

You might need to install the CUDA Toolkit from NVIDIA: https://developer.nvidia.com/cuda-toolkit-archive

Moreover, the script deliberately turns off CUDA if you are using AI-assisted translations (see [step 5](#5-optional-install-oobaboogatext-generation-webui-for-ai-assisted-translations)). This is because most of your VRAM will be used for loading the AI model, which is much more intensive than just doing OCR. If you want to use CUDA regardless, you can edit the `main.py` file manually.

</br>

### 4. Install the required libraries

In your virtual environment, run:
```bash
pip3 install -r requirements.txt
```

***In some cases, the installation on Windows may fail at the `EasyNMT` library, somewhere around `fasttext` or `sentencepiece`. This is a [known issue](https://github.com/UKPLab/EasyNMT/issues/3) with the `EasyNMT` library.***

To solve this, simply open the `requirements.txt` file, and delete the (last) `EasyNMT==2.0.2` line, then run the command above again.

Afterward, you can install the `EasyNMT` library manually by running:
```bash
pip3 install --no-deps EasyNMT==2.0.2
```

</br>

### 5. (Optional) Install [oobabooga/text-generation-webui](https://github.com/oobabooga/text-generation-webui) for AI-assisted translations

You can skip this step if you do not want to use this feature. ([Jump to next step](#6-pray-and-enjoy))

The repo [oobabooga/text-generation-webui](https://github.com/oobabooga/text-generation-webui) offers a simple one-click installer. Follow the instruction on their repo to install the web UI.

After that, launch the web UI, and go to the `Model` tab and download this following model: [TheBloke/airoboros-l2-7B-gpt4-m2.0-GPTQ](https://huggingface.co/TheBloke/airoboros-l2-7B-gpt4-m2.0-GPTQ). This is one of the best 7B models, which would fit into 8 GB of VRAM.

You can simply paste in the name of the model into the `Download model or LoRA` field:
```txt
TheBloke/airoboros-l2-7B-gpt4-m2.0-GPTQ
```

After the model is downloaded, you can update the `CMD-FLAGS.txt` file in the `text-generation-webui` folder to use the model you just downloaded, as well as opting in for the api extension. Copy this line into the `CMD-FLAGS.txt` file:
```txt
--model TheBloke_airoboros-l2-7B-gpt4-m2.0-GPTQ --model_type llama --loader exllama_hf --listen-port 7860 --extensions api
```

**Back to this repo's folder**

To enable AI translation, update the `.env` file with the correct URL for the webui websocket and HTTP server. Also, change the `USE_AI` flag to `True`:
```txt
AI_HOST_WS_URL="ws://127.0.0.1:5005/api/v1/stream" # or whatever the URL is
AI_HOST_HTTP_URL="http://127.0.0.1:5000/api/v1" # or whatever the URL is
USE_AI="true"
```

</br>

### 6. Pray and enjoy?

#### *On Windows*

Simply double-click and run the start script: `start_ocr.bat` on Windows. You can also start the virtual environment manually and run:
```bash
python main.py
```

#### *On Mac/Linux*

Run the `start_ocr.sh` quick script in your terminal like this:
```bash
. start_ocr.sh
```
Or, manually:
```bash
source venv/bin/activate
python3 main.py
```

</br>

#### The first time you run the script,

It will download the Optical Character Recognition (OCR) model, as well as 3 different offline translation models. This may take a while, depending on your internet connection. This only happens once.

</br>

## Use?

### 1. Start up the script

Exactly as described in the `How?` section above [@ step 6](#6-pray-and-enjoy).


### 2. Select a few options

As you are being prompted.

- First, you have the option to use online translators. This includes Google, Bing, and [Reverso](https://www.reverso.net/text-translation). Of course, if you are offline, you should select `No` here.

- Next, you can have an option to use a "custom" dictionary. Since katakana and character names are often translated differently from what is written, you can add your own dictionary to replace the translations. Take a quick look at the `/custom-dictionary/` folder and create your own `.json` file.

</br>

***Note:***

There are 3 offline translation models that will automatically be downloaded when you run the script for the first time. The offline translation models are quite fast and reliable (connection-wise), though they are not as accurate as the online ones. They also require more memory (especially the `m2m_100_1.2b` model (model2, translation 0.2)). If you are running this on a low-end machine, you may want to edit the `main.py` file to remove some or all of the offline models.


</br>

### *It's happening!*

</br>

### 3. To select the text

Use your OS native way to screen snip. On Windows, that is `Windows+Shift+S`. You can bind that combination to a non-primary mouse button or another keyboard key for convenience.

The script will automatically detect the image in your clipboard, run the OCR, and translate it. The clipboard will be cleared after the translation is done. You might want to turn off auto-save screen snips in the Snipping Tools app settings.


### 4. You will need to wait...

For the translations to finish before snipping new text. If you select `Yes` to use all translators, it may take a while, depending on your machine specs and internet connection.

Anything you select, while it's translating, will be ignored.

### 5. To exit, spam `Ctrl+C`

Or just close the terminal window.

</br>

## Thanks!
1. [manga_ocr](https://github.com/kha-white/manga-ocr)
2. [argostranslate](https://github.com/argosopentech/argos-translate)
3. [translators](https://github.com/uliontse/translators)
4. [EasyNMT](https://github.com/UKPLab/EasyNMT)
5. [pyperclip](https://github.com/asweigart/pyperclip)

## Issues
This was made for my personal, selfish use. I will try to update or patch any bug whenever I feel like it. Again, it's literally 160 lines. Suggestions are welcome, though <3
