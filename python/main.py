"""Color Detection-Based Automatic Light Control

รันด้วย:  python main.py
"""
import sys

from PyQt6.QtWidgets import QApplication

from gui.main_window import MainWindow
from gui.styles import QSS


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Color LED Control")
    app.setStyle("Fusion")
    app.setStyleSheet(QSS)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
