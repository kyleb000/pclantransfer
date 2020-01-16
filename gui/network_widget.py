from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QWidget, \
    QAction, QTabWidget,QVBoxLayout, QHBoxLayout, QPlainTextEdit, QToolButton ,QSizePolicy, QLabel, QLineEdit, QMessageBox
from PyQt5.QtGui import QIcon, QPixmap
from utils.gui_functions import deleteLayout
from gui.file_entry_label import FileEntryLabel

class NetworkFolderManager(QWidget):
    def __init__(self, parent, client):
        super().__init__(parent)
        self.client = client

        root_layout = QVBoxLayout()

        self.roots = self.client.get_roots()

        root_list = self.roots.split('/::/')

        for root in root_list:
            """name_layout = QHBoxLayout()
            icon_widget = QLabel()
            if root.split('-')[0] == '0':
                logo_path = "res/file_logo.png"
            else:
                logo_path = "res/folder_logo.png"
            icon_widget.setPixmap(QPixmap(logo_path).scaled(20, 20))
            icon_widget.show()
            name_layout.addWidget(icon_widget)
            root_label = QLabel(root.split('/')[1])
            root_label.setAccessibleName(root)
            name_layout.addWidget(root_label)
            name_layout.addStretch(1)"""
            name_layout = FileEntryLabel(root, self)
            root_layout.addLayout(name_layout)

        root_layout.addStretch(1)

        self.setLayout(root_layout)
