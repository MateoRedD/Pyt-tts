import threading
import tkinter as tk

from smart_pdf import process_smart_pdf
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from config import load_last_output_folder, save_last_output_folder
from pdf_reader import extract_text
from table_reader import NoTableFoundError
from table_to_audio import process_table
from tts_engine import text_to_mp3

BG_COLOR = "#1e1e2e"
CARD_COLOR = "#2A2A3C"
ACCENT_COLOR = "#3C9EFF"
ACCENT_HOVER = "#6A8BEF"
TEXT_COLOR = "#E8E8F0"
MUTED_TEXT_COLOR = "#A0A0B0"
FONT_TITLE = ("Segoe UI", 22, "bold")
FONT_SUBTILE = ("Segoe UI", 13, "bold")
FONT_BUTTON = ("Segoe UI", 13, "bold")
FONT_LABEL = ("Segoe UI", 10)


class PytTTSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("pyt.tts")
        self.geometry("640x680")
        self.configure(bg=BG_COLOR)
        self.resizable(False, False)

        self.container = tk.Frame(self, bg=BG_COLOR)
        self.container.pack(fill="both", expand=True)

        self.show_home_screen()

    def _clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def show_home_screen(self):
        self._clear_container()
        HomeScreen(self.container, self)

    def show_text_screen(self):
        self._clear_container()
        TextToAudioScreen(self.container, self)

    def show_pdf_screen(self):
        self._clear_container()
        PdfToAudioScreen(self.container, self)

    def show_smart_pdf_screen(self):
        self._clear_container()
        SmartPdfScreen(self.container, self)

    def show_table_screen(self):
        self._clear_container()
        TableToAudioScreen(self.container, self)
    
class HomeScreen(tk.Frame):
    def __init__(self, parent, app: PytTTSApp):
        super().__init__(parent, bg=BG_COLOR)
        self.pack(fill="both", expand=True)

        tk.Label(
            self, text="pyt-tts", font=FONT_TITLE, bg=BG_COLOR, fg=TEXT_COLOR
        ).pack(pady=(60, 5))
        tk.Label(
            self,
            text="Turn text, PDFs, or tables into MP3 audio",
            font=FONT_SUBTILE,
            bg=BG_COLOR,
            fg=MUTED_TEXT_COLOR,
        ).pack(pady=(0, 50))

        self._make_big_button("Text to Audio", app.show_text_screen).pack(pady=12)
        self._make_big_button("PDF to Audio", app.show_text_screen).pack(pady=12)
        self._make_big_button("Table to Audio", app.show_table_screen).pack(pady=12)
        self._make_big_button("Smart PDF (text + tablas)", app.show_smart_pdf_screen).pack(pady=12)

    def _make_big_button(self, text, command):
        btn = tk.Button(
            self,
            text=text,
            font=FONT_BUTTON,
            bg=ACCENT_COLOR,
            fg="white",
            activebackground=ACCENT_HOVER,
            activeforeground="white",
            relief="flat",
            width=22,
            height=2,
            cursor="hand2",
            command=command,
        )
        return btn

class BaseConverterScreen(tk.Frame):
    def __init__(self, parent, app: PytTTSApp, title: str, default_filename: str = ""):
        super().__init__(parent, bg=BG_COLOR)
        self.pack(fill="both", expand=True)
        self.app = app
        self.output_folder = load_last_output_folder(default=str(Path.home()))
        self.filename_var = tk.StringVar(value=default_filename)

        top_bar = tk.Frame(self, bg=BG_COLOR)
        top_bar.pack(fill="x", padx=20, pady=(20, 0))
        tk.Button(
            top_bar,
            text="< Back",
            font=FONT_LABEL,
            bg=BG_COLOR,
            fg=MUTED_TEXT_COLOR,
            relief="flat",
            cursor="hand2",
            command=app.show_home_screen,
        ).pack(side="left")

        tk.Label(
            self, text=title, font=FONT_TITLE, bg=BG_COLOR, fg=TEXT_COLOR
        ).pack(pady=(10, 20))

        self.body = tk.Frame(self, bg=BG_COLOR)
        self.body.pack(fill="both", expand=True, padx=30)

        filename_row = tk.Frame(self, bg=BG_COLOR)
        filename_row.pack(pady=(15, 5))
        tk.Label(
            filename_row, text="Output file name:", font=FONT_LABEL,
            bg=BG_COLOR, fg=MUTED_TEXT_COLOR,
        ).pack(side="left", padx=(0, 8))
        tk.Entry(
            filename_row, textvariable=self.filename_var, font=FONT_LABEL,
            bg=CARD_COLOR, fg=TEXT_COLOR, insertbackground=TEXT_COLOR,
            relief="flat", width=25,
        ).pack(side="left")
        tk.Label(
            filename_row, text=".mp3", font=FONT_LABEL,
            bg=BG_COLOR, fg=MUTED_TEXT_COLOR,
        ).pack(side="left", padx=(4, 0))

        self.folder_label = tk.Label(
            self,
            text=f"Output folder: {self.output_folder}",
            font=FONT_LABEL,
            bg=BG_COLOR,
            fg=MUTED_TEXT_COLOR,
            wraplength=560,
        )
        self.folder_label.pack(pady=(5, 5))

        tk.Button(
            self,
            text="Choose output folder",
            font=FONT_LABEL,
            bg=BG_COLOR,
            fg=TEXT_COLOR,
            relief="flat",
            cursor="hand2",
            command=self._choose_output_folder,
        ).pack(pady=(0, 10))

        self.generate_btn = tk.Button(
            self,
            text="Generate MP3",
            font=FONT_BUTTON,
            bg=ACCENT_COLOR,
            fg="white",
            activebackground=ACCENT_HOVER,
            activeforeground="white",
            relief="flat",
            width=20,
            height=2,
            cursor="hand2",
            command=self._on_generate,
        )
        self.generate_btn.pack(pady=(10, 10))

        self.progress_bar = ttk.Progressbar(
            self, mode="indeterminate", length = 300
        )
        self.progress_bar.pack(pady=(0, 10))

        self.status_label = tk.Label(
            self, text="", font=FONT_LABEL, bg=BG_COLOR, fg=MUTED_TEXT_COLOR
        )
        self.status_label.pack(pady=(5, 10))

    def _choose_output_folder(self):
        folder = filedialog.askdirectory(initialdir=self.output_folder)
        if folder:
            self.output_folder = folder
            self.folder_label.config(text=f"Output folder: {self.output_folder}")
            save_last_output_folder(folder)

    def _get_output_filename(self, fallback: str) -> str:
        name = self.filename_var.get().strip()
        if not name:
            name = fallback
        if name.lower().endswith(".mp3"):
            name = name[:-4]
        return name

    def _set_status(self, text, color=MUTED_TEXT_COLOR):
        self.status_label.config(text=text, fg=color)

    def _run_in_thread(self, target):
        self.generate_btn.config(state="disabled")
        self._set_status("Generating audio... this may take a moment.")
        self.progress_bar.start(12)
        thread = threading.Thread(target=target, daemon=True)
        thread.start()

    def _on_succes(self, output_path):
        self.progress_bar.stop()
        self.generate_btn.config(state="normal")
        self._set_status(f"Done! Saved to: {output_path}", color="#8fd47a")

    def _on_error(self, message):
        self.progress_bar.stop()
        self.generate_btn.config(state="normal")
        self._set_status(f"Error: {message}", color="#E06C75")

    def _on_generate(self):
        raise NotImplementedError


class TextToAudioScreen(BaseConverterScreen):
    def __init__(self, parent, app: PytTTSApp):
        super().__init__(parent, app, "Text to Audio", default_filename="text_output")

        tk.Button(
            self.body,
            text="Load .txt file",
            font=FONT_LABEL,
            bg=CARD_COLOR,
            fg=TEXT_COLOR,
            relief="flat",
            cursor="hand2",
            command=self._load_txt_file,
        ).pack(anchor="w", pady=(0, 8))

        self.text_box = tk.Text(
            self.body,
            font=FONT_LABEL,
            bg=CARD_COLOR,
            fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR,
            relief="flat",
            wrap="word",
            height=10,
        )
        self.text_box.pack(fill="both", expand=True)

    def _load_txt_file(self):
        file_path = filedialog.askopenfile(
            filetypes=[("Text files", "*.txt")]
        )
        if not file_path:
            return
        try:
            content = Path(file_path).read_text(encoding="utf-8")
            self.text_box.delete("1.0", "end")
            self.text_box.insert("1.0", content)
        except Exception as e:
            messagebox.showerror("pyt-tts", f"Could not read file: {e}")

    def _on_generate(self):
        text = self.text_box.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("pyt-tts", "Please enter or load some text first")
            return

        filename = self._get_output_filename(fallback="text_output")
        output_path = str(Path(self.output_folder) / f"{filename}.mp3")
        self._run_in_thread(lambda: self._generate(text, output_path))

    def _generate(self, text, output_path):
        try:
            text_to_mp3(text, output_path)
            self.after(0, self._on_succes, output_path)
        except Exception as e:
            self.after(0, self._on_error, str(e))


class PdfToAudioScreen(BaseConverterScreen):
    def __init__(self, parent, app: PytTTSApp):
        super().__init__(parent, app, "PDF to audio")
        self.pdf_path = None

        tk.Button(
            self.body,
            text="Choose PDF file",
            font=FONT_LABEL,
            bg=CARD_COLOR,
            fg=TEXT_COLOR,
            relief="flat",
            cursor="hand2",
            command=self._choose_pdf,
        ).pack(anchor="w", pady=(0, 8))

        self.pdf_label = tk.Label(
            self.body,
            text="No PDF selected.",
            font=FONT_LABEL,
            bg=BG_COLOR,
            fg=MUTED_TEXT_COLOR,
            wraplength=560,
            justify="left",
        )
        self.pdf_label.pack(anchor="w")

    def _choose_pdf(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            self.pdf_path = file_path
            self.pdf_label.config(text=f"Selected: {file_path}")
            if not self.filename_var.get().strip():
                self.filename_var.set(Path(file_path).stem)

    def _on_generate(self):
        if not self.pdf_path:
            messagebox.showwarning("pyt-tts", "Please choose a PDF file first.")
            return

        filename = self._get_output_filename(fallback=Path(self.pdf_path).stem)
        output_path = str(Path(self.output_folder) / f"{filename}.mp3")
        self._run_in_thread(lambda: self._generate(output_path))

    def _generate(self, output_path):
        try:
            text = extract_text(self.pdf_path)
            if not text or not text.strip():
                self.after(
                    0, self._on_error,
                    "Could not extract text from PDF (scanned/image-based PDF?)"
                )
                return
            text_to_mp3(text, output_path)
            self.after(0, self._on_succes, output_path)
        except Exception as e:
            self.after(0, self._on_error, str(e))


class TableToAudioScreen(BaseConverterScreen):
    def __init__(self, parent, app:PytTTSApp):
        super().__init__(parent, app, "Table to Audio")
        self.table_path = None

        tk.Button(
            self.body,
            text="Choose table file (.csv, .xlsx, .pdf)",
            font=FONT_LABEL,
            bg=CARD_COLOR,
            fg=TEXT_COLOR,
            relief="flat",
            cursor="hand2",
            command=self._choose_table_file,
        ).pack(anchor="w", pady=(0, 8))

        self.table_label = tk.Label(
            self.body,
            text="No file selected.",
            font=FONT_LABEL,
            bg=BG_COLOR,
            fg=MUTED_TEXT_COLOR,
            wraplength=560,
            justify="left",
        )
        self.table_label.pack(anchor="w")

    def _choose_table_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Table files", "*.csv *.xlsx *.pdf")]
        )
        if file_path:
            self.table_path = file_path
            self.table_label.config(text=f"Selected: {file_path}")
            if not self.filename_var.get().strip():
                self.filename_var.set(Path(file_path).stem)

    def _on_generate(self):
        if not self.table_path:
            messagebox.showwarning("pyt-tts", "Please choose a table file first")
            return
        filename = self._get_output_filename(fallback=Path(self.table_path).stem)
        self._run_in_thread(lambda: self._generate(filename))

    def _generate(self, filename):
        try:
            mp3_path, png_path = process_table(
                self.table_path, self.output_folder, filename
            )
            self.after(0, self._on_table_success, mp3_path, png_path)
        except NoTableFoundError:
            self.after(
                0, self._on_error,
                "No table could be found in that file (it may be an image-based table)"
            )
        except Exception as e:
            self.after(0, self._on_error, str(e))

    def _on_table_success(self, mp3_path, png_path):
        self.progress_bar.stop()
        self.generate_btn.config(state="normal")
        self._set_status(
            f"Done! Audio: {mp3_path} | Chart: {png_path}", color="#8FD47A"
        )


class SmartPdfScreen(BaseConverterScreen):
    def __init__(self, parent, app: PytTTSApp):
        super().__init__(parent, app, "Smart PDF")
        self.pdf_path = None
        tk.Button(
            self.body,
            text="Choose PDF file",
            font=FONT_LABEL,
            bg=CARD_COLOR,
            fg=TEXT_COLOR,
            relief="flat",
            cursor="hand2",
            command=self._choose_pdf,
        ).pack(anchor="w", pady=(0, 8))

        self.pdf_label = tk.Label(
            self.body,
            text="No PDF selected",
            font=FONT_LABEL,
            bg=BG_COLOR,
            fg=MUTED_TEXT_COLOR,
            wraplength=560,
            justify="left",
        )
        self.pdf_label.pack(anchor="w", pady=(0, 8))

        tk.Label(
            self.body,
            text="Detects text, tables, and image-based tables automatically. "
                 "Image tables are read using Gemini (requires an internet connection "
                 "and a GEMINI_API_KEY in your .env file).",
            font=FONT_LABEL,
            bg=BG_COLOR,
            fg=MUTED_TEXT_COLOR,
            wraplength=560,
            justify="left",
        ).pack(anchor="w")
    def _choose_pdf(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            self.pdf_path = file_path
            self.pdf_label.config(text=f"Selected: {file_path}")
            if not self.filename_var.get().strip():
                self.filename_var.set(Path(file_path).stem)

    def _on_generate(self):
        if not self.pdf_path:
            messagebox.showwarning("pyt-tts", "Please choose a PDF file first.")
            return
        filename = self._get_output_filename(fallback=Path(self.pdf_path).stem)
        self._run_in_thread(lambda: self._generate(filename))

    def _generate(self, filename):
        try:
            result = process_smart_pdf(self.pdf_path, self.output_folder, filename)
            self.after(0, self._on_smart_pdf_success, result)
        except Exception as e:
            self.after(0, self._on_error, str(e))

    def _on_smart_pdf_success(self, result):
        self.progress_bar.stop()
        self.generate_btn.config(state="normal")
        chart_count = len(result["chart_paths"])
        chart_note = f" | {chart_count} chart(s) generated" if chart_count else ""
        self._set_status(
            f"Done! Audio: {result['mp3_path']}{chart_note}", color="#8FD47A"
        )
if __name__ == "__main__":
    app = PytTTSApp()
    app.mainloop()