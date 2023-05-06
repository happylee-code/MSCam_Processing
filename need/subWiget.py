#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
@author: Gao
@project: MSCam_Processing
@file: subWiget.py
@function:
@time: 2022/4/12 9:18
"""
import cv2
import numpy as np
from PyQt5.QtWidgets import *

class SubWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(500,500)
        self.setContextMenuPolicy(2)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        array = [0, 1]
        numarray = np.array(array)
        menu.addAction("子菜单",str(numarray[0]))
        menu.addAction('子菜单2')
        menu.exec_(self.mapToGlobal(event.pos()))