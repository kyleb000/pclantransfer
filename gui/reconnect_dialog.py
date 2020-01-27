from PyQt5.QtWidgets import QPushButton, QWidget, QAction, QTabWidget, \
    QVBoxLayout, QHBoxLayout, QPlainTextEdit, QToolButton ,QSizePolicy, \
    QLabel, QLineEdit, QDialog
from PyQt5.QtGui import QIcon, QPixmap

class ReconnectDialog(QDialog):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        self.setWindowTitle("Connection Information")

        label = QLabel("Connection already established. Would you like to reconnect?")
        layout.addWidget(label)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)
        btn_layout.addWidget(QPushButton("No"))
        btn_layout.addStretch(1)
        btn_layout.addWidget(QPushButton("Yes"))
        btn_layout.addStretch(1)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
