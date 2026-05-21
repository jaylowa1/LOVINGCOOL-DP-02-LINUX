from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QComboBox,
)

from .protocol import LcdProtocol
from .settings import AppSettings


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.protocol = LcdProtocol()
        self.settings = AppSettings()
        self.settings_data = self.settings.load()
        self.selected_image: Path | None = None

        self.setWindowTitle("LOVINGCOOL LCD")
        self.resize(560, 460)
        self._build_ui()
        self._refresh_ports()
        self._restore_last_image()

    def _build_ui(self) -> None:
        root = QVBoxLayout()
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        self.path_label = QLabel("No image selected")
        self.path_label.setObjectName("PathLabel")
        self.path_label.setWordWrap(True)

        self.preview = QLabel("Preview")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumHeight(280)
        self.preview.setObjectName("PreviewBox")

        port_row = QHBoxLayout()
        self.port_combo = QComboBox()
        self.refresh_button = QPushButton("Refresh Ports")
        self.refresh_button.clicked.connect(self._refresh_ports)
        port_row.addWidget(self.port_combo)
        port_row.addWidget(self.refresh_button)

        action_row = QHBoxLayout()
        self.pick_button = QPushButton("Choose Image")
        self.send_button = QPushButton("Send to LCD")
        self.send_button.setEnabled(False)

        self.pick_button.clicked.connect(self._choose_image)
        self.send_button.clicked.connect(self._send_image)

        action_row.addWidget(self.pick_button)
        action_row.addWidget(self.send_button)

        root.addWidget(self.path_label)
        root.addLayout(port_row)
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

    def _choose_image(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if not file_path:
            return

        self.selected_image = Path(file_path)
        self._update_preview()
        self._save_settings()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self.selected_image is not None:
            self._update_preview()

    def _send_image(self) -> None:
        if self.selected_image is None:
            QMessageBox.warning(self, "No image", "Choose an image first.")
            return

        port = self.port_combo.currentText()
        if not port:
            QMessageBox.warning(self, "No device", "No /dev/ttyACM* port found.")
            return

        self.send_button.setEnabled(False)
        self.send_button.setText("Sending...")

        try:
            self.protocol.send_image_file(self.selected_image, port)
        except Exception as exc:
            QMessageBox.critical(self, "Send failed", str(exc))
        else:
            self._save_settings()
            QMessageBox.information(self, "Done", "Image sent to LCD successfully.")
        finally:
            self.send_button.setEnabled(True)
            self.send_button.setText("Send to LCD")

    def closeEvent(self, event) -> None:  # noqa: N802
        self._save_settings()
        super().closeEvent(event)

    def _restore_last_image(self) -> None:
        last_image = self.settings_data.get("last_image", "")
        if not last_image:
            return

        candidate = Path(last_image)
        if candidate.exists() and candidate.is_file():
            self.selected_image = candidate
            self._update_preview()

    def _update_preview(self) -> None:
        if self.selected_image is None:
            return

        self.path_label.setText(str(self.selected_image))
        pixmap = QPixmap(str(self.selected_image))
        scaled = pixmap.scaled(
            self.preview.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview.setPixmap(scaled)
        self.send_button.setEnabled(True)

    def _save_settings(self) -> None:
        self.settings_data["last_port"] = self.port_combo.currentText()
        self.settings_data["last_image"] = str(self.selected_image) if self.selected_image else ""
        self.settings.save(self.settings_data)
