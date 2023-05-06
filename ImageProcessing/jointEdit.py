import sys

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication, QDialog, QLabel, QLineEdit, QPushButton, QWidget, QVBoxLayout, \
    QListWidget, QDialogButtonBox, QGridLayout, QRadioButton, QHBoxLayout


class JointDialog(QDialog):
    def __init__(self,fileNames,parent=None):
        super(JointDialog, self).__init__(parent)
        self.flag = 0
        self.resize(600, 600)
        self.setWindowTitle("图像拼接")
        vBox = QVBoxLayout()
        self.listWidget = QListWidget(self)
        self.listWidget.addItems(fileNames)
        self.listWidget.doubleClicked.connect(self.__add)
        self.line = QtWidgets.QFrame(self)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.boxLayout = QVBoxLayout()

        self.bt1 = QRadioButton("左右拼接",self)
        self.bt1.setChecked(True)
        self.bt1.toggled.connect(lambda :self.selectedButtion(self.bt1))
        self.bt2 = QRadioButton("上下拼接",self)
        self.bt2.toggled.connect(lambda: self.selectedButtion(self.bt2))
        self.hBox = QHBoxLayout()
        self.hBox.addStretch(1)
        self.hBox.addWidget(self.bt1)
        self.hBox.addStretch(1)
        self.hBox.addWidget(self.bt2)
        self.hBox.addStretch(1)

        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        vBox.addWidget(self.listWidget)
        vBox.addWidget(self.line)
        vBox.addLayout(self.boxLayout)
        vBox.addLayout(self.hBox)
        vBox.addWidget(self.buttonBox)
        self.setLayout(vBox)

        band = self.listWidget.count()
        self.box = BoxWidget(band)
        self.boxLayout.addWidget(self.box)

    def selectedButtion(self,button):
        if button.text() == "左右拼接" :
            if button.isChecked():
                self.flag = 0
        if button.text() == "上下拼接":
            if button.isChecked():
                self.flag = 1

    def __add(self):
        index = self.box.count
        if index < self.listWidget.count():
            filename = self.listWidget.currentItem().text()
            self.box.setText(index,filename)
            self.box.count += 1






class BoxWidget(QWidget):

    def __init__(self,band,parent=None):
        super(BoxWidget, self).__init__(parent)
        self.count = 0
        self.texts = []
        self.buttons = []
        grid = QGridLayout()
        for i in range(band):
            label = QLabel("band"+str(i+1), self)
            text = QLineEdit(self)
            text.setReadOnly(True)
            self.texts.append(text)
            button = QPushButton("删除", self)
            self.buttons.append(button)
            button.clicked.connect(self.delete)
            grid.addWidget(label,i,0)
            grid.addWidget(text, i, 1)
            grid.addWidget(button, i, 2)
        self.setLayout(grid)


    def delete(self):
        ind = self.buttons.index(self.sender())
        if self.texts[ind].text() != "":
            self.texts[ind].setText("")
            self.count -= 1

    def setText(self,index,filename):
        self.texts[index].setText(filename)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = JointDialog(["高","xing"])
    win.show()
    sys.exit(app.exec_())
