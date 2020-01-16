from PyQt5.QtWidgets import QVBoxLayout, QPlainTextEdit, QLabel
from PyQt5.QtGui import QIcon, QPixmap

class LogWindowManager(QVBoxLayout):
    def __init__(self, parent):
        super().__init__(parent)
        wdg = QLabel("A program by: Kyle Barry")
        wdg.setStyleSheet("background-color: white")
        self.addWidget(QLabel("A program by: Kyle Barry"))
