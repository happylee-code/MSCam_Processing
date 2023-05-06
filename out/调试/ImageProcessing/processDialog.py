#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
@author: Gao
@project: Qt_project
@file: processDialog.py
@function:进度条
@time: 2021/11/26 17:38
"""
import sys
from PyQt5.QtWidgets import QApplication, QDialog, QProgressBar, QPushButton, QVBoxLayout, QLabel
from PyQt5.QtCore import QBasicTimer,Qt


class ProcessDialog(QDialog):

    def __init__(self):
        super(ProcessDialog,self).__init__()
        self.resize(300,100)
        vBox = QVBoxLayout()
        label = QLabel("处理中...",self)
        self.pbar = QProgressBar()
        self.pbar.setMaximum(100)
        self.timer = QBasicTimer()
        self.step = 0
        vBox.addWidget(label)
        vBox.addWidget(self.pbar)
        self.setLayout(vBox)
        self.setWindowTitle('提示')
        self.timer.start(10, self)
        # 新建的窗口始终位于当前屏幕的最前面
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        # 阻塞父类窗口不能点击
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlags(Qt.WindowCloseButtonHint)



    def timerEvent(self, e):
        if self.step >= 100:
            self.quit()
            return

        # if self.step == 0:
        #     QTimer.singleShot(10000, self.quit)

    def quit(self):
        QApplication.processEvents() #会使窗口变换流畅
        self.step = 0
        self.pbar.setValue(self.step)
        self.timer.stop()
        self.close()

        # if self.step<99:
        #     self.step = self.step+1
        # self.pbar.setValue(self.step)

if __name__ == '__main__':
     app = QApplication(sys.argv)
     ex = ProcessDialog()
     # QTimer.singleShot(1000, app.quit)
     sys.exit(app.exec_())