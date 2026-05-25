from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QSize, Qt, QTimer, QUrl
from PyQt6.QtGui import QDesktopServices, QIcon, QMovie, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .autostart import AutostartManager
from .gif_process import GifProcessManager
from .media_store import MediaStore
from .protocol import LcdProtocol
from .settings import AppSettings

MAX_HISTORY_ITEMS = 20
SUPPORTED_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif"}


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.autostart = AutostartManager()
        self.autostart.ensure_current()
        self.gif_process = GifProcessManager()
        self.media_store = MediaStore()
        self.protocol = LcdProtocol()
        self.settings = AppSettings()
        self.settings_data = self.settings.load()
        self.selected_image: Path | None = None
        self.preview_movie: QMovie | None = None

        self.status_timer = QTimer(self)
        self.status_timer.setInterval(1000)
        self.status_timer.timeout.connect(self._sync_controls)

        self.setAcceptDrops(True)
        self.setWindowTitle("LOVINGCOOL LCD")
        self.resize(660, 560)
        self._build_ui()
        self._refresh_ports()
        self._load_history()
        self._restore_last_media()
        self._sync_controls()
        self.status_timer.start()

    def _build_ui(self) -> None:
        root = QVBoxLayout()
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(10)

        self.path_label = QLabel("No media selected")
        self.path_label.setObjectName("PathLabel")
        self.path_label.setWordWrap(True)

        self.preview = QLabel("Preview")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setFixedHeight(300)
        self.preview.setObjectName("PreviewBox")

        top_row = QHBoxLayout()
        self.autostart_checkbox = QCheckBox("Run on startup")
        self.autostart_checkbox.setChecked(self.autostart.is_enabled())
        self.autostart_checkbox.toggled.connect(self._toggle_autostart)
        self.port_combo = QComboBox()
        self.refresh_button = QPushButton("Refresh Ports")
        self.refresh_button.clicked.connect(self._refresh_ports)
        top_row.addWidget(self.autostart_checkbox)
        top_row.addStretch(1)
        top_row.addWidget(self.port_combo)
        top_row.addWidget(self.refresh_button)

        library_label = QLabel("Library")
        library_label.setObjectName("SectionLabel")

        history_row = QHBoxLayout()
        self.history_list = QListWidget()
        self.history_list.setObjectName("HistoryList")
        self.history_list.setFlow(QListWidget.Flow.LeftToRight)
        self.history_list.setWrapping(False)
        self.history_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.history_list.setMovement(QListWidget.Movement.Static)
        self.history_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.history_list.setSpacing(10)
        self.history_list.setFixedHeight(112)
        self.history_list.setIconSize(QSize(72, 72))
        self.history_list.itemClicked.connect(self._history_selected)
        self.history_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.history_list.customContextMenuRequested.connect(self._open_history_menu)

        add_column = QVBoxLayout()
        add_column.setSpacing(2)
        self.choose_button = QPushButton("Add an image or GIF")
        self.choose_button.clicked.connect(self._choose_image)
        self.drag_hint_label = QLabel("Or drag & drop onto the window")
        self.drag_hint_label.setObjectName("HintLabel")
        add_column.addWidget(self.choose_button)
        add_column.addWidget(self.drag_hint_label)
        add_column.addStretch(1)

        history_row.addWidget(self.history_list)
        history_row.addLayout(add_column)

        action_row = QHBoxLayout()
        self.apply_button = QPushButton("Apply to LCD")
        self.apply_button.setEnabled(False)
        self.playback_button = QPushButton("Start Playback")
        self.playback_button.setEnabled(False)
        self.apply_button.clicked.connect(self._apply_media)
        self.playback_button.clicked.connect(self._toggle_playback)
        action_row.addWidget(self.apply_button)
        action_row.addWidget(self.playback_button)

        root.addWidget(self.path_label)
        root.addLayout(top_row)
        root.addWidget(library_label)
        root.addLayout(history_row)
        root.addWidget(self.preview)
        root.addLayout(action_row)

        self.setLayout(root)
        self.setStyleSheet(
            """
            QWidget {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #08090b,
                    stop: 1 #14171c
                );
                color: #f1f5f9;
                font-family: 'Noto Sans', 'DejaVu Sans', sans-serif;
                font-size: 14px;
            }
            QLabel#PathLabel {
                color: #cbd5e1;
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
                padding: 8px 10px;
            }
            QLabel#HintLabel {
                color: #94a3b8;
                font-size: 12px;
                padding-left: 4px;
            }
            QLabel#SectionLabel {
                color: #cbd5e1;
                font-weight: 600;
                padding: 4px 2px 0 2px;
            }
            QLabel#PreviewBox {
                border: 1px solid rgba(255, 255, 255, 0.16);
                border-radius: 14px;
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #111418,
                    stop: 1 #0d1014
                );
                color: #64748b;
            }
            QCheckBox {
                color: #cbd5e1;
                spacing: 10px;
                padding: 2px 0;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 5px;
                border: 1px solid rgba(255, 255, 255, 0.18);
                background: #0d1117;
            }
            QCheckBox::indicator:checked {
                background: #f8fafc;
                border: 1px solid #ffffff;
            }
            QPushButton {
                background: #f8fafc;
                color: #0f172a;
                border: 1px solid #ffffff;
                border-radius: 11px;
                padding: 10px 16px;
                font-weight: 600;
            }
            QPushButton:disabled {
                background: #475569;
                color: #94a3b8;
                border: 1px solid #475569;
            }
            QPushButton:hover:!disabled {
                background: #e2e8f0;
            }
            QPushButton:pressed:!disabled {
                background: #cbd5e1;
            }
            QComboBox {
                background: #0d1117;
                color: #e2e8f0;
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-radius: 11px;
                padding: 8px 10px;
                min-width: 160px;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox QAbstractItemView {
                background: #0d1117;
                color: #e2e8f0;
                border: 1px solid rgba(255, 255, 255, 0.18);
                selection-background-color: #1e293b;
            }
            QListWidget#HistoryList {
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 8px;
                outline: none;
            }
            QListWidget#HistoryList::item {
                width: 88px;
                padding: 6px;
                border-radius: 10px;
                color: #e2e8f0;
            }
            QListWidget#HistoryList::item:selected {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(255, 255, 255, 0.18);
            }
            """
        )

    def _refresh_ports(self) -> None:
        previous_port = self.port_combo.currentText() or self.settings_data.get("last_port", "")
        ports = self.protocol.list_ports()
        self.port_combo.clear()
        self.port_combo.addItems(ports)
        if previous_port:
            index = self.port_combo.findText(previous_port)
            if index >= 0:
                self.port_combo.setCurrentIndex(index)
        self._sync_controls()

    def _choose_image(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Media",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp *.gif)",
        )
        if not file_path:
            return
        self._import_media(Path(file_path))

    def _history_selected(self, item: QListWidgetItem) -> None:
        media_path = Path(item.data(Qt.ItemDataRole.UserRole))
        if not media_path.is_file():
            QMessageBox.warning(self, "Missing media", f"Saved media not found: {media_path}")
            return

        self._set_selected_media(media_path, update_history_selection=False)
        self._save_settings()
        self._sync_controls()

    def _open_history_menu(self, position: QPoint) -> None:
        item = self.history_list.itemAt(position)
        menu = QMenu(self)

        open_folder_action = menu.addAction("Open media library folder")
        remove_action = None
        if item is not None:
            remove_action = menu.addAction("Remove from library")

        chosen = menu.exec(self.history_list.viewport().mapToGlobal(position))
        if chosen == open_folder_action:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.media_store.root)))
        elif remove_action is not None and chosen == remove_action:
            self._remove_media(Path(item.data(Qt.ItemDataRole.UserRole)))

    def _remove_media(self, media_path: Path) -> None:
        reply = QMessageBox.question(
            self,
            "Remove media",
            f"Remove {media_path.name} from the media library?",
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        running_state = self.gif_process.current_state()
        if running_state and Path(running_state.get("gif_path", "")) == media_path:
            self.gif_process.stop()

        history = self.settings_data.get("media_history", [])
        self.settings_data["media_history"] = [entry for entry in history if entry.get("path") != str(media_path)]

        try:
            media_path.unlink(missing_ok=True)
        except OSError as exc:
            QMessageBox.critical(self, "Remove failed", str(exc))
            return

        if self.selected_image == media_path:
            self.selected_image = None
            self.preview_movie = None
            self.preview.setMovie(None)
            self.preview.setPixmap(QPixmap())
            self.preview.setText("Preview")
            self.path_label.setText("No media selected")
            self.settings_data["last_media"] = ""
            self.settings_data["last_image"] = ""

        self._load_history()
        self._save_settings()
        self._sync_controls()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self.selected_image is not None:
            self._update_preview()

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if any(Path(url.toLocalFile()).suffix.lower() in SUPPORTED_SUFFIXES for url in event.mimeData().urls()):
            event.acceptProposedAction()
            return
        event.ignore()

    def dropEvent(self, event) -> None:  # noqa: N802
        for url in event.mimeData().urls():
            local_path = Path(url.toLocalFile())
            if local_path.suffix.lower() in SUPPORTED_SUFFIXES:
                self._import_media(local_path)
                event.acceptProposedAction()
                return
        event.ignore()

    def _import_media(self, source_path: Path) -> None:
        try:
            imported_path = self.media_store.import_file(source_path)
        except Exception as exc:
            QMessageBox.critical(self, "Import failed", str(exc))
            return

        self._save_history_entry(imported_path)
        self._save_settings()
        self._sync_controls()

    def _apply_media(self) -> None:
        if self.selected_image is None:
            QMessageBox.warning(self, "No media", "Choose media first.")
            return

        port = self.port_combo.currentText()
        if not port:
            QMessageBox.warning(self, "No device", "No /dev/ttyACM* port found.")
            return

        try:
            if self.selected_image.suffix.lower() == ".gif":
                if self.gif_process.is_running():
                    self.gif_process.stop()
                self.gif_process.start(self.selected_image, port)
                message = "GIF playback is running in the background."
            else:
                if self.gif_process.is_running():
                    self.gif_process.stop()
                self.apply_button.setEnabled(False)
                self.apply_button.setText("Applying...")
                self.protocol.send_image_file(self.selected_image, port)
                message = "Image sent to LCD successfully."
        except Exception as exc:
            QMessageBox.critical(self, "Apply failed", str(exc))
        else:
            self._save_settings()
            QMessageBox.information(self, "Done", message)
        finally:
            self.apply_button.setText("Apply to LCD")
            self._sync_controls()

    def _toggle_playback(self) -> None:
        if self.gif_process.is_running():
            self.gif_process.stop()
            self._sync_controls()
            return

        if self.selected_image is None or self.selected_image.suffix.lower() != ".gif":
            return

        port = self.port_combo.currentText()
        if not port:
            QMessageBox.warning(self, "No device", "No /dev/ttyACM* port found.")
            return

        try:
            self.gif_process.start(self.selected_image, port)
        except Exception as exc:
            QMessageBox.critical(self, "Playback failed", str(exc))
            return

        self._save_settings()
        self._sync_controls()

    def _toggle_autostart(self, enabled: bool) -> None:
        try:
            self.autostart.set_enabled(enabled)
        except OSError as exc:
            self.autostart_checkbox.blockSignals(True)
            self.autostart_checkbox.setChecked(not enabled)
            self.autostart_checkbox.blockSignals(False)
            QMessageBox.critical(self, "Startup update failed", str(exc))

    def closeEvent(self, event) -> None:  # noqa: N802
        self._save_settings()
        self.status_timer.stop()
        super().closeEvent(event)

    def _preview_target_size(self) -> QSize:
        return QSize(max(1, self.preview.width() - 24), max(1, self.preview.height() - 24))

    def _load_history(self) -> None:
        history = self.settings_data.get("media_history", [])
        self.history_list.blockSignals(True)
        self.history_list.clear()
        for entry in history:
            media_path = Path(entry.get("path", ""))
            if media_path.is_file():
                label = entry.get("label", media_path.name)
                item = QListWidgetItem(QIcon(self._thumbnail_for_media(media_path)), label)
                item.setData(Qt.ItemDataRole.UserRole, str(media_path))
                item.setToolTip(str(media_path))
                self.history_list.addItem(item)
        self.history_list.blockSignals(False)

    def _restore_last_media(self) -> None:
        last_media = self.settings_data.get("last_media", self.settings_data.get("last_image", ""))
        if not last_media:
            return

        candidate = Path(last_media)
        if candidate.exists() and candidate.is_file():
            self._set_selected_media(candidate, update_history_selection=True)

    def _set_selected_media(self, media_path: Path, update_history_selection: bool = True) -> None:
        self.selected_image = media_path
        self._update_preview()

        if not update_history_selection:
            return

        for index in range(self.history_list.count()):
            item = self.history_list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == str(media_path):
                self.history_list.setCurrentItem(item)
                break

    def _update_preview(self) -> None:
        if self.selected_image is None:
            return

        if self.selected_image.suffix.lower() == ".gif":
            self.path_label.setText(f"{self.selected_image.name} (stored in media library)")
            self.preview_movie = QMovie(str(self.selected_image))
            self.preview_movie.setScaledSize(self._preview_target_size())
            self.preview.setMovie(self.preview_movie)
            self.preview_movie.start()
            return

        self.path_label.setText(f"{self.selected_image.name} (stored in media library)")
        self.preview_movie = None
        self.preview.setMovie(None)
        pixmap = QPixmap(str(self.selected_image))
        scaled = pixmap.scaled(
            self._preview_target_size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview.setPixmap(scaled)

    def _sync_controls(self) -> None:
        running = self.gif_process.is_running()
        has_media = self.selected_image is not None
        has_port = bool(self.port_combo.currentText())
        is_gif = has_media and self.selected_image is not None and self.selected_image.suffix.lower() == ".gif"

        self.apply_button.setEnabled(has_media and has_port)
        self.playback_button.setEnabled(is_gif and has_port or running)
        self.playback_button.setText("Stop Playback" if running else "Start Playback")

    def _save_history_entry(self, media_path: Path) -> None:
        history = self.settings_data.get("media_history", [])
        history = [entry for entry in history if entry.get("path") != str(media_path)]
        history.insert(0, {"path": str(media_path), "label": media_path.name})
        self.settings_data["media_history"] = history[:MAX_HISTORY_ITEMS]
        self._load_history()
        self._set_selected_media(media_path)

    def _thumbnail_for_media(self, media_path: Path) -> QPixmap:
        if media_path.suffix.lower() == ".gif":
            movie = QMovie(str(media_path))
            movie.jumpToFrame(0)
            pixmap = movie.currentPixmap()
        else:
            pixmap = QPixmap(str(media_path))

        if pixmap.isNull():
            pixmap = QPixmap(72, 72)
            pixmap.fill(Qt.GlobalColor.black)

        return pixmap.scaled(
            72,
            72,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    def _save_settings(self) -> None:
        self.settings_data["last_port"] = self.port_combo.currentText()
        self.settings_data["last_media"] = str(self.selected_image) if self.selected_image else ""
        self.settings_data["last_image"] = self.settings_data["last_media"]
        self.settings.save(self.settings_data)
