#!/usr/bin/env python3
"""
Anime Character Crawler - Desktop Application

A user-friendly GUI application for searching and downloading
anime images from booru-style imageboards.

Usage:
    python app.py

Or after building:
    ./AnimeCharacterCrawler.exe  (Windows)
    ./AnimeCharacterCrawler      (Linux/Mac)
"""

import sys
import os
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))


def main():
    """Main entry point for the application."""
    # Set environment variables for high DPI support
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    # Import PyQt6 after setting env vars
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont, QFontDatabase, QPalette, QColor

    # Create application
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("Anime Character Crawler")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("AnimeCharacterCrawler")

    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Set dark palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#1a1a2e"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#16213e"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#1a1a2e"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#16213e"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#16213e"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#e94560"))
    palette.setColor(QPalette.ColorRole.Link, QColor("#e94560"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#e94560"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    # Import and create main window
    from gui import MainWindow
    window = MainWindow()

    # Show window
    window.show()

    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
