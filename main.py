import sys
import os
from PyQt5.QtWidgets import QApplication, QSplashScreen, QLabel, QVBoxLayout, QProgressBar, QWidget
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

    splash_pix = QPixmap(500, 300)
    splash_pix.fill(Qt.white)
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)

    splash_layout = QVBoxLayout()
    splash_layout.addWidget(QLabel("Android Automation Tool"))
    splash_layout.addWidget(QLabel("Initializing..."))

    progress = QProgressBar()
    progress.setRange(0, 100)
    progress.setValue(0)
    splash_layout.addWidget(progress)

    splash_widget = QWidget()
    splash_widget.setLayout(splash_layout)

    splash.show()
    app.processEvents()

    config_manager, driver_manager, driver_status = initialize_app()

    progress.setValue(50)
    app.processEvents()

    window = MainWindow(config_manager, driver_manager)

    progress.setValue(100)
    app.processEvents()

    QTimer.singleShot(1000, splash.close)
    QTimer.singleShot(1000, window.show)

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()