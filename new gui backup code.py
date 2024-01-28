import tkinter as tk
from tkinter import ttk
import tkinter.filedialog as filedialog
import threading
import os
import PyPDF2
import fitz
import pyttsx3
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from nltk.sentiment import SentimentIntensityAnalyzer

def set_style():
    style = ttk.Style()
    style.configure('TButton', padding=6, relief="flat", background="#4CAF50", foreground="black", font=('Helvetica', 10, 'bold'))
    style.configure('TLabel', font=('Helvetica', 12, 'bold'))
    style.configure('TEntry', font=('Helvetica', 10))
    style.configure('TText', font=('Helvetica', 10))
    style.configure('TCombobox', font=('Helvetica', 10))

root = tk.Tk()
root.title("PDF Listener & Summarizer with Sentiment Analysis")
root.geometry('820x680')

set_style()

def execute_action():
    selected_action = action_var.get()
    selected_page = page_var.get()

    if selected_action == 'Listen to Page':
        threading.Thread(target=read_specific_page).start()
    elif selected_action == 'Summarize':
        threading.Thread(target=summarize_pdf).start()
    elif selected_action == 'Sentiment Analysis':
        if not selected_page:
            threading.Thread(target=perform_sentiment_analysis_whole_pdf).start()
        else:
            threading.Thread(target=perform_sentiment_analysis).start()
    else:
        display_text.delete('1.0', tk.END)
        display_text.insert(tk.END, "No action selected.")

ulabel = ttk.Label(root, text="PDF File Path:")
ulabel.grid(row=0, column=0, padx=10, pady=10, sticky="w")

page_label = ttk.Label(root, text="Enter page number:")
page_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")

action_label = ttk.Label(root, text="Select Action:")
action_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")

page_range_label = ttk.Label(root, text="Page Range:")
page_range_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")

utext = ttk.Entry(root, font=('Helvetica', 10), width=50)
utext.grid(row=0, column=1, padx=10, pady=10, sticky="w")

page_var = tk.StringVar(root)
page_entry = ttk.Entry(root, textvariable=page_var, font=('Helvetica', 10), width=50)
page_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")

action_var = tk.StringVar(root)
actions = ['Listen to Page', 'Summarize', 'Sentiment Analysis', 'No Action']
action_var.set(actions[0])
action_menu = ttk.Combobox(root, textvariable=action_var, values=actions, font=('Helvetica', 10), width=47)
action_menu.grid(row=2, column=1, padx=10, pady=10, sticky="w")

page_range_var = tk.StringVar(root)
page_range_label_display = ttk.Label(root, textvariable=page_range_var, font=('Helvetica', 10))
page_range_label_display.grid(row=3, column=1, padx=10, pady=10, sticky="w")

def open_file_dialog():
    file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    utext.delete('0', tk.END)
    utext.insert(tk.END, file_path)
    update_page_range(file_path)

open_file_button = ttk.Button(root, text="Open File", command=open_file_dialog, style='TButton')
open_file_button.grid(row=0, column=2, padx=10, pady=10)

confirm_btn = ttk.Button(root, text="Confirm Action", command=execute_action, style='TButton')
confirm_btn.grid(row=4, column=1, pady=20)

display_text = tk.Text(root, height=20, width=100, font=('Helvetica', 10))
display_text.grid(row=5, column=0, columnspan=3, padx=10, pady=10)

def read_specific_page():
    try:
        global speaker_thread, engine_speaking
        file_path = utext.get().strip()
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

def summarize_pdf():
    try:
        file_path = utext.get().strip()
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
        summary = summarizer(parser.document, 3)

        summary_text = "\n".join(str(sentence) for sentence in summary)

        display_text.delete('1.0', tk.END)
        display_text.insert(tk.END, summary_text)
    except Exception as e:
        display_text.delete('1.0', tk.END)
        display_text.insert(tk.END, f"Error summarizing the PDF: {e}")

def perform_sentiment_analysis_whole_pdf():
    try:
        file_path = utext.get().strip()
        if not os.path.exists(file_path):
            display_text.delete('1.0', tk.END)
            display_text.insert(tk.END, "File path does not exist.")
            return

        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()

        sia = SentimentIntensityAnalyzer()
        sentiment_score = sia.polarity_scores(text)

        sentiment_label = get_sentiment_label(sentiment_score['compound'])

        display_text.delete('1.0', tk.END)
        display_text.insert(tk.END, "Sentiment Analysis for the Whole PDF:\n")
        display_text.insert(tk.END, f"Sentiment: {sentiment_label}\n")
        display_text.insert(tk.END, f"  - Negative: {sentiment_score['neg']}\n")
        display_text.insert(tk.END, f"  - Neutral: {sentiment_score['neu']}\n")
        display_text.insert(tk.END, f"  - Positive: {sentiment_score['pos']}\n")
        #display_text.insert(tk.END, f"  - Compound: {sentiment_score['compound']}\n\n")

    except Exception as e:
        display_text.delete('1.0', tk.END)
        display_text.insert(tk.END, f"Error performing sentiment analysis: {e}")

def perform_sentiment_analysis():
    try:
        file_path = utext.get().strip()
        if not os.path.exists(file_path):
            display_text.delete('1.0', tk.END)
            display_text.insert(tk.END, "File path does not exist.")
            return

        doc = fitz.open(file_path)
        sentiment_results = []

        page_number = int(page_var.get())
        for current_page_number, page in enumerate(doc, start=1):
            text = page.get_text()
            sia = SentimentIntensityAnalyzer()
            sentiment_score = sia.polarity_scores(text)

            sentiment_label = get_sentiment_label(sentiment_score['compound'])

            if current_page_number == page_number:
                display_text.delete('1.0', tk.END)
                display_text.insert(tk.END, f"Sentiment Analysis for Page {page_number}:\n")
                display_text.insert(tk.END, f"Sentiment: {sentiment_label}\n")
                display_text.insert(tk.END, f"  - Negative: {sentiment_score['neg']}\n")
                display_text.insert(tk.END, f"  - Neutral: {sentiment_score['neu']}\n")
                display_text.insert(tk.END, f"  - Positive: {sentiment_score['pos']}\n")
                #display_text.insert(tk.END, f"  - Compound: {sentiment_score['compound']}\n\n")
                break

            sentiment_results.append((current_page_number, sentiment_label, sentiment_score))

    except Exception as e:
        display_text.delete('1.0', tk.END)
        display_text.insert(tk.END, f"Error performing sentiment analysis: {e}")

def get_sentiment_label(compound_score):
    if compound_score >= 0.05:
        return 'Positive'
    elif compound_score <= -0.05:
        return 'Negative'
    else:
        return 'Neutral'

def update_page_range(file_path):
    try:
        pdf_reader = PyPDF2.PdfReader(file_path)
        pages = len(pdf_reader.pages)
        page_range_var.set(f"1 - {pages}")
    except Exception as e:
        print(f"Error updating page range: {e}")

engine_speaking = False
def speak_text(text):
    global engine, engine_speaking
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
    engine_speaking = False

root.mainloop()
