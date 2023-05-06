#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
@author: Gao
@project: Qt_project
@file: ContextMenuTest.py
@function:用来测试嵌套窗口的右键菜单调用
@time: 2022/4/11 10:50
"""
import sys
import numpy as np
from PyQt5.QtWidgets import *
from need.subWiget import SubWidget
import cv2

class Main(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(600,600)
        layout = QHBoxLayout(self)
        subWidget = SubWidget()
        layout.addWidget(subWidget)
        self.setLayout(layout)
        self.setContextMenuPolicy(1)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        array = [0,1]
        numarray = np.array(array)
        menu.addAction(str(numarray[0]))
        menu.addAction('父菜单2')
        menu.exec_(self.mapToGlobal(event.pos()))




