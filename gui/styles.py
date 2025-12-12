"""
Modern styling for the Anime Character Crawler application.
Provides a clean, dark theme with accent colors.
"""


class AppStyles:
    """Application-wide styling constants and stylesheets."""

    # Color palette
    COLORS = {
        "bg_dark": "#1a1a2e",
        "bg_medium": "#16213e",
        "bg_light": "#0f3460",
        "accent": "#e94560",
        "accent_hover": "#ff6b6b",
        "text_primary": "#ffffff",
        "text_secondary": "#a0a0a0",
        "border": "#2a2a4a",
        "success": "#4ecca3",
        "warning": "#ffc107",
        "error": "#ff4757",
    }

    # Main application stylesheet
    MAIN_STYLESHEET = """
        QMainWindow {
            background-color: #1a1a2e;
        }

        QWidget {
            background-color: #1a1a2e;
            color: #ffffff;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 13px;
        }

        /* Search Bar */
        QLineEdit {
            background-color: #16213e;
            border: 2px solid #2a2a4a;
            border-radius: 20px;
            padding: 12px 20px;
            font-size: 14px;
            color: #ffffff;
            selection-background-color: #e94560;
        }

        QLineEdit:focus {
            border-color: #e94560;
        }

        QLineEdit::placeholder {
            color: #a0a0a0;
        }

        /* Buttons */
        QPushButton {
            background-color: #e94560;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 24px;
            font-size: 14px;
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
            color: #808080;
        }

        /* Secondary Button */
        QPushButton[class="secondary"] {
            background-color: transparent;
            border: 2px solid #e94560;
            color: #e94560;
        }

        QPushButton[class="secondary"]:hover {
            background-color: rgba(233, 69, 96, 0.1);
        }

        /* Labels */
        QLabel {
            color: #ffffff;
        }

        QLabel[class="title"] {
            font-size: 24px;
            font-weight: bold;
            color: #e94560;
        }

        QLabel[class="subtitle"] {
            font-size: 14px;
            color: #a0a0a0;
        }

        /* Scroll Area */
        QScrollArea {
            border: none;
            background-color: transparent;
        }

        QScrollBar:vertical {
            background-color: #16213e;
            width: 12px;
            border-radius: 6px;
        }

        QScrollBar::handle:vertical {
            background-color: #e94560;
            border-radius: 6px;
            min-height: 30px;
        }

        QScrollBar::handle:vertical:hover {
            background-color: #ff6b6b;
        }

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }

        QScrollBar:horizontal {
            background-color: #16213e;
            height: 12px;
            border-radius: 6px;
        }

        QScrollBar::handle:horizontal {
            background-color: #e94560;
            border-radius: 6px;
            min-width: 30px;
        }

        /* ComboBox */
        QComboBox {
            background-color: #16213e;
            border: 2px solid #2a2a4a;
            border-radius: 8px;
            padding: 8px 16px;
            color: #ffffff;
            min-width: 120px;
        }

        QComboBox:hover {
            border-color: #e94560;
        }

        QComboBox::drop-down {
            border: none;
            width: 30px;
        }

        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 8px solid #e94560;
            margin-right: 10px;
        }

        QComboBox QAbstractItemView {
            background-color: #16213e;
            border: 2px solid #e94560;
            border-radius: 8px;
            selection-background-color: #e94560;
            padding: 4px;
            outline: none;
        }

        QComboBox QAbstractItemView::item {
            padding: 8px 16px;
            min-height: 24px;
            color: #ffffff;
        }

        QComboBox QAbstractItemView::item:hover {
            background-color: rgba(233, 69, 96, 0.3);
        }

        QComboBox QAbstractItemView::item:selected {
            background-color: #e94560;
        }

        /* SpinBox */
        QSpinBox {
            background-color: #16213e;
            border: 2px solid #2a2a4a;
            border-radius: 8px;
            padding: 8px;
            color: #ffffff;
        }

        QSpinBox:focus {
            border-color: #e94560;
        }

        /* CheckBox */
        QCheckBox {
            color: #ffffff;
            spacing: 8px;
        }

        QCheckBox::indicator {
            width: 20px;
            height: 20px;
            border-radius: 4px;
            border: 2px solid #2a2a4a;
            background-color: #16213e;
        }

        QCheckBox::indicator:checked {
            background-color: #e94560;
            border-color: #e94560;
        }

        QCheckBox::indicator:hover {
            border-color: #e94560;
        }

        /* Progress Bar */
        QProgressBar {
            background-color: #16213e;
            border: none;
            border-radius: 8px;
            height: 16px;
            text-align: center;
            color: #ffffff;
        }

        QProgressBar::chunk {
            background-color: #e94560;
            border-radius: 8px;
        }

        /* Tab Widget */
        QTabWidget::pane {
            border: 2px solid #2a2a4a;
            border-radius: 8px;
            background-color: #16213e;
        }

        QTabBar::tab {
            background-color: #1a1a2e;
            color: #a0a0a0;
            padding: 12px 24px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            margin-right: 4px;
        }

        QTabBar::tab:selected {
            background-color: #16213e;
            color: #e94560;
            font-weight: bold;
        }

        QTabBar::tab:hover {
            color: #ffffff;
        }

        /* Group Box */
        QGroupBox {
            border: 2px solid #2a2a4a;
            border-radius: 8px;
            margin-top: 16px;
            padding: 16px;
            font-weight: bold;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 8px;
            color: #e94560;
        }

        /* List Widget */
        QListWidget {
            background-color: #16213e;
            border: 2px solid #2a2a4a;
            border-radius: 8px;
            padding: 8px;
        }

        QListWidget::item {
            padding: 8px;
            border-radius: 4px;
        }

        QListWidget::item:selected {
            background-color: #e94560;
        }

        QListWidget::item:hover {
            background-color: rgba(233, 69, 96, 0.3);
        }

        /* Tool Tip */
        QToolTip {
            background-color: #16213e;
            color: #ffffff;
            border: 1px solid #e94560;
            border-radius: 4px;
            padding: 8px;
        }

        /* Menu */
        QMenuBar {
            background-color: #1a1a2e;
            color: #ffffff;
            padding: 4px;
        }

        QMenuBar::item:selected {
            background-color: #e94560;
            border-radius: 4px;
        }

        QMenu {
            background-color: #16213e;
            border: 1px solid #2a2a4a;
            border-radius: 8px;
            padding: 8px;
        }

        QMenu::item {
            padding: 8px 24px;
            border-radius: 4px;
        }

        QMenu::item:selected {
            background-color: #e94560;
        }

        /* Status Bar */
        QStatusBar {
            background-color: #16213e;
            color: #a0a0a0;
            border-top: 1px solid #2a2a4a;
        }

        /* Dialog */
        QDialog {
            background-color: #1a1a2e;
        }

        /* Splitter */
        QSplitter::handle {
            background-color: #2a2a4a;
        }

        QSplitter::handle:hover {
            background-color: #e94560;
        }
    """

    # Image card styling
    IMAGE_CARD_STYLE = """
        QFrame {
            background-color: #16213e;
            border-radius: 12px;
            border: 2px solid #2a2a4a;
        }

        QFrame:hover {
            border-color: #e94560;
        }
    """

    # Tag chip styling
    TAG_CHIP_STYLE = """
        QPushButton {
            background-color: rgba(233, 69, 96, 0.2);
            color: #e94560;
            border: 1px solid #e94560;
            border-radius: 12px;
            padding: 4px 12px;
            font-size: 11px;
        }

        QPushButton:hover {
            background-color: #e94560;
            color: white;
        }

        QPushButton:checked {
            background-color: #e94560;
            color: white;
        }
    """

    # Category tag colors
    TAG_COLORS = {
        "character": "#4ecca3",
        "series": "#ffc107",
        "artist": "#9b59b6",
        "general": "#3498db",
        "meta": "#95a5a6",
    }

    @classmethod
    def get_tag_style(cls, category: str) -> str:
        """Get styling for a specific tag category."""
        color = cls.TAG_COLORS.get(category, cls.TAG_COLORS["general"])
        return f"""
            QPushButton {{
                background-color: rgba({cls._hex_to_rgb(color)}, 0.2);
                color: {color};
                border: 1px solid {color};
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 11px;
            }}

            QPushButton:hover {{
                background-color: {color};
                color: white;
            }}

            QPushButton:checked {{
                background-color: {color};
                color: white;
            }}
        """

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> str:
        """Convert hex color to RGB string."""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f"{r}, {g}, {b}"
