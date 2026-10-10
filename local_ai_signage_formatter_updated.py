"""
Local AI Signage & Translation Formatter
- Desktop GUI using Python's built-in Tkinter
- Uses a local Ollama model for translation (no cloud API, no database)
- Exports editable SVG signage files and plain-text copies
"""


import json
import os
import re
import unicodedata
import threading
import urllib.error
import urllib.request
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


APP_NAME = "Local AI Signage & Translation Formatter"
OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen2.5:7b"


LANGUAGES = {
    "Japanese": "Japanese",
    "Mandarin Chinese (Simplified)": "Simplified Chinese (Mandarin)",
    "Samoan": "Samoan",
    "Tongan": "Tongan",
    "Spanish": "Spanish",
    "Korean": "Korean",
    "French": "French",
    "English (original)": "English (do not translate; preserve the wording)",
}


def xml_escape(value):
    return (value.replace("&", "&amp;").replace("<", "&lt;")
                 .replace(">", "&gt;").replace('"', "&quot;")
                 .replace("'", "&apos;"))

def _char_display_width(char):
    """Approximate visual width in columns for common Unicode scripts."""
    category = unicodedata.category(char)
    if category in ("Mn", "Me", "Cf"):
        return 0

    east_asian = unicodedata.east_asian_width(char)
    if east_asian in ("W", "F"):
        return 2

    # Emoji and many symbols occupy roughly two character cells in browsers.
    if category.startswith("S"):
        return 2
    return 1


def wrap_text(text, max_width):
    """Wrap text by approximate display width, supporting Latin, CJK, and other scripts."""
    output = []

    for paragraph in text.splitlines() or [""]:
        if not paragraph.strip():
            output.append("")
            continue

        # If spaces are present, preserve word boundaries where possible.
        words = paragraph.split()
        if not words:
            output.append("")
            continue

        line = ""
        line_width = 0

        for word in words:
            word_width = sum(_char_display_width(ch) for ch in word)
            space_width = 1 if line else 0

            if line and line_width + space_width + word_width <= max_width:
                line += " " + word
                line_width += space_width + word_width
                continue

            if line:
                output.append(line)
                line = ""
                line_width = 0

            # Split oversized words by visual width. This handles Japanese,
            # Chinese, Korean, long URLs, and long words without spaces.
            chunk = ""
            chunk_width = 0
            for char in word:
                char_width = _char_display_width(char)
                if chunk and chunk_width + char_width > max_width:
                    output.append(chunk)
                    chunk = ""
                    chunk_width = 0
                chunk += char
                chunk_width += char_width

            if chunk:
                line = chunk
                line_width = chunk_width

        if line:
            output.append(line)

    return output or [""]


def translate_with_ollama(text, language, model, context):
    if language == "English (original)":
        return text.strip()
    
    prompt = f"""You are a careful professional translator preparing public-facing visitor signage.
            Translate the source text into {LANGUAGES[language]}.
            Requirements:
            - Preserve the meaning, names, dates, times, prices, phone numbers, and safety instructions exactly.
            - Use natural, polite wording suitable for a public sign.
            - Do not add explanations, notes, quotation marks, or alternative translations.
            - If wording is ambiguous, choose the safest faithful translation.
            - Return only the translated sign text.
            Optional context from the staff member: {context.strip() or "No extra context provided."}
            Source text:
            {text.strip()}
    """ 

    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1}
    }).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            data = json.loads(response.read().decode("utf-8"))
        result = data.get("response", "").strip()
        if not result:
            raise RuntimeError("The local model returned an empty translation.")
        return result

    except urllib.error.URLError as exc:
        raise RuntimeError(
            "Could not reach Ollama at http://localhost:11434. "
            "Install/start Ollama, download a model, then try again. "
            f"Details: {exc}"
        )


def make_svg(title, body, language, width, height, font_size):
    # The exported SVG opens as a screen-friendly canvas with the sign centered.
    canvas_width, canvas_height = 1280, 720
    sign_width, sign_height = 440, 560
    x = (canvas_width - sign_width) / 2
    y = (canvas_height - sign_height) / 2
    margin = 28

    # Keep the text readable inside the smaller sign.
    body_font_size = min(max(14, int(font_size * 0.65)), 22)
    title_size = min(max(20, int(body_font_size * 1.35)), 30)
    inner_width = sign_width - 2 * margin

    # Convert the available pixel width into approximate display columns.
    # Full-width scripts (Japanese, Chinese, Korean) count as two columns;
    # Latin letters and most other narrow characters count as one.
    body_columns = max(8, int(inner_width / max(body_font_size * 0.55, 1)))
    title_columns = max(8, int(inner_width / max(title_size * 0.55, 1)))

    body_lines = wrap_text(body, body_columns)
    title_lines = wrap_text(title, title_columns) if title else []

    title_line_height = int(title_size * 1.3)
    body_line_height = int(body_font_size * 1.5)
    title_block_height = len(title_lines) * title_line_height
    body_block_height = len(body_lines) * body_line_height
    gap = 24 if title_lines else 0
    total_text_height = title_block_height + gap + body_block_height
    text_y = y + (sign_height - total_text_height) / 2

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="100vw" height="100vh" viewBox="0 0 {canvas_width} {canvas_height}" preserveAspectRatio="xMidYMid meet">',
        '<rect width="100%" height="100%" fill="#f3f4f6"/>',
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{sign_width}" height="{sign_height}" rx="12" fill="#ffffff" stroke="#222222" stroke-width="3"/>',
    ]

    if title_lines:
        ty = text_y + title_size
        for line in title_lines:
            svg.append(
                f'<text x="{canvas_width/2:.1f}" y="{ty:.1f}" '
                f'text-anchor="middle" font-family="Noto Sans, Noto Sans CJK JP, '
                f'Noto Sans CJK SC, sans-serif" font-size="{title_size}" '
                f'font-weight="700" fill="#111111">{xml_escape(line)}</text>'
            )
            ty += title_line_height
        text_y += title_block_height + gap

    for line in body_lines:
        svg.append(
            f'<text x="{canvas_width/2:.1f}" y="{text_y + body_font_size:.1f}" '
            f'text-anchor="middle" font-family="Noto Sans, Noto Sans CJK JP, '
            f'Noto Sans CJK SC, sans-serif" font-size="{body_font_size}" '
            f'fill="#111111">{xml_escape(line)}</text>'
        )
        text_y += body_line_height

    svg.append(
        f'<text x="{canvas_width/2:.1f}" y="{y + sign_height - 18:.1f}" '
        f'text-anchor="middle" font-family="Noto Sans, sans-serif" '
        f'font-size="12" fill="#666666">{xml_escape(language)}</text>'
    )
    svg.append('</svg>')
    return "\\n".join(svg)


class SignageApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("920x760")
        self.root.minsize(760, 620)
        self.output_dir = os.path.join(os.path.expanduser("~"), "LocalAISignage")
        self._build_ui()

    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=16)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text=APP_NAME, font=("TkDefaultFont", 17, "bold")).pack(anchor="w")
        ttk.Label(
            outer,
            text="Translate visitor notices with a local AI model and export print-ready SVG files. Your text stays on this computer.",
            wraplength=850
        ).pack(anchor="w", pady=(4, 12))

        source_frame = ttk.LabelFrame(outer, text="1. Sign content", padding=10)
        source_frame.pack(fill="both", expand=True)
        ttk.Label(source_frame, text="Heading (optional)").pack(anchor="w")
        self.title_text = tk.StringVar(value="PLEASE NOTE")
        ttk.Entry(source_frame, textvariable=self.title_text).pack(fill="x", pady=(2, 8))
        ttk.Label(source_frame, text="Notice / message").pack(anchor="w")
        self.body = tk.Text(source_frame, height=7, wrap="word", font=("TkDefaultFont", 11))
        self.body.pack(fill="both", expand=True, pady=(2, 8))
        self.body.insert("1.0", "Please keep this area clean. Thank you for your cooperation.")
        ttk.Label(source_frame, text="Context for the translator (optional, e.g. location, tone, audience)").pack(anchor="w")
        self.context = tk.StringVar()
        ttk.Entry(source_frame, textvariable=self.context).pack(fill="x", pady=(2, 0))

        settings = ttk.LabelFrame(outer, text="2. Translation and layout", padding=10)
        settings.pack(fill="x", pady=10)
        row1 = ttk.Frame(settings)
        row1.pack(fill="x")
        ttk.Label(row1, text="Languages").pack(side="left")
        self.lang_list = tk.Listbox(row1, selectmode="multiple", height=5, exportselection=False)
        
        for language in LANGUAGES:
            self.lang_list.insert("end", language)

        self.lang_list.pack(side="left", fill="x", expand=True, padx=(10, 16))
        self.lang_list.selection_set(0, 3)
        controls = ttk.Frame(row1)
        controls.pack(side="left", fill="y")
        ttk.Label(controls, text="Local Ollama model").pack(anchor="w")
        self.model = tk.StringVar(value=DEFAULT_MODEL)
        ttk.Entry(controls, textvariable=self.model, width=25).pack(anchor="w", pady=(2, 10))
        ttk.Label(controls, text="Paper size").pack(anchor="w")
        self.paper = tk.StringVar(value="A4 Portrait")
        ttk.Combobox(controls, textvariable=self.paper, values=["A4 Portrait", "A4 Landscape", "Letter Portrait", "Letter Landscape"], state="readonly", width=22).pack(anchor="w", pady=(2, 10))
        ttk.Label(controls, text="Body font size").pack(anchor="w")
        self.font_size = tk.IntVar(value=28)
        ttk.Spinbox(controls, from_=18, to=72, textvariable=self.font_size, width=8).pack(anchor="w", pady=(2, 0))

        outrow = ttk.Frame(outer)
        outrow.pack(fill="x", pady=(0, 8))
        ttk.Label(outrow, text="Output folder").pack(side="left")
        self.out_label = ttk.Label(outrow, text=self.output_dir, wraplength=590)
        self.out_label.pack(side="left", padx=8, fill="x", expand=True)
        ttk.Button(outrow, text="Choose…", command=self.choose_folder).pack(side="right")

        actions = ttk.Frame(outer)
        actions.pack(fill="x")
        self.generate_btn = ttk.Button(actions, text="Translate & Export SVGs", command=self.start_generation)
        self.generate_btn.pack(side="left")
        ttk.Button(actions, text="Open output folder", command=self.open_folder).pack(side="left", padx=8)
        self.status = tk.StringVar(value="Ready. Requires Ollama running locally for AI translation.")
        ttk.Label(outer, textvariable=self.status, wraplength=850).pack(anchor="w", pady=(10, 0))

    def choose_folder(self):
        folder = filedialog.askdirectory(initialdir=self.output_dir, title="Choose output folder")
        if folder:
            self.output_dir = folder
            self.out_label.configure(text=folder)

    def open_folder(self):
        os.makedirs(self.output_dir, exist_ok=True)
        try:
            if os.name == "nt":
                os.startfile(self.output_dir)
            elif os.sys.platform == "darwin":
                os.system('open "{}"'.format(self.output_dir.replace('"', '\\\\"')))
            else:
                os.system('xdg-open "{}"'.format(self.output_dir.replace('"', '\\\\"')))
        except Exception as exc:
            messagebox.showerror("Could not open folder", str(exc))

    def start_generation(self):
        text = self.body.get("1.0", "end").strip()
        languages = [self.lang_list.get(i) for i in self.lang_list.curselection()]
        if not text:
            messagebox.showwarning("Missing text", "Enter the notice text first.")
            return
        if not languages:
            messagebox.showwarning("No languages selected", "Select at least one language.")
            return
        if not self.model.get().strip():
            messagebox.showwarning("Missing model", "Enter your local Ollama model name.")
            return
        
        self.generate_btn.configure(state="disabled")
        self.status.set("Working… translations may take a little while.")
        thread = threading.Thread(target=self._generate_worker, args=(text, languages), daemon=True)
        thread.start()

    def _generate_worker(self, source_text, languages):
        try:
            width, height = {
                "A4 Portrait": (2480, 3508),
                "A4 Landscape": (3508, 2480),
                "Letter Portrait": (2550, 3300),
                "Letter Landscape": (3300, 2550),
            }[self.paper.get()]

            title = self.title_text.get().strip()
            model = self.model.get().strip()
            context = self.context.get().strip()
            os.makedirs(self.output_dir, exist_ok=True)

            exported = []
            for language in languages:
                translated = translate_with_ollama(source_text, language, model, context)
                safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", language).strip("_")
                svg_path = os.path.join(self.output_dir, f"sign_{safe_name}.svg")
                txt_path = os.path.join(self.output_dir, f"sign_{safe_name}.txt")
                svg = make_svg(title, translated, language, width, height, int(self.font_size.get()))

                with open(svg_path, "w", encoding="utf-8") as file:
                    file.write(svg)
                with open(txt_path, "w", encoding="utf-8") as file:
                    file.write(f"{title}\n\n{translated}\n")
                exported.append(os.path.basename(svg_path))

            self.root.after(0, lambda: self._done(exported))

        except Exception as exc:
            self.root.after(0, lambda error=str(exc): self._failed(error))

    def _done(self, exported):
        self.generate_btn.configure(state="normal")
        self.status.set(f"Done. Exported {len(exported)} SVG sign(s) and matching TXT files to: {self.output_dir}")
        messagebox.showinfo("Export complete", "Created:\n" + "\n".join(exported) + "\n\nYou can open the SVG files in a browser, Inkscape, or a vector editor.")

    def _failed(self, error):
        self.generate_btn.configure(state="normal")
        self.status.set("Could not finish. See the message for details.")
        messagebox.showerror("Translation/export failed", error)


def main():
    root = tk.Tk()
    SignageApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
