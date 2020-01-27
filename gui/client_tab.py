from PyQt5.QtWidgets import QPushButton, QWidget, QAction, QTabWidget, \
    QVBoxLayout, QHBoxLayout, QPlainTextEdit, QToolButton ,QSizePolicy, \
    QLabel, QLineEdit, QMessageBox
from PyQt5.QtGui import QIcon, QPixmap

from gui.network_widget import NetworkFolderManager
from gui.reconnect_dialog import ReconnectDialog
from utils.gui_functions import deleteLayout
from client import FailedToConnect
from loghandler import ClientAlreadyExists

class ClientTabManager(QWidget):

    opened_tabs = []

    tab_counter = 0

    client = None

    def __init__(self, parent, clt):
        super().__init__(parent)
        self.client_layout = QVBoxLayout(self)
        self.client = clt

        # Initialize tab screen
        self.client_tabs = QTabWidget()
        self.client_tabs.setTabsClosable(False)
        self.client_tabs.tabCloseRequested.connect(self.close_tab)
        self.client_tabs.tabBarClicked.connect(lambda x: print(x))
        self.client_tabs.resize(900,600)

        # Add tabs
        self.add_tab_button = QToolButton(self)
        self.add_tab_button.setText('+')
        font = self.add_tab_button.font()
        font.setBold(True)
        self.add_tab_button.setFont(font)
        self.client_tabs.setCornerWidget(self.add_tab_button)
        self.add_tab_button.clicked.connect(self.add_tab)
        tab1 = QWidget()
        self.setup_tab(tab1)
        self.opened_tabs.append((tab1, "New Tab"))
        self.client_tabs.addTab(self.opened_tabs[0][0], self.opened_tabs[0][1])

        # Add tabs to widget
        self.client_layout.addWidget(self.client_tabs)
        self.setLayout(self.client_layout)



    def connect(self, ip, port, layout):
        #old_layout = copy.deepcopy(layout)
        deleteLayout(layout)
        try:
            self.client.connect_to_server(ip, int(port))
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("Connection successful!")
            msg.setWindowTitle("Connection info")
            msg.exec_()
            layout.addWidget(NetworkFolderManager(self, self.client))
        except FailedToConnect as e:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Error)
            msg.setText("Connection Failed!")
            msg.setInformativeText(str(e))
            msg.setWindowTitle("Connection info")
            msg.exec_()
            self.setup_tab(layout)

        except ClientAlreadyExists as e:
            msg = ReconnectDialog()
            msg.exec_();
            """msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("Connection Failed!")
            msg.setInformativeText(str(e))
            msg.setWindowTitle("Connection info")
            msg.exec_()
            self.setup_tab(layout)"""

    def setup_tab(self, tab_widget):
        tab1_layout = QVBoxLayout()

        conn_btn = QPushButton("Connect...")
        conn_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn_layout = QHBoxLayout()
        btn_layout.addLayout(QVBoxLayout(), 2)
        btn_layout.addWidget(conn_btn, 3)
        btn_layout.addLayout(QVBoxLayout(), 2)

        ip_layout = QHBoxLayout()
        ip_main_layout = QHBoxLayout()
        ip_label = QLabel("IP Address: ")
        ip_edit = QLineEdit()
        ip_layout.addWidget(ip_label)
        ip_layout.addWidget(ip_edit)
        ip_main_layout.addLayout(QVBoxLayout(), 2)
        ip_main_layout.addLayout(ip_layout, 3)
        ip_main_layout.addLayout(QVBoxLayout(), 2)

        port_layout = QHBoxLayout()
        port_main_layout = QHBoxLayout()
        port_label = QLabel("Port: ")
        port_edit = QLineEdit()
        port_edit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        port_layout.addWidget(port_label)
        port_layout.addWidget(port_edit)
        port_main_layout.addLayout(QVBoxLayout(), 2)
        port_main_layout.addLayout(port_layout, 3)
        port_main_layout.addLayout(QVBoxLayout(), 2)

        tab_main = QVBoxLayout()
        tab1_layout.addLayout(ip_main_layout, 2)
        tab1_layout.addLayout(port_main_layout, 2)
        tab1_layout.addLayout(btn_layout, 2)

        tab1_layout.setSpacing(20)
        conn_btn.clicked.connect(lambda x: self.connect(ip_edit.text(), port_edit.text(), tab1_layout))

        tab_main.addLayout(QVBoxLayout(), 2)
        tab_main.addLayout(tab1_layout, 3)
        tab_main.addLayout(QVBoxLayout(), 2)
        #tab1_layout.addStretch(100)
        tab_widget.setLayout(tab_main)

    def add_tab(self):
        if not self.tab_counter:
            self.client_tabs.setTabsClosable(True)
        self.tab_counter += 1
        new_tab = (QWidget(), "New Tab")
        self.setup_tab(new_tab[0])
        self.opened_tabs.append(new_tab)
        self.client_tabs.addTab(new_tab[0], new_tab[1])

    def close_tab(self, index):
        if self.tab_counter == 1:
            self.client_tabs.setTabsClosable(False)

        # TODO: Close any client connections and do cleaning up here
        self.client_tabs.removeTab(index)
        self.tab_counter -= 1
