#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
@author: Gao
@project: MSCam_Processing
@file: __init__.py.py
@function:
@time: 2022/4/12 10:21
"""
from utils.myUtils import MyUtils
import os
filepath = MyUtils.saveJoint_addr
temfile = MyUtils.saveJoint_addr_tem
if not os.path.exists(filepath):
    os.mkdir(filepath) #创建保存文件夹
if not os.path.exists(temfile):
    os.mkdir(temfile) #创建临时保存文件夹
