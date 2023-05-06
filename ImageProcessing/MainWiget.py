#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
@author: Gao
@project: Qt_project
@file: MainWiget.py
@function:图像处理软件的主界面
@time: 2021/10/4 15:39
"""
import re
import os
import time

from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtWidgets import QMainWindow, QWidget, QAction, qApp, QDesktopWidget, QFrame, QTreeWidget, \
    QTreeWidgetItem, QTabWidget, QVBoxLayout, QTextEdit, QSplitter, QFileDialog, QMenu, QMdiSubWindow, \
    QMdiArea,QMessageBox

from PyQt5.QtCore import Qt,  QCoreApplication
from utils.myUtils import MyUtils
from ImageProcessing.imageWiget import ImageWidget,Add_ImageWidget
from ImageProcessing.headEdit import CallEditWidget
from ImageProcessing.mergeEdit import MergeDialog
from ImageProcessing.jointEdit import JointDialog
from ImageProcessing.expandEdit import ExpandEdit
from ImageProcessing.shearEdit import ShearEdit
from ImageProcessing.myCustomEvent import CustomEvent
from ImageProcessing.processDialog import ProcessDialog
from ImageProcessing.mythread import Joint_01_Thread,Joint_2AThread,Joint_2BThread
from ImageProcessing.batchEdit import BatchEdit
from ImageProcessing.parameterWidget import ParaWidget
import numpy as np
import cv2
from ImageProcessing import LAST_DIR
from pds4_tools import pds4_read

class MainWindow(QMainWindow):
    tabCount = 0

    def __init__(self):
        super(MainWindow, self).__init__()
        # 初始化参数
        self.fileNames_1 = []
        self.paths_1 = []
        self.fileNames_2A = []
        self.paths_2A = []
        self.fileNames_2B = []
        self.paths_2B = []
        self.fileNames_2CS = []
        self.paths_2CS = []
        self.fileNames_other = []
        self.paths_other = []
        self.isSelect = True
        self.widget = QWidget(self)
        self.height = QDesktopWidget().availableGeometry().height()
        self.width = QDesktopWidget().availableGeometry().width()
        self.resize(self.width,self.height)
        self.widget.setGeometry(0, 25, self.width, self.height - 25)
        self.setCentralWidget(self.widget)
        self.setWindowTitle("火星多光谱图像处理")
        # 初始化界面
        self.initUI_menu()
        self.initUI_windows()
        print("运行成功")

    def initUI_menu(self):
        # 创建一个状态栏
        self.statusBar()
        # 创建一个菜单栏
        menuBar = self.menuBar()

        # 添加菜单
        fileMenu = menuBar.addMenu('File')
        dealMenu = menuBar.addMenu("标记点")
        # 退出事件
        exitAction = QAction('&退出', self)
        exitAction.setShortcut("ctrl+Q")
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.closeApp)
        # 打开文件事件
        openAction = QAction('打开', self)
        openAction.setShortcut("ctrl+O")
        openAction.setStatusTip('open file')
        openAction.triggered.connect(self.openFile)
        # 保存文件事件
        saveAction = QAction("保存", self)
        saveAction.setShortcut("ctrl+S")
        saveAction.setStatusTip('save file')
        saveAction.triggered.connect(self.saveTemFile)

        # 选择关键点
        selectAction = QAction("选择", self)
        selectAction.setShortcut("ctrl+A")
        selectAction.setStatusTip('选择关键特征点')
        selectAction.triggered.connect(self.selectPoint)

        cancelAction = QAction("取消选择", self)
        cancelAction.setShortcut("ctrl+C")
        cancelAction.setStatusTip('取消选择')
        cancelAction.triggered.connect(self.cancelPoint)
        # 添加文件菜单的处理事件
        fileMenu.addActions([openAction,saveAction,exitAction])
        dealMenu.addActions([selectAction,cancelAction])

    def initUI_windows(self):
        self.initUI_topLeft()
        self.initUI_topMid()
        self.initUI_topRight()
        splitter_H = QSplitter(Qt.Horizontal,self.widget)
        splitter_H.addWidget(self.topLeft)
        splitter_H.addWidget(self.topMid)
        splitter_H.addWidget(self.topRight)
        splitter_H.setStretchFactor(0, 2)
        splitter_H.setStretchFactor(1, 10)
        splitter_H.setStretchFactor(2, 3)

        hBox = QVBoxLayout()
        hBox.addWidget(splitter_H)
        self.widget.setLayout(hBox)



    def initUI_topLeft(self):
        self.topLeft = QFrame(self.widget)
        self.topLeft.setFrameShape(QFrame.StyledPanel)
        self.tree = QTreeWidget(self.topLeft)
        self.tree.itemDoubleClicked['QTreeWidgetItem*','int'].connect(self.openImage)
        self.tree.setFrameShape(0)
        vBox = QVBoxLayout()

        vBox.addWidget(self.tree)
        self.tree.setSelectionMode(3)  # 可选中多个
        # 右键菜单
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.openMenu)
        # 设置列数
        # self.tree.setColumnCount(2)
        # 设置头部控件标题
        self.tree.setHeaderLabels(["文件名","文件大小"])
        # 树形控件的列宽度
        # self.tree.setColumnWidth(0, 160)
        # 设置根节点
        self.root_1 = QTreeWidgetItem(self.tree)
        self.root_1.setText(0, '1级产品')
        self.root_1.setIcon(0, QIcon("icon.png"))

        self.root_2A = QTreeWidgetItem(self.tree)
        self.root_2A.setText(0, '2A级产品')
        self.root_2A.setIcon(0, QIcon("icon.png"))

        self.root_2B = QTreeWidgetItem(self.tree)
        self.root_2B.setText(0, '2B级产品')
        self.root_2B.setIcon(0, QIcon("icon.png"))

        self.root_2CS = QTreeWidgetItem(self.tree)
        self.root_2CS.setText(0, '2CS级产品')
        self.root_2CS.setIcon(0, QIcon("icon.png"))

        self.root_other = QTreeWidgetItem(self.tree)
        self.root_other.setText(0, '其他')
        self.root_other.setIcon(0, QIcon("icon.png"))

        self.topLeft.setLayout(vBox)

    def initUI_topMid(self):
        self.topMid = QFrame(self.widget)
        self.topMid.setFrameShape(QFrame.StyledPanel)
        self.tabWiget = QTabWidget(self.topMid)
        splitter_V = QSplitter(Qt.Vertical)
        splitter_V.addWidget(self.tabWiget)
        vBox = QVBoxLayout()
        self.tabWiget.setTabsClosable(True)
        self.tabWiget.tabCloseRequested.connect(self.closeTab)

        # 信息框
        self.messageLog = QTextEdit(self)
        self.messageLog.setReadOnly(True)
        self.messageLog.setAutoFillBackground(True)
        self.messageLog.setText("操作日志:")
        splitter_V.addWidget(self.messageLog)
        splitter_V.setStretchFactor(0, 150)
        splitter_V.setStretchFactor(1, 1)
        vBox.addWidget(splitter_V)
        self.topMid.setLayout(vBox)

    def initUI_topRight(self):
        self.topRight = QFrame(self.widget)
        self.topRight.setFrameShape(QFrame.StyledPanel)
        splitter_V = QSplitter(Qt.Vertical)
        vBox = QVBoxLayout()
        self.chartLayout = QVBoxLayout()
        self.chartWidget = QWidget(self)
        self.chartWidget.setHidden(True)
        self.chartWidget.setLayout(self.chartLayout)
        # mpl = MyCanvas(self, width=3, height=4, dpi=100)
        # # 画统计图
        # mpl.draw_figure()
        splitter_V.addWidget(self.chartWidget)
        # 信息框
        self.message = QTextEdit(self.topRight)
        self.message.setReadOnly(True)
        self.message.setAutoFillBackground(True)
        self.message.setText("图像相关信息:")
        splitter_V.addWidget(self.message)
        splitter_V.setStretchFactor(0, 15)
        splitter_V.setStretchFactor(1, 1)
        vBox.addWidget(splitter_V)
        self.topRight.setLayout(vBox)

    def selectPoint(self):
        if self.tabWiget.currentWidget() is not None:
            self.isSelect = False
            # 使用SendEvent方式发送
            imageWidget = self.tabWiget.currentWidget().findChild(ImageWidget, "imageWidget")
            imageWidget.setCursor(Qt.CrossCursor)

            sendEvent = CustomEvent(self.isSelect)
            QCoreApplication.sendEvent(imageWidget, sendEvent)

    def cancelPoint(self):
        if self.tabWiget.currentWidget() is not None:
            self.isSelect = True
            # 使用SendEvent方式发送
            imageWidget = self.tabWiget.currentWidget().findChild(ImageWidget, "imageWidget")
            imageWidget.setCursor(Qt.ArrowCursor)
            # 使用SendEvent方式发送
            sendEvent = CustomEvent(self.isSelect)
            QCoreApplication.sendEvent(imageWidget, sendEvent)


    def openFile(self):
        # 每次打开前清空
        self.fileNames_1 = []
        self.paths_1 = []
        self.fileNames_2A = []
        self.paths_2A = []
        self.fileNames_2B = []
        self.paths_2B = []
        self.fileNames_2CS = []
        self.paths_2CS = []
        self.fileNames_other = []
        self.paths_other = []

        # 清空QTreeWidgetItem中的项目
        self.root_1.takeChildren()
        self.root_2A.takeChildren()
        self.root_2B.takeChildren()
        self.root_2CS.takeChildren()
        self.root_other.takeChildren()

        download_path = QFileDialog.getExistingDirectory(self, "浏览", ".")
        download_path = download_path.replace("/","\\")
        if len(download_path) < 4: return 0
        MyUtils.fileNames = []
        MyUtils.paths = []
        MyUtils.get_all(download_path)
        # 对文件夹中的文件进行过滤

        pattern_1 = re.compile(r'.*SCI_N.*(\.01)$') #匹配以.01结尾的字符串
        pattern_2A = re.compile(r'.*(\.2A)$')
        pattern_2B = re.compile(r'.*(\.2B)$')
        pattern_2CS = re.compile(r'.*(\.2C)$')
        pattern_other = re.compile(r'.*(\.raw|\.img)$')

        for fileName,path in zip(MyUtils.fileNames,MyUtils.paths):
            if re.match(pattern_1, fileName):
                self.fileNames_1.append(fileName)
                self.paths_1.append(path)
            if re.match(pattern_2A, fileName):
                self.fileNames_2A.append(fileName)
                self.paths_2A.append(path)
            if re.match(pattern_2B, fileName):
                self.fileNames_2B.append(fileName)
                self.paths_2B.append(path)
            if re.match(pattern_2CS, fileName):
                self.fileNames_2CS.append(fileName)
                self.paths_2CS.append(path)
            if re.match(pattern_other,fileName):
                self.fileNames_other.append(fileName)
                self.paths_other.append(path)

        for fileName_1,path_1 in zip(self.fileNames_1,self.paths_1):
            # 为根目录添加子项目
            child = QTreeWidgetItem(self.root_1)
            child.setText(0, fileName_1)
            child.setText(1, MyUtils.get_fileSize(path_1))

        for fileName_2A,path_2A in zip(self.fileNames_2A,self.paths_2A):
            child = QTreeWidgetItem(self.root_2A)
            child.setText(0, fileName_2A)
            child.setText(1, MyUtils.get_fileSize(path_2A))

        for fileName_2B,path_2B in zip(self.fileNames_2B,self.paths_2B):
            child = QTreeWidgetItem(self.root_2B)
            child.setText(0, fileName_2B)
            child.setText(1, MyUtils.get_fileSize(path_2B))

        for fileName_2CS,path_2CS in zip(self.fileNames_2CS,self.paths_2CS):
            child = QTreeWidgetItem(self.root_2CS)
            child.setText(0, fileName_2CS)
            child.setText(1, MyUtils.get_fileSize(path_2CS))

        for fileName_other,path_other in zip(self.fileNames_other,self.paths_other):
            child = QTreeWidgetItem(self.root_other)
            child.setText(0, fileName_other)
            child.setText(1, MyUtils.get_fileSize(path_other))

        self.tree.addTopLevelItems([self.root_1,self.root_2A,self.root_2B,self.root_2CS,self.root_other])
        # 节点展开
        self.tree.expandAll()

    def saveTemFile(self):
        MyUtils.save_file(MyUtils.saveJoint_addr_tem,MyUtils.saveJoint_addr)
        QMessageBox.information(self, "提示：", '已保存!')

    def saveFile(self,image,message_dic):
        dataType = type(image.flatten()[0])
        if len(image.shape)>2:
            bsqImage = np.zeros((image.shape[2], image.shape[0],image.shape[1]),dtype=dataType) #转变为bsq
            for i in range(image.shape[2]):
                bsqImage[i,:,:] = image[:,:,i]
        else:
            bsqImage = image.copy()
        dataType = str(dataType)
        datatype = dataType[dataType.find(".") + 1:-2]
        dataNum = MyUtils.ENVIDateType_re[datatype]#  将类型转换为ENVI的数字表示
        dir_path = QFileDialog.getSaveFileName(self, '选择保存路径', str(int(time.time())),'*.raw;;*.bmp;;*.png;;*.jpg')
        if len(dir_path[0]) == 0: return 0
        if dir_path[0][-4:] == '.raw':
            bsqImage.tofile(dir_path[0])
            h1 = 'ENVI'
            h2 = 'description ='
            h3 = '{\n'    #'File Imported into ENVI. }'
            for k,v in message_dic.items():
                tem = k+":"+v+"\n"
                h3 += tem
            h3 += '}'
            h4 = 'samples = ' + str(image.shape[1])  # 列
            h5 = 'lines   = ' + str(image.shape[0])  # 行
            if len(image.shape)>2:
                h6 = 'bands   =  ' + str(image.shape[2])  # 波段数
            else:
                h6 = 'bands   =  ' + str(1)  # 波段数
            h7 = 'header offset = 0'
            h8 = 'file type = ENVI Standard'
            h9 = 'data type = ' + dataNum # 数据格式
            h10 = 'interleave = bsq'  # 存储格式
            h11 = 'sensor type = Unknown'
            h12 = 'byte order = 0'
            if not message_dic.keys().__contains__("central_wavelength"):
                h13 = 'wavelength units = Unknown'
            else:
                h13 = 'wavelength = {'+message_dic["central_wavelength"]+'}'
            h = [h1, h2, h3, h4, h5, h6, h7, h8, h9, h10, h11, h12, h13]
            doc = open(dir_path[0][:-4]+".hdr", 'w')
            for i in range(len(h)):
                print(h[i], end='\n', file=doc)
                # print('\n', end='', file=doc)
            doc.close()
            self.messageLog.append("已保存")
        else:
            image = MyUtils.normalize(image)
            if len(image.shape)==3 and image.shape[2]==3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            cv2.imwrite(dir_path[0], image)
            self.messageLog.append("已保存")

    def openMenu(self):
        """
        @function:文件列表的菜单处理
        """
        menu = QMenu(self)
        items = self.tree.selectedItems()
        is_01 = True # 判定选择的item是否全为01文件
        is_2A = True
        is_2B = True
        is_2CS = True
        is_other = True

        for item in items:
            if not self.fileNames_1.__contains__(item.text(0)):
                is_01 = False
            if not self.fileNames_2A.__contains__(item.text(0)):
                is_2A = False
            if not self.fileNames_2B.__contains__(item.text(0)):
                is_2B = False
            if not self.fileNames_2CS.__contains__(item.text(0)):
                is_2CS = False
            if not self.fileNames_other.__contains__(item.text(0)):
                is_other = False

        if is_01:
            action1 = menu.addAction('打开')
            action1.triggered.connect(lambda:self.openImage_type("01"))
            action = menu.addAction('拆分')
            action.triggered.connect(self.splitImage_01)
            action = menu.addAction('自动拼接')
            action.triggered.connect(self.fileJoint_01)
            # action = menu.addAction('合成')
            # action.triggered.connect(...)
            menu.exec_(QCursor.pos())
        if is_2A:
            action1 = menu.addAction('打开')
            action1.triggered.connect(lambda:self.openImage_type("2A"))
            action = menu.addAction('拼接')
            action.triggered.connect(self.joint_2A)
            action = menu.addAction('合成')
            action.triggered.connect(lambda:self.merge("2A"))
            action = menu.addAction('嵌入')
            action.triggered.connect(lambda:self.embed("2A"))
            action = menu.addAction('裁剪')
            action.triggered.connect(lambda:self.shear("2A"))
            menu.exec_(QCursor.pos())
        if is_2B:
            action1 = menu.addAction('打开')
            action1.triggered.connect(lambda:self.openImage_type("2B"))
            action = menu.addAction('拼接')
            action.triggered.connect(self.joint_2A)
            action = menu.addAction('合成')
            action.triggered.connect(lambda: self.merge("2B"))
            action = menu.addAction('嵌入')
            action.triggered.connect(lambda:self.embed("2B"))
            action = menu.addAction('裁剪')
            action.triggered.connect(lambda:self.shear("2B"))
            menu.exec_(QCursor.pos())
        if is_2CS:
            action1 = menu.addAction('打开2CS')
            # action1.triggered.connect(self.selectItems)
            action = menu.addAction('rename')
            # action.triggered.connect(...)
            # action = menu.addAction('delete')
            # action.triggered.connect(...)
            menu.exec_(QCursor.pos())

        if is_other:
            action1 = menu.addAction('打开raw')
            action1.triggered.connect(lambda :self.openImage_other(os.path.getsize(self.paths_other[self.fileNames_other.index(items[0].text(0))])))
            # action = menu.addAction('rename')
            # action.triggered.connect(...)
            # action = menu.addAction('delete')
            # action.triggered.connect(...)
            menu.exec_(QCursor.pos())

        if len(items) == 1 and items[0].text(0) == "1级产品":
            action1 = menu.addAction("自动批处理")
            action1.triggered.connect(lambda :self.autoBatch("01")) # self.autoJoint_01
            # action = menu.addAction('rename')
            # action.triggered.connect(...)
            # action = menu.addAction('delete')
            # action.triggered.connect(...)
            menu.exec_(QCursor.pos())

        if len(items) == 1 and items[0].text(0) == "2A级产品":
            action1 = menu.addAction("自动批处理")
            action1.triggered.connect(lambda :self.autoBatch("2A"))
            menu.exec_(QCursor.pos())

        if len(items) == 1 and items[0].text(0) == "2B级产品":
            action1 = menu.addAction("自动批处理")
            action1.triggered.connect(lambda :self.autoBatch("2B"))
            menu.exec_(QCursor.pos())

    def autoBatch(self,string): #自动批处理文件
        batchEdit = BatchEdit(string)
        if batchEdit.exec_():
            batchDic = batchEdit.getBatchDict()
            if not os.path.exists(MyUtils.translateTform_addr): #如果参数不存在
                paraWidget = ParaWidget()
                if paraWidget.exec_():
                    MyUtils.translateTform_addr = paraWidget.lineEdit.text()
            if string=="01":
                self.autoJoint_01(batchDic)
            if string=="2A":
                self.autoJoint_2A(batchDic)
            if string=="2B":
                self.autoJoint_2B(batchDic)
            if string=="2CS":
                pass

    def openImage(self,item,column_no): # 实现双击打开图片
        if self.fileNames_1.__contains__(item.text(0)):
            self.openImage_type("01")
        if self.fileNames_2A.__contains__(item.text(0)):
            self.openImage_type("2A")
        if self.fileNames_2B.__contains__(item.text(0)):
            self.openImage_type("2B")
        if self.fileNames_other.__contains__(item.text(0)):
            self.openImage_other(os.path.getsize(self.paths_other[self.fileNames_other.index(item.text(0))]))
        elif item.text(0).endswith(".raw"):
            self.openImage_tem()



    def openImage_type(self,string):
        items = self.tree.selectedItems()
        tabArea = QMdiArea()  # 添加页面窗口
        if string == "01":
            fileNames = self.fileNames_1
            paths = self.paths_1
        if string == "2A":
            fileNames = self.fileNames_2A
            paths = self.paths_2A
        if string == "2B":
            fileNames = self.fileNames_2B
            paths = self.paths_2B
        for item in items:
            ind = fileNames.index(str(item.text(0)))
            path = paths[ind]
            try:
                MyUtils.readXML(path + 'L', fileType=string)
                if string == "01":
                    dir_message = MyUtils.dir_message_01
                    band = int(dir_message["Time"])
                    mode = '>u2'
                else:
                    band = 1
                    mode = '<u2'
                if string == "2A":
                    dir_message = MyUtils.dir_message_2A
                if string == "2B":
                    dir_message = MyUtils.dir_message_2B
                width = int(dir_message["Sample"])
                height = int(dir_message["Line"])
                image = MyUtils.read_type(path, width, height,band,string,mode)
                sub = QMdiSubWindow()
                sub.setWindowIcon(QIcon(os.path.join(LAST_DIR,"icon.png")))
                sub.setWindowFlags(Qt.Tool)
                if string == "01":
                    imageWidget = Add_ImageWidget(image, self)
                    imageWidget.all_detalMessage = MyUtils.dir_message_01.copy()
                    imageWidget.part_detalMessage = MyUtils.list_message_01.copy()
                    for part in imageWidget.part_detalMessage:
                        band = int(part["Band_Number"][-1])
                        part.update({"central_wavelength": MyUtils.CentralWavelength[band - 1]})
                else:
                    imageWidget = ImageWidget(image, self)
                    imageWidget.detailMessage = dir_message.copy()
                sub.resize(image.shape[1] + 80, image.shape[0] + 80)
                sub.setMaximumSize(1200, 1200)
                imageWidget.setWindowTitle(item.text(0))
                self.messageLog.append("打开" + item.text(0) + "...")
                sub.setWidget(imageWidget)
                tabArea.addSubWindow(sub)
            except Exception:
                QMessageBox.information(self, "提示：", '文件打开失败!')

        MainWindow.tabCount += 1
        self.tabWiget.addTab(tabArea, "页面" + str(MainWindow.tabCount))
        self.tabWiget.setCurrentWidget(tabArea)  # 设置为当前页面


    def splitImage_01(self):
        items = self.tree.selectedItems()
        if len(items)>1:
            QMessageBox.information(self, "提示：", '只能选择一项!')
        else:
            ind = self.fileNames_1.index(str(items[0].text(0)))
            path = self.paths_1[ind]
            try:
                # 打开01文件
                MyUtils.readXML(path + 'L', fileType="01")
                MyUtils.width_01 = int(MyUtils.dir_message_01["Sample"])
                MyUtils.height_01 = int(MyUtils.dir_message_01["Line"])
                MyUtils.band_01 = int(MyUtils.dir_message_01["Time"])
                MyUtils.mode_01 = '>u2'
                images = MyUtils.read_01(path, MyUtils.width_01, MyUtils.height_01, MyUtils.band_01,
                                     MyUtils.mode_01)
                # 保存拆分文件
                save_path = QFileDialog.getExistingDirectory(self, "选择拆分到文件夹", "./")
                if len(save_path) == 0: return 0
                self.messageLog.append("拆分" + self.paths_1[ind] + "...")
                for i in range(MyUtils.band_01):
                    fileName = "HX1-Ro_GRAS_MSCam-W-" + str(i + 1) + "-" + str(int(time.time())) + ".raw"
                    images[i].tofile(os.path.join(save_path, fileName))
                self.messageLog.append("已拆分到" + save_path + "文件夹")
            except Exception:
                QMessageBox.information(self, "提示：", '文件打开失败!')

    def autoJoint_01(self,batchDic):  # 对01文件夹下的所有文件进行处理输出展示,batchDic是编辑窗口返回的信息
        for i in range(self.root_1.childCount()):
            filename = self.root_1.child(i).text(0)
            path = self.paths_1[self.fileNames_1.index(filename)]
            self.joint_01(path,batchDic)

    def fileJoint_01(self): # 对01多个选中文件的处理输出展示
        batchEdit = BatchEdit("01")
        if batchEdit.exec_():
            batchDic = batchEdit.getBatchDict()
            items = self.tree.selectedItems()
            for i, item in enumerate(items):
                filename = item.text(0)
                path = self.paths_1[self.fileNames_1.index(filename)]
                self.joint_01(path,batchDic)

    def joint_01(self,path,dic): # 对01单个文件的处理输出展示,dic存放选项
        self.joint_01Thread = Joint_01_Thread(path,dic)
        self.processDiaog = ProcessDialog()

        # 添加临时文件树结构目录
        self.root_tem = QTreeWidgetItem()
        self.root_tem.setText(0, '01临时文件')
        self.root_tem.setIcon(0, QIcon("tem_icon.png"))
        items = self.tree.findItems("01临时文件",Qt.MatchContains,0)
        if len(items)==0:
            self.tree.insertTopLevelItem(0,self.root_tem)
        self.joint_01Thread.finish.connect(self.addTable)
        self.joint_01Thread.excepted.connect(self.threadException)
        self.joint_01Thread.start()
        if not self.processDiaog.exec_():
            self.joint_01Thread.terminate()

    def threadException(self,string): #string为接收到的异常信息
        self.processDiaog.quit()
        self.messageLog.append(string)
        QMessageBox.information(self, "提示：", '操作失败!')

    def addTable(self,new_image,step,title,all_message_dic,part_message_list,isShow,fileType): # 用于在主窗口界面添加页面
        # new_image是numpy图片
        # step表示进度条的进程
        # title表示页面的标题
        self.processDiaog.step = step
        self.processDiaog.pbar.setValue(step)

        child = QTreeWidgetItem()
        child.setText(0, all_message_dic["product_id"])
        if fileType == "01":
            items = self.tree.findItems("01临时文件", Qt.MatchContains, 0)
            targetItem = items[0]
            targetItem.insertChild(0, child)
            targetItem.setExpanded(True)
        if fileType == "2A":
            items = self.tree.findItems("2A临时文件", Qt.MatchContains, 0)
            targetItem = items[0]
            targetItem.insertChild(0, child)
            targetItem.setExpanded(True)
        if fileType == "2B":
            items = self.tree.findItems("2B临时文件", Qt.MatchContains, 0)
            targetItem = items[0]
            targetItem.insertChild(0, child)
            targetItem.setExpanded(True)

        if isShow:
            tabArea = QMdiArea()  # 添加页面窗口
            sub = QMdiSubWindow()
            sub.setWindowIcon(QIcon(os.path.join(LAST_DIR,"icon.png")))
            sub.setWindowFlags(Qt.Tool)
            sub.resize(new_image.shape[1]+50, new_image.shape[0]+80)
            sub.setMaximumSize(1200, 800)
            add_imageWidget = Add_ImageWidget(new_image, self)
            add_imageWidget.all_detalMessage = all_message_dic
            add_imageWidget.part_detalMessage = part_message_list
            add_imageWidget.setObjectName("add_imageWidget")
            add_imageWidget.setWindowTitle(title)
            self.messageLog.append("合并图像")
            sub.setWidget(add_imageWidget)
            tabArea.addSubWindow(sub)

            MainWindow.tabCount += 1
            self.tabWiget.addTab(tabArea, "页面" + str(MainWindow.tabCount))
            self.tabWiget.setCurrentWidget(tabArea)  # 设置为当前页面



    def autoJoint_2A(self,batchDic): # batchDic传入批处理信息字典
        self.joint_2AThread = Joint_2AThread(self.fileNames_2A,self.paths_2A,batchDic)
        self.processDiaog = ProcessDialog()
        self.root_tem = QTreeWidgetItem()
        self.root_tem.setText(0, '2A临时文件')
        self.root_tem.setIcon(0, QIcon("tem_icon.png"))
        items = self.tree.findItems("2A临时文件", Qt.MatchContains, 0)
        if len(items) == 0:
            self.tree.insertTopLevelItem(0, self.root_tem)

        self.joint_2AThread.start()
        self.joint_2AThread.finish.connect(self.addTable)
        self.joint_2AThread.excepted.connect(self.threadException)
        if not self.processDiaog.exec_():
            self.joint_2AThread.terminate()

    def autoJoint_2B(self,batchDic):
        self.joint_2BThread = Joint_2BThread(self.fileNames_2B, self.paths_2B, batchDic)
        self.processDiaog = ProcessDialog()
        self.root_tem = QTreeWidgetItem()
        self.root_tem.setText(0, '2B临时文件')
        self.root_tem.setIcon(0, QIcon("tem_icon.png"))
        items = self.tree.findItems("2B临时文件", Qt.MatchContains, 0)
        if len(items) == 0:
            self.tree.insertTopLevelItem(0, self.root_tem)

        self.joint_2BThread.start()
        self.joint_2BThread.finish.connect(self.addTable)
        self.joint_2BThread.excepted.connect(self.threadException)
        if not self.processDiaog.exec_():
            self.joint_2BThread.terminate()


    def openImage_other(self, size): # 用来打开raw格式图像
        items = self.tree.selectedItems()
        tabArea = QMdiArea()  # 添加页面窗口
        for i, item in enumerate(items):
            ind = self.fileNames_other.index(str(item.text(0)))
            path = self.paths_other[ind]
            if path.endswith(".raw"):
                strings = path.split(".",1)
                hdrPath = strings[0]+'.hdr'
                try:
                    hdrDic,description = MyUtils.readHDR(hdrPath)
                    width = int(hdrDic["samples"])
                    height = int(hdrDic["lines"])
                    band = int(hdrDic["bands"])
                    dataType = MyUtils.ENVIDateType[hdrDic["data type"]]
                    byteOrder = hdrDic["byte order"]
                    values = [e for e in MyUtils.dir2.values()]
                    mode = values[int(byteOrder)]+MyUtils.dir1[dataType]
                    images = MyUtils.read_other(path, width, height,band,mode)
                    # 添加到页面
                    sub = QMdiSubWindow()
                    sub.setWindowIcon(QIcon(os.path.join(LAST_DIR,"icon.png")))
                    sub.setWindowFlags(Qt.Tool)
                    sub.resize(images.shape[1] + 40, images.shape[0] + 60)
                    sub.setMaximumSize(1200, 800)
                    add_imageWidget = Add_ImageWidget(images, self)
                    add_imageWidget.all_detalMessage = description #添加描述信息
                    add_imageWidget.part_detalMessage = []
                    #添加描述信息
                    add_imageWidget.setObjectName("add_imageWidget")
                    add_imageWidget.setWindowTitle(item.text(0))
                    self.messageLog.append("打开" + item.text(0) + "...")
                    sub.setWidget(add_imageWidget)
                    tabArea.addSubWindow(sub)
                except IOError:
                    hrdWidget = CallEditWidget(MyUtils.width_other, MyUtils.height_other, MyUtils.band_other,
                                               MyUtils.mode_other[1:],
                                               MyUtils.mode_other[0])
                    hrdWidget.setWindowTitle("打开文件")
                    hrdWidget.label.setText("共：{0}字节".format(size))
                    if hrdWidget.exec_():
                        images = MyUtils.read_other(path, MyUtils.width_other, MyUtils.height_other,
                                                    MyUtils.band_other,
                                                    MyUtils.mode_other)
                        sub = QMdiSubWindow()
                        sub.setWindowIcon(QIcon(os.path.join(LAST_DIR,"icon.png")))
                        sub.setWindowFlags(Qt.Tool)
                        sub.resize(images.shape[1] + 40, images.shape[0] + 60)
                        sub.setMaximumSize(1200, 800)
                        add_imageWidget = Add_ImageWidget(images, self)
                        add_imageWidget.setObjectName("add_imageWidget")
                        add_imageWidget.setWindowTitle(item.text(0))
                        self.messageLog.append("打开" + item.text(0) + "...")
                        sub.setWidget(add_imageWidget)
                        tabArea.addSubWindow(sub)

            if path.endswith(".img"):
                strings = path.split(".", 1)
                xmlPath = strings[0] + '.xml'
                d = pds4_read(xmlPath, quiet=True)
                images = np.array(d[0].data)
                dataType = type(images.flatten()[0])
                img = np.zeros((images.shape[1], images.shape[2], images.shape[0]), dtype=dataType)
                for j in range(images.shape[0]):
                    img[:, :, j] = images[j, :, :]
                # MyUtils.readXML(xmlPath,"2A")
                sub = QMdiSubWindow()
                sub.setWindowIcon(QIcon(os.path.join(LAST_DIR, "icon.png")))
                sub.setWindowFlags(Qt.Tool)
                sub.resize(img.shape[1] + 40, img.shape[0] + 60)
                sub.setMaximumSize(1200, 800)
                add_imageWidget = Add_ImageWidget(img, self)
                all_detalMessage = dict()
                root = d.label.to_dict()['Product_Observational']  # 读取图像说明文件
                for j in MyUtils.dict_generator(root):
                    all_detalMessage.update({'.'.join(j[0:-1]): j[-1]})
                add_imageWidget.all_detalMessage =  all_detalMessage # 添加描述信息
                add_imageWidget.part_detalMessage = []
                # 添加描述信息
                add_imageWidget.setObjectName("add_imageWidget")
                add_imageWidget.setWindowTitle(item.text(0))
                self.messageLog.append("打开" + item.text(0) + "...")
                sub.setWidget(add_imageWidget)
                tabArea.addSubWindow(sub)

        MainWindow.tabCount += 1
        self.tabWiget.addTab(tabArea, "页面" + str(MainWindow.tabCount))
        self.tabWiget.setCurrentWidget(tabArea)  # 设置为当前页面

    def openImage_tem(self):
        items = self.tree.selectedItems()
        tabArea = QMdiArea()  # 添加页面窗口
        for i, item in enumerate(items):
            path = os.path.join(MyUtils.saveJoint_addr_tem,item.text(0))
            strings = path.split(".", 1)
            hdrPath = strings[0] + '.hdr'
            try:
                hdrDic, description = MyUtils.readHDR(hdrPath)
                width = int(hdrDic["samples"])
                height = int(hdrDic["lines"])
                band = int(hdrDic["bands"])
                dataType = MyUtils.ENVIDateType[hdrDic["data type"]]
                byteOrder = hdrDic["byte order"]
                values = [e for e in MyUtils.dir2.values()]
                mode = values[int(byteOrder)] + MyUtils.dir1[dataType]
                images = MyUtils.read_other(path, width, height, band, mode)
                # 添加到页面
                sub = QMdiSubWindow()
                sub.setWindowIcon(QIcon(os.path.join(LAST_DIR, "icon.png")))
                sub.setWindowFlags(Qt.Tool)
                sub.resize(images.shape[1] + 40, images.shape[0] + 60)
                sub.setMaximumSize(1200, 800)
                add_imageWidget = Add_ImageWidget(images, self)
                add_imageWidget.all_detalMessage = description  # 添加描述信息
                # 添加描述信息
                add_imageWidget.setObjectName("add_imageWidget")
                add_imageWidget.setWindowTitle(item.text(0))
                self.messageLog.append("打开" + item.text(0) + "...")
                sub.setWidget(add_imageWidget)
                tabArea.addSubWindow(sub)
            except IOError:
                QMessageBox.information(self, "提示：", '请确保该图像的hdr文件未被删除！')
        MainWindow.tabCount += 1
        self.tabWiget.addTab(tabArea, "页面" + str(MainWindow.tabCount))
        self.tabWiget.setCurrentWidget(tabArea)  # 设置为当前页面


    def merge(self,type):
        items = self.tree.selectedItems()
        fileNames = []
        for item in items:
            fileNames.append(item.text(0))
        labelNames = ["band{0}:".format(i) for i in range(1, len(fileNames) + 1)]
        mergeWidget = MergeDialog(fileNames, labelNames)
        mergeWidget.setWindowTitle("通道合成")
        if mergeWidget.exec_():
            fileNames_order = []
            for text in mergeWidget.box.texts:
                if text.text() != '':
                    fileNames_order.append(text.text())  # 转变顺序

            if type == "2A":
                width = MyUtils.width_2A
                height = MyUtils.height_2A
                mode = MyUtils.mode_2A
                band = MyUtils.band_2A
                fileNames = self.fileNames_2A
                paths = self.paths_2A

            if type == "2B":
                width = MyUtils.width_2B
                height = MyUtils.height_2B
                mode = MyUtils.mode_2B
                band = MyUtils.band_2B
                fileNames = self.fileNames_2B
                paths = self.paths_2B

            images = np.zeros((width, height, len(fileNames_order)), "uint16")
            messageList = []
            for i, fileName_order in enumerate(fileNames_order):
                dic2 = {}
                dic2.update({"Source": fileName_order})
                messageList.append(dic2)
                ind = fileNames.index(fileName_order)
                path = paths[ind]
                image = MyUtils.read_type(path, width, height,band,type,mode)
                images[:, :, i] = image

            if len(fileNames_order) == 0: return 0
            dic = {}

            dic.update({"comes form": str(fileNames_order), "Lines": str(images.shape[1]),
                        "Samples": str(images.shape[0]), "Bands": str(len(fileNames_order))
                        })
            self.saveFile(images, dic)
            self.messageLog.append("已合并")

            tabArea = QMdiArea()  # 添加页面窗口
            sub = QMdiSubWindow()
            sub.setWindowIcon(QIcon(os.path.join(LAST_DIR,"icon.png")))
            sub.setWindowFlags(Qt.Tool)
            sub.resize(500, 500)
            sub.setMaximumSize(1200, 800)
            MyUtils.band_other = len(fileNames_order)
            add_imageWidget = Add_ImageWidget(images, self)
            add_imageWidget.all_detalMessage = dic
            add_imageWidget.part_detalMessage = messageList
            add_imageWidget.setObjectName("add_imageWidget")
            add_imageWidget.setWindowTitle("合并通道图像")
            self.messageLog.append("打开合并通道图像...")
            sub.setWidget(add_imageWidget)
            tabArea.addSubWindow(sub)
            MainWindow.tabCount += 1
            self.tabWiget.addTab(tabArea, "页面" + str(MainWindow.tabCount))
            self.tabWiget.setCurrentWidget(tabArea)  # 设置为当前页面

    def embed(self,type):
        items = self.tree.selectedItems()
        expandEdit = ExpandEdit()
        if expandEdit.exec_():
            tabArea = QMdiArea()  # 添加页面窗口
            width_ = int(expandEdit.lineEdit.text())
            height_ = int(expandEdit.lineEdit_2.text())
            pos_x = int(expandEdit.lineEdit_3.text())
            pos_y = int(expandEdit.lineEdit_4.text())

            if type == "2A":
                width = MyUtils.width_2A
                height = MyUtils.height_2A
                mode = MyUtils.mode_2A
                band = MyUtils.band_2A
                fileNames = self.fileNames_2A
                paths = self.paths_2A

            if type == "2B":
                width = MyUtils.width_2B
                height = MyUtils.height_2B
                mode = MyUtils.mode_2B
                band = MyUtils.band_2B
                fileNames = self.fileNames_2B
                paths = self.paths_2B
            for item in items:
                ind = fileNames.index(item.text(0))
                path = paths[ind]
                new_image = np.zeros((height_, width_), dtype='uint16')
                try:
                    image = MyUtils.read_type(path, width, height,band,type,mode)
                    self.messageLog.append("填充" + item.text(0) + "...")
                    new_image[pos_y:pos_y + image.shape[0], pos_x:pos_x + image.shape[1]] = image
                    self.messageLog.append("填充完成")
                    sub = QMdiSubWindow()
                    sub.setWindowIcon(QIcon(os.path.join(LAST_DIR,"icon.png")))
                    sub.setWindowFlags(Qt.Tool)
                    sub.resize(width_ + 30, height_ + 30)
                    sub.setMaximumSize(1200, 800)
                    # new_image = MyUtils.normalize(new_image)
                    imageWidget = ImageWidget(new_image,self)
                    imageWidget.setObjectName("imageWidget")
                    imageWidget.setWindowTitle(item.text(0))
                    self.messageLog.append("打开" + item.text(0) + "...")
                    sub.setWidget(imageWidget)
                    tabArea.addSubWindow(sub)

                except Exception:
                    QMessageBox.information(self, "提示：", '合成失败！')
                    self.messageLog.append("合成失败！")

            MainWindow.tabCount += 1
            self.tabWiget.addTab(tabArea, "页面" + str(MainWindow.tabCount))
            self.tabWiget.setCurrentWidget(tabArea)  # 设置为当前页面

    def shear(self,type):
        items = self.tree.selectedItems()
        shearEdit = ShearEdit()
        if shearEdit.exec_():
            tabArea = QMdiArea()  # 添加页面窗口
            width_1 = int(shearEdit.lineEdit_1.text())
            width_2 = int(shearEdit.lineEdit_2.text())
            height_1 = int(shearEdit.lineEdit_3.text())
            height_2 = int(shearEdit.lineEdit_4.text())
            if type == "2A":
                width = MyUtils.width_2A
                height = MyUtils.height_2A
                mode = MyUtils.mode_2A
                band = MyUtils.band_2A
                fileNames = self.fileNames_2A
                paths = self.paths_2A

            if type == "2B":
                width = MyUtils.width_2B
                height = MyUtils.height_2B
                mode = MyUtils.mode_2B
                band = MyUtils.band_2B
                fileNames = self.fileNames_2B
                paths = self.paths_2B
            for item in items:
                ind = fileNames.index(item.text(0))
                path = paths[ind]
                try:
                    image = MyUtils.read_type(path, width, height,band, type,mode)
                    self.messageLog.append("裁剪" + item.text(0) + "...")
                    new_image = image[height_1:height_2, width_1:width_2].copy()
                    self.messageLog.append("裁剪完成")
                    sub = QMdiSubWindow()
                    sub.setWindowIcon(QIcon(os.path.join(LAST_DIR,"icon.png")))
                    sub.setWindowFlags(Qt.Tool)
                    sub.resize(new_image.shape[1] + 30, new_image.shape[0] + 30)
                    sub.setMaximumSize(1200, 800)
                    # new_image = MyUtils.normalize(new_image)
                    imageWidget = ImageWidget(new_image,self)
                    imageWidget.setObjectName("imageWidget")
                    imageWidget.setWindowTitle(item.text(0))
                    self.messageLog.append("打开" + item.text(0) + "...")
                    sub.setWidget(imageWidget)
                    tabArea.addSubWindow(sub)
                except Exception as e:
                    QMessageBox.information(self, "提示：", '裁剪失败！')
                    self.messageLog.append("裁剪失败！")

            MainWindow.tabCount += 1
            self.tabWiget.addTab(tabArea, "页面" + str(MainWindow.tabCount))
            self.tabWiget.setCurrentWidget(tabArea)  # 设置为当前页面

    def joint_2A(self):
        items = self.tree.selectedItems()
        fileNames = []
        for item in items:
            fileNames.append(item.text(0))
        jointWidget = JointDialog(fileNames)
        jointWidget.setWindowTitle("图像拼接")
        if jointWidget.exec_():
            messageDic = {}
            messageList = [] #存放信息
            fileNames_order = []
            images = []
            for text in jointWidget.box.texts:
                if text.text() != '':
                    fileNames_order.append(text.text())  # 转变顺序
                    ind = self.fileNames_2A.index(text.text())
                    path = self.paths_2A[ind]
                    try:
                        MyUtils.readXML(path + 'L', fileType="2A")
                        MyUtils.width_2A = int(MyUtils.dir_message_2A["Sample"])
                        MyUtils.height_2A = int(MyUtils.dir_message_2A["Line"])
                        MyUtils.mode_2A = '<u2'
                        image = MyUtils.read_2A(path, MyUtils.width_2A, MyUtils.height_2A, MyUtils.mode_2A)
                        messageDic.update({"Samples":str(MyUtils.width_2A),
                                           "Lines":str(MyUtils.height_2A),
                                           "band":str(1)})
                        images.append(image)
                    except Exception:
                        QMessageBox.information(self, "提示：", '文件读取失败!')
                        self.messageLog.append("文件读取失败!")
                        return 0
            jointImage = None
            if len(images)==0:return 0
            if jointWidget.flag == 0:  # 左右拼接
                jointImage = np.hstack(images)
            if jointWidget.flag == 1:  # 上下拼接
                jointImage = np.vstack(images)

            self.messageLog.append("图像拼接中...")
            newImage = np.zeros((jointImage.shape[0],jointImage.shape[1],1),dtype=type(jointImage.flatten()[0]))
            newImage[:,:,0] = jointImage #将二维扩展到三维
            messageDic.update({"Source":str(fileNames_order)})

            self.saveFile(newImage,messageDic)
            self.messageLog.append("已保存图片文件")

            tabArea = QMdiArea()  # 添加页面窗口
            sub = QMdiSubWindow()
            sub.setWindowIcon(QIcon(os.path.join(LAST_DIR,"icon.png")))
            sub.setWindowFlags(Qt.Tool)
            sub.resize(newImage.shape[1]+50, newImage.shape[0]+50)
            sub.setMaximumSize(1200, 800)
            add_imageWidget = Add_ImageWidget(newImage,self)
            add_imageWidget.part_detalMessage = messageList
            add_imageWidget.all_detalMessage = messageDic
            add_imageWidget.setObjectName("add_imageWidget")
            add_imageWidget.setWindowTitle("拼接图像")
            self.messageLog.append("打开拼接图像...")
            sub.setWidget(add_imageWidget)
            tabArea.addSubWindow(sub)
            MainWindow.tabCount += 1
            self.tabWiget.addTab(tabArea, "页面" + str(MainWindow.tabCount))
            self.tabWiget.setCurrentWidget(tabArea)  # 设置为当前页面

    def  closeTab(self,index):
        # 关闭页面
        MainWindow.tabCount -= 1
        self.tabWiget.removeTab(index)

    def closeEvent(self, event):
        if self.closeApp():
            event.accept()
        else:
            event.ignore()

    def closeApp(self):
        reply =  QMessageBox.information(self, '提示', '确定退出？', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            qApp.quit()
            MyUtils.del_file(MyUtils.saveJoint_addr_tem) #清空临时文件夹
            return True
        return False


# if __name__ == '__main__':
#     import sys
#     app = QApplication(sys.argv)
#     win = MainWindow()
#     win.show()
#     sys.exit(app.exec_())
