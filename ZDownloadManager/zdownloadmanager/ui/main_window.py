"""Graphical interface for ZDownloadManager.

The main window contains two tabs: Downloads and Library. Users can add
downloads (with optional mirrors), monitor their status and browse their
organised library. Context menu actions are configurable via the configuration
file and executed when selected.
"""
from __future__ import annotations

import os
import threading
import traceback
from functools import partial
import sys
from pathlib import Path
from typing import List

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QInputDialog,
)
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl

from ..core.config import Config
from ..core.downloader import SegmentedDownloader
from ..core.organizer import Organizer
from ..core.library import Library


class DownloadWorker(QThread):
    """Thread wrapper around the SegmentedDownloader for the GUI."""

    progress = pyqtSignal(int, int)  # completed pieces, total pieces
    finished = pyqtSignal(Path, Exception)

    def __init__(self, urls: List[str], dest: Path, cfg: Config) -> None:
        super().__init__()
        self.urls = urls
        self.dest = dest
        self.cfg = cfg

    def run(self) -> None:
        try:
            dl = SegmentedDownloader(
                self.urls,
                self.dest,
                piece_size=self.cfg.piece_size,
                concurrency=self.cfg.concurrency,
            )
            # monkey patch progress printing to emit a Qt signal
            orig_print = print

            def progress_print(*args, **kwargs):
                # parse "Downloaded X/Y pieces"
                if args and isinstance(args[0], str) and args[0].startswith("\rDownloaded"):
                    parts = args[0].split()
                    if len(parts) >= 2 and "/" in parts[1]:
                        done, total = parts[1].split("/")
                        try:
                            self.progress.emit(int(done), int(total))
                        except Exception:
                            pass
                orig_print(*args, **kwargs)

            import builtins

            builtins.print = progress_print  # type: ignore
            dl.download()
            builtins.print = orig_print  # restore
            # Organise file
            org = Organizer(self.cfg)
            new_path = org.organise(self.dest)
            self.finished.emit(new_path, None)
        except Exception as e:
            self.finished.emit(self.dest, e)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.cfg = Config()
        self.organizer = Organizer(self.cfg)
        self.library = Library(self.cfg)
        self.setWindowTitle("ZDownloadManager")
        self.resize(800, 600)
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)
        self._setup_download_tab()
        self._setup_library_tab()
        # Menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        act_quit = QAction("&Quit", self)
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)
        cfg_menu = menubar.addMenu("&Config")
        act_reload = QAction("Reload Config", self)
        act_reload.triggered.connect(self.reload_config)
        cfg_menu.addAction(act_reload)
        act_edit_actions = QAction("Edit Actions", self)
        act_edit_actions.triggered.connect(self.edit_actions)
        cfg_menu.addAction(act_edit_actions)
        # Add menu item to change library root
        act_set_lib = QAction("Set Library Root", self)
        act_set_lib.triggered.connect(self.choose_library_root)
        cfg_menu.addAction(act_set_lib)
        act_piece = QAction("Set Piece Size", self)
        act_piece.triggered.connect(self.set_piece_size)
        cfg_menu.addAction(act_piece)
        act_concurrency = QAction("Set Concurrency", self)
        act_concurrency.triggered.connect(self.set_concurrency)
        cfg_menu.addAction(act_concurrency)
        self.act_suggestions = QAction("Enable Suggestions", self, checkable=True)
        self.act_suggestions.setChecked(self.cfg.suggestions_enabled)
        self.act_suggestions.triggered.connect(self.toggle_suggestions)
        cfg_menu.addAction(self.act_suggestions)
        act_api = QAction("Set OpenRouter API Key", self)
        act_api.triggered.connect(self.set_openrouter_api_key)
        cfg_menu.addAction(act_api)

    def _setup_download_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        # Input row
        input_layout = QHBoxLayout()
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("Primary URL")
        self.mirrors_edit = QLineEdit()
        self.mirrors_edit.setPlaceholderText("Comma separated mirrors (optional)")
        self.dest_edit = QLineEdit()
        self.dest_edit.setPlaceholderText("Destination path (optional)")
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_dest)
        add_btn = QPushButton("Add Download")
        add_btn.clicked.connect(self.add_download)
        input_layout.addWidget(QLabel("URL:"))
        input_layout.addWidget(self.url_edit)
        input_layout.addWidget(QLabel("Mirrors:"))
        input_layout.addWidget(self.mirrors_edit)
        input_layout.addWidget(QLabel("Dest:"))
        input_layout.addWidget(self.dest_edit)
        input_layout.addWidget(browse_btn)
        input_layout.addWidget(add_btn)
        layout.addLayout(input_layout)
        # List of downloads
        self.download_list = QListWidget()
        layout.addWidget(self.download_list)
        self.tabs.addTab(tab, "Downloads")

    def _setup_library_tab(self) -> None:
        tab = QWidget()
        vbox = QVBoxLayout(tab)
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search library...")
        self.search_edit.textChanged.connect(self.refresh_library)
        search_layout.addWidget(self.search_edit)
        vbox.addLayout(search_layout)
        # Create splitter for tree and description
        splitter = QSplitter(Qt.Horizontal)
        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Name", "Category", "Tags"])
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.on_tree_context_menu)
        self.tree.itemSelectionChanged.connect(self.on_tree_selection_changed)
        self.tree.setSortingEnabled(True)
        splitter.addWidget(self.tree)
        # Description area
        from PyQt5.QtWidgets import QTextEdit
        self.description = QTextEdit()
        self.description.setReadOnly(True)
        self.description.setPlaceholderText("Select a file to see details and suggestions...")
        splitter.addWidget(self.description)
        splitter.setSizes([600, 200])
        vbox.addWidget(splitter)
        self.tabs.addTab(tab, "Library")
        self.refresh_library()

    def reload_config(self) -> None:
        self.cfg.load()
        self.organizer = Organizer(self.cfg)
        self.library = Library(self.cfg)
        self.refresh_library()
        self.act_suggestions.setChecked(self.cfg.suggestions_enabled)

    def edit_actions(self) -> None:
        from .actions_editor import ActionsEditor
        dlg = ActionsEditor(self.cfg, self)
        dlg.exec_()

    def set_piece_size(self) -> None:
        size, ok = QInputDialog.getInt(
            self,
            "Piece Size",
            "Piece size (MiB):",
            self.cfg.piece_size // (1024 * 1024),
            1,
            1024,
        )
        if ok:
            self.cfg.update(piece_size=size * 1024 * 1024)

    def set_concurrency(self) -> None:
        conc, ok = QInputDialog.getInt(
            self,
            "Concurrency",
            "Number of connections:",
            self.cfg.concurrency,
            1,
            64,
        )
        if ok:
            self.cfg.update(concurrency=conc)

    def toggle_suggestions(self, checked: bool) -> None:
        self.cfg.update(suggestions_enabled=checked)

    def set_openrouter_api_key(self) -> None:
        key, ok = QInputDialog.getText(
            self,
            "OpenRouter API Key",
            "Enter API key:",
            text=self.cfg.openrouter_api_key,
        )
        if ok:
            self.cfg.update(openrouter_api_key=key)

    def browse_dest(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Select destination")
        if path:
            self.dest_edit.setText(path)

    def add_download(self) -> None:
        url = self.url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "Input", "Please specify a URL")
            return
        mirrors = [u.strip() for u in self.mirrors_edit.text().split(",") if u.strip()]
        dest_text = self.dest_edit.text().strip()
        dest = Path(dest_text) if dest_text else Path(Path(url).name)
        # Add entry to the list
        item = QListWidgetItem(f"{dest.name}: queued")
        self.download_list.addItem(item)
        worker = DownloadWorker([url] + mirrors, dest, self.cfg)
        # Connect signals
        worker.progress.connect(lambda d, t, itm=item: self.on_download_progress(itm, d, t))
        worker.finished.connect(lambda p, e, itm=item: self.on_download_finished(itm, p, e))
        worker.start()
        # Clear inputs
        self.url_edit.clear()
        self.mirrors_edit.clear()
        self.dest_edit.clear()

    def on_download_progress(self, item: QListWidgetItem, done: int, total: int) -> None:
        item.setText(item.text().split(":")[0] + f": {done}/{total}")

    def on_download_finished(self, item: QListWidgetItem, new_path: Path, error: Exception) -> None:
        if error:
            item.setText(item.text().split(":")[0] + ": error")
            QMessageBox.critical(self, "Download failed", str(error))
        else:
            item.setText(new_path.name + ": done")
            self.refresh_library()

    def refresh_library(self) -> None:
        query = self.search_edit.text().strip()
        items = self.library.search(query) if query else self.library.scan()
        self.tree.clear()
        for path, category, tags in items:
            node = QTreeWidgetItem([Path(path).name, category, ", ".join(tags)])
            node.setData(0, Qt.UserRole, path)
            self.tree.addTopLevelItem(node)

    def on_tree_context_menu(self, pos) -> None:
        item = self.tree.itemAt(pos)
        if item is None:
            return
        path = item.data(0, Qt.UserRole)
        menu = QMenu(self)
        # Built‑in actions
        open_act = QAction("Open", self)
        open_act.triggered.connect(lambda: self.open_file(path))
        menu.addAction(open_act)
        reveal_act = QAction("Reveal in Explorer/Finder", self)
        reveal_act.triggered.connect(lambda: self.reveal_file(path))
        menu.addAction(reveal_act)
        # Tag actions
        add_tag_act = QAction("Add Tag", self)
        add_tag_act.triggered.connect(lambda: self.add_tag_dialog(path))
        menu.addAction(add_tag_act)
        # Custom openers based on file extension
        ext = Path(path).suffix.lower()
        opener_cmd = self.cfg.custom_openers.get(ext)
        if opener_cmd:
            custom_open_act = QAction(f"Open with {opener_cmd}", self)
            custom_open_act.triggered.connect(lambda: self.run_custom_opener(path, opener_cmd))
            menu.addAction(custom_open_act)
        # Custom actions from config
        for name, spec in self.cfg.actions.items():
            # Check platform
            plats = spec.get("platform", ["any"])
            if "any" not in plats and sys.platform not in plats and (sys.platform != "win32" or "win32" not in plats):
                continue
            act = QAction(name, self)
            act.triggered.connect(partial(self.run_action, path, spec.get("cmd")))
            menu.addAction(act)

        # File operations: rename and delete
        rename_act = QAction("Rename", self)
        rename_act.triggered.connect(lambda: self.rename_file(path))
        menu.addAction(rename_act)
        delete_act = QAction("Delete", self)
        delete_act.triggered.connect(lambda: self.delete_file(path))
        menu.addAction(delete_act)
        menu.exec_(self.tree.viewport().mapToGlobal(pos))

    def on_tree_selection_changed(self) -> None:
        selected = self.tree.selectedItems()
        if not selected:
            self.description.clear()
            return
        item = selected[0]
        path = item.data(0, Qt.UserRole)
        name = Path(path).name
        category = item.text(1)
        tags = item.text(2)
        # Show basic info
        from ..core.suggestions import get_suggestion
        suggestion = get_suggestion(self.cfg, f"Describe the program or file named '{name}'")
        if suggestion:
            self.description.setPlainText(f"Name: {name}\nCategory: {category}\nTags: {tags}\n\n{suggestion}")
        else:
            self.description.setPlainText(f"Name: {name}\nCategory: {category}\nTags: {tags}\n\nNo description available.")

    def open_file(self, path: str) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))  # type: ignore

    def reveal_file(self, path: str) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(path).parent)))  # type: ignore

    def add_tag_dialog(self, path: str) -> None:
        tag, ok = QInputDialog.getText(self, "Add Tag", f"Enter tag for {Path(path).name}")
        if ok and tag:
            self.library.add_tag(path, tag.strip())
            self.refresh_library()

    def run_action(self, path: str, cmd_template: str) -> None:
        if not cmd_template:
            return
        # Replace tokens
        cmd = cmd_template.replace("{path}", str(path)).replace("{dir}", str(Path(path).parent))
        # Execute in background
        def run() -> None:
            try:
                import subprocess
                subprocess.run(cmd, shell=True)
            except Exception:
                traceback.print_exc()
        threading.Thread(target=run, daemon=True).start()

    def run_custom_opener(self, path: str, opener: str) -> None:
        """Execute a custom opener command for the given file.

        The command string may contain `{path}` and `{dir}` tokens which will
        be replaced with the file's full path and directory respectively.
        """
        cmd = opener.replace("{path}", str(path)).replace("{dir}", str(Path(path).parent))
        def run() -> None:
            import subprocess
            try:
                subprocess.Popen(cmd, shell=True)
            except Exception:
                traceback.print_exc()
        threading.Thread(target=run, daemon=True).start()

    # --- New file operations ---
    def rename_file(self, path: str) -> None:
        """Prompt the user to rename the selected file and apply changes."""
        from PyQt5.QtWidgets import QInputDialog, QMessageBox
        old_path = Path(path)
        new_name, ok = QInputDialog.getText(
            self,
            "Rename File",
            f"Enter new name for {old_path.name}",
            text=old_path.name,
        )
        if not ok or not new_name:
            return
        new_name = new_name.strip()
        # Prevent paths with separators
        if os.path.sep in new_name:
            QMessageBox.warning(self, "Rename", "Filename cannot contain path separators.")
            return
        new_path = old_path.with_name(new_name)
        # If file exists, confirm overwrite
        if new_path.exists():
            reply = QMessageBox.question(
                self,
                "Overwrite File",
                f"{new_path.name} already exists. Overwrite?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return
        try:
            old_path.rename(new_path)
            # Update tags mapping
            tags = self.library.tags.pop(str(old_path), None)
            if tags:
                self.library.tags[str(new_path)] = tags
                self.library._save_tags()
            self.refresh_library()
        except Exception as e:
            QMessageBox.critical(self, "Rename", f"Failed to rename file: {e}")

    def delete_file(self, path: str) -> None:
        """Prompt the user to delete the selected file and remove tags."""
        from PyQt5.QtWidgets import QMessageBox
        file_path = Path(path)
        reply = QMessageBox.question(
            self,
            "Delete File",
            f"Are you sure you want to delete {file_path.name}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            # Remove file
            file_path.unlink()
            # Remove tags
            self.library.tags.pop(str(file_path), None)
            self.library._save_tags()
            self.refresh_library()
        except Exception as e:
            QMessageBox.critical(self, "Delete", f"Failed to delete file: {e}")

    def choose_library_root(self) -> None:
        """Allow the user to select a new library root directory."""
        from PyQt5.QtWidgets import QFileDialog
        path = QFileDialog.getExistingDirectory(self, "Select Library Root")
        if not path:
            return
        roots = self.cfg.library_roots
        # Replace the first root with the selected one
        if roots:
            roots[0] = path
        else:
            roots.append(path)
        self.cfg.update(library_roots=roots)
        # Reload library to reflect new root
        self.library = Library(self.cfg)
        self.refresh_library()


def main() -> None:
    app = QApplication([])
    win = MainWindow()
    win.show()
    app.exec_()


if __name__ == "__main__":
    main()
