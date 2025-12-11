"""
Settings dialog for application configuration.
"""

import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QSpinBox, QCheckBox, QFileDialog, QTabWidget,
    QWidget, QGroupBox, QFormLayout, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class SettingsDialog(QDialog):
    """
    Settings dialog for configuring the application.
    """

    settings_changed = pyqtSignal(dict)

    def __init__(self, settings: dict = None, parent=None):
        super().__init__(parent)
        self.settings = settings or self._default_settings()
        self._init_ui()
        self._load_settings()

    def _default_settings(self) -> dict:
        """Return default settings."""
        return {
            "download_dir": str(Path.home() / "Downloads" / "AnimeImages"),
            "max_concurrent": 1,
            "download_delay": 3.0,
            "auto_download": True,
            "skip_duplicates": True,
            "min_width": 200,
            "min_height": 200,
            "preferred_site": "danbooru",
            "default_rating": "general",
            "default_pages": 5,
            "theme": "dark",
        }

    def _init_ui(self):
        """Initialize the dialog UI."""
        self.setWindowTitle("Settings")
        self.setMinimumSize(500, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a2e;
            }
            QLabel {
                color: #ffffff;
            }
            QGroupBox {
                color: #e94560;
                border: 2px solid #2a2a4a;
                border-radius: 8px;
                margin-top: 16px;
                padding-top: 16px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Tab widget
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #2a2a4a;
                border-radius: 8px;
                background-color: #16213e;
            }
            QTabBar::tab {
                background-color: #1a1a2e;
                color: #a0a0a0;
                padding: 10px 20px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background-color: #16213e;
                color: #e94560;
            }
        """)

        # Download tab
        download_tab = self._create_download_tab()
        tabs.addTab(download_tab, "📥 Downloads")

        # Search tab
        search_tab = self._create_search_tab()
        tabs.addTab(search_tab, "🔍 Search")

        # Quality tab
        quality_tab = self._create_quality_tab()
        tabs.addTab(quality_tab, "✨ Quality")

        layout.addWidget(tabs)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #a0a0a0;
                border: 1px solid #a0a0a0;
                border-radius: 8px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                color: #ffffff;
                border-color: #ffffff;
            }
        """)
        reset_btn.clicked.connect(self._reset_defaults)
        btn_layout.addWidget(reset_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a4a;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #3a3a5a;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save Settings")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #e94560;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff6b6b;
            }
        """)
        save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _create_download_tab(self) -> QWidget:
        """Create the download settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Download location
        loc_group = QGroupBox("Download Location")
        loc_layout = QHBoxLayout(loc_group)

        self.dir_input = QLineEdit()
        self.dir_input.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a2e;
                border: 2px solid #2a2a4a;
                border-radius: 8px;
                padding: 10px;
                color: #ffffff;
            }
            QLineEdit:focus {
                border-color: #e94560;
            }
        """)
        loc_layout.addWidget(self.dir_input)

        browse_btn = QPushButton("Browse...")
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a4a;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
            }
            QPushButton:hover {
                background-color: #e94560;
            }
        """)
        browse_btn.clicked.connect(self._browse_directory)
        loc_layout.addWidget(browse_btn)

        layout.addWidget(loc_group)

        # Download behavior
        behavior_group = QGroupBox("Download Behavior")
        behavior_layout = QFormLayout(behavior_group)
        behavior_layout.setSpacing(12)

        self.auto_download_check = QCheckBox("Automatically download images")
        self.auto_download_check.setStyleSheet("color: #ffffff;")
        behavior_layout.addRow(self.auto_download_check)

        self.skip_dupes_check = QCheckBox("Skip duplicate images")
        self.skip_dupes_check.setStyleSheet("color: #ffffff;")
        behavior_layout.addRow(self.skip_dupes_check)

        # Concurrent downloads
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(1, 5)
        self.concurrent_spin.setStyleSheet("""
            QSpinBox {
                background-color: #1a1a2e;
                border: 2px solid #2a2a4a;
                border-radius: 8px;
                padding: 8px;
                color: #ffffff;
            }
        """)
        behavior_layout.addRow("Max concurrent downloads:", self.concurrent_spin)

        # Delay
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(1, 30)
        self.delay_spin.setSuffix(" seconds")
        self.delay_spin.setStyleSheet("""
            QSpinBox {
                background-color: #1a1a2e;
                border: 2px solid #2a2a4a;
                border-radius: 8px;
                padding: 8px;
                color: #ffffff;
            }
        """)
        behavior_layout.addRow("Delay between requests:", self.delay_spin)

        layout.addWidget(behavior_group)
        layout.addStretch()

        return widget

    def _create_search_tab(self) -> QWidget:
        """Create the search settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Default search settings
        search_group = QGroupBox("Default Search Settings")
        search_layout = QFormLayout(search_group)
        search_layout.setSpacing(12)

        # Preferred site
        self.site_combo = QComboBox()
        self.site_combo.addItems(["Danbooru", "Safebooru", "Gelbooru"])
        self.site_combo.setStyleSheet("""
            QComboBox {
                background-color: #1a1a2e;
                border: 2px solid #2a2a4a;
                border-radius: 8px;
                padding: 8px;
                color: #ffffff;
                min-width: 150px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #16213e;
                border: 2px solid #2a2a4a;
                selection-background-color: #e94560;
            }
        """)
        search_layout.addRow("Preferred site:", self.site_combo)

        # Default rating
        self.rating_combo = QComboBox()
        self.rating_combo.addItems(["General (Safe)", "All Ratings"])
        self.rating_combo.setStyleSheet("""
            QComboBox {
                background-color: #1a1a2e;
                border: 2px solid #2a2a4a;
                border-radius: 8px;
                padding: 8px;
                color: #ffffff;
                min-width: 150px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #16213e;
                border: 2px solid #2a2a4a;
                selection-background-color: #e94560;
            }
        """)
        search_layout.addRow("Default rating:", self.rating_combo)

        # Default pages
        self.pages_spin = QSpinBox()
        self.pages_spin.setRange(1, 100)
        self.pages_spin.setStyleSheet("""
            QSpinBox {
                background-color: #1a1a2e;
                border: 2px solid #2a2a4a;
                border-radius: 8px;
                padding: 8px;
                color: #ffffff;
            }
        """)
        search_layout.addRow("Default pages to fetch:", self.pages_spin)

        layout.addWidget(search_group)
        layout.addStretch()

        return widget

    def _create_quality_tab(self) -> QWidget:
        """Create the quality settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Image quality
        quality_group = QGroupBox("Image Quality Filters")
        quality_layout = QFormLayout(quality_group)
        quality_layout.setSpacing(12)

        # Minimum dimensions
        self.min_width_spin = QSpinBox()
        self.min_width_spin.setRange(0, 4000)
        self.min_width_spin.setSuffix(" px")
        self.min_width_spin.setStyleSheet("""
            QSpinBox {
                background-color: #1a1a2e;
                border: 2px solid #2a2a4a;
                border-radius: 8px;
                padding: 8px;
                color: #ffffff;
            }
        """)
        quality_layout.addRow("Minimum width:", self.min_width_spin)

        self.min_height_spin = QSpinBox()
        self.min_height_spin.setRange(0, 4000)
        self.min_height_spin.setSuffix(" px")
        self.min_height_spin.setStyleSheet("""
            QSpinBox {
                background-color: #1a1a2e;
                border: 2px solid #2a2a4a;
                border-radius: 8px;
                padding: 8px;
                color: #ffffff;
            }
        """)
        quality_layout.addRow("Minimum height:", self.min_height_spin)

        # Info label
        info_label = QLabel("Images smaller than these dimensions will be skipped.")
        info_label.setStyleSheet("color: #a0a0a0; font-size: 11px;")
        info_label.setWordWrap(True)
        quality_layout.addRow(info_label)

        layout.addWidget(quality_group)
        layout.addStretch()

        return widget

    def _browse_directory(self):
        """Open directory browser."""
        current = self.dir_input.text() or str(Path.home())
        directory = QFileDialog.getExistingDirectory(
            self, "Select Download Directory", current
        )
        if directory:
            self.dir_input.setText(directory)

    def _load_settings(self):
        """Load settings into UI."""
        self.dir_input.setText(self.settings.get("download_dir", ""))
        self.auto_download_check.setChecked(self.settings.get("auto_download", True))
        self.skip_dupes_check.setChecked(self.settings.get("skip_duplicates", True))
        self.concurrent_spin.setValue(self.settings.get("max_concurrent", 1))
        self.delay_spin.setValue(int(self.settings.get("download_delay", 3)))

        site = self.settings.get("preferred_site", "danbooru").capitalize()
        index = self.site_combo.findText(site)
        if index >= 0:
            self.site_combo.setCurrentIndex(index)

        rating = self.settings.get("default_rating", "general")
        self.rating_combo.setCurrentIndex(0 if rating == "general" else 1)

        self.pages_spin.setValue(self.settings.get("default_pages", 5))
        self.min_width_spin.setValue(self.settings.get("min_width", 200))
        self.min_height_spin.setValue(self.settings.get("min_height", 200))

    def _save_settings(self):
        """Save settings and close dialog."""
        self.settings = {
            "download_dir": self.dir_input.text(),
            "auto_download": self.auto_download_check.isChecked(),
            "skip_duplicates": self.skip_dupes_check.isChecked(),
            "max_concurrent": self.concurrent_spin.value(),
            "download_delay": float(self.delay_spin.value()),
            "preferred_site": self.site_combo.currentText().lower(),
            "default_rating": "general" if self.rating_combo.currentIndex() == 0 else "all",
            "default_pages": self.pages_spin.value(),
            "min_width": self.min_width_spin.value(),
            "min_height": self.min_height_spin.value(),
            "theme": "dark",
        }

        # Create download directory if needed
        download_dir = Path(self.settings["download_dir"])
        try:
            download_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            QMessageBox.warning(
                self, "Warning",
                f"Could not create download directory: {e}"
            )

        self.settings_changed.emit(self.settings)
        self.accept()

    def _reset_defaults(self):
        """Reset to default settings."""
        self.settings = self._default_settings()
        self._load_settings()

    def get_settings(self) -> dict:
        """Return current settings."""
        return self.settings
