#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
@author: Gao
@project: Qt_project
@file: __init__.py.py
@function:
@time: 2021/10/4 15:38
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LAST_DIR = os.path.abspath(os.path.dirname(BASE_DIR))
sys.path.append(os.path.join(BASE_DIR,'client'))
print("当前路径:",BASE_DIR)
# print(LAST_DIR)
print("第一次运行较慢，请稍等...")