#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
@author: Gao
@project: Qt_project
@file: mycostomEvent.py
@function:
@time: 2021/11/17 11:40
"""
from PyQt5.QtCore import QEvent


class CustomEvent(QEvent):
    # 注册事件类型
    selectedEvent = QEvent.registerEventType()

    def __init__(self, data):
        super(CustomEvent, self).__init__(CustomEvent.selectedEvent)
        self.data = data

    def getData(self):
        return self.data