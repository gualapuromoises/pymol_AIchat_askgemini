import os
import json
import time
import urllib.request
import urllib.error
import threading
import re

try:
    from pymol.Qt import QtWidgets, QtCore
except ImportError:
    from qtpy import QtWidgets, QtCore

class ChatInputField(QtWidgets.QTextEdit):
    def __init__(self, send_callback, parent=None):
        super().__init__(parent)
        self.send_callback = send_callback
        self.setPlaceholderText("Type a prompt... (Shift+Enter for a new line)")
        self.setFixedHeight(85)

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter) and not event.modifiers() & QtCore.Qt.ShiftModifier:
            self.send_callback()
        else:
            super().keyPressEvent(event)

class GeminiAdvisorWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # INSERT YOUR ACTUAL API KEY HERE
        self.api_key = "YOUR_API_KEY_HERE"
        
        self.available_models = [
            "gemini-3.8-flash", 
            "gemini-3.1-pro-preview",
            "gemini-3.5-flash"
        ]
        self.init_ui()
        threading.Thread(target=self.fetch_available_models).start()

    def init_ui(self):
        self.setStyleSheet("background-color: #202124;")
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        top_layout = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Ask Gemini (Advisor)")
        title.setStyleSheet("font-weight: bold; font-size: 12pt; color: #e8eaed; border: none;")
        top_layout.addWidget(title)
        
        top_layout.addStretch()

        self.model_selector = QtWidgets.QComboBox(self)
        self.model_selector.addItems(self.available_models)
        self.model_selector.setStyleSheet(
            "background-color: #303134; color: #e8eaed; padding: 2px; border: 1px solid #5f6368; border-radius: 3px;"
        )
        top_layout.addWidget(self.model_selector)
        
        layout.addLayout(top_layout)

        self.chat_display = QtWidgets.QTextBrowser(self)
        self.chat_display.setOpenExternalLinks(True)
        self.chat_display.setStyleSheet(
            "background-color: #202124; color: #e8eaed; "
            "font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 10pt; "
            "border: 1px solid #3c4043; border-radius: 4px;"
        )
        layout.addWidget(self.chat_display)

        input_layout = QtWidgets.QHBoxLayout()
        self.input_field = ChatInputField(self.handle_send, self)
        self.input_field.setStyleSheet(
            "background-color: #303134; color: #e8eaed; padding: 4px; "
            "border: 1px solid #5f6368; border-radius: 4px;"
        )
        input_layout.addWidget(self.input_field)

        self.send_button = QtWidgets.QPushButton("Ask", self)
        self.send_button.setStyleSheet(
            "font-weight: bold; background-color: #303134; color: #8ab4f8; "
            "border: 1px solid #5f6368; border-radius: 4px;"
        )
        self.send_button.setFixedHeight(85)
        self.send_button.clicked.connect(self.handle_send)
        input_layout.addWidget(self.send_button)

        layout.addLayout(input_layout)

        if not self.api_key or self.api_key == "YOUR_API_KEY_HERE":
            self.append_chat("System", "Error: Hardcoded API key is missing. Edit line 31.", is_error=True)
        else:
            self.append_chat("System", "Ready. Fetching available 3.x+ models...", is_system=True)

    def fetch_available_models(self):
        if not self.api_key or self.api_key == "YOUR_API_KEY_HERE":
            return
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.api_key}"
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                models = []
                for m in data.get("models", []):
                    if "generateContent" in m.get("supportedGenerationMethods", []):
                        name = m.get("name", "").replace("models/", "")
                        if "gemini" in name and "gemini-1" not in name and "gemini-2" not in name:
                            models.append(name)
                if models:
                    self.available_models = models
                    models_str = ",".join(models)
                    QtCore.QMetaObject.invokeMethod(
                        self, "update_model_dropdown_full", QtCore.Qt.QueuedConnection,
                        QtCore.Q_ARG(str, models_str)
                    )
        except Exception as e:
            self.notify_system(f"Could not dynamically fetch models: {str(e)}", True)

    @QtCore.Slot(str)
    def update_model_dropdown_full(self, models_str):
        self.model_selector.clear()
        models = models_str.split(",")
        self.model_selector.addItems(models)
        self.append_chat("System", f"Dynamically loaded {len(models)} active models.", is_system=True)

    def highlight_code(self, code_str):
        lines = code_str.strip().split('\n')
        formatted_lines = []
        
        pymol_keywords = {
            'fetch', 'hide', 'show', 'color', 'select', 'set', 'bg_color', 'create', 
            'align', 'super', 'remove', 'zoom', 'center', 'spectrum', 'save', 'load', 'util', 'fetchaf'
        }

        for line in lines:
            line = line.replace('<', '&lt;').replace('>', '&gt;')
            
            if '#' in line:
                code_part, comment_part = line.split('#', 1)
                comment_html = f'<span style="color: #8b949e; font-style: italic;">#{comment_part}</span>'
            else:
                code_part = line
                comment_html = ""
            
            words = code_part.split(' ')
            for i, w in enumerate(words):
                clean_w = w.strip(',()')
                if clean_w in pymol_keywords:
                    words[i] = w.replace(clean_w, f'<span style="color: #ff7b72; font-weight: bold;">{clean_w}</span>')
                elif clean_w.replace('.', '', 1).isdigit():
                    words[i] = w.replace(clean_w, f'<span style="color: #79c0ff;">{clean_w}</span>')
            
            formatted_lines.append(' '.join(words) + comment_html)
        
        return '<br>'.join(formatted_lines)

    def append_chat(self, sender, text, is_system=False, is_error=False):
        parts = re.split(r'```(?:pymol|python)?\n?(.*?)```', text, flags=re.DOTALL)
        
        html_parts = []
        for i, part in enumerate(parts):
            if i % 2 == 0:
                escaped = part.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')
                html_parts.append(escaped)
            else:
                highlighted_code = self.highlight_code(part)
                block = (
                    f'<div style="background-color:#17181a; color:#c9d1d9; padding:10px; margin:8px 0; '
                    f'border: 1px solid #3c4043; border-radius: 6px; font-family: monospace; font-size: 9.5pt;">'
                    f'{highlighted_code}</div>'
                )
                html_parts.append(block)

        final_html = "".join(html_parts)
        
        if is_error: color = "#f28b82" 
        elif is_system: color = "#81c995" 
        elif sender == "User": color = "#8ab4f8" 
        else: color = "#e8eaed" 

        message = f'<span style="color: {color}; font-weight: bold;">{sender}:</span><br><span style="color: #e8eaed;">{final_html}</span><br><br>'
        self.chat_display.append(message)

    def handle_send(self):
        user_text = self.input_field.toPlainText().strip()
        if not user_text:
            return
        
        self.append_chat("User", user_text)
        self.input_field.clear()

        count = self.model_selector.count()
        models = [self.model_selector.itemText(i) for i in range(count)]
        current_idx = self.model_selector.currentIndex()
        
        models_to_try = models[current_idx:] + models[:current_idx]

        threading.Thread(target=self.call_gemini_api, args=(user_text, models_to_try)).start()

    def call_gemini_api(self, prompt, models_to_try):
        system_instruction = (
            "You are an expert structural biology co-pilot and PyMOL advisor. "
            "When the user asks how to load, color, select, or modify structures, "
            "provide a detailed scientific explanation first. "
            "Then, provide the exact PyMOL commands enclosed in a markdown code block (```pymol ... ```). "
            "DO NOT assume the commands will be auto-executed. Your goal is to teach "
            "and provide clean code."
        )

        payload = {
            "contents": [{"parts": [{"text": f"{system_instruction}\n\nUser Request: {prompt}"}]}]
        }
        data = json.dumps(payload).encode("utf-8")
        
        for attempt, model in enumerate(models_to_try):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")

            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    candidates = res_data.get("candidates", [])
                    if candidates:
                        content = candidates[0].get("content", {})
                        parts = content.get("parts", [])
                        reply_text = "".join([p.get("text", "") for p in parts])
                        
                        QtCore.QMetaObject.invokeMethod(
                            self, "update_dropdown_ui", QtCore.Qt.QueuedConnection,
                            QtCore.Q_ARG(str, model)
                        )

                        QtCore.QMetaObject.invokeMethod(
                            self, "append_chat_safe", QtCore.Qt.QueuedConnection,
                            QtCore.Q_ARG(str, f"Gemini ({model})"), QtCore.Q_ARG(str, reply_text),
                            QtCore.Q_ARG(bool, False), QtCore.Q_ARG(bool, False)
                        )
                    else:
                        self.notify_system("No response candidates returned.", True)
                break 

            except urllib.error.HTTPError as e:
                if e.code in [429, 503] and attempt < len(models_to_try) - 1:
                    reason = "Quota Exceeded (429)" if e.code == 429 else "Server Busy (503)"
                    self.notify_system(f"Model {model} failed ({reason}). Auto-switching to next model...", True)
                    time.sleep(1.0)
                    continue
                else:
                    err_body = e.read().decode("utf-8", "errors='ignore'")
                    self.notify_system(f"API Error ({e.code}) on {model}: {err_body}", True)
                    break
            except Exception as e:
                self.notify_system(f"Connection Error: {str(e)}", True)
                break

    @QtCore.Slot(str)
    def update_dropdown_ui(self, model_name):
        index = self.model_selector.findText(model_name)
        if index >= 0:
            self.model_selector.setCurrentIndex(index)

    @QtCore.Slot(str, str, bool, bool)
    def append_chat_safe(self, sender, text, is_system, is_error):
        self.append_chat(sender, text, is_system, is_error)

    def notify_system(self, msg, is_error=False):
        QtCore.QMetaObject.invokeMethod(
            self, "append_chat_safe", QtCore.Qt.QueuedConnection,
            QtCore.Q_ARG(str, "System"), QtCore.Q_ARG(str, msg),
            QtCore.Q_ARG(bool, True), QtCore.Q_ARG(bool, is_error)
        )

def __init_plugin__(app=None):
    def register_widget():
        try:
            main_window = None
            for widget in QtWidgets.QApplication.topLevelWidgets():
                if widget.inherits("QMainWindow") and "PyMOL" in widget.windowTitle():
                    main_window = widget
                    break
            if main_window:
                dock = QtWidgets.QDockWidget("Ask Gemini", main_window)
                dock.setAllowedAreas(QtCore.Qt.RightDockWidgetArea | QtCore.Qt.LeftDockWidgetArea)
                chat_widget = GeminiAdvisorWidget(dock)
                dock.setWidget(chat_widget)
                main_window.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
        except Exception as e:
            print(f"Gemini advisor dock error: {e}")
            
    QtCore.QTimer.singleShot(1000, register_widget)
