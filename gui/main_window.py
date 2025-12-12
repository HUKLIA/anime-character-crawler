"""
Main application window.
Combines all GUI components into a cohesive interface.
"""

import os
import json
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QStatusBar, QProgressBar, QLabel, QPushButton, QMenuBar,
    QMenu, QMessageBox, QApplication, QFrame
)
from PyQt6.QtCore import Qt, QSettings, QSize
from PyQt6.QtGui import QAction, QIcon, QFont, QDesktopServices
from PyQt6.QtCore import QUrl

from .search_widget import SearchWidget
from .image_grid import ImageGrid
from .tag_panel import TagPanel
from .settings_dialog import SettingsDialog
from .crawler_thread import CrawlerThread, ImageResult
from .image_detail_dialog import ImageDetailDialog
from .styles import AppStyles


class MainWindow(QMainWindow):
    """
    Main application window for the Anime Character Crawler.
    """

    def __init__(self):
        super().__init__()
        self.settings = QSettings("AnimeCharacterCrawler", "Settings")
        self.app_settings = self._load_app_settings()
        self.crawler_thread: Optional[CrawlerThread] = None

        self._init_ui()
        self._create_menus()
        self._connect_signals()
        self._apply_settings()

    def _init_ui(self):
        """Initialize the main UI."""
        self.setWindowTitle("Anime Character Crawler")
        self.setMinimumSize(900, 600)
        # Auto-size to screen
        screen = QApplication.primaryScreen().geometry()
        self.resize(int(screen.width() * 0.85), int(screen.height() * 0.85))

        # Apply stylesheet
        self.setStyleSheet(AppStyles.MAIN_STYLESHEET)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(4)
        main_layout.setContentsMargins(8, 4, 8, 4)

        # Search widget at top (compact)
        self.search_widget = SearchWidget()
        main_layout.addWidget(self.search_widget)

        # Content area with splitter
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #2a2a4a;
                width: 2px;
            }
            QSplitter::handle:hover {
                background-color: #e94560;
            }
        """)

        # Left side - Tag panel (collapsible)
        self.tag_panel = TagPanel()
        self.tag_panel.setMinimumWidth(200)
        self.tag_panel.setMaximumWidth(280)
        content_splitter.addWidget(self.tag_panel)

        # Right side - Image grid
        self.image_grid = ImageGrid()
        content_splitter.addWidget(self.image_grid)

        # Set splitter sizes (tag panel smaller)
        content_splitter.setSizes([220, 900])
        content_splitter.setStretchFactor(0, 0)
        content_splitter.setStretchFactor(1, 1)

        main_layout.addWidget(content_splitter, 1)  # Stretch factor 1 to take remaining space

        # Status bar
        self._create_status_bar()

    def _create_menus(self):
        """Create the menu bar."""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #1a1a2e;
                color: #ffffff;
                padding: 4px;
                border-bottom: 1px solid #2a2a4a;
            }
            QMenuBar::item:selected {
                background-color: #e94560;
                border-radius: 4px;
            }
        """)

        # File menu
        file_menu = menubar.addMenu("&File")
        file_menu.setStyleSheet("""
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

        open_folder_action = QAction("📁 Open Downloads Folder", self)
        open_folder_action.triggered.connect(self._open_downloads_folder)
        file_menu.addAction(open_folder_action)

        file_menu.addSeparator()

        settings_action = QAction("⚙️ Settings", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._show_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")
        help_menu.setStyleSheet(file_menu.styleSheet())

        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        help_action = QAction("How to Use", self)
        help_action.setShortcut("F1")
        help_action.triggered.connect(self._show_help)
        help_menu.addAction(help_action)

    def _create_status_bar(self):
        """Create the status bar with progress indicator."""
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #16213e;
                color: #a0a0a0;
                border-top: 1px solid #2a2a4a;
                padding: 4px;
            }
        """)
        self.setStatusBar(self.status_bar)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)

        # Spacer
        spacer = QWidget()
        spacer.setFixedWidth(20)
        self.status_bar.addWidget(spacer)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(200)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1a1a2e;
                border: none;
                border-radius: 4px;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #e94560;
                border-radius: 4px;
            }
        """)
        self.status_bar.addPermanentWidget(self.progress_bar)

        # Image count
        self.count_label = QLabel("0 images")
        self.count_label.setStyleSheet("color: #4ecca3;")
        self.status_bar.addPermanentWidget(self.count_label)

    def _connect_signals(self):
        """Connect widget signals to slots."""
        # Search widget
        self.search_widget.search_requested.connect(self._on_search_requested)
        self.search_widget.cancel_requested.connect(self._on_cancel_requested)

        # Tag panel
        self.tag_panel.tag_filter_changed.connect(self._on_tag_filter_changed)

        # Image grid
        self.image_grid.image_clicked.connect(self._on_image_clicked)

    def _on_search_requested(self, tags: str, site: str, max_pages: int, rating: str, download: bool):
        """Handle search request from search widget."""
        # Clear previous results
        self.image_grid.clear_images()
        self.tag_panel.clear_all()

        # Create and configure crawler thread
        self.crawler_thread = CrawlerThread()
        self.crawler_thread.configure(
            search_tags=tags,
            site=site,
            max_pages=max_pages,
            rating_filter=rating,
            download_images=download,
            output_dir=self.app_settings.get("download_dir", "downloaded_images")
        )

        # Connect signals
        self.crawler_thread.progress.connect(self._on_crawl_progress)
        self.crawler_thread.image_found.connect(self._on_image_found)
        self.crawler_thread.page_complete.connect(self._on_page_complete)
        self.crawler_thread.finished_crawling.connect(self._on_crawl_finished)
        self.crawler_thread.error.connect(self._on_crawl_error)

        # Update UI
        self.search_widget.set_searching(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(max_pages)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Searching for '{tags}'...")

        # Start crawling
        self.crawler_thread.start()

    def _on_cancel_requested(self):
        """Handle cancel request."""
        if self.crawler_thread and self.crawler_thread.isRunning():
            self.status_label.setText("Cancelling...")
            self.crawler_thread.cancel()

    def _on_crawl_progress(self, current: int, total: int, message: str):
        """Handle crawl progress updates."""
        self.progress_bar.setValue(current)
        self.status_label.setText(message)

    def _on_image_found(self, image_result: ImageResult):
        """Handle new image found."""
        # Add to grid
        self.image_grid.add_image(image_result)

        # Process tags
        self.tag_panel.process_image(image_result)

        # Update count
        count = self.image_grid.get_image_count()
        self.count_label.setText(f"{count} images")

    def _on_page_complete(self, page_num: int, images_count: int):
        """Handle page completion."""
        self.progress_bar.setValue(page_num)

    def _on_crawl_finished(self, total: int):
        """Handle crawl completion."""
        self.search_widget.set_searching(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Done! Found {total} images")
        self.count_label.setText(f"{total} images")

    def _on_crawl_error(self, error: str):
        """Handle crawl error."""
        self.status_label.setText(f"Error: {error}")
        # Don't show message box for minor errors, just log to status

    def _on_tag_filter_changed(self, tag: str):
        """Handle tag filter selection."""
        current = self.search_widget.get_search_tags()
        if tag not in current:
            new_search = f"{current} {tag}".strip()
            self.search_widget.search_input.setText(new_search)
            self.search_widget.search_input.setFocus()

    def _on_image_clicked(self, image_result: ImageResult):
        """Handle image click - show detail popup."""
        dialog = ImageDetailDialog(image_result, self)
        dialog.exec()

    def _show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self.app_settings, self)
        dialog.settings_changed.connect(self._on_settings_changed)
        dialog.exec()

    def _on_settings_changed(self, new_settings: dict):
        """Handle settings changes."""
        self.app_settings = new_settings
        self._save_app_settings()
        self._apply_settings()

    def _apply_settings(self):
        """Apply current settings."""
        # Update search widget defaults
        site = self.app_settings.get("preferred_site", "danbooru").capitalize()
        index = self.search_widget.site_combo.findText(site)
        if index >= 0:
            self.search_widget.site_combo.setCurrentIndex(index)

        self.search_widget.pages_spin.setValue(
            self.app_settings.get("default_pages", 5)
        )

        self.search_widget.download_check.setChecked(
            self.app_settings.get("auto_download", True)
        )

    def _load_app_settings(self) -> dict:
        """Load application settings."""
        settings_path = Path.home() / ".anime_crawler_settings.json"
        if settings_path.exists():
            try:
                with open(settings_path) as f:
                    return json.load(f)
            except:
                pass

        # Use project folder for downloads
        project_dir = Path(__file__).parent.parent / "downloaded_images"
        return {
            "download_dir": str(project_dir),
            "max_concurrent": 1,
            "download_delay": 3.0,
            "auto_download": False,  # Off by default
            "skip_duplicates": True,
            "min_width": 200,
            "min_height": 200,
            "preferred_site": "danbooru",
            "default_rating": "general",
            "default_pages": 5,
        }

    def _save_app_settings(self):
        """Save application settings."""
        settings_path = Path.home() / ".anime_crawler_settings.json"
        try:
            with open(settings_path, "w") as f:
                json.dump(self.app_settings, f, indent=2)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def _open_downloads_folder(self):
        """Open the downloads folder in file explorer."""
        download_dir = Path(self.app_settings.get("download_dir", "downloaded_images"))
        download_dir.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(download_dir)))

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Anime Character Crawler",
            """
            <h2 style="color: #e94560;">Anime Character Crawler</h2>
            <p>Version 1.0.0</p>
            <p>A user-friendly tool to search and download anime images from popular booru sites.</p>
            <p><b>Features:</b></p>
            <ul>
                <li>Search by character, tags, or series</li>
                <li>Autocomplete suggestions</li>
                <li>Multiple site support (Danbooru, Safebooru, Gelbooru)</li>
                <li>Image deduplication</li>
                <li>Tag-based filtering</li>
            </ul>
            <p style="color: #a0a0a0;">For educational and personal use only.</p>
            """
        )

    def _show_help(self):
        """Show help dialog."""
        QMessageBox.information(
            self,
            "How to Use",
            """
            <h3>Quick Start Guide</h3>

            <p><b>1. Search for Images</b></p>
            <p>Type character names or tags in the search bar. Use underscores for multi-word tags (e.g., hatsune_miku, blue_hair).</p>

            <p><b>2. Use Quick Tags</b></p>
            <p>Click the colorful tag buttons below the search bar to quickly add common tags.</p>

            <p><b>3. Filter Results</b></p>
            <ul>
                <li><b>Site:</b> Choose between Danbooru, Safebooru, or Gelbooru</li>
                <li><b>Rating:</b> Filter by safe/general content</li>
                <li><b>Pages:</b> Set how many pages to fetch (more pages = more images)</li>
            </ul>

            <p><b>4. View & Download</b></p>
            <ul>
                <li>Click an image to open it in your browser</li>
                <li>Right-click for more options</li>
                <li>Images are automatically saved to your downloads folder</li>
            </ul>

            <p><b>5. Use Tag Filters</b></p>
            <p>Click tags in the left panel to refine your search.</p>

            <p style="color: #a0a0a0;">Tip: Use "rating:general" tag for safe content.</p>
            """
        )

    def closeEvent(self, event):
        """Handle window close."""
        # Cancel any running crawl
        if self.crawler_thread and self.crawler_thread.isRunning():
            self.crawler_thread.cancel()
            self.crawler_thread.wait(2000)

        # Save settings
        self._save_app_settings()

        event.accept()
