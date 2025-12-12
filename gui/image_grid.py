"""
Image grid display widget.
Shows scraped images in a responsive grid with thumbnails and metadata.
"""

import os
from pathlib import Path
from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QSizePolicy, QMenu,
    QApplication, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QUrl
from PyQt6.QtGui import QPixmap, QImage, QFont, QDesktopServices, QCursor

import requests
from io import BytesIO

from .crawler_thread import ImageResult
from .styles import AppStyles


class ImageCard(QFrame):
    """
    Individual image card widget showing thumbnail and metadata.
    """

    clicked = pyqtSignal(object)  # ImageResult
    download_requested = pyqtSignal(object)  # ImageResult

    def __init__(self, image_result: ImageResult, parent=None):
        super().__init__(parent)
        self.image_result = image_result
        self._pixmap = None
        self._init_ui()

    def _init_ui(self):
        """Initialize the card UI."""
        self.setFixedSize(300, 400)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QFrame {
                background-color: #16213e;
                border-radius: 12px;
                border: 2px solid #2a2a4a;
            }
            QFrame:hover {
                border-color: #e94560;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        # Thumbnail container
        thumb_container = QFrame()
        thumb_container.setFixedSize(284, 280)
        thumb_container.setStyleSheet("""
            QFrame {
                background-color: #1a1a2e;
                border-radius: 8px;
                border: none;
            }
        """)
        thumb_layout = QVBoxLayout(thumb_container)
        thumb_layout.setContentsMargins(0, 0, 0, 0)

        # Thumbnail image
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(284, 280)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setStyleSheet("background: transparent; border: none;")
        self.thumb_label.setText("Loading...")
        self.thumb_label.setStyleSheet("color: #a0a0a0; background: transparent;")
        thumb_layout.addWidget(self.thumb_label)

        layout.addWidget(thumb_container)

        # Info section
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        # Title (character or first tags)
        title_text = self._get_title()
        self.title_label = QLabel(title_text)
        self.title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #ffffff; border: none; background: transparent;")
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumHeight(40)
        info_layout.addWidget(self.title_label)

        # Metadata row
        meta_layout = QHBoxLayout()
        meta_layout.setSpacing(8)

        # Site badge
        site_label = QLabel(self.image_result.source_site.capitalize())
        site_label.setStyleSheet("""
            color: #e94560;
            font-size: 10px;
            background-color: rgba(233, 69, 96, 0.2);
            border-radius: 4px;
            padding: 2px 6px;
            border: none;
        """)
        meta_layout.addWidget(site_label)

        # Score
        if self.image_result.score:
            score_label = QLabel(f"⭐ {self.image_result.score}")
            score_label.setStyleSheet("color: #ffc107; font-size: 10px; border: none; background: transparent;")
            meta_layout.addWidget(score_label)

        # Dimensions
        if self.image_result.width and self.image_result.height:
            dim_label = QLabel(f"{self.image_result.width}x{self.image_result.height}")
            dim_label.setStyleSheet("color: #a0a0a0; font-size: 10px; border: none; background: transparent;")
            meta_layout.addWidget(dim_label)

        meta_layout.addStretch()
        info_layout.addLayout(meta_layout)

        layout.addLayout(info_layout)

        # Load thumbnail
        self._load_thumbnail()

    def _get_title(self) -> str:
        """Get display title for the card."""
        if self.image_result.character:
            # Clean up character name
            chars = self.image_result.character.replace("_", " ")
            return chars[:30] + "..." if len(chars) > 30 else chars

        if self.image_result.tags_list:
            # Use first few tags
            tags = [t.replace("_", " ") for t in self.image_result.tags_list[:3]]
            return ", ".join(tags)[:30]

        return f"Image #{self.image_result.post_id}"

    def _load_thumbnail(self):
        """Load the thumbnail image."""
        # Try to load from local file first
        if self.image_result.local_path and os.path.exists(self.image_result.local_path):
            pixmap = QPixmap(self.image_result.local_path)
            if not pixmap.isNull():
                self._set_pixmap(pixmap)
                return

        # Use preview URL for better quality, fallback to thumbnail
        thumb_url = self.image_result.preview_url or self.image_result.thumbnail_url
        if thumb_url:
            try:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

                # Pixiv requires Referer header
                if self.image_result.source_site == "pixiv" or "pximg.net" in thumb_url or "pixiv" in thumb_url:
                    headers["Referer"] = "https://www.pixiv.net/"

                response = requests.get(thumb_url, headers=headers, timeout=10)
                response.raise_for_status()

                image_data = BytesIO(response.content)
                image = QImage()
                image.loadFromData(image_data.getvalue())

                if not image.isNull():
                    pixmap = QPixmap.fromImage(image)
                    self._set_pixmap(pixmap)
                    return
            except:
                pass

        # Show placeholder
        self.thumb_label.setText("No Preview")
        self.thumb_label.setStyleSheet("color: #a0a0a0; background: #1a1a2e;")

    def _set_pixmap(self, pixmap: QPixmap):
        """Set and scale the thumbnail pixmap."""
        self._pixmap = pixmap
        scaled = pixmap.scaled(
            284, 280,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.thumb_label.setPixmap(scaled)

    def mousePressEvent(self, event):
        """Handle mouse click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.image_result)
        super().mousePressEvent(event)

    def contextMenuEvent(self, event):
        """Show context menu on right-click."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #16213e;
                border: 1px solid #2a2a4a;
                border-radius: 8px;
                padding: 8px;
            }
            QMenu::item {
                padding: 8px 24px;
                border-radius: 4px;
                color: #ffffff;
            }
            QMenu::item:selected {
                background-color: #e94560;
            }
        """)

        # Open in browser
        open_action = menu.addAction("🌐 Open in Browser")
        open_action.triggered.connect(self._open_in_browser)

        # Copy URL
        copy_action = menu.addAction("📋 Copy Image URL")
        copy_action.triggered.connect(self._copy_url)

        # Open local file
        if self.image_result.local_path:
            open_local = menu.addAction("📁 Open Downloaded File")
            open_local.triggered.connect(self._open_local)

        menu.exec(event.globalPos())

    def _open_in_browser(self):
        """Open the post page in browser."""
        url = self.image_result.page_url or self.image_result.image_url
        if url:
            QDesktopServices.openUrl(QUrl(url))

    def _copy_url(self):
        """Copy image URL to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.image_result.image_url)

    def _open_local(self):
        """Open the downloaded file."""
        if self.image_result.local_path and os.path.exists(self.image_result.local_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.image_result.local_path))


class ImageGrid(QWidget):
    """
    Grid widget displaying multiple image cards.
    """

    image_clicked = pyqtSignal(object)  # ImageResult

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_cards: List[ImageCard] = []
        self.columns = 3
        self._init_ui()

    def _init_ui(self):
        """Initialize the grid UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header with count
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(8, 8, 8, 8)

        self.count_label = QLabel("No images yet")
        self.count_label.setStyleSheet("color: #a0a0a0; font-size: 14px;")
        header_layout.addWidget(self.count_label)

        header_layout.addStretch()

        # Clear button
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #e94560;
                border: 1px solid #e94560;
                border-radius: 8px;
                padding: 6px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(233, 69, 96, 0.2);
            }
        """)
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.clicked.connect(self.clear_images)
        self.clear_btn.setVisible(False)
        header_layout.addWidget(self.clear_btn)

        layout.addLayout(header_layout)

        # Scroll area for grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        # Grid container
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setContentsMargins(8, 8, 8, 8)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        scroll.setWidget(self.grid_widget)
        layout.addWidget(scroll)

        # Empty state
        self.empty_label = QLabel("🔍 Search for anime images to get started!")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("""
            color: #a0a0a0;
            font-size: 16px;
            padding: 60px;
        """)
        self.grid_layout.addWidget(self.empty_label, 0, 0, 1, 4)

    def add_image(self, image_result: ImageResult):
        """Add an image to the grid."""
        # Hide empty state
        if self.empty_label.isVisible():
            self.empty_label.setVisible(False)

        # Create card
        card = ImageCard(image_result)
        card.clicked.connect(lambda r: self.image_clicked.emit(r))
        self.image_cards.append(card)

        # Calculate position
        count = len(self.image_cards)
        row = (count - 1) // self.columns
        col = (count - 1) % self.columns

        self.grid_layout.addWidget(card, row, col)

        # Update count
        self._update_count()
        self.clear_btn.setVisible(True)

    def clear_images(self):
        """Clear all images from the grid."""
        for card in self.image_cards:
            self.grid_layout.removeWidget(card)
            card.deleteLater()

        self.image_cards.clear()
        self.empty_label.setVisible(True)
        self._update_count()
        self.clear_btn.setVisible(False)

    def _update_count(self):
        """Update the image count label."""
        count = len(self.image_cards)
        if count == 0:
            self.count_label.setText("No images yet")
        elif count == 1:
            self.count_label.setText("1 image found")
        else:
            self.count_label.setText(f"{count} images found")

    def get_image_count(self) -> int:
        """Get number of images in the grid."""
        return len(self.image_cards)

    def set_columns(self, columns: int):
        """Set number of columns in the grid."""
        if columns != self.columns:
            self.columns = columns
            self._relayout()

    def _relayout(self):
        """Re-layout all cards after column change."""
        for i, card in enumerate(self.image_cards):
            row = i // self.columns
            col = i % self.columns
            self.grid_layout.addWidget(card, row, col)
