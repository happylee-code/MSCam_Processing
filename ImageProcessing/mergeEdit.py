import sys

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication, QDialog,  QLabel, QLineEdit, QPushButton, QWidget, QVBoxLayout, \
    QListWidget, QDialogButtonBox, QGridLayout


class MergeDialog(QDialog):
    def __init__(self,fileNames,labelNames,parent=None):
        super(MergeDialog, self).__init__(parent)
        self.resize(600, 600)
        vBox = QVBoxLayout()
        self.labelNames = labelNames
        self.listWidget = QListWidget(self)
        self.listWidget.addItems(fileNames)
        self.listWidget.doubleClicked.connect(self.__add)
        self.line = QtWidgets.QFrame(self)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.boxLayout = QVBoxLayout()
        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        vBox.addWidget(self.listWidget)
        vBox.addWidget(self.line)
        vBox.addLayout(self.boxLayout)
        vBox.addWidget(self.buttonBox)
        self.setLayout(vBox)

        self.box = BoxWidget(labelNames)
        self.boxLayout.addWidget(self.box)

    def __add(self):
        filename = self.listWidget.currentItem().text()
        for i,item in enumerate(self.box.editList):
            if item == 0:
                self.box.setText(i, filename)
                self.box.editList[i]=1
                break



class BoxWidget(QWidget):

    def __init__(self,labels,parent=None):
        super(BoxWidget, self).__init__(parent)
        self.texts = []
        self.buttons = []
        self.editList = [0 for _ in range(len(labels))]  #用来记录edit的状态，0表示未占
        grid = QGridLayout()
        for i,label_name in enumerate(labels):
            label = QLabel(label_name, self)
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
            self.editList[ind]=0

    def setText(self,index,filename):
        self.texts[index].setText(filename)


