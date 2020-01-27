from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QWidget, \
    QAction, QTabWidget,QVBoxLayout, QHBoxLayout, QPlainTextEdit, QToolButton ,QSizePolicy, QLabel, QLineEdit, QMessageBox
from PyQt5.QtGui import QIcon, QPixmap
from utils.gui_functions import deleteLayout
from gui.file_entry_label import FileEntryLabel
from gui.yorn_dialog import YorNDialog
from loghandler import LogHandler
import threading

class NetworkFolderManager(QWidget):
    def __init__(self, parent, client):
        super().__init__(parent)
        self.client = client

        root_layout = QVBoxLayout()

        self.roots = self.client.get_roots()

        list_logger = LogHandler(LogHandler.LOG_FILELIST)
        prog_logger = LogHandler(LogHandler.LOG_FILEPROGRESS)

        file_progress = prog_logger.log_instance.get_outstanding_files(self.client.current_client[1])
        file_list = list_logger.log_instance.get_file_list(self.client.current_client[1])

        if file_progress or file_list:
            dlg = YorNDialog(self, "There are files that have not yet been copied\nWould you like to copy them?")
            if dlg.get_response():

                if file_progress:
                    print(file_progress)

                if file_list:
                    print(file_list)

            else:
                print("Deleting old logs")

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
