import tkinter as tk
import tkinter.filedialog as filedialog
import threading
import os
import PyPDF2
import fitz  
import pyttsx3
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

root = tk.Tk()
root.title("PDF Listener & Summarizer")
root.geometry('820x680') 

def execute_action():
    selected_action = action_var.get()

    if selected_action == 'listen_page':
        threading.Thread(target=read_specific_page).start()
    elif selected_action == 'summarize':
        threading.Thread(target=summarize_pdf).start()
    else:
        display_text.delete('1.0', tk.END)
        display_text.insert(tk.END, "No action selected.")


def open_file_dialog():
    file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    utext.delete('1.0', tk.END)
    utext.insert(tk.END, file_path)

def read_specific_page():
    try:
        global speaker_thread, engine_speaking
        file_path = utext.get('1.0', "end").strip()
        if not os.path.exists(file_path):
            display_text.delete('1.0', tk.END)
            display_text.insert(tk.END, "File path does not exist.")
            return

        pdf_reader = PyPDF2.PdfReader(file_path)
        pages = len(pdf_reader.pages)

        page_number = int(page_var.get())
        if 1 <= page_number <= pages:
            page = pdf_reader.pages[page_number - 1]
            text = page.extract_text()
            if text:
                display_text.delete('1.0', tk.END)
                display_text.insert(tk.END, f"Page {page_number} Content:\n\n{text}\n\n--- Speaking ---")
                
                if engine_speaking:
                    engine.stop()
                    speaker_thread.join()
                speaker_thread = threading.Thread(target=speak_text, args=(text,))
                speaker_thread.start()
                engine_speaking = True
            else:
                display_text.delete('1.0', tk.END)
                display_text.insert(tk.END, f"No text found on page {page_number}")
        else:
            display_text.delete('1.0', tk.END)
            display_text.insert(tk.END, f"Invalid page number. Please select a number between 1 and {pages}")

    except Exception as e:
        display_text.delete('1.0', tk.END)
        display_text.insert(tk.END, f"Error: {e}")

engine_speaking=False
def speak_text(text):
    global engine, engine_speaking
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
    engine_speaking = False

def summarize_pdf():
    try:
        file_path = utext.get('1.0', "end").strip()
        if not os.path.exists(file_path):
            display_text.delete('1.0', tk.END)
            display_text.insert(tk.END, "File path does not exist.")
            return

        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()

        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summary = summarizer(parser.document, 3)  # Change '3' to desired number of sentences in summary

        summary_text = "\n".join(str(sentence) for sentence in summary)

        display_text.delete('1.0', tk.END)
        display_text.insert(tk.END, summary_text)
    except Exception as e:
        display_text.delete('1.0', tk.END)
        display_text.insert(tk.END, f"Error summarizing the PDF: {e}")

ulabel = tk.Label(root, text="PDF File Path")
ulabel.pack()

utext = tk.Text(root, height=1, width=70)
utext.pack()

open_file_button = tk.Button(root, text="Open File", command=open_file_dialog)
open_file_button.pack()

page_label = tk.Label(root, text="Enter page number:")
page_var = tk.StringVar(root)
page_entry = tk.Entry(root, textvariable=page_var)
page_label.pack()
page_entry.pack()

action_label = tk.Label(root, text="Select Action:")
action_var = tk.StringVar(root)
actions = ['listen_page', 'summarize', 'no_action']
action_var.set(actions[0])  
action_menu = tk.OptionMenu(root, action_var, *actions)
action_label.pack()
action_menu.pack()

confirm_btn = tk.Button(root, text="Confirm Action", command=execute_action)
confirm_btn.pack()

display_text = tk.Text(root, height=20, width=100)
display_text.pack()

speaker_thread=None
engine = pyttsx3.init()

root.mainloop()
