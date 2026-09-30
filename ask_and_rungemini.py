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

from pymol import cmd

class GeminiRestChatWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_key = os.environ.get("GEMINI_API_KEY", "")
        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        top_layout = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Gemini PyMOL Assistant")
        title.setStyleSheet("font-weight: bold; font-size: 11pt; color: #111111;")
        top_layout.addWidget(title)
        
        top_layout.addStretch()

        # The Dropdown Menu
        self.model_selector = QtWidgets.QComboBox(self)
        self.model_selector.addItems([
            "gemini-3.8-flash", 
            "gemini-3.1-pro-preview",
            "gemini-3.5-flash"
        ])
        self.model_selector.setStyleSheet("background-color: #ffffff; color: #111111;")
        top_layout.addWidget(self.model_selector)
        
        layout.addLayout(top_layout)

        self.chat_display = QtWidgets.QTextEdit(self)
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("background-color: #f9f9f9; color: #333333; font-size: 10pt;")
        layout.addWidget(self.chat_display)

        input_layout = QtWidgets.QHBoxLayout()
        self.input_field = QtWidgets.QLineEdit(self)
        self.input_field.setPlaceholderText("Type a command (e.g., fetch 2HHB)...")
        self.input_field.setStyleSheet("background-color: #ffffff; color: #111111;")
        self.input_field.returnPressed.connect(self.handle_send)
        input_layout.addWidget(self.input_field)

        self.send_button = QtWidgets.QPushButton("Send", self)
        self.send_button.clicked.connect(self.handle_send)
        input_layout.addWidget(self.send_button)

        layout.addLayout(input_layout)

        if not self.api_key:
            self.append_chat("System", "Error: GEMINI_API_KEY environment variable not set.")
        else:
            self.append_chat("System", "Ready.")

    def append_chat(self, sender, text):
        self.chat_display.append(f"<b>{sender}:</b> {text}\n")

    def handle_send(self):
        user_text = self.input_field.text().strip()
        if not user_text:
            return
        
        self.append_chat("User", user_text)
        self.input_field.clear()

        # Gather models starting from the one currently selected in the dropdown
        count = self.model_selector.count()
        models = [self.model_selector.itemText(i) for i in range(count)]
        current_idx = self.model_selector.currentIndex()
        
        # Reorder list so it tries the user's selected model first, then the others
        models_to_try = models[current_idx:] + models[:current_idx]

        threading.Thread(target=self.call_gemini_api, args=(user_text, models_to_try)).start()

    def call_gemini_api(self, prompt, models_to_try):
        system_instruction = (
            "You are an expert structural biology co-pilot embedded inside PyMOL. "
            "When the user asks to load, color, select, or modify structures, output valid PyMOL commands "
            "enclosed in a markdown code block like ```pymol\n[commands]\n```. "
            "Also provide a brief scientific explanation."
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
                        
                        self.extract_and_execute_pymol(reply_text)

                        # Update the UI dropdown to match the model that succeeded
                        QtCore.QMetaObject.invokeMethod(
                            self, "update_dropdown_ui", QtCore.Qt.QueuedConnection,
                            QtCore.Q_ARG(str, model)
                        )

                        QtCore.QMetaObject.invokeMethod(
                            self, "append_chat_safe", QtCore.Qt.QueuedConnection,
                            QtCore.Q_ARG(str, f"Gemini ({model})"), QtCore.Q_ARG(str, reply_text)
                        )
                    else:
                        self.notify_system("No response candidates returned.")
                break 

            except urllib.error.HTTPError as e:
                if e.code in [429, 503] and attempt < len(models_to_try) - 1:
                    reason = "Quota Exceeded (429)" if e.code == 429 else "Server Busy (503)"
                    self.notify_system(f"Model {model} failed ({reason}). Auto-switching to next model...")
                    time.sleep(1.0)
                    continue
                else:
                    err_body = e.read().decode("utf-8", "errors='ignore'")
                    self.notify_system(f"API Error ({e.code}) on {model}: {err_body}")
                    break
            except Exception as e:
                self.notify_system(f"Connection Error: {str(e)}")
                break

    @QtCore.Slot(str)
    def update_dropdown_ui(self, model_name):
        # Update the combo box selection automatically on fallback
        index = self.model_selector.findText(model_name)
        if index >= 0:
            self.model_selector.setCurrentIndex(index)

    @QtCore.Slot(str, str)
    def append_chat_safe(self, sender, text):
        self.append_chat(sender, text)

    @QtCore.Slot(str)
    def safe_cmd_do(self, cmd_str):
        try:
            cmd.do(cmd_str)
        except Exception as ex:
            print(f"PyMOL execution error for '{cmd_str}': {ex}")

    def extract_and_execute_pymol(self, text):
        code_blocks = re.findall(r"```pymol(.*?)```", text, re.DOTALL)
        if not code_blocks:
            code_blocks = re.findall(r"```(.*?)```", text, re.DOTALL)
            
        for block in code_blocks:
            lines = block.strip().split("\n")
            for line in lines:
                cmd_str = line.strip()
                if cmd_str and not cmd_str.startswith("#") and not cmd_str.startswith("pymol"):
                    QtCore.QMetaObject.invokeMethod(
                        self, "safe_cmd_do", QtCore.Qt.QueuedConnection,
                        QtCore.Q_ARG(str, cmd_str)
                    )

    def notify_system(self, msg):
        QtCore.QMetaObject.invokeMethod(
            self, "append_chat_safe", QtCore.Qt.QueuedConnection,
            QtCore.Q_ARG(str, "System"), QtCore.Q_ARG(str, msg)
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
                dock = QtWidgets.QDockWidget("Gemini Chat", main_window)
                dock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea | QtCore.Qt.LeftDockWidgetArea)
                chat_widget = GeminiRestChatWidget(dock)
                dock.setWidget(chat_widget)
                main_window.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dock)
        except Exception as e:
            print(f"Gemini plugin dock error: {e}")
            
    QtCore.QTimer.singleShot(1000, register_widget)
