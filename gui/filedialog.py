from PyQt5.QtWidgets import QPushButton, QWidget, \
    QAction, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QSizePolicy, QLabel, \
    QLineEdit, QMessageBox, QFileDialog, QListView, QAbstractItemView, QTreeView, QDialog
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import QEvent

# see: https://www.qtcentre.org/threads/43841-QFileDialog-to-select-files-AND-folders
class CustomFileDialog(QFileDialog):
    def __init__(self):
        super().__init__()

        self.m_btnOpen = None
        self.m_listView = None
        self.m_treeView = None
        self.m_selectedFiles = []

        btns = self.findChildren(QPushButton)

        # find the open or choose button
        for btn in btns:
            text = btn.text()
            if text.lower().find("open") != -1 or text.lower().find("choose") != -1:
                self.m_btnOpen = btn
                break

        # install an event fileter
        self.m_btnOpen.installEventFilter(self)
        self.m_btnOpen.clicked.connect(lambda x: self.chooseClicked())

        # find references to the list and tree view
        self.m_listView = self.findChild(QListView, "listView");
        self.m_treeView = self.findChild(QTreeView)

        self.setFileMode(QFileDialog.Directory)
        self.setOption(QFileDialog.DontUseNativeDialog, True)

    # ensure the open/choose button is always activated
    def eventFilter(self, watched, event):
        if watched:
            if event.type() == QEvent.EnabledChange:
                if not watched.isEnabled():
                    watched.setEnabled(True)
        return QWidget.eventFilter(self, watched, event)

    # get the chosen file/folder and accept the choice
    def chooseClicked(self):
        indexList = self.m_listView.selectionModel().selectedIndexes()
        for index in indexList:
            if index.column() == 0:
                self.m_selectedFiles.append(self.directory().absolutePath() + str(index.data()))

        QDialog.accept(self)
