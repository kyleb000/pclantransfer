from PyQt5.QtWidgets import QPushButton, QWidget, QAction, QTabWidget, \
    QVBoxLayout, QHBoxLayout, QPlainTextEdit, QToolButton ,QSizePolicy, \
    QLabel, QLineEdit, QDialog
from PyQt5.QtGui import QIcon, QPixmap
import time

class YorNDialog(QDialog):
    response = False
    def __init__(self, parent, message):
        super().__init__(parent)
        layout = QVBoxLayout()

        self.setWindowTitle("Connection Information")

        label = QLabel(message)
        layout.addWidget(label)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)
        yes_btn = QPushButton("Yes")
        yes_btn.clicked.connect(lambda x: self.set_response(True))
        no_btn = QPushButton("No")
        no_btn.clicked.connect(lambda x: self.set_response(False))
        btn_layout.addWidget(no_btn)
        btn_layout.addStretch(1)
        btn_layout.addWidget(yes_btn)
        btn_layout.addStretch(1)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def get_response(self):
        self.exec_()
        return self.response

    def set_response(self, resp):
        self.response = resp
        self.close()
