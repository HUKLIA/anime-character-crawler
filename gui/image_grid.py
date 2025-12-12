"""
Image grid display widget with pagination and async loading.
"""

import os
from pathlib import Path
from typing import Optional, List, Dict
from queue import Queue
from threading import Lock

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QFrame, QSizePolicy, QMenu,
    QApplication, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QUrl, QThread, QObject, QTimer
from PyQt6.QtGui import QPixmap, QImage, QFont, QDesktopServices, QCursor

import requests
from io import BytesIO

from .crawler_thread import ImageResult
from .styles import AppStyles


class ImageLoaderWorker(QObject):
    """Worker for loading images in background thread."""

    image_loaded = pyqtSignal(str, QPixmap)  # card_id, pixmap

    def __init__(self):
        super().__init__()
        self._queue = Queue()
        self._running = True
        self._cache: Dict[str, QPixmap] = {}
        self._cache_lock = Lock()

    def add_task(self, card_id: str, url: str, source_site: str):
        """Add image loading task to queue."""
        self._queue.put((card_id, url, source_site))

    def stop(self):
        """Stop the worker."""
        self._running = False
        self._queue.put(None)  # Unblock queue

    def process(self):
        """Process image loading tasks."""
        while self._running:
            try:
                task = self._queue.get(timeout=0.5)
                if task is None:
                    continue

                card_id, url, source_site = task

                # Check cache first
                with self._cache_lock:
                    if url in self._cache:
                        self.image_loaded.emit(card_id, self._cache[url])
                        continue

                # Load image
                try:
                    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                    if source_site == "pixiv" or "pximg.net" in url:
                        headers["Referer"] = "https://www.pixiv.net/"

                    response = requests.get(url, headers=headers, timeout=8)
                    response.raise_for_status()

                    image = QImage()
                    image.loadFromData(response.content)

                    if not image.isNull():
                        pixmap = QPixmap.fromImage(image)
                        # Cache the pixmap
                        with self._cache_lock:
                            if len(self._cache) < 200:  # Limit cache size
                                self._cache[url] = pixmap
                        self.image_loaded.emit(card_id, pixmap)
                except:
                    pass  # Silent fail for image loading

            except:
                continue


class ImageLoaderThread(QThread):
    """Thread for running the image loader worker."""

    image_loaded = pyqtSignal(str, QPixmap)

    def __init__(self):
        super().__init__()
        self.worker = ImageLoaderWorker()
        self.worker.image_loaded.connect(self.image_loaded.emit)

    def run(self):
        self.worker.process()

    def add_task(self, card_id: str, url: str, source_site: str):
        self.worker.add_task(card_id, url, source_site)

    def stop(self):
        self.worker.stop()
        self.wait(2000)


# Global image loader instance
_image_loader: Optional[ImageLoaderThread] = None

def get_image_loader() -> ImageLoaderThread:
    """Get or create the global image loader."""
    global _image_loader
    if _image_loader is None or not _image_loader.isRunning():
        _image_loader = ImageLoaderThread()
        _image_loader.start()
    return _image_loader


class ImageCard(QFrame):
    """Individual image card widget with async loading."""

    clicked = pyqtSignal(object)
    _card_counter = 0

    def __init__(self, image_result: ImageResult, parent=None):
        super().__init__(parent)
        self.image_result = image_result
        self._pixmap = None

        # Generate unique card ID
        ImageCard._card_counter += 1
        self._card_id = f"card_{ImageCard._card_counter}"

        self._init_ui()
        self._start_loading()

    def _init_ui(self):
        """Initialize the card UI."""
        self.setFixedSize(200, 280)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QFrame {
                background-color: #16213e;
                border-radius: 8px;
                border: 2px solid #2a2a4a;
            }
            QFrame:hover {
                border-color: #e94560;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)

        # Thumbnail
        thumb_container = QFrame()
        thumb_container.setFixedSize(192, 180)
        thumb_container.setStyleSheet("background-color: #1a1a2e; border-radius: 6px; border: none;")
        thumb_layout = QVBoxLayout(thumb_container)
        thumb_layout.setContentsMargins(0, 0, 0, 0)

        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(192, 180)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setStyleSheet("color: #404040; background: transparent; font-size: 11px;")
        self.thumb_label.setText("Loading...")
        thumb_layout.addWidget(self.thumb_label)

        layout.addWidget(thumb_container)

        # Title
        title_text = self._get_title()
        self.title_label = QLabel(title_text)
        self.title_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #ffffff; border: none; background: transparent;")
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumHeight(32)
        layout.addWidget(self.title_label)

        # Metadata row
        meta_layout = QHBoxLayout()
        meta_layout.setSpacing(4)

        site_label = QLabel(self.image_result.source_site.capitalize()[:6])
        site_label.setStyleSheet("""
            color: #e94560; font-size: 9px;
            background-color: rgba(233, 69, 96, 0.2);
            border-radius: 3px; padding: 1px 4px; border: none;
        """)
        meta_layout.addWidget(site_label)

        if self.image_result.width and self.image_result.height:
            dim_label = QLabel(f"{self.image_result.width}x{self.image_result.height}")
            dim_label.setStyleSheet("color: #606060; font-size: 9px; border: none; background: transparent;")
            meta_layout.addWidget(dim_label)

        meta_layout.addStretch()
        layout.addLayout(meta_layout)

    def _get_title(self) -> str:
        """Get display title for the card."""
        if self.image_result.character:
            chars = self.image_result.character.replace("_", " ")
            return chars[:25] + "..." if len(chars) > 25 else chars
        if self.image_result.tags_list:
            tags = [t.replace("_", " ") for t in self.image_result.tags_list[:2]]
            return ", ".join(tags)[:25]
        return f"#{self.image_result.post_id}"

    def _start_loading(self):
        """Start async image loading."""
        # Check for local file first
        if self.image_result.local_path and os.path.exists(self.image_result.local_path):
            pixmap = QPixmap(self.image_result.local_path)
            if not pixmap.isNull():
                self._set_pixmap(pixmap)
                return

        # Get URL to load
        thumb_url = self.image_result.preview_url or self.image_result.thumbnail_url
        if thumb_url:
            loader = get_image_loader()
            loader.image_loaded.connect(self._on_image_loaded)
            loader.add_task(self._card_id, thumb_url, self.image_result.source_site)
        else:
            self.thumb_label.setText("No Preview")

    def _on_image_loaded(self, card_id: str, pixmap: QPixmap):
        """Handle loaded image from worker."""
        if card_id == self._card_id and not pixmap.isNull():
            self._set_pixmap(pixmap)

    def _set_pixmap(self, pixmap: QPixmap):
        """Set and scale the thumbnail pixmap."""
        self._pixmap = pixmap
        scaled = pixmap.scaled(192, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.thumb_label.setPixmap(scaled)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.image_result)
        super().mousePressEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #16213e; border: 1px solid #2a2a4a; border-radius: 6px; padding: 4px; }
            QMenu::item { padding: 6px 16px; border-radius: 3px; color: #ffffff; }
            QMenu::item:selected { background-color: #e94560; }
        """)
        open_action = menu.addAction("Open in Browser")
        open_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(self.image_result.page_url or self.image_result.image_url)))
        copy_action = menu.addAction("Copy Image URL")
        copy_action.triggered.connect(lambda: QApplication.clipboard().setText(self.image_result.image_url))
        menu.exec(event.globalPos())


class ImageGrid(QWidget):
    """Grid widget with pagination and async loading."""

    image_clicked = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_images: List[ImageResult] = []
        self.image_cards: List[ImageCard] = []
        self.current_page = 0
        self.images_per_page = 12
        self._pending_update = False
        self._init_ui()

        # Debounce timer for resize
        self._resize_timer = QTimer()
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._do_resize_update)

    def _init_ui(self):
        """Initialize the grid UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Header with count and pagination
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(4, 4, 4, 4)

        self.count_label = QLabel("No images yet")
        self.count_label.setStyleSheet("color: #a0a0a0; font-size: 12px;")
        header_layout.addWidget(self.count_label)

        header_layout.addStretch()

        # Pagination controls
        self.prev_btn = QPushButton("◀ Prev")
        self.prev_btn.setFixedSize(70, 26)
        self.prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_btn.setStyleSheet("""
            QPushButton { background-color: #2a2a4a; color: #ffffff; border: none; border-radius: 4px; font-size: 11px; }
            QPushButton:hover { background-color: #3a3a5a; }
            QPushButton:disabled { background-color: #1a1a2e; color: #404040; }
        """)
        self.prev_btn.clicked.connect(self._prev_page)
        self.prev_btn.setEnabled(False)
        header_layout.addWidget(self.prev_btn)

        self.page_label = QLabel("Page 1/1")
        self.page_label.setStyleSheet("color: #a0a0a0; font-size: 11px; padding: 0 8px;")
        header_layout.addWidget(self.page_label)

        self.next_btn = QPushButton("Next ▶")
        self.next_btn.setFixedSize(70, 26)
        self.next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_btn.setStyleSheet(self.prev_btn.styleSheet())
        self.next_btn.clicked.connect(self._next_page)
        self.next_btn.setEnabled(False)
        header_layout.addWidget(self.next_btn)

        header_layout.addSpacing(10)

        # Clear button
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.setFixedSize(70, 26)
        self.clear_btn.setStyleSheet("""
            QPushButton { background-color: transparent; color: #e94560; border: 1px solid #e94560; border-radius: 4px; font-size: 11px; }
            QPushButton:hover { background-color: rgba(233, 69, 96, 0.2); }
        """)
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.clicked.connect(self.clear_images)
        self.clear_btn.setVisible(False)
        header_layout.addWidget(self.clear_btn)

        layout.addLayout(header_layout)

        # Grid container
        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(8)
        self.grid_layout.setContentsMargins(4, 4, 4, 4)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(self.grid_widget, 1)

        # Empty state
        self.empty_label = QLabel("Search for anime images to get started")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #606060; font-size: 14px; padding: 40px;")
        self.grid_layout.addWidget(self.empty_label, 0, 0, 1, 6)

    def _calculate_columns(self) -> int:
        """Calculate number of columns based on widget width."""
        width = self.width()
        card_width = 208
        cols = max(1, width // card_width)
        return min(cols, 6)

    def _update_images_per_page(self):
        """Update images per page based on available space."""
        cols = self._calculate_columns()
        height = self.height() - 50
        card_height = 288
        rows = max(1, height // card_height)
        self.images_per_page = max(6, cols * rows)

    def resizeEvent(self, event):
        """Handle resize with debounce."""
        super().resizeEvent(event)
        self._resize_timer.start(150)  # Debounce resize

    def _do_resize_update(self):
        """Perform resize update after debounce."""
        self._update_images_per_page()
        self._show_current_page()

    def add_image(self, image_result: ImageResult):
        """Add an image to the collection."""
        self.all_images.append(image_result)

        # Only update display periodically to avoid performance issues
        if len(self.all_images) % 5 == 0 or len(self.all_images) <= 5:
            self._update_pagination()
            self._show_current_page()

    def _show_current_page(self):
        """Display images for current page."""
        # Clear existing cards
        for card in self.image_cards:
            self.grid_layout.removeWidget(card)
            card.deleteLater()
        self.image_cards.clear()

        if not self.all_images:
            self.empty_label.setVisible(True)
            return

        self.empty_label.setVisible(False)

        # Calculate page range
        start_idx = self.current_page * self.images_per_page
        end_idx = min(start_idx + self.images_per_page, len(self.all_images))
        page_images = self.all_images[start_idx:end_idx]

        # Create cards
        cols = self._calculate_columns()
        for i, img in enumerate(page_images):
            card = ImageCard(img)
            card.clicked.connect(lambda r: self.image_clicked.emit(r))
            self.image_cards.append(card)
            row = i // cols
            col = i % cols
            self.grid_layout.addWidget(card, row, col)

        self._update_count()
        self.clear_btn.setVisible(True)
        self._update_pagination()

    def _update_pagination(self):
        """Update pagination controls."""
        if self.images_per_page <= 0:
            self.images_per_page = 12
        total_pages = max(1, (len(self.all_images) + self.images_per_page - 1) // self.images_per_page)
        self.page_label.setText(f"Page {self.current_page + 1}/{total_pages}")
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < total_pages - 1)

    def _prev_page(self):
        """Go to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            self._show_current_page()

    def _next_page(self):
        """Go to next page."""
        total_pages = (len(self.all_images) + self.images_per_page - 1) // self.images_per_page
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self._show_current_page()

    def clear_images(self):
        """Clear all images."""
        for card in self.image_cards:
            self.grid_layout.removeWidget(card)
            card.deleteLater()
        self.image_cards.clear()
        self.all_images.clear()
        self.current_page = 0
        self.empty_label.setVisible(True)
        self._update_count()
        self._update_pagination()
        self.clear_btn.setVisible(False)

    def _update_count(self):
        """Update the image count label."""
        count = len(self.all_images)
        if count == 0:
            self.count_label.setText("No images yet")
        elif count == 1:
            self.count_label.setText("1 image found")
        else:
            self.count_label.setText(f"{count} images found")

    def get_image_count(self) -> int:
        """Get number of images."""
        return len(self.all_images)
