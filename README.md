# Local AI Signage & Translation Formatter

A desktop application built with Python and Tkinter that uses a locally running AI model to translate visitor notices into multiple languages and export them as editable SVG signage files and plain-text copies.

The application uses [Ollama](https://ollama.com/) to run translations locally, without relying on cloud-based AI APIs or an external database.

## Features

- **Local AI translation:** Uses Ollama with a configurable language model.
- **Multiple languages:** Supports Japanese, Simplified Chinese (Mandarin), Samoan, Tongan, Spanish, Korean, French, and English (original).
- **Custom signage content:** Add an optional heading, notice text, and context for the translator.
- **Editable SVG exports:** Generates SVG files that can be opened in web browsers, Inkscape, or other vector graphics editors.
- **Plain-text copies:** Saves a corresponding `.txt` file for each language.
- **Multilingual text wrapping:** Estimates character widths to wrap Latin, CJK, and other Unicode text within the sign layout.
- **Customizable settings:** Configure the Ollama model, paper size, font size, and output directory.
- **Background processing:** Runs translation tasks on a separate thread to keep the desktop interface responsive.
- **Privacy-conscious design:** Sends translation requests to a locally running Ollama service rather than a cloud AI API.

## Technologies Used

- **Python** — Application logic and file handling
- **Tkinter / ttk** — Desktop graphical user interface
- **Ollama** — Local AI inference and translation
- **SVG** — Editable vector signage
- **JSON and urllib** — Communication with the local Ollama API
- **Unicode and regular expressions** — Text-width estimation, wrapping, and output filenames

## Requirements

- Python 3.10 or later recommended
- [Ollama](https://ollama.com/) installed and running
- A compatible Ollama model downloaded locally

The default model is `qwen2.5:7b`. Other compatible Ollama models can be selected in the application.

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/ShaleemLabs/AI-Driven-Signage.git
cd AI-Driven-Signage
```

### 2. Install and start Ollama

Download and install Ollama from:

https://ollama.com/download

Download the default model:

```bash
ollama pull qwen2.5:7b
```

Make sure Ollama is running before requesting translations. Its default local API endpoint is:

```text
http://localhost:11434/api/generate
```

### 3. Run the application

Save the Python script as `local_ai_signage_formatter.py`, then run:

```bash
python local_ai_signage_formatter.py
```

No additional Python packages are required for the application's current implementation because it uses Python's standard library.

## How to Use

1. **Enter the sign content.** Provide an optional heading and the notice or message you want to display.
2. **Add translation context (optional).** Include relevant information about the location, audience, or desired tone.
3. **Select languages.** Choose one or more languages for translation. English (original) preserves the source wording without translation.
4. **Configure the settings.** Enter your local Ollama model name, choose a paper-size option, and set the body font size.
5. **Choose an output folder.** Use the default directory or select another location.
6. **Generate the signs.** Click **Translate & Export SVGs** and wait for the translations and files to be generated.
7. **Open your files.** Click **Open output folder** to access the exported files.

## Output Files

For every selected language, the application generates two files:

| File | Description |
|---|---|
| `sign_Japanese.svg` | Editable SVG sign |
| `sign_Japanese.txt` | Plain-text heading and translated notice |

Filenames are generated from the selected language. Files are saved to the configured output directory, which defaults to:

```text
~/LocalAISignage/
```

On Windows, this normally resolves to a folder named `LocalAISignage` inside your user directory.

## Privacy and Limitations

- Translation requests are sent to the local Ollama service running on your computer.
- The application does not use a cloud AI API or an external database.
- The Ollama model must be downloaded and available locally before translations can be generated.
- Translation quality depends on the selected model. Important public-facing, safety, or emergency notices should be reviewed by a qualified human translator before use.
- Font availability and SVG rendering may vary between computers and applications.
- Although paper-size options are provided, the current SVG generator uses a fixed 1280 × 720 viewBox and a centered sign layout. The selected paper size does not currently change the SVG canvas dimensions.
- The application estimates text width for wrapping; it does not measure actual rendered font widths.

## Project Purpose

This project explores how locally running AI models can help streamline multilingual signage creation while keeping translation requests on the user's computer. It combines desktop application development, local AI integration, Unicode text processing, and vector graphics generation in one practical tool.

## License

No license has been specified yet. Unless a license is added to this repository, the project should be treated as having all rights reserved by its author.
