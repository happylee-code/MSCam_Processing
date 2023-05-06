#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
@author: Gao
@project: Qt_project
@file: matplotlibBar.py
@function:继承修改 NavigationToolbar2QT中的一些参数
@time: 2021/11/19 11:17
"""
from PyQt5 import QtGui
from matplotlib import cbook
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar, SubplotToolQt


class ToolBar(NavigationToolbar):
    def configure_subplots(self):
        image = str(cbook._get_data_path('images/matplotlib.png'))
        dia = SubplotToolQt(self.canvas.figure, self.canvas.parent())
        dia.setWindowTitle("Configuration")
        dia.setWindowIcon(QtGui.QIcon(image))
        dia.exec_()