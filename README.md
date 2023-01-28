# jp-to-en-ocr
A scuff quality-of-life manga translator, using [manga_ocr](https://github.com/kha-white/manga-ocr) and [translators](https://github.com/uliontse/translators) libraries.

## Demo

![](https://github.com/codynhanpham/jp-to-en-ocr/blob/master/jp-en_manga-ocr_demo_15s.gif?raw=true)

## Why?
- I'm ~not a weeb~
- Japanese is hard. I'm trying my best to learn this fascinating language.
- Even with [manga_ocr](https://github.com/kha-white/manga-ocr) doing the text extraction, pasting the text into Google Translate alone is already a super repetitive and tedious task.
- Google Translate is not enough. Japanese is context-heavy, and a single translator can easily mess up the translation. Outputting some additional translations helps with this, even just a tiny bit.
- You may want to add your own custom dictionary for the series you are reading. Katakana, or other made-up terms in manga and light novels can be translated quite differently from what the machine can understand. 

And because this script is literally under 90 lines of code.

## How?
0. Install Python 3.9 from the [official site](https://www.python.org/downloads/). Again, Python 3.9, as many dependencies used here does not have support for Python 3.10+ (yet).

**Open the terminal/command prompt**

1. Install [manga_ocr](https://github.com/kha-white/manga-ocr) for extracting text. It was trained on manga specifically, so idk if you are reading manga that's great, if not good luck XD
```
pip3 install manga-ocr
```
2. Download this repository for translation. Well, at least download the `main.py` file AND the `custom-dictionary` folder.
3. Take a look around if you want to. Note that you can add your own "dictionary" in the `custom-dictionary` folder.
4. Install some dependencies, including [translators](https://github.com/uliontse/translators), for this script:
```
pip3 install pyperclip translators
```
5. Pray that things work perfectly.

## Use?
1. Open the terminal/command prompt and start [manga_ocr](https://github.com/kha-white/manga-ocr). Leave it run in the background.
```
manga_ocr
```
2. Open another tab/windows of the terminal/command prompt, then move to the directory of the `main.py` file:
    - Change drive by typing the drive name, follows by the colon `d:`
    - Move to the directory by `cd <path>`, for example, `cd D:\Code-and-Stuff\jp-to-en-ocr`

3. Run
```
python main.py
```

---

4. To select the text, use your OS native way to screen snip. On Windows, that is `Ctrl+Shift+S`. You can bind that combination to a non-primary mouse button or another keyboard key for convenience.
5. After doing the screen snip, [manga_ocr](https://github.com/kha-white/manga-ocr) takes care of the character recognition, and this script does the translation.
6. You will need to wait for the translations to finish before snipping new text. If you select `Yes` to use all 4 translators, it may take a while, depending on your internet connection.
7. To exit, just close the window or spam `Ctrl+C`

## Thanks!
1. [manga_ocr](https://github.com/kha-white/manga-ocr)
2. [translators](https://github.com/uliontse/translators)
3. [pyperclip](https://github.com/asweigart/pyperclip)

## Issues
This was made for my personal, selfish use. I will try to update or patch any bug whenever I feel like it. Again, it's literally 90 lines. Suggestions are welcome, though <3
