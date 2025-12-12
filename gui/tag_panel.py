"""
Tag filter panel widget - compact with scroll.
"""

from typing import Dict, List
from collections import defaultdict

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from .crawler_thread import ImageResult
from .styles import AppStyles


class TagButton(QPushButton):
    """Clickable tag button with category styling."""

    tag_clicked = pyqtSignal(str, str)

    def __init__(self, tag: str, category: str = "general", count: int = 0, parent=None):
        super().__init__(parent)
        self.tag = tag
        self.category = category
        self.count = count
        self._init_ui()

    def _init_ui(self):
        display_text = self.tag.replace("_", " ")
        if self.count > 0:
            self.setText(f"{display_text} ({self.count})")
        else:
            self.setText(display_text)

        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        colors = {
            "character": "#4ecca3",
            "series": "#ffc107",
            "artist": "#9b59b6",
            "general": "#3498db",
        }
        color = colors.get(self.category, colors["general"])

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba({self._hex_to_rgb(color)}, 0.2);
                color: {color};
                border: 1px solid {color};
                border-radius: 10px;
                padding: 3px 8px;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: {color};
                color: white;
            }}
        """)

        self.clicked.connect(lambda: self.tag_clicked.emit(self.tag, self.category))

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> str:
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f"{r}, {g}, {b}"


class TagSection(QFrame):
    """Section containing tags of a specific category."""

    tag_selected = pyqtSignal(str, str)

    def __init__(self, title: str, category: str, icon: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.category = category
        self.icon = icon
        self.tags: Dict[str, int] = {}
        self.tag_buttons: List[TagButton] = []
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("background-color: #16213e; border-radius: 6px;")

        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(6, 4, 6, 4)

        # Header
        header = QHBoxLayout()
        header.setSpacing(4)

        title_label = QLabel(f"{self.icon} {self.title}")
        title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {self._get_color()}; background: transparent;")
        header.addWidget(title_label)

        self.count_label = QLabel("(0)")
        self.count_label.setStyleSheet("color: #606060; font-size: 9px; background: transparent;")
        header.addWidget(self.count_label)
        header.addStretch()

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setStyleSheet("background: transparent; color: #606060; border: none; font-size: 9px;")
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.setVisible(False)
        self.clear_btn.clicked.connect(self.clear_tags)
        header.addWidget(self.clear_btn)

        layout.addLayout(header)

        # Tags flow container
        self.tags_widget = QWidget()
        self.tags_widget.setStyleSheet("background: transparent;")
        self.tags_layout = QHBoxLayout(self.tags_widget)
        self.tags_layout.setSpacing(4)
        self.tags_layout.setContentsMargins(0, 0, 0, 0)
        self.tags_layout.addStretch()

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidget(self.tags_widget)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFixedHeight(32)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:horizontal { height: 3px; background: #1a1a2e; }
            QScrollBar::handle:horizontal { background: #3a3a5a; border-radius: 1px; }
        """)

        layout.addWidget(scroll)

        # Empty message
        self.empty_label = QLabel("No tags")
        self.empty_label.setStyleSheet("color: #404040; font-size: 9px; background: transparent;")
        layout.addWidget(self.empty_label)

    def _get_color(self) -> str:
        colors = {"character": "#4ecca3", "series": "#ffc107", "artist": "#9b59b6", "general": "#3498db"}
        return colors.get(self.category, "#3498db")

    def add_tags(self, tags: List[str]):
        for tag in tags:
            if tag and tag not in self.tags:
                self.tags[tag] = 1
            elif tag:
                self.tags[tag] += 1
        self._rebuild_buttons()

    def _rebuild_buttons(self):
        for btn in self.tag_buttons:
            self.tags_layout.removeWidget(btn)
            btn.deleteLater()
        self.tag_buttons.clear()

        sorted_tags = sorted(self.tags.items(), key=lambda x: -x[1])

        for tag, count in sorted_tags[:10]:
            btn = TagButton(tag, self.category, count)
            btn.tag_clicked.connect(lambda t, c: self.tag_selected.emit(t, c))
            self.tag_buttons.append(btn)
            self.tags_layout.insertWidget(self.tags_layout.count() - 1, btn)

        self.count_label.setText(f"({len(self.tags)})")
        self.empty_label.setVisible(len(self.tags) == 0)
        self.clear_btn.setVisible(len(self.tags) > 0)

    def clear_tags(self):
        self.tags.clear()
        for btn in self.tag_buttons:
            self.tags_layout.removeWidget(btn)
            btn.deleteLater()
        self.tag_buttons.clear()
        self.count_label.setText("(0)")
        self.empty_label.setVisible(True)
        self.clear_btn.setVisible(False)


class TagPanel(QWidget):
    """Panel showing all tag categories."""

    tag_filter_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sections: Dict[str, TagSection] = {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)

        # Title
        title = QLabel("🏷️ Tags & Filters")
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff;")
        layout.addWidget(title)

        # Scroll area for sections
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { width: 6px; background: #1a1a2e; border-radius: 3px; }
            QScrollBar::handle:vertical { background: #3a3a5a; border-radius: 3px; }
        """)

        sections_widget = QWidget()
        sections_widget.setStyleSheet("background: transparent;")
        sections_layout = QVBoxLayout(sections_widget)
        sections_layout.setSpacing(4)
        sections_layout.setContentsMargins(0, 0, 0, 0)

        sections_data = [
            ("Characters", "character", "👤"),
            ("Series", "series", "📺"),
            ("Artists", "artist", "🎨"),
            ("Tags", "general", "🔖"),
        ]

        for title_text, category, icon in sections_data:
            section = TagSection(title_text, category, icon)
            section.tag_selected.connect(self._on_tag_selected)
            self.sections[category] = section
            sections_layout.addWidget(section)

        sections_layout.addStretch()
        scroll.setWidget(sections_widget)
        layout.addWidget(scroll, 1)

    def _on_tag_selected(self, tag: str, category: str):
        self.tag_filter_changed.emit(tag)

    def process_image(self, image_result: ImageResult):
        if image_result.character:
            chars = [c.strip() for c in image_result.character.split() if c.strip()]
            self.sections["character"].add_tags(chars)

        if image_result.series:
            series = [s.strip() for s in image_result.series.split() if s.strip()]
            self.sections["series"].add_tags(series)

        if image_result.artist:
            artists = [a.strip() for a in image_result.artist.split() if a.strip()]
            self.sections["artist"].add_tags(artists)

        if image_result.tags_list:
            general_tags = [t for t in image_result.tags_list[:8]
                          if t not in (image_result.character or "").split()
                          and t not in (image_result.series or "").split()
                          and t not in (image_result.artist or "").split()]
            self.sections["general"].add_tags(general_tags)

    def clear_all(self):
        for section in self.sections.values():
            section.clear_tags()
