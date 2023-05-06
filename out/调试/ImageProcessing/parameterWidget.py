import sys

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog
import scipy.io as sio


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.setWindowModality(QtCore.Qt.WindowModal)
        Dialog.resize(352, 150)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(40, 100, 301, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.horizontalLayoutWidget = QtWidgets.QWidget(Dialog)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(9, 30, 331, 50))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(7)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lineEdit = QtWidgets.QLineEdit(self.horizontalLayoutWidget)
        self.lineEdit.setObjectName("lineEdit")
        self.horizontalLayout.addWidget(self.lineEdit)
        self.pushButton = QtWidgets.QPushButton(self.horizontalLayoutWidget)
        self.pushButton.setObjectName("pushButton")
        self.pushButton.clicked.connect(self.importFile)
        self.horizontalLayout.addWidget(self.pushButton)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "导入通道配准参数"))
        self.pushButton.setText(_translate("Dialog", "添加"))

    def importFile(self, Dialog):
        openfile_name = QFileDialog.getOpenFileName(self, '选择目录', './', "matlab Files (*.mat)")
        if len(openfile_name[0])==0:return 0
        self.lineEdit.setText(openfile_name[0])
        self.loadmat(openfile_name[0])
        # addr1 = roadef_info['addr1']
        # addr2 = roadef_info['addr2']
        # addr3 = roadef_info['addr3']
        # addr4 = roadef_info['addr4']
        # addr5 = roadef_info['addr5']
        # addr6 = roadef_info['addr6']

    def loadmat(self,string):
        self.mat_Info = sio.loadmat(string)


class ParaWidget(QtWidgets.QDialog,Ui_Dialog):
    def __init__(self,parent=None):
        super(ParaWidget,self).__init__(parent)
        self.setupUi(self)
        # 新建的窗口始终位于当前屏幕的最前面
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        # 阻塞父类窗口不能点击
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlags(Qt.WindowCloseButtonHint)

class Ui_Dialog2(Ui_Dialog):
    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "导入畸变矫正参数"))
        self.pushButton.setText(_translate("Dialog", "添加"))

    def importFile(self, Dialog):
        openfile_name = QFileDialog.getOpenFileName(self, '选择目录', './', "matlab Files (*.mat)")
        if len(openfile_name[0])==0:return 0
        self.lineEdit.setText(openfile_name[0])
        self.loadmat(openfile_name[0])

    def loadmat(self,string):
        self.mat_Info = sio.loadmat(string)

class ParaWidget2(QtWidgets.QDialog,Ui_Dialog2):
    def __init__(self,parent=None):
        super(ParaWidget2,self).__init__(parent)
        self.setupUi(self)
        # 新建的窗口始终位于当前屏幕的最前面
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        # 阻塞父类窗口不能点击
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlags(Qt.WindowCloseButtonHint)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = ParaWidget2()
    win.show()
    sys.exit(app.exec_())

