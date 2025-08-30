"""Dialog for editing custom context menu actions.

This dialog allows users to modify the JSON definition of the actions shown
in the library context menu. The actions are stored in the configuration
file under the ``actions`` key.
"""
from __future__ import annotations

import json

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QTextEdit,
    QPushButton,
    QMessageBox,
)

from ..core.config import Config


class ActionsEditor(QDialog):
    def __init__(self, config: Config, parent=None) -> None:
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Edit Context Menu Actions")
        self.resize(600, 400)
        layout = QVBoxLayout(self)
        self.text_edit = QTextEdit()
        # Pretty print current actions
        self.text_edit.setText(json.dumps(self.config.actions, indent=2))
        layout.addWidget(self.text_edit)
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save)
        layout.addWidget(save_btn)

    def save(self) -> None:
        try:
            data = json.loads(self.text_edit.toPlainText())
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Error", f"Invalid JSON: {e}")
            return
        if not isinstance(data, dict):
            QMessageBox.critical(self, "Error", "Actions must be a JSON object")
            return
        self.config.update(actions=data)
        QMessageBox.information(self, "Saved", "Actions updated successfully.")
        self.accept()
