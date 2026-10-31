import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
import html
import re

from pypinyin import lazy_pinyin, Style
from pykakasi import kakasi
from hangul_romanize import Transliter
from hangul_romanize.rule import academic
from unidecode import unidecode


API_URL = "https://api.mymemory.translated.net/get"

LANGUAGES = {
    "English": "en",
    "Urdu": "ur",
    "Chinese": "zh-CN",
    "Japanese": "ja",
    "Korean": "ko",
    "Arabic": "ar",
    "Hindi": "hi",
    "French": "fr",
    "German": "de",
    "Spanish": "es",
    "Italian": "it",
    "Turkish": "tr",
    "Portuguese": "pt",
    "Russian": "ru"
}

BG = "#111827"
CARD = "#1F2937"
PURPLE = "#8B7CFF"
WHITE = "#F9FAFB"
GRAY = "#AAB3C5"
GREEN = "#34D399"

root = tk.Tk()
root.title("LINGUA | Language Translator")
root.geometry("1050x760")
root.minsize(850, 680)
root.configure(bg=BG)

style = ttk.Style()
style.theme_use("clam")
style.configure(
    "TCombobox",
    padding=9,
    fieldbackground=CARD,
    background=CARD,
    foreground=WHITE
)

# Header

tk.Label(
    root,
    text="LINGUA",
    font=("Segoe UI", 30, "bold"),
    bg=BG,
    fg=PURPLE
).pack(pady=(22, 0))

tk.Label(
    root,
    text="Break Language Barriers.",
    font=("Segoe UI", 15, "bold"),
    bg=BG,
    fg=WHITE
).pack(pady=5)

tk.Label(
    root,
    text="Translate naturally. Understand every word.",
    bg=BG,
    fg=GRAY
).pack(pady=(0, 20))

# Language selection

top = tk.Frame(root, bg=BG)
top.pack(pady=10)

source = tk.StringVar(value="English")
target = tk.StringVar(value="Chinese")

source_box = ttk.Combobox(
    top,
    textvariable=source,
    values=list(LANGUAGES),
    state="readonly",
    width=19
)
source_box.pack(side="left", padx=12)

swap_btn = tk.Button(
    top,
    text="⇄",
    font=("Segoe UI", 18, "bold"),
    bg=BG,
    fg=PURPLE,
    relief="flat",
    cursor="hand2"
)
swap_btn.pack(side="left", padx=15)

target_box = ttk.Combobox(
    top,
    textvariable=target,
    values=list(LANGUAGES),
    state="readonly",
    width=19
)
target_box.pack(side="left", padx=12)

# Text areas

container = tk.Frame(root, bg=BG)
container.pack(fill="both", expand=True, padx=30, pady=15)

def create_card(parent, title, height):
    frame = tk.Frame(parent, bg=CARD, padx=15, pady=12)

    tk.Label(
        frame,
        text=title,
        font=("Segoe UI", 12, "bold"),
        bg=CARD,
        fg=WHITE
    ).pack(anchor="w", pady=(0, 8))

    box = tk.Text(
        frame,
        height=height,
        font=("Segoe UI", 12),
        bg=CARD,
        fg=WHITE,
        insertbackground=WHITE,
        relief="flat",
        wrap="word",
        padx=8,
        pady=8
    )
    box.pack(fill="both", expand=True)

    return frame, box


left, input_box = create_card(
    container, "Enter Your Text", 7
)
left.pack(side="left", fill="both", expand=True, padx=(0, 8))

right, output_box = create_card(
    container, "Translated Text", 7
)
right.pack(side="left", fill="both", expand=True, padx=(8, 0))

output_box.config(state="disabled")

# Romanization area

roman_card = tk.Frame(
    root,
    bg=CARD,
    padx=18,
    pady=12
)
roman_card.pack(fill="x", padx=30, pady=8)

tk.Label(
    roman_card,
    text="ROMANIZED TEXT / PRONUNCIATION",
    font=("Segoe UI", 11, "bold"),
    bg=CARD,
    fg=PURPLE
).pack(anchor="w")

roman_box = tk.Text(
    roman_card,
    height=3,
    font=("Segoe UI", 12),
    bg=CARD,
    fg=WHITE,
    insertbackground=WHITE,
    relief="flat",
    wrap="word"
)
roman_box.pack(fill="x", pady=8)

roman_box.config(state="disabled")

# Status

status = tk.Label(
    root,
    text="Ready to translate",
    bg=BG,
    fg=GRAY
)
status.pack(pady=8)

# Character counter

counter = tk.Label(
    root,
    text="0 characters",
    bg=BG,
    fg=GRAY
)
counter.pack()

def update_counter(event=None):
    count = len(input_box.get("1.0", "end-1c"))
    counter.config(text=f"{count} characters")

input_box.bind("<KeyRelease>", update_counter)

# Romanization

def romanize(text, language):

    if language == "Chinese":
        if re.search(r"[\u4e00-\u9fff]", text):
            return " ".join(
                lazy_pinyin(text, style=Style.TONE)
            )

    elif language == "Japanese":
        if re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", text):
            converter = kakasi()
            return "".join(
                item["hepburn"]
                for item in converter.convert(text)
            )

    elif language == "Korean":
        if re.search(r"[\uac00-\ud7af]", text):
            return Transliter(academic).translit(text)

    elif language in ("Urdu", "Arabic", "Hindi"):
        return unidecode(text)

    return text


# Translation

busy = False

def translate():

    global busy

    if busy:
        return

    text = input_box.get("1.0", "end-1c").strip()

    src = source.get()
    dst = target.get()

    if not text:
        messagebox.showwarning(
            "Empty Text",
            "Please enter text first."
        )
        return

    if src == dst:
        messagebox.showwarning(
            "Language Selection",
            "Please select different languages."
        )
        return

    if len(text.encode("utf-8")) > 450:
        messagebox.showwarning(
            "Text Limit",
            "Please enter text within 450 UTF-8 bytes."
        )
        return

    busy = True

    translate_btn.config(state="disabled")
    swap_btn.config(state="disabled")
    source_box.config(state="disabled")
    target_box.config(state="disabled")
    input_box.config(state="disabled")

    status.config(
        text="Translating...",
        fg=PURPLE
    )

    threading.Thread(
        target=translation_worker,
        args=(text, src, dst),
        daemon=True
    ).start()


def translation_worker(text, src, dst):

    try:

        response = requests.get(
            API_URL,
            params={
                "q": text,
                "langpair": (
                    f"{LANGUAGES[src]}|{LANGUAGES[dst]}"
                )
            },
            timeout=25
        )

        response.raise_for_status()

        data = response.json()

        if data.get("responseStatus") != 200:
            raise Exception(
                data.get(
                    "responseDetails",
                    "Translation service unavailable."
                )
            )

        translated = html.unescape(
            data["responseData"]["translatedText"]
        )

        if not translated.strip():
            raise Exception("Empty translation received.")

        roman = romanize(translated, dst)

        root.after(
            0,
            lambda: show_result(translated, roman)
        )

    except Exception as error:

        root.after(
            0,
            lambda: show_error(str(error))
        )


def show_result(translated, roman):

    global busy

    output_box.config(state="normal")
    output_box.delete("1.0", "end")
    output_box.insert("1.0", translated)
    output_box.config(state="disabled")

    roman_box.config(state="normal")
    roman_box.delete("1.0", "end")
    roman_box.insert("1.0", roman)
    roman_box.config(state="disabled")

    finish_translation(
        "Translation completed successfully!",
        GREEN
    )


def show_error(error):

    finish_translation("Translation failed.", "red")

    messagebox.showerror(
        "Translation Error",
        error
    )


def finish_translation(message, color):

    global busy

    busy = False

    translate_btn.config(state="normal")
    swap_btn.config(state="normal")
    source_box.config(state="readonly")
    target_box.config(state="readonly")
    input_box.config(state="normal")

    status.config(
        text=message,
        fg=color
    )


# Swap languages

def swap_languages():

    if busy:
        return

    old_source = source.get()
    old_target = target.get()

    source.set(old_target)
    target.set(old_source)

    old_input = input_box.get("1.0", "end-1c")
    old_output = output_box.get("1.0", "end-1c")

    input_box.delete("1.0", "end")
    input_box.insert("1.0", old_output)

    output_box.config(state="normal")
    output_box.delete("1.0", "end")
    output_box.insert("1.0", old_input)
    output_box.config(state="disabled")

    roman_box.config(state="normal")
    roman_box.delete("1.0", "end")
    roman_box.config(state="disabled")

    update_counter()

    status.config(
        text="Languages swapped. Translate again.",
        fg=GRAY
    )


swap_btn.config(command=swap_languages)

# Copy functions

def copy_text(box):

    text = box.get("1.0", "end-1c").strip()

    if not text:
        messagebox.showwarning(
            "Empty Result",
            "Nothing to copy."
        )
        return

    root.clipboard_clear()
    root.clipboard_append(text)

    status.config(
        text="Copied successfully!",
        fg=GREEN
    )


# Clear

def clear_all():

    if busy:
        return

    input_box.delete("1.0", "end")

    output_box.config(state="normal")
    output_box.delete("1.0", "end")
    output_box.config(state="disabled")

    roman_box.config(state="normal")
    roman_box.delete("1.0", "end")
    roman_box.config(state="disabled")

    update_counter()

    status.config(
        text="Ready to translate",
        fg=GRAY
    )


# Buttons

buttons = tk.Frame(root, bg=BG)
buttons.pack(pady=15)

translate_btn = tk.Button(
    buttons,
    text="Translate Text",
    command=translate,
    bg=PURPLE,
    fg=WHITE,
    font=("Segoe UI", 11, "bold"),
    padx=25,
    pady=10,
    relief="flat",
    cursor="hand2"
)
translate_btn.pack(side="left", padx=6)

tk.Button(
    buttons,
    text="Copy Translation",
    command=lambda: copy_text(output_box),
    bg=CARD,
    fg=WHITE,
    padx=15,
    pady=10,
    relief="flat",
    cursor="hand2"
).pack(side="left", padx=6)

tk.Button(
    buttons,
    text="Copy Romanized",
    command=lambda: copy_text(roman_box),
    bg=CARD,
    fg=WHITE,
    padx=15,
    pady=10,
    relief="flat",
    cursor="hand2"
).pack(side="left", padx=6)

tk.Button(
    buttons,
    text="Clear All",
    command=clear_all,
    bg=CARD,
    fg=WHITE,
    padx=15,
    pady=10,
    relief="flat",
    cursor="hand2"
).pack(side="left", padx=6)

tk.Label(
    root,
    text="Powered by MyMemory Translation API",
    bg=BG,
    fg=GRAY,
    font=("Segoe UI", 9)
).pack(pady=(0, 15))

root.mainloop()