# PyMOL Ask Gemini Advisor (`askgemini.py`)

An integrated, dark-mode customized AI side-panel for PyMOL powered by the Google Gemini API. Designed specifically for structural biology workflows to provide safe, reasoning-based command explanations without auto-executing scripts.

## Features
* **Advisory Safety:** Returns highly consistent scientific explanations and copy-pasteable PyMOL commands (Markdown formatted) without executing them, giving you complete manual control and preventing application crashes.

* **Dynamic Model Fetching:** Automatically queries the Google API on startup to list all available active `3.x+` models on your account, keeping the dropdown menu permanently up to date without manual coding.

* **Auto-Healing Quota Management:** Designed to maximize free-tier API quotas. If a model hits a limit (429 Quota Exceeded) or lags (503 Server Busy), the plugin automatically routes your prompt to the next available model in the dropdown.

* **Native Dark Mode & Syntax Highlighting:** Fully styled for dark environments. Python and PyMOL commands inside markdown blocks are cleanly syntax-highlighted for instant readability.

* **Multi-line Inputs:** Supports multi-paragraph prompts for complex biological context (Shift+Enter for new line, Enter to send).

## Installation
1. Open `askgemini.py` in a text editor.
3. Locate ** ~ line 31** and replace `"YOUR_API_KEY_HERE"` with your actual Gemini API Key.
   ```python
   self.api_key = "AIzaSy..."
   ```
4. Move the script into your PyMOL startup directory:
  ```bash
  mv askgemini.py ~/.pymol/startup/
  ```
4. Restart PyMOL. The "Ask Gemini" panel will automatically dock to the right side of your interface.

## Usage

- **Chat Input**: Type your structural biology question or command request into the bottom input field.

- Submit: Press `Enter` or click `Ask`.

- New Line: Press `Shift + Enter` to drop to a new line without sending.

- Model Selection: Use the dropdown at the top to manually switch between models (e.g.,` gemini-3.5-flash`, `gemini-3.8-flash`).
