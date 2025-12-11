"""
Search widget with autocomplete functionality.
Provides a search bar with tag suggestions and quick filters.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton,
    QCompleter, QListWidget, QListWidgetItem, QLabel, QFrame,
    QComboBox, QSpinBox, QCheckBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QStringListModel
from PyQt6.QtGui import QIcon, QFont

from .crawler_thread import TagSuggestionThread
from .styles import AppStyles


class SearchWidget(QWidget):
    """
    Search widget with autocomplete and filters.

    Signals:
        search_requested: Emitted when user wants to search (tags, site, max_pages)
        cancel_requested: Emitted when user wants to cancel search
    """

    search_requested = pyqtSignal(str, str, int, str, bool)  # tags, site, max_pages, rating, download
    cancel_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.suggestion_thread = TagSuggestionThread()
        self.suggestion_timer = QTimer()
        self.suggestion_timer.setSingleShot(True)
        self.suggestion_timer.timeout.connect(self._fetch_suggestions)

        self._is_searching = False
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        # Title section
        title_label = QLabel("🎨 Anime Image Crawler")
        title_label.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #e94560; margin-bottom: 8px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        subtitle_label = QLabel("Search and download anime images from popular booru sites")
        subtitle_label.setStyleSheet("color: #a0a0a0; font-size: 14px; margin-bottom: 16px;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)

        # Search bar section
        search_frame = QFrame()
        search_frame.setStyleSheet("""
            QFrame {
                background-color: #16213e;
                border-radius: 16px;
                padding: 16px;
            }
        """)
        search_layout = QVBoxLayout(search_frame)
        search_layout.setSpacing(12)

        # Main search row
        search_row = QHBoxLayout()
        search_row.setSpacing(12)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Enter character name, tags, or series... (e.g., hatsune_miku, blue_hair)")
        self.search_input.setMinimumHeight(50)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a2e;
                border: 2px solid #2a2a4a;
                border-radius: 25px;
                padding: 12px 24px;
                font-size: 15px;
                color: #ffffff;
            }
            QLineEdit:focus {
                border-color: #e94560;
            }
        """)
        search_row.addWidget(self.search_input)

        # Search button
        self.search_btn = QPushButton("Search")
        self.search_btn.setMinimumSize(120, 50)
        self.search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #e94560;
                color: white;
                border: none;
                border-radius: 25px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff6b6b;
            }
            QPushButton:pressed {
                background-color: #c73e54;
            }
            QPushButton:disabled {
                background-color: #4a4a6a;
            }
        """)
        search_row.addWidget(self.search_btn)

        search_layout.addLayout(search_row)

        # Suggestion list (hidden by default)
        self.suggestion_list = QListWidget()
        self.suggestion_list.setMaximumHeight(200)
        self.suggestion_list.setVisible(False)
        self.suggestion_list.setStyleSheet("""
            QListWidget {
                background-color: #1a1a2e;
                border: 2px solid #e94560;
                border-radius: 12px;
                padding: 8px;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 8px;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: rgba(233, 69, 96, 0.3);
            }
            QListWidget::item:selected {
                background-color: #e94560;
            }
        """)
        search_layout.addWidget(self.suggestion_list)

        # Filter row
        filter_row = QHBoxLayout()
        filter_row.setSpacing(16)

        # Site selector
        site_label = QLabel("Site:")
        site_label.setStyleSheet("color: #a0a0a0;")
        filter_row.addWidget(site_label)

        self.site_combo = QComboBox()
        self.site_combo.addItems(["Danbooru", "Safebooru", "Gelbooru"])
        self.site_combo.setMinimumWidth(130)
        self.site_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        filter_row.addWidget(self.site_combo)

        filter_row.addSpacing(20)

        # Rating filter
        rating_label = QLabel("Rating:")
        rating_label.setStyleSheet("color: #a0a0a0;")
        filter_row.addWidget(rating_label)

        self.rating_combo = QComboBox()
        self.rating_combo.addItems(["General (Safe)", "All Ratings"])
        self.rating_combo.setMinimumWidth(140)
        self.rating_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        filter_row.addWidget(self.rating_combo)

        filter_row.addSpacing(20)

        # Max pages
        pages_label = QLabel("Pages:")
        pages_label.setStyleSheet("color: #a0a0a0;")
        filter_row.addWidget(pages_label)

        self.pages_spin = QSpinBox()
        self.pages_spin.setRange(1, 50)
        self.pages_spin.setValue(5)
        self.pages_spin.setMinimumWidth(80)
        self.pages_spin.setStyleSheet("""
            QSpinBox {
                background-color: #1a1a2e;
                border: 2px solid #2a2a4a;
                border-radius: 8px;
                padding: 8px;
                color: #ffffff;
            }
            QSpinBox:focus {
                border-color: #e94560;
            }
        """)
        filter_row.addWidget(self.pages_spin)

        filter_row.addSpacing(20)

        # Download checkbox
        self.download_check = QCheckBox("Download Images")
        self.download_check.setChecked(True)
        self.download_check.setCursor(Qt.CursorShape.PointingHandCursor)
        filter_row.addWidget(self.download_check)

        filter_row.addStretch()

        search_layout.addLayout(filter_row)

        # Quick tag buttons
        quick_tags_layout = QHBoxLayout()
        quick_tags_layout.setSpacing(8)

        quick_label = QLabel("Quick Tags:")
        quick_label.setStyleSheet("color: #a0a0a0; margin-right: 8px;")
        quick_tags_layout.addWidget(quick_label)

        quick_tags = [
            ("1girl", "#4ecca3"),
            ("blue_hair", "#3498db"),
            ("school_uniform", "#9b59b6"),
            ("smile", "#ffc107"),
            ("rating:general", "#e94560"),
        ]

        for tag, color in quick_tags:
            btn = QPushButton(tag)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba({self._hex_to_rgb(color)}, 0.2);
                    color: {color};
                    border: 1px solid {color};
                    border-radius: 12px;
                    padding: 6px 14px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: {color};
                    color: white;
                }}
            """)
            btn.clicked.connect(lambda checked, t=tag: self._add_quick_tag(t))
            quick_tags_layout.addWidget(btn)

        quick_tags_layout.addStretch()
        search_layout.addLayout(quick_tags_layout)

        layout.addWidget(search_frame)

    def _connect_signals(self):
        """Connect widget signals to slots."""
        self.search_input.textChanged.connect(self._on_text_changed)
        self.search_input.returnPressed.connect(self._on_search_clicked)
        self.search_btn.clicked.connect(self._on_search_clicked)
        self.suggestion_list.itemClicked.connect(self._on_suggestion_clicked)
        self.suggestion_thread.suggestions_ready.connect(self._on_suggestions_ready)
        self.site_combo.currentTextChanged.connect(self._on_site_changed)

    def _on_text_changed(self, text: str):
        """Handle search text changes for autocomplete."""
        # Reset timer for debouncing
        self.suggestion_timer.stop()

        if len(text) >= 2:
            # Start timer to fetch suggestions
            self.suggestion_timer.start(300)  # 300ms debounce
        else:
            self.suggestion_list.setVisible(False)

    def _fetch_suggestions(self):
        """Fetch tag suggestions from the API."""
        text = self.search_input.text().strip()

        # Get the last word for suggestion
        words = text.split()
        if words:
            query = words[-1]
            site = self.site_combo.currentText().lower()
            self.suggestion_thread.configure(query, site)
            self.suggestion_thread.start()

    def _on_suggestions_ready(self, suggestions: list):
        """Handle received tag suggestions."""
        self.suggestion_list.clear()

        if not suggestions:
            self.suggestion_list.setVisible(False)
            return

        for suggestion in suggestions:
            name = suggestion.get("name", "")
            count = suggestion.get("count", 0)
            category = suggestion.get("category", "general")

            # Format count nicely
            if count >= 1000000:
                count_str = f"{count / 1000000:.1f}M"
            elif count >= 1000:
                count_str = f"{count / 1000:.1f}K"
            else:
                count_str = str(count)

            # Category color
            cat_colors = {
                "0": "#3498db",      # General
                "1": "#e94560",      # Artist
                "3": "#9b59b6",      # Copyright/Series
                "4": "#4ecca3",      # Character
                "5": "#ffc107",      # Meta
                "general": "#3498db",
                "artist": "#e94560",
                "copyright": "#9b59b6",
                "character": "#4ecca3",
                "meta": "#ffc107",
            }
            color = cat_colors.get(str(category), "#3498db")

            item = QListWidgetItem(f"{name}  ({count_str} posts)")
            item.setData(Qt.ItemDataRole.UserRole, name)
            item.setForeground(self.palette().text())
            self.suggestion_list.addItem(item)

        self.suggestion_list.setVisible(True)

    def _on_suggestion_clicked(self, item: QListWidgetItem):
        """Handle suggestion selection."""
        tag = item.data(Qt.ItemDataRole.UserRole)
        current_text = self.search_input.text().strip()

        # Replace last word with selected tag
        words = current_text.split()
        if words:
            words[-1] = tag
        else:
            words = [tag]

        self.search_input.setText(" ".join(words) + " ")
        self.suggestion_list.setVisible(False)
        self.search_input.setFocus()

    def _add_quick_tag(self, tag: str):
        """Add a quick tag to the search input."""
        current = self.search_input.text().strip()
        if current:
            if tag not in current:
                self.search_input.setText(f"{current} {tag}")
        else:
            self.search_input.setText(tag)
        self.search_input.setFocus()

    def _on_site_changed(self, site: str):
        """Handle site selection change."""
        # Clear suggestions when site changes
        self.suggestion_list.clear()
        self.suggestion_list.setVisible(False)

    def _on_search_clicked(self):
        """Handle search button click."""
        if self._is_searching:
            # Cancel search
            self.cancel_requested.emit()
            return

        tags = self.search_input.text().strip()
        if not tags:
            return

        site = self.site_combo.currentText().lower()
        max_pages = self.pages_spin.value()
        rating = "general" if self.rating_combo.currentIndex() == 0 else "all"
        download = self.download_check.isChecked()

        self.suggestion_list.setVisible(False)
        self.search_requested.emit(tags, site, max_pages, rating, download)

    def set_searching(self, is_searching: bool):
        """Update UI state for searching status."""
        self._is_searching = is_searching

        if is_searching:
            self.search_btn.setText("Cancel")
            self.search_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ff4757;
                    color: white;
                    border: none;
                    border-radius: 25px;
                    font-size: 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #ff6b81;
                }
            """)
            self.search_input.setEnabled(False)
            self.site_combo.setEnabled(False)
            self.rating_combo.setEnabled(False)
            self.pages_spin.setEnabled(False)
        else:
            self.search_btn.setText("Search")
            self.search_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e94560;
                    color: white;
                    border: none;
                    border-radius: 25px;
                    font-size: 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #ff6b6b;
                }
                QPushButton:pressed {
                    background-color: #c73e54;
                }
            """)
            self.search_input.setEnabled(True)
            self.site_combo.setEnabled(True)
            self.rating_combo.setEnabled(True)
            self.pages_spin.setEnabled(True)

    def get_search_tags(self) -> str:
        """Get current search tags."""
        return self.search_input.text().strip()

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> str:
        """Convert hex color to RGB string."""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f"{r}, {g}, {b}"
