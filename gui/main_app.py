from gui.client_tab import ClientTabManager
from gui.server_widget import ServerWidgetManager
from gui.log_widget import LogWindowManager

from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QMainWindow, QApplication

class App(QMainWindow):

    backend = None

    def __init__(self, back):
        super().__init__()
        self.backend = back
        self.title = 'PCLanTransfer - Quick Version'
        self.left = 0
        self.top = 0
        self.width = 900
        self.height = 600
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.table_widget = QWidget(self)
        client_side = QVBoxLayout()
        tab_layout = QVBoxLayout()
        central = QHBoxLayout()
        self.client_tabs = ClientTabManager(self, self.backend.client)
        self.server_bar = ServerWidgetManager(self, self.backend.server)
        self.log_window = LogWindowManager(self)
        tab_layout.addWidget(self.client_tabs)
        client_side.addLayout(tab_layout, 3)
        client_side.addLayout(self.log_window, 1)
        central.addLayout(client_side, 3)
        central.addLayout(self.server_bar, 1)
        self.table_widget.setLayout(central)
        self.setCentralWidget(self.table_widget)

        self.center()
        self.show()

    def center(self):
        frameGm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())
