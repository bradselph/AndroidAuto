import sys
import os
from PyQt5.QtWidgets import QApplication, QSplashScreen, QLabel, QVBoxLayout, QProgressBar, QWidget, QPushButton
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
from ui.main_window import MainWindow
from utils.config_manager import ConfigManager
from drivers import DriverManager

def initialize_app():
    config_manager = ConfigManager()

    driver_manager = DriverManager(config_manager)

    driver_status = driver_manager.check_drivers()

    return config_manager, driver_manager, driver_status

def main():
    app = QApplication(sys.argv)

    splash_widget = QWidget()
    splash_widget.setFixedSize(500, 300)
    splash_widget.setWindowFlags(Qt.SplashScreen | Qt.WindowStaysOnTopHint)

    splash_layout = QVBoxLayout(splash_widget)
    splash_layout.addWidget(QLabel("Android Automation Tool"))
    splash_layout.addWidget(QLabel("Initializing..."))

    progress = QProgressBar()
    progress.setRange(0, 100)
    progress.setValue(0)
    splash_layout.addWidget(progress)

    splash_widget.show()
    app.processEvents()

    try:
        config_manager, driver_manager, driver_status = initialize_app()

        progress.setValue(50)
        app.processEvents()

        window = MainWindow(config_manager, driver_manager)

        progress.setValue(100)
        app.processEvents()

        QTimer.singleShot(1000, splash_widget.close)
        QTimer.singleShot(1100, window.show)
    except Exception as e:
        error_label = QLabel(f"Error initializing application: {str(e)}")
        error_label.setWordWrap(True)
        splash_layout.addWidget(error_label)
        app.processEvents()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(app.quit)
        splash_layout.addWidget(close_btn)

        QTimer.singleShot(30000, app.quit)

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()