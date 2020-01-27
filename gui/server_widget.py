from PyQt5.QtWidgets import QPushButton, QWidget, \
    QAction, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QSizePolicy, QLabel, \
    QLineEdit, QMessageBox, QFileDialog, QListView, QAbstractItemView, QTreeView, QScrollArea
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import QRunnable, pyqtSlot
from utils.gui_functions import deleteLayout
from gui.filedialog import CustomFileDialog
from gui.del_window import DelRootWindow
import getpass
import os
import time
import threading

class ServerWidgetManager(QVBoxLayout):
    server = None
    stretched = False
    _parent = None
    username = None
    def __init__(self, parent, srv):
        super().__init__(parent)
        self._parent = parent
        self.server = srv
        #self.setStyleSheet("background-color: white")
        server_add_btn = QPushButton("Open Server")
        server_add_btn.clicked.connect(lambda x: self.setup_server())
        self.addWidget(server_add_btn)

    def setup_server(self):
        deleteLayout(self)

        content_layout = QVBoxLayout()

        name_layout = QHBoxLayout()
        name_label = QLabel("Server Name:")
        name_edit = QLineEdit()

        username = getpass.getuser()
        self.username = F"{username}_server"

        name_edit.setText(username)

        name_layout.addWidget(name_label)
        name_layout.addWidget(name_edit)

        port_layout = QHBoxLayout()
        port_label = QLabel("Listening Port:")
        port_edit = QLineEdit()
        port_edit.setText("10031")

        port_layout.addWidget(port_label)
        port_layout.addWidget(port_edit)

        btn_layout = QHBoxLayout()
        start_btn = QPushButton("Start")
        start_btn.clicked.connect(lambda x: self.manage_server(name_edit.text(), port_edit.text()))
        cncl_btn = QPushButton("Cancel")
        cncl_btn.clicked.connect(lambda x: self.reset())
        btn_layout.addWidget(start_btn)
        btn_layout.addWidget(cncl_btn)

        content_layout.addLayout(name_layout)
        content_layout.addLayout(port_layout)
        content_layout.addLayout(btn_layout)

        self.addLayout(QVBoxLayout(),2)
        self.addLayout(content_layout, 3)
        self.addLayout(QVBoxLayout(), 2)

    def manage_server(self, name, port):
        deleteLayout(self)

        self.server.open_server(self.username)

        info_layout = QVBoxLayout()
        info_layout.addWidget(QLabel(F"Server Name: {name}"))
        info_layout.addWidget(QLabel(F"Listening Port: {port}"))

        btn_layout = QVBoxLayout()
        root_widget = QWidget()
        roots_layout = QVBoxLayout()

        scroll = QScrollArea()
        roots_layout.addWidget(scroll)
        scroll.setWidgetResizable(True)
        root_widget = QWidget()

        scrollLayout = QVBoxLayout()
        scrollLayout.addStretch(1)
        root_widget.setLayout(scrollLayout)
        scroll.setWidget(root_widget)

        root_widget.setStyleSheet("background-color: white")

        root_btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add File/Folder")
        add_btn.clicked.connect(lambda x: self.add_root(scrollLayout))
        root_btn_layout.addWidget(add_btn)
        rm_btn = QPushButton("Remove File/Folder")
        rm_btn.clicked.connect(lambda x: self.del_root(scrollLayout))
        root_btn_layout.addWidget(rm_btn)
        btn_layout.addLayout(root_btn_layout)
        close_btn = QPushButton("Stop Server")
        close_btn.clicked.connect(lambda x: self.close_server())
        btn_layout.addWidget(close_btn)


        self.addLayout(info_layout, 1)
        self.addLayout(roots_layout, 5)
        self.addLayout(btn_layout, 2)

    def add_root(self, layout):
        dlg = CustomFileDialog()
        filenames = []

        existing_files = []
        for i in range(0, layout.count()):
            if layout.itemAt(i).widget() is not None:
                existing_files.append(layout.itemAt(i).widget().accessibleName())

        if dlg.exec_():
            filenames = dlg.selectedFiles()

        if len(filenames):
            file_name = os.path.basename(filenames[0])
            if filenames[0] not in existing_files:
                self.server.add_root(filenames[0])
                file_label = QLabel(file_name)
                file_label.setAccessibleName(filenames[0])
                layout.insertWidget(layout.count()-1, file_label)

    def del_root(self, layout):
        dw = DelRootWindow(self._parent, layout, self.server)

    def say_hello(self):
        print("Hello")

    def close_server(self):
        self.server.close()
        self.reset()

    def reset(self):
        deleteLayout(self)
        server_add_btn = QPushButton("Open Server")
        server_add_btn.clicked.connect(lambda x: self.setup_server())
        self.addWidget(server_add_btn)
