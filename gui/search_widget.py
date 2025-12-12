"""
Search widget with autocomplete functionality.
Provides a search bar with tag suggestions and quick filters.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton,
    QCompleter, QListWidget, QListWidgetItem, QLabel, QFrame,
    QComboBox, QSpinBox, QCheckBox, QSizePolicy, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QStringListModel
from PyQt6.QtGui import QIcon, QFont

from .crawler_thread import TagSuggestionThread
from .styles import AppStyles


class SearchWidget(QWidget):
    """
    Search widget with autocomplete and filters.
    """

    search_requested = pyqtSignal(str, str, int, str, bool)
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
        layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)

        # Compact search frame
        search_frame = QFrame()
        search_frame.setStyleSheet("""
            QFrame {
                background-color: #16213e;
                border-radius: 8px;
            }
        """)
        search_layout = QVBoxLayout(search_frame)
        search_layout.setSpacing(4)
        search_layout.setContentsMargins(8, 6, 8, 6)

        # Row 1: Title + Search bar + Button
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        # Title
        title_label = QLabel("🎨 Anime Crawler")
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #e94560;")
        title_label.setFixedWidth(130)
        row1.addWidget(title_label)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter character, tags, or series (spaces auto-convert to underscores)")
        self.search_input.setMinimumHeight(32)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a2e;
                border: 1px solid #2a2a4a;
                border-radius: 16px;
                padding: 6px 14px;
                font-size: 12px;
                color: #ffffff;
            }
            QLineEdit:focus {
                border-color: #e94560;
            }
        """)
        row1.addWidget(self.search_input, 1)

        # Search button
        self.search_btn = QPushButton("Search")
        self.search_btn.setMinimumSize(70, 32)
        self.search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #e94560;
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff6b6b;
            }
            QPushButton:pressed {
                background-color: #c73e54;
            }
        """)
        row1.addWidget(self.search_btn)

        search_layout.addLayout(row1)

        # Suggestion list (hidden by default)
        self.suggestion_list = QListWidget()
        self.suggestion_list.setMaximumHeight(120)
        self.suggestion_list.setVisible(False)
        self.suggestion_list.setStyleSheet("""
            QListWidget {
                background-color: #1a1a2e;
                border: 1px solid #e94560;
                border-radius: 6px;
                padding: 2px;
            }
            QListWidget::item {
                padding: 4px;
                border-radius: 3px;
                color: #ffffff;
                font-size: 11px;
            }
            QListWidget::item:hover {
                background-color: rgba(233, 69, 96, 0.3);
            }
            QListWidget::item:selected {
                background-color: #e94560;
            }
        """)
        search_layout.addWidget(self.suggestion_list)

        # Row 2: All filters in one line with scroll
        filter_scroll = QScrollArea()
        filter_scroll.setWidgetResizable(True)
        filter_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        filter_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        filter_scroll.setFixedHeight(36)
        filter_scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:horizontal { height: 4px; background: #1a1a2e; }
            QScrollBar::handle:horizontal { background: #3a3a5a; border-radius: 2px; }
        """)

        filter_widget = QWidget()
        filter_widget.setStyleSheet("background: transparent;")
        row2 = QHBoxLayout(filter_widget)
        row2.setSpacing(6)
        row2.setContentsMargins(0, 0, 0, 0)

        # Site selector
        site_label = QLabel("Site:")
        site_label.setStyleSheet("color: #a0a0a0; font-size: 11px;")
        row2.addWidget(site_label)

        self.site_combo = QComboBox()
        self.site_combo.addItems(["Danbooru", "Safebooru", "Gelbooru", "Konachan", "Yande.re", "Zerochan", "Anime-Pictures", "Pixiv"])
        self.site_combo.setFixedWidth(100)
        self.site_combo.setStyleSheet("font-size: 11px;")
        self.site_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        row2.addWidget(self.site_combo)

        # Rating filter
        rating_label = QLabel("Rating:")
        rating_label.setStyleSheet("color: #a0a0a0; font-size: 11px;")
        row2.addWidget(rating_label)

        self.rating_combo = QComboBox()
        self.rating_combo.addItems(["Safe", "All"])
        self.rating_combo.setFixedWidth(60)
        self.rating_combo.setStyleSheet("font-size: 11px;")
        self.rating_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        row2.addWidget(self.rating_combo)

        # Max pages
        pages_label = QLabel("Pages:")
        pages_label.setStyleSheet("color: #a0a0a0; font-size: 11px;")
        row2.addWidget(pages_label)

        self.pages_spin = QSpinBox()
        self.pages_spin.setRange(1, 50)
        self.pages_spin.setValue(5)
        self.pages_spin.setFixedWidth(50)
        self.pages_spin.setStyleSheet("""
            QSpinBox {
                background-color: #1a1a2e;
                border: 1px solid #2a2a4a;
                border-radius: 4px;
                padding: 2px;
                color: #ffffff;
                font-size: 11px;
            }
        """)
        row2.addWidget(self.pages_spin)

        # Download checkbox
        self.download_check = QCheckBox("Download")
        self.download_check.setChecked(False)
        self.download_check.setCursor(Qt.CursorShape.PointingHandCursor)
        self.download_check.setStyleSheet("font-size: 11px; color: #a0a0a0;")
        row2.addWidget(self.download_check)

        # Separator
        sep = QLabel("|")
        sep.setStyleSheet("color: #3a3a5a;")
        row2.addWidget(sep)

        # Quick tags
        quick_label = QLabel("Quick:")
        quick_label.setStyleSheet("color: #a0a0a0; font-size: 11px;")
        row2.addWidget(quick_label)

        quick_tags = [
            ("1girl", "#4ecca3"),
            ("blue_hair", "#3498db"),
            ("school_uniform", "#9b59b6"),
            ("smile", "#ffc107"),
        ]

        for tag, color in quick_tags:
            btn = QPushButton(tag)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(22)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba({self._hex_to_rgb(color)}, 0.2);
                    color: {color};
                    border: 1px solid {color};
                    border-radius: 8px;
                    padding: 2px 8px;
                    font-size: 10px;
                }}
                QPushButton:hover {{
                    background-color: {color};
                    color: white;
                }}
            """)
            btn.clicked.connect(lambda checked, t=tag: self._add_quick_tag(t))
            row2.addWidget(btn)

        row2.addStretch()

        filter_scroll.setWidget(filter_widget)
        search_layout.addWidget(filter_scroll)

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
        self.suggestion_timer.stop()
        if len(text) >= 2:
            self.suggestion_timer.start(300)
        else:
            self.suggestion_list.setVisible(False)

    def _fetch_suggestions(self):
        """Fetch tag suggestions from the API."""
        text = self.search_input.text().strip()
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
            if count >= 1000000:
                count_str = f"{count / 1000000:.1f}M"
            elif count >= 1000:
                count_str = f"{count / 1000:.1f}K"
            else:
                count_str = str(count)

            item = QListWidgetItem(f"{name}  ({count_str})")
            item.setData(Qt.ItemDataRole.UserRole, name)
            self.suggestion_list.addItem(item)

        self.suggestion_list.setVisible(True)

    def _on_suggestion_clicked(self, item: QListWidgetItem):
        """Handle suggestion selection."""
        tag = item.data(Qt.ItemDataRole.UserRole)
        current_text = self.search_input.text().strip()
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
        self.suggestion_list.clear()
        self.suggestion_list.setVisible(False)

    def _on_search_clicked(self):
        """Handle search button click."""
        if self._is_searching:
            self.cancel_requested.emit()
            return

        tags = self.search_input.text().strip()
        if not tags:
            return

        # Auto-convert spaces to underscores
        tag_parts = []
        for part in tags.split(","):
            part = part.strip()
            if part:
                tag_parts.append(part.replace(" ", "_"))
        tags = " ".join(tag_parts)
        self.search_input.setText(tags)

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
                    border-radius: 16px;
                    font-size: 12px;
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
                    border-radius: 16px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #ff6b6b;
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
