from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QMainWindow, QApplication, QLabel, QCheckBox, QScrollArea, QSizePolicy
import copy
from utils.gui_functions import deleteLayout

class DelRootWindow(QMainWindow):
    def __init__(self, parent, layout, server):
        super().__init__(parent)
        self.layout = layout
        self.server = server

        self.checkboxes = []
        self.selected_boxes = {}

        self.title = 'Select Folders to Remove'
        self.left = 0
        self.top = 0
        self.width = 400
        self.height = 600
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.roots = []
        self.selected_roots = []
        for i in range(0, self.layout.count()):
            if self.layout.itemAt(i).widget() is not None:
                self.roots.append(self.layout.itemAt(i).widget())

        file_layout = QVBoxLayout()
        main_layout = QVBoxLayout()

        file_scroll = QScrollArea()

        file_layout.addWidget(file_scroll)

        file_scroll.setWidgetResizable(True)

        files_widget = QWidget()

        file_scroll_layout = QVBoxLayout()
        files_widget.setLayout(file_scroll_layout)
        file_scroll.setWidget(files_widget)

        for i in self.roots:
            both_layout = QHBoxLayout()
            both_layout.addWidget(QLabel(i.text()))
            both_layout.addStretch(1)
            chkbox = QCheckBox()
            chkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            self.checkboxes.append(chkbox)
            chkbox.stateChanged.connect(lambda: self.handle_toggle())
            both_layout.addWidget(chkbox)
            file_scroll_layout.addLayout(both_layout)

        file_scroll_layout.addStretch(1)

        main_layout.addWidget(QLabel("Select Files/Folders to remove, then close window"))

        main_layout.addLayout(file_layout)

        file_wid = QWidget()
        file_wid.setLayout(main_layout)

        self.setCentralWidget(file_wid)

        self.center()
        self.show()

    def handle_toggle(self):
        pos = 0
        for i in self.checkboxes:
            if i.isChecked():
                self.selected_boxes[pos] = True
            else:
                self.selected_boxes[pos] = False
            pos += 1

    def center(self):
        frameGm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    # update the given layout here
    def closeEvent(self,event):
        final_roots = []
        pos = 0
        for i in self.roots:
            try:
                if not self.selected_boxes[pos]:
                    final_roots.append([i.text(), i.accessibleName()])
                else:
                    self.server.remove_root(i.text())
            except KeyError:
                final_roots.append([i.text(), i.accessibleName()])
            except Exception as e:
                print(e)
                pass
            pos += 1
        deleteLayout(self.layout)
        ordered_list = []
        while True:
            try:
                ordered_list.append(final_roots.pop())
            except:
                break
        for i in ordered_list:
            new_label = QLabel(i[0])
            new_label.setAccessibleName(i[1])
            self.layout.insertWidget(self.layout.count()-1, new_label)
        self.layout.addStretch(1)
