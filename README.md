# PyMOL Ask Gemini Advisor

# `askgemini.py`

An integrated, dark-mode customized AI side-panel for PyMOL powered by the Google Gemini API. Designed specifically for structural biology workflows to provide safe, reasoning-based command explanations without auto-executing scripts.

## Features
* **Advisory Safety:** Returns highly consistent scientific explanations and copy-pasteable PyMOL commands (Markdown formatted) without executing them, giving you complete manual control and preventing application crashes.

* **Dynamic Model Fetching:** Automatically queries the Google API on startup to list all available active `3.x+` models on your account, keeping the dropdown menu permanently up to date without manual coding.

* **Auto-Healing Quota Management:** Designed to maximize free-tier API quotas. If a model hits a limit (429 Quota Exceeded) or lags (503 Server Busy), the plugin automatically routes your prompt to the next available model in the dropdown.

* **Native Dark Mode & Syntax Highlighting:** Fully styled for dark environments. Python and PyMOL commands inside markdown blocks are cleanly syntax-highlighted for instant readability.

* **Multi-line Inputs:** Supports multi-paragraph prompts for complex biological context (Shift+Enter for new line, Enter to send).

## Installation

1. Open `askgemini.py` in a text editor.

2. Locate ** ~ line 31** and replace `"YOUR_API_KEY_HERE"` with your actual Gemini API Key.
   ```python
   self.api_key = "AIzaSy..."
   ```

3. Move the script into your PyMOL startup directory:
  ```bash
  mv askgemini.py ~/.pymol/startup/
  ```

4. Restart PyMOL. The "Ask Gemini" panel will automatically dock to the right side of your interface.

## Usage

- **Chat Input**: Type your structural biology question or command request into the bottom input field.

- Submit: Press `Enter` or click `Ask`.

- New Line: Press `Shift + Enter` to drop to a new line without sending.

- Model Selection: Use the dropdown at the top to manually switch between models (e.g.,` gemini-3.5-flash`, `gemini-3.8-flash`).


# PyMOL Auto-Executing Gemini Assistant 

# `ask_and_rungemini.py`

An interactive, AI-powered chat panel for PyMOL that translates natural language into PyMOL commands and **automatically executes them** in your viewport, saving you from having to copy and paste code manually.

> ⚠️ **IMPORTANT WARNING: Free Tier Token Consumption**

> Generating reasoning-based structural biology annotations and parsing PyMOL commands is highly token-intensive. If you are using a Free Tier Gemini API key, you are limited to **20 requests per day, per model**. Because this auto-executing script dynamically routes through models when it encounters errors, **you can burn through your entire daily free-tier quota very quickly.** 

> * If you hit a `429 Quota Exceeded` error across all models, your access will not reset until midnight Pacific Time. 

> * To conserve tokens for complex tasks, consider using the non-executing `askgemini.py` advisor plugin instead.

## Features

* **Live Command Execution:** Automatically parses Markdown code blocks from Gemini's response and safely executes the underlying PyMOL commands directly on the main GUI thread to prevent application crashes or segmentation faults.

* **Auto-Healing Quota Routing:** Designed for free-tier users. Automatically detects API rate limits (429 Quota Exceeded) or server delays (503 Server Busy) and seamlessly reroutes your prompt to the next available Gemini model without breaking the loop.

* **Dynamic Model Dropdown:** Automatically queries the Google API on startup to list all available active `3.x+` models on your account, keeping your model list permanently up-to-date.

* **Thread-Safe Architecture:** Handles network requests in the background so the PyMOL interface never freezes while waiting for the Gemini API to respond.

## Installation

1. Open `ask_and_rungemini.py` in your preferred text editor.

2. Locate **line 19** and insert your actual Gemini API Key into the script:
   ```python
   self.api_key = "AIzaSy..."
   ```
   
3. Move the script into your PyMOL startup directory:

4. Restart PyMOL. The chat widget will automatically dock to your interface.

## Usage

- Type a natural language command into the input box (e.g., "Fetch 1L0O, hide the water molecules, and color the structure by secondary structure").

- Hit Enter to send.

- The assistant will generate a brief scientific explanation, and the structure in your PyMOL viewport will update instantly as the commands are executed in the background.

- Use the dropdown menu to manually switch to a different Gemini model if you want to spread out your free-tier token usage.
