"""
Stylesheet and UI styling for the Torchlight Infinite Price Tracker.
"""

from typing import Dict
from ..constants import UI_COLORS


def get_stylesheet(colors: Dict[str, str] = None) -> str:
    """
    Generate Qt Style Sheet for the application.

    Args:
        colors: Optional color palette dictionary. If None, uses UI_COLORS from constants.

    Returns:
        Qt Style Sheet string
    """
    if colors is None:
        colors = UI_COLORS

    return f"""
        QMainWindow {{
            background-color: {colors['bg_primary']};
        }}

        QWidget {{
            background-color: {colors['bg_primary']};
            color: {colors['text_primary']};
            font-family: 'Segoe UI';
            font-size: 11pt;
        }}

        QFrame.card {{
            background-color: {colors['bg_tertiary']};
            border-radius: 8px;
            padding: 15px;
        }}

        QLabel {{
            color: {colors['text_primary']};
            background-color: transparent;
        }}

        QLabel.header {{
            font-size: 13pt;
            font-weight: bold;
            color: {colors['text_primary']};
            padding: 5px;
        }}

        QLabel.status {{
            font-size: 9pt;
            color: {colors['text_secondary']};
        }}

        QPushButton {{
            background-color: {colors['accent']};
            color: {colors['text_primary']};
            border: none;
            border-radius: 6px;
            padding: 8px 15px;
            font-weight: bold;
            font-size: 10pt;
        }}

        QPushButton:hover {{
            background-color: {colors['accent_hover']};
        }}

        QPushButton:pressed {{
            background-color: {colors['accent']};
        }}

        QPushButton.secondary {{
            background-color: {colors['bg_secondary']};
            color: {colors['text_primary']};
            padding: 6px 12px;
            font-size: 9pt;
            font-weight: normal;
        }}

        QPushButton.secondary:hover {{
            background-color: {colors['bg_tertiary']};
        }}

        QPushButton.filter-active {{
            background-color: {colors['accent']};
            color: {colors['text_primary']};
            padding: 6px 12px;
            font-size: 9pt;
            font-weight: bold;
        }}

        QPushButton.filter-active:hover {{
            background-color: {colors['accent_hover']};
        }}

        QPushButton.danger {{
            background-color: {colors['error']};
            color: {colors['text_primary']};
        }}

        QPushButton.danger:hover {{
            background-color: #dc2626;
        }}

        QPushButton:disabled {{
            background-color: {colors['bg_secondary']};
            color: {colors['text_secondary']};
        }}

        QListWidget {{
            background-color: {colors['bg_secondary']};
            color: {colors['text_primary']};
            border: none;
            border-radius: 6px;
            padding: 5px;
            font-size: 10pt;
        }}

        QListWidget::item {{
            padding: 5px;
        }}

        QListWidget::item:selected {{
            background-color: {colors['accent']};
            color: {colors['text_primary']};
        }}

        QComboBox {{
            background-color: {colors['bg_secondary']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
            padding: 5px 10px;
            min-width: 150px;
        }}

        QComboBox:hover {{
            border-color: {colors['accent']};
        }}

        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {colors['bg_secondary']};
            color: {colors['text_primary']};
            selection-background-color: {colors['accent']};
            border: 1px solid {colors['border']};
        }}

        QDialog {{
            background-color: {colors['bg_primary']};
        }}
    """
