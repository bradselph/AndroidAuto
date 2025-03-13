from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt
import os

class ThemeManager:
    """Manages application themes"""
    
    def __init__(self):
        # Define theme directories
        self.themes_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "themes")
        os.makedirs(self.themes_dir, exist_ok=True)
    
    def apply_theme(self, parent, theme_name):
        """Apply the selected theme to the application"""
        if theme_name == "Light":
            self._apply_light_theme()
        elif theme_name == "Dark":
            self._apply_dark_theme()
        elif theme_name == "System":
            self._apply_system_theme()
    
    def _apply_light_theme(self):
        """Apply light theme"""
        app = QApplication.instance()
        app.setStyle("Fusion")
        
        palette = QPalette()
        
        # Base colors
        palette.setColor(QPalette.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.AlternateBase, QColor(233, 233, 233))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.Text, QColor(0, 0, 0))
        
        # Button colors
        palette.setColor(QPalette.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
        
        # Highlight colors
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        # Link colors
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.LinkVisited, QColor(100, 100, 200))
        
        # Apply palette
        app.setPalette(palette)
        
        # Apply stylesheet for more customizations
        stylesheet = """
        QGroupBox {
            border: 1px solid #cccccc;
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 8px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 3px;
            background-color: #f0f0f0;
        }
        
        QPushButton {
            background-color: #f0f0f0;
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 4px 8px;
        }
        
        QPushButton:hover {
            background-color: #e0e0e0;
        }
        
        QPushButton:pressed {
            background-color: #d0d0d0;
        }
        
        QComboBox, QSpinBox, QLineEdit {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 2px 4px;
        }
        
        QTabWidget::pane {
            border: 1px solid #cccccc;
            border-radius: 4px;
        }
        
        QTabBar::tab {
            background-color: #e0e0e0;
            border: 1px solid #cccccc;
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            padding: 4px 8px;
        }
        
        QTabBar::tab:selected {
            background-color: #ffffff;
        }
        
        QListWidget {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            border-radius: 4px;
        }
        
        QSplitter::handle {
            background-color: #cccccc;
        }
        
        QScrollBar {
            background-color: #f0f0f0;
        }
        """
        
        app.setStyleSheet(stylesheet)
    
    def _apply_dark_theme(self):
        """Apply dark theme"""
        app = QApplication.instance()
        app.setStyle("Fusion")
        
        palette = QPalette()
        
        # Base colors
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, QColor(25, 25, 25))
        palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.Text, QColor(255, 255, 255))
        
        # Button colors
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        
        # Highlight colors
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        # Link colors
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.LinkVisited, QColor(100, 100, 200))
        
        # Disabled colors
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
        
        # Apply palette
        app.setPalette(palette)
        
        # Apply stylesheet for more customizations
        stylesheet = """
        QGroupBox {
            border: 1px solid #555555;
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 8px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 3px;
            background-color: #353535;
        }
        
        QPushButton {
            background-color: #353535;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 4px 8px;
        }
        
        QPushButton:hover {
            background-color: #454545;
        }
        
        QPushButton:pressed {
            background-color: #252525;
        }
        
        QComboBox, QSpinBox, QLineEdit {
            background-color: #252525;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 2px 4px;
            color: white;
        }
        
        QTabWidget::pane {
            border: 1px solid #555555;
            border-radius: 4px;
        }
        
        QTabBar::tab {
            background-color: #353535;
            border: 1px solid #555555;
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            padding: 4px 8px;
        }
        
        QTabBar::tab:selected {
            background-color: #252525;
        }
        
        QListWidget {
            background-color: #252525;
            border: 1px solid #555555;
            border-radius: 4px;
        }
        
        QSplitter::handle {
            background-color: #555555;
        }
        
        QScrollBar {
            background-color: #353535;
        }
        
        QScrollBar::handle {
            background-color: #555555;
        }
        
        QHeaderView::section {
            background-color: #353535;
            border: 1px solid #555555;
        }
        
        QCheckBox {
            color: white;
        }
        
        QLabel {
            color: white;
        }
        """
        
        app.setStyleSheet(stylesheet)
    
    def _apply_system_theme(self):
        """Apply system default theme"""
        app = QApplication.instance()
        app.setStyle("Fusion")
        app.setPalette(app.style().standardPalette())
        app.setStyleSheet("")