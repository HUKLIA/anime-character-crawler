"""
Tag filter panel widget.
Displays categorized tags (character, series, artist, etc.) for filtering.
"""

from typing import Dict, List, Set
from collections import defaultdict

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from .crawler_thread import ImageResult
from .styles import AppStyles


class FlowLayout(QVBoxLayout):
    """Simple flow layout that wraps widgets."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSpacing(8)


class TagButton(QPushButton):
    """
    Clickable tag button with category styling.
    """

    tag_clicked = pyqtSignal(str, str)  # tag_name, category

    def __init__(self, tag: str, category: str = "general", count: int = 0, parent=None):
        super().__init__(parent)
        self.tag = tag
        self.category = category
        self.count = count

        self._init_ui()

    def _init_ui(self):
        """Initialize the button UI."""
        # Display text
        display_text = self.tag.replace("_", " ")
        if self.count > 0:
            self.setText(f"{display_text} ({self.count})")
        else:
            self.setText(display_text)

        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Category colors
        colors = {
            "character": "#4ecca3",
            "series": "#ffc107",
            "artist": "#9b59b6",
            "general": "#3498db",
            "meta": "#95a5a6",
        }
        color = colors.get(self.category, colors["general"])

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba({self._hex_to_rgb(color)}, 0.2);
                color: {color};
                border: 1px solid {color};
                border-radius: 12px;
                padding: 6px 14px;
                font-size: 11px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {color};
                color: white;
            }}
            QPushButton:checked {{
                background-color: {color};
                color: white;
            }}
        """)

        self.clicked.connect(lambda: self.tag_clicked.emit(self.tag, self.category))

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> str:
        """Convert hex to RGB string."""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f"{r}, {g}, {b}"


class TagSection(QFrame):
    """
    Section containing tags of a specific category.
    """

    tag_selected = pyqtSignal(str, str)  # tag, category

    def __init__(self, title: str, category: str, icon: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.category = category
        self.icon = icon
        self.tags: Dict[str, int] = {}  # tag -> count
        self.tag_buttons: List[TagButton] = []

        self._init_ui()

    def _init_ui(self):
        """Initialize section UI."""
        self.setStyleSheet("""
            QFrame {
                background-color: #16213e;
                border-radius: 12px;
                border: none;
                padding: 12px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        # Header
        header_layout = QHBoxLayout()

        title_label = QLabel(f"{self.icon} {self.title}")
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {self._get_category_color()}; background: transparent;")
        header_layout.addWidget(title_label)

        self.count_label = QLabel("(0)")
        self.count_label.setStyleSheet("color: #a0a0a0; background: transparent;")
        header_layout.addWidget(self.count_label)

        header_layout.addStretch()

        # Clear button
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #a0a0a0;
                border: none;
                font-size: 11px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                color: #e94560;
            }
        """)
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.setVisible(False)
        self.clear_btn.clicked.connect(self.clear_tags)
        header_layout.addWidget(self.clear_btn)

        layout.addLayout(header_layout)

        # Tags container (flow layout)
        self.tags_widget = QWidget()
        self.tags_widget.setStyleSheet("background: transparent;")
        self.tags_layout = QHBoxLayout(self.tags_widget)
        self.tags_layout.setSpacing(8)
        self.tags_layout.setContentsMargins(0, 0, 0, 0)
        self.tags_layout.addStretch()

        # Wrap in scroll area for horizontal scrolling
        scroll = QScrollArea()
        scroll.setWidget(self.tags_widget)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setMaximumHeight(60)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

        layout.addWidget(scroll)

        # Empty message
        self.empty_label = QLabel("No tags yet")
        self.empty_label.setStyleSheet("color: #a0a0a0; font-size: 11px; background: transparent;")
        layout.addWidget(self.empty_label)

    def _get_category_color(self) -> str:
        """Get color for this category."""
        colors = {
            "character": "#4ecca3",
            "series": "#ffc107",
            "artist": "#9b59b6",
            "general": "#3498db",
            "meta": "#95a5a6",
        }
        return colors.get(self.category, "#3498db")

    def add_tags(self, tags: List[str]):
        """Add tags to this section."""
        for tag in tags:
            if tag and tag not in self.tags:
                self.tags[tag] = 1
            elif tag:
                self.tags[tag] += 1

        self._rebuild_buttons()

    def _rebuild_buttons(self):
        """Rebuild tag buttons based on current tags."""
        # Clear existing buttons
        for btn in self.tag_buttons:
            self.tags_layout.removeWidget(btn)
            btn.deleteLater()
        self.tag_buttons.clear()

        # Sort by count (most popular first)
        sorted_tags = sorted(self.tags.items(), key=lambda x: -x[1])

        # Create buttons (limit to top 20)
        for tag, count in sorted_tags[:20]:
            btn = TagButton(tag, self.category, count)
            btn.tag_clicked.connect(lambda t, c: self.tag_selected.emit(t, c))
            self.tag_buttons.append(btn)
            self.tags_layout.insertWidget(self.tags_layout.count() - 1, btn)

        # Update UI state
        self.count_label.setText(f"({len(self.tags)})")
        self.empty_label.setVisible(len(self.tags) == 0)
        self.clear_btn.setVisible(len(self.tags) > 0)

    def clear_tags(self):
        """Clear all tags."""
        self.tags.clear()
        self._rebuild_buttons()


class TagPanel(QWidget):
    """
    Panel showing all tag categories with filtering options.
    """

    tag_filter_changed = pyqtSignal(str)  # Emits tag to add to search

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sections: Dict[str, TagSection] = {}
        self._init_ui()

    def _init_ui(self):
        """Initialize the panel UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)

        # Title
        title = QLabel("🏷️ Tags & Filters")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff;")
        layout.addWidget(title)

        # Create sections
        sections_data = [
            ("Characters", "character", "👤"),
            ("Series / Anime", "series", "📺"),
            ("Artists", "artist", "🎨"),
            ("General Tags", "general", "🔖"),
        ]

        for title_text, category, icon in sections_data:
            section = TagSection(title_text, category, icon)
            section.tag_selected.connect(self._on_tag_selected)
            self.sections[category] = section
            layout.addWidget(section)

        layout.addStretch()

    def _on_tag_selected(self, tag: str, category: str):
        """Handle tag selection."""
        self.tag_filter_changed.emit(tag)

    def process_image(self, image_result: ImageResult):
        """Extract and add tags from an image result."""
        # Character tags
        if image_result.character:
            chars = [c.strip() for c in image_result.character.split() if c.strip()]
            self.sections["character"].add_tags(chars)

        # Series tags
        if image_result.series:
            series = [s.strip() for s in image_result.series.split() if s.strip()]
            self.sections["series"].add_tags(series)

        # Artist tags
        if image_result.artist:
            artists = [a.strip() for a in image_result.artist.split() if a.strip()]
            self.sections["artist"].add_tags(artists)

        # General tags (first 10)
        if image_result.tags_list:
            general_tags = [t for t in image_result.tags_list[:10]
                          if t not in (image_result.character or "").split()
                          and t not in (image_result.series or "").split()
                          and t not in (image_result.artist or "").split()]
            self.sections["general"].add_tags(general_tags)

    def clear_all(self):
        """Clear all tag sections."""
        for section in self.sections.values():
            section.clear_tags()
