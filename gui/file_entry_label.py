from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QWidget, \
    QAction, QTabWidget,QVBoxLayout, QHBoxLayout, QPlainTextEdit, QToolButton, \
    QSizePolicy, QLabel, QLineEdit, QMessageBox, QMenu, QFileDialog
from PyQt5.QtGui import QIcon, QPixmap, QDrag, QPainter, QCursor
from PyQt5.QtCore import Qt, QMimeData, QUrl
from utils.gui_functions import deleteLayout
import pickle
import constants

class FileEntryLabel(QHBoxLayout):
    def __init__(self, file_text, parent):
        super().__init__()

        self.parent = parent

        self.ico_label = QLabel()
        if file_text.split('-')[0] == '0':
            logo_path = "res/file_logo.png"
        else:
            logo_path = "res/folder_logo.png"
        self.ico_label.setPixmap(QPixmap(logo_path).scaled(20, 20))
        self.ico_label.show()

        self.root_label = QLabel(file_text.split(constants.GENERIC_PATH)[1])
        self.root_label.setAccessibleName(file_text)

        self.addWidget(self.ico_label)
        self.addWidget(self.root_label)
        self.addStretch(1)

        self.root_label.mousePressEvent = lambda x: self.mousePressEvent(x)

    def mousePressEvent(self, event):
        """if event.button() == Qt.RightButton:
            self.contextMenuEvent(event)"""
        if event.button() == Qt.LeftButton:
            dlg = QFileDialog()
            dlg.setFileMode(QFileDialog.Directory)
            filenames = []

            if dlg.exec_():
                filenames = dlg.selectedFiles()

            if len(filenames):
                dest_dir = filenames[0]
                print(self.root_label.accessibleName(), " ", dest_dir)
                input("::")
                self.parent.client.transfer_data(self.root_label.accessibleName(), dest_dir)

    """def contextMenuEvent(self, event):
        menu = QMenu()
        openAction = menu.addAction("Copy to...")
        action = menu.exec_(event.globalPos())
        if action ==openAction:
            #self.openAction(row, column)
            print("Hello world")"""
