"""
Image detail popup dialog.
Shows full image preview with metadata and download options.
"""

import os
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QFileDialog, QMessageBox, QApplication,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, QUrl
from PyQt6.QtGui import QPixmap, QImage, QFont, QDesktopServices

import requests
from io import BytesIO

from .crawler_thread import ImageResult


class ImageDetailDialog(QDialog):
    """
    Modal dialog showing image details with download and navigation options.
    """

    def __init__(self, image_result: ImageResult, parent=None):
        super().__init__(parent)
        self.image_result = image_result
        self._pixmap = None
        self._init_ui()
        self._load_image()

    def _init_ui(self):
        """Initialize the dialog UI."""
        self.setWindowTitle("Image Details")
        self.setMinimumSize(900, 700)
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
                background-color: #0f0f1a;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Main content area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # Left side - Image preview
        image_frame = QFrame()
        image_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a2e;
                border-radius: 12px;
                border: 2px solid #2a2a4a;
            }
        """)
        image_layout = QVBoxLayout(image_frame)
        image_layout.setContentsMargins(10, 10, 10, 10)

        # Scroll area for large images
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(500, 450)
        self.image_label.setStyleSheet("background: transparent;")
        self.image_label.setText("Loading image...")
        scroll.setWidget(self.image_label)

        image_layout.addWidget(scroll)
        content_layout.addWidget(image_frame, stretch=2)

        # Right side - Info panel
        info_frame = QFrame()
        info_frame.setFixedWidth(300)
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #16213e;
                border-radius: 12px;
                border: 2px solid #2a2a4a;
            }
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(12)
        info_layout.setContentsMargins(16, 16, 16, 16)

        # Title
        title_label = QLabel("Image Info")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #e94560;")
        info_layout.addWidget(title_label)

        # Character name
        if self.image_result.character:
            char_name = self.image_result.character.replace("_", " ")
            self._add_info_row(info_layout, "Character", char_name[:50])

        # Series/Copyright
        if self.image_result.series:
            series_name = self.image_result.series.replace("_", " ")
            self._add_info_row(info_layout, "Series", series_name[:50])

        # Artist
        if self.image_result.artist:
            artist_name = self.image_result.artist.replace("_", " ")
            self._add_info_row(info_layout, "Artist", artist_name[:50])

        # Source site
        self._add_info_row(info_layout, "Source", self.image_result.source_site.capitalize())

        # Post ID
        self._add_info_row(info_layout, "Post ID", self.image_result.post_id)

        # Dimensions
        if self.image_result.width and self.image_result.height:
            dims = f"{self.image_result.width} x {self.image_result.height}"
            self._add_info_row(info_layout, "Dimensions", dims)

        # Score
        if self.image_result.score:
            self._add_info_row(info_layout, "Score", str(self.image_result.score))

        # Rating
        rating_map = {"g": "General", "s": "Sensitive", "q": "Questionable", "e": "Explicit", "safe": "Safe"}
        rating_text = rating_map.get(self.image_result.rating, self.image_result.rating)
        self._add_info_row(info_layout, "Rating", rating_text)

        # Tags section
        if self.image_result.tags_list:
            tags_label = QLabel("Tags")
            tags_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            tags_label.setStyleSheet("color: #a0a0a0; margin-top: 8px;")
            info_layout.addWidget(tags_label)

            tags_text = ", ".join(self.image_result.tags_list[:15])
            if len(self.image_result.tags_list) > 15:
                tags_text += f" (+{len(self.image_result.tags_list) - 15} more)"
            tags_value = QLabel(tags_text)
            tags_value.setWordWrap(True)
            tags_value.setStyleSheet("color: #ffffff; font-size: 11px;")
            info_layout.addWidget(tags_value)

        info_layout.addStretch()
        content_layout.addWidget(info_frame)

        layout.addLayout(content_layout)

        # Button row
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        # Back button
        back_btn = QPushButton("Back")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a4a;
                color: #ffffff;
                border: 2px solid #3a3a5a;
            }
            QPushButton:hover {
                background-color: #3a3a5a;
            }
        """)
        back_btn.clicked.connect(self.close)
        button_layout.addWidget(back_btn)

        button_layout.addStretch()

        # Copy URL button
        copy_btn = QPushButton("Copy URL")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: #ffffff;
                border: none;
            }
            QPushButton:hover {
                background-color: #5dade2;
            }
        """)
        copy_btn.clicked.connect(self._copy_url)
        button_layout.addWidget(copy_btn)

        # Open in browser button
        browser_btn = QPushButton("Open in Browser")
        browser_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browser_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: #ffffff;
                border: none;
            }
            QPushButton:hover {
                background-color: #bb8fce;
            }
        """)
        browser_btn.clicked.connect(self._open_in_browser)
        button_layout.addWidget(browser_btn)

        # Download button
        download_btn = QPushButton("Download Image")
        download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        download_btn.setStyleSheet("""
            QPushButton {
                background-color: #e94560;
                color: #ffffff;
                border: none;
            }
            QPushButton:hover {
                background-color: #ff6b6b;
            }
        """)
        download_btn.clicked.connect(self._download_image)
        button_layout.addWidget(download_btn)

        layout.addLayout(button_layout)

    def _add_info_row(self, layout: QVBoxLayout, label: str, value: str):
        """Add an info row to the layout."""
        label_widget = QLabel(label)
        label_widget.setFont(QFont("Segoe UI", 10))
        label_widget.setStyleSheet("color: #a0a0a0;")
        layout.addWidget(label_widget)

        value_widget = QLabel(value)
        value_widget.setFont(QFont("Segoe UI", 12))
        value_widget.setStyleSheet("color: #ffffff;")
        value_widget.setWordWrap(True)
        layout.addWidget(value_widget)

    def _load_image(self):
        """Load the preview image."""
        # Use preview_url for better quality, fallback to thumbnail
        image_url = self.image_result.preview_url or self.image_result.image_url

        try:
            headers = {"User-Agent": "AnimeCharacterCrawler/1.0"}
            response = requests.get(image_url, headers=headers, timeout=30)
            response.raise_for_status()

            image_data = BytesIO(response.content)
            image = QImage()
            image.loadFromData(image_data.getvalue())

            if not image.isNull():
                pixmap = QPixmap.fromImage(image)
                self._pixmap = pixmap

                # Scale to fit the label while maintaining aspect ratio
                scaled = pixmap.scaled(
                    550, 500,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_label.setPixmap(scaled)
            else:
                self.image_label.setText("Failed to load image")
        except Exception as e:
            self.image_label.setText(f"Error: {str(e)[:50]}")

    def _copy_url(self):
        """Copy image URL to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.image_result.image_url)
        QMessageBox.information(self, "Copied", "Image URL copied to clipboard!")

    def _open_in_browser(self):
        """Open the post page in browser."""
        url = self.image_result.page_url or self.image_result.image_url
        if url:
            QDesktopServices.openUrl(QUrl(url))

    def _download_image(self):
        """Download the full image to a user-selected location."""
        # Get default filename
        url_path = self.image_result.image_url.split("?")[0]
        ext = os.path.splitext(url_path)[1] or ".jpg"
        default_name = f"{self.image_result.source_site}_{self.image_result.post_id}{ext}"

        # Ask user where to save
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Image",
            default_name,
            "Images (*.jpg *.jpeg *.png *.gif *.webp);;All Files (*)"
        )

        if not file_path:
            return

        try:
            headers = {"User-Agent": "AnimeCharacterCrawler/1.0"}
            response = requests.get(
                self.image_result.image_url,
                headers=headers,
                timeout=60,
                stream=True
            )
            response.raise_for_status()

            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            QMessageBox.information(
                self,
                "Downloaded",
                f"Image saved to:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Download Failed",
                f"Failed to download image:\n{str(e)}"
            )
