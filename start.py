#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
@author: Gao
@project: MSCam_Processing
@file: start.py
@function:
@time: 2022/4/12 15:53
"""
import sys
from PyQt5.QtWidgets import QApplication
from ImageProcessing.MainWiget import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())