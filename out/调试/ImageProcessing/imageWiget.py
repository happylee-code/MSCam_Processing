#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
@author: Gao
@project: Qt_project
@file: imageWiget.py
@function:图片移动放大
@time: 2021/10/12 16:23
"""

import os
from PyQt5.QtGui import QPainter, QImage, QCursor, QRegExpValidator, QIcon, QPen, QColor
from PyQt5.QtWidgets import QWidget, QMenu, QMessageBox, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, \
    QLabel, QMdiArea, QMdiSubWindow
from PyQt5.QtCore import Qt, QPoint, QRegExp

from ImageProcessing.expandEdit import ExpandEdit
from ImageProcessing.shearEdit import ShearEdit
from ImageProcessing.mergeEdit import MergeDialog
from ImageProcessing.myCustomEvent import CustomEvent
from ImageProcessing.chartWiget import MyCanvas
from ImageProcessing.matplotlibBar import ToolBar
from ImageProcessing.parameterWidget import ParaWidget,ParaWidget2
import numpy as np
from utils.myUtils import MyUtils
import cv2
from ImageProcessing import LAST_DIR

# 图片展示窗口
class ImageWidget(QWidget):

    def __init__(self,image,parent=None):
        super(ImageWidget,self).__init__(parent)
        self.parent = parent
        self.MAX = 1024 # 只能显示的最大图像
        self.endPoint = QPoint(0,0) # 存储最后所在位置
        self.endScaled = 1 # 存储最后放大倍率
        self.markPoints =[] #保存标记点的绝对位置坐标
        self.relatedMarkPoints = [] #保存标记点的图像位置坐标
        self.color = ["#800000", "#FF0000", "#C71585", "#4B0082", "#800080", "#6A5ACD", "#8B4513", "#D2691E", "#FF4500",
                      "#FF8C00", "#B8860B",
                      "#FFFF00", "#808000", "#00FF00", "#00FA9A", "#006400"] #颜色表
        self.detailMessage={}
        self.isSelectPoint = True
        self.ctrl = False
        self.parent = parent
        self.setFocusPolicy(Qt.ClickFocus) # 可以通过鼠标单击的方式获取焦点
        self.setMouseTracking(True)  # 设置鼠标移动跟踪是否有效
        self.setObjectName("imageWidget")
        # self.setAttribute(Qt.WA_TranslucentBackground)
        # self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        # self.pix.setGeometry(0, 0, self.width(), self.height())

        self.np_image = image # 用来保存传入的numpy uint16类型的图像
        if len(self.np_image.shape) == 2: # 2D-array
            self.currentImage = self.np_image # 当前屏幕显示的单通道uint16图像
            currentImage = MyUtils.normalize(self.currentImage)
            # self.image 是归一化QImage uint8类型的图像
            self.image = QImage(currentImage.data,currentImage.shape[1], currentImage.shape[0],currentImage.shape[1], QImage.Format_Grayscale8)
        else:
            self.currentImage = self.np_image[:,:,0].copy() #如果是三维则默认展示第一通道
            currentImage = MyUtils.normalize(self.currentImage)
            self.image = QImage(currentImage,currentImage.shape[1], currentImage.shape[0],currentImage.shape[1], QImage.Format_Grayscale8)

        if self.image.width()>self.MAX or self.image.height()>self.MAX:
            bigger = max(self.image.width(),self.image.height())
            scaled = self.MAX/bigger
            self.scaled_img = self.image.scaled(self.image.width()*scaled,self.image.height()*scaled)
            # self.parent.messageLog.append("超过显示的范围，缩小为原来的"+str(scaled))
        else:
            self.scaled_img = self.image # 是QImage类型的伸缩变换的图像

        self.point = QPoint((self.width()-self.scaled_img.width())/2,(self.height()-self.scaled_img.height())/2)
        self.leftClick = False
        self.startPos = QPoint(0,0)
        self.endPos = QPoint(0,0)


        # self.setContextMenuPolicy(Qt.CustomContextMenu)
        # # self.setFocusPolicy(self,Qt.FocusPolicy)
        # # 创建QMenu信号事件
        # self.customContextMenuRequested.connect(self.showMenu)


    def contextMenuEvent(self, event):
        contextMenu = QMenu(self)
        Mess = contextMenu.addAction('详细信息')
        Save = contextMenu.addAction('保存')
        Expand = contextMenu.addAction('填充')
        Shear = contextMenu.addAction('裁剪')

        # 事件绑定
        Mess.triggered.connect(self.Event)
        Save.triggered.connect(self.Event)
        Expand.triggered.connect(self.Event)
        Shear.triggered.connect(self.Event)
        if not self.ctrl:
            contextMenu.exec_(self.mapToGlobal(event.pos()))  # 在鼠标位置显示

    def Event(self):
        # sender()记录了发送信号的对象
        titleName = self.windowTitle()
        text = self.sender().text()
        if self.parent is None:return 0
        if text == '详细信息':
            self.parent.message.setText("图像相关信息:")
            self.parent.messageLog.append("打开" + titleName + "的详细信息...")
            try:
                for k, v in self.detailMessage.items():
                    self.parent.message.append(k + ":" + v)
            except Exception as e:
                self.parent.message.append("无详细信息")
        if text == '保存':
            self.parent.saveFile(self.currentImage,self.detailMessage)
        if text== '填充':
            self.parent.messageLog.append("填充" + titleName + "...")
            expandEdit = ExpandEdit()
            image = self.currentImage
            if expandEdit.exec_():
                width = int(expandEdit.lineEdit.text())
                height = int(expandEdit.lineEdit_2.text())
                pos_x = int(expandEdit.lineEdit_3.text())
                pos_y = int(expandEdit.lineEdit_4.text())
                new_image = np.zeros((height, width), dtype='uint16')
                try:
                    new_image[pos_y:pos_y + image.shape[0], pos_x:pos_x + image.shape[1]] = image
                    self.setImage(new_image)
                    self.parentWidget().resize(width + 30, height + 60)  # 改变QMdiSubWindow的大小
                except Exception as e:
                    self.parent.messageLog.append("填充失败！")
        if text== '裁剪':
            self.parent.messageLog.append("裁剪" + titleName + "...")
            shearEdit = ShearEdit()
            image = self.currentImage
            if shearEdit.exec_():
                width_1 = int(shearEdit.lineEdit_1.text())
                width_2 = int(shearEdit.lineEdit_2.text())
                height_1 = int(shearEdit.lineEdit_3.text())
                height_2 = int(shearEdit.lineEdit_4.text())
                if len(image.shape)>2: # 二维彩色
                    try:
                        new_image = image[height_1:height_2, width_1:width_2,:].copy()
                        self.setImage(new_image,color=True)
                    except Exception as e:
                        self.parent.messageLog.append("裁剪失败！")
                else:
                    try:
                        new_image = image[height_1:height_2, width_1:width_2].copy()
                        self.setImage(new_image)
                    except Exception as e:
                        self.parent.messageLog.append("裁剪失败！")

    def paintEvent(self, event):
        painter = QPainter(self)
        # painter.begin(self)
        self.drawImage(painter)
        if not self.isSelectPoint:
            self.drawPoint(painter)
        # painter.end()

    def drawImage(self, painter):
        painter.drawImage(self.point,self.scaled_img)
        self.endPoint = self.point
        self.endScaled = self.scaled_img.width()/self.image.width()

    def drawPoint(self,painter):
        pen = QPen(Qt.red, 4, Qt.SolidLine)
        # size = self.size()
        # for i in range(1000):
        #     x = 100*(-1+2.0*i/1000)+size.width()/2.0
        #     y = -50*math.sin((x-size.width()/2.0)*math.pi/50)+size.height()/2.0
        #     painter.drawPoint(x,y)
        for i,pos in enumerate(self.markPoints):
            pen.setColor(QColor(self.color[i%len(self.color)]))
            painter.setPen(pen)
            painter.drawPoint(pos.x(), pos.y())

    def setImage(self,image,start_point,scaled,color=False):
        self.currentImage = image
        currentImage = MyUtils.normalize(self.currentImage)
        if color:
            # image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            self.image = QImage(currentImage,currentImage.shape[1], currentImage.shape[0],currentImage.shape[1]*3, QImage.Format_RGB888)
        else:
            # 第四个参数表示图像每行有多少个字节，不设定时，图像有时会歪，所以一定要设定
            self.image = QImage(currentImage, currentImage.shape[1], currentImage.shape[0],currentImage.shape[1], QImage.Format_Grayscale8)

        # if self.image.width() > self.MAX or self.image.height() > self.MAX:
        #     bigger = max(self.image.width(), self.image.height())
        #     scaled = self.MAX / bigger
        #     self.scaled_img = self.image.scaled(self.image.width() * scaled, self.image.height() * scaled)
        #     # self.parent.messageLog.append("超过显示的范围，缩小为原来的"+str(scaled))
        # else:
        #     self.scaled_img = self.image  # 是QImage类型的伸缩变换的图像
        # self.point = QPoint((self.width()-self.scaled_img.width())/2,(self.height()-self.scaled_img.height())/2)
        if start_point is not None:
            self.point = start_point
        else: # 如果还没有历史记录，使用最原始获取的方法
            self.point = QPoint((self.width() - self.scaled_img.width()) / 2,
                                (self.height() - self.scaled_img.height()) / 2)
        if scaled is not None:
            self.scaled_img = self.image.scaled(self.image.width() * scaled, self.image.height() * scaled)
        else: # 如果还没有历史记录，使用最原始获取的方法
            if self.image.width() > self.MAX or self.image.height() > self.MAX:
                bigger = max(self.image.width(), self.image.height())
                scaled = self.MAX / bigger
                self.scaled_img = self.image.scaled(self.image.width() * scaled, self.image.height() * scaled)
                # self.parent.messageLog.append("超过显示的范围，缩小为原来的"+str(scaled))
            else:
                self.scaled_img = self.image  # 是QImage类型的伸缩变换的图像
        self.markPoints = [] #切换图片时，标记点清空
        self.repaint()

    def mousePressEvent(self, event):
        if self.isSelectPoint:
            # 按下左键
            if event.button() == Qt.LeftButton and self.isSelectPicture(event):
                self.leftClick = True
                self.startPos = event.pos()
        else:
            # 按下左键
            if event.button() == Qt.LeftButton and self.isSelectPicture(event):
                self.markPoints.append(event.pos())

                self.repaint()

    def customEvent(self, event):
        if event.type() == CustomEvent.selectedEvent:
            self.isSelectPoint = event.getData()
            #取消选择时清除点
            self.markPoints = []
            self.relatedMarkPoints = []
            self.repaint()

    def mouseMoveEvent(self, event):
        if self.isSelectPoint:
            if self.isSelectPicture(event):
                self.setCursor(Qt.SizeAllCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
        # 移动按住移动鼠标
            if self.leftClick:
                self.endPos = event.pos() - self.startPos
                self.point = self.point + self.endPos
                self.startPos = event.pos()
                self.repaint()
        else:
            self.setCursor(Qt.CrossCursor)

    def mouseReleaseEvent(self, event):
        if self.isSelectPoint:
            # 释放鼠标
            if event.button() == Qt.LeftButton:
                self.leftClick = False
            elif event.button() == Qt.RightButton and self.ctrl: # crl+右键复位
                self.recover_state()

    def recover_state(self):
        if self.image.width() > self.MAX or self.image.height() > self.MAX:
            bigger = max(self.image.width(), self.image.height())
            scaled = self.MAX / bigger
            self.scaled_img = self.image.scaled(self.image.width() * scaled, self.image.height() * scaled)
        #     # self.parent.messageLog.append("超过显示的范围，缩小为原来的"+str(scaled))
        else:
            self.scaled_img = self.image
        self.point = QPoint((self.width() - self.scaled_img.width()) / 2,
                            (self.height() - self.scaled_img.height()) / 2)
        self.repaint()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Control:
            self.ctrl = True
        if event.modifiers()==Qt.ControlModifier and event.key()== Qt.Key_Z:
            if len(self.markPoints)>0:
                self.markPoints.pop(-1)
            self.repaint()

        return QWidget.keyReleaseEvent(self,event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.ctrl = False
        return QWidget.keyReleaseEvent(self,event)

    def wheelEvent(self, event):
        if self.isSelectPoint:
            speed = 0.2
            if event.angleDelta().y() > 0 and self.isSelectPicture(event):
                # 放大图片
                dis_x = self.scaled_img.width() * speed
                dis_y = self.scaled_img.height() * speed
                self.scaled_img = self.image.scaled(self.scaled_img.width()*(1+speed), self.scaled_img.height()*(1+speed))

                # 保证放大图片时，从鼠标处向周围放大
                pos_x = (event.x()-self.point.x())/(self.scaled_img.width()-dis_x) # pos_x为鼠标在放大前图像位置的比例
                pos_y = (event.y()-self.point.y())/(self.scaled_img.height()-dis_y)
                new_x = dis_x * pos_x # new_x为需要向左移动的距离
                new_y = dis_y * pos_y
                self.point = QPoint(self.point.x()-new_x, self.point.y()-new_y)
                self.repaint()
            elif event.angleDelta().y() < 0 and self.isSelectPicture(event):
                # 缩小图片
                dis_x = self.scaled_img.width() * speed
                dis_y = self.scaled_img.height() * speed
                self.scaled_img = self.image.scaled(self.scaled_img.width()*(1-speed), self.scaled_img.height()*(1-speed))

                # 保证缩小图片时，从周围鼠标处缩小
                pos_x = (event.x() - self.point.x()) / (self.scaled_img.width() + dis_x)
                pos_y = (event.y() - self.point.y()) / (self.scaled_img.height() + dis_y)
                new_x = dis_x * pos_x
                new_y = dis_y * pos_y
                self.point = QPoint(self.point.x() + new_x, self.point.y() + new_y)
                self.repaint()

    def resizeEvent(self, event):

        if self.image.width() > self.MAX or self.image.height() > self.MAX:
            bigger = max(self.image.width(), self.image.height())
            scaled = self.MAX / bigger
            self.scaled_img = self.image.scaled(self.image.width() * scaled, self.image.height() * scaled)
            # self.parent.messageLog.append("超过显示的范围，缩小为原来的"+str(scaled))
        else:
            self.scaled_img = self.image  # 是QImage类型的伸缩变换的图像

        self.point = QPoint((self.width() - self.scaled_img.width()) / 2, (self.height() - self.scaled_img.height()) / 2)
        ralateMoves = []
        for markPoint in self.markPoints:
            ralateMoves.append(markPoint-self.point)
        self.markPoints = []
        for ralateMove in ralateMoves:
            self.markPoints.append(ralateMove+self.point)
        self.update()

    def isSelectPicture(self,event):
        # 鼠标是否放在图片的范围内
        if self.point.x()<event.x()<self.point.x()+self.scaled_img.width():
            if self.point.y()<event.y()<self.point.y()+self.scaled_img.height():
                return True
        return False

# 一个带有跳转切换功能的图像窗口，是ImageWidget的扩展
class Add_ImageWidget(QWidget):

    def __init__(self,image,parent=None):
        super(Add_ImageWidget,self).__init__(parent)
        # self.resize(image.shape[1]+30,image.shape[0]+30)
        # self.resize(1024,1024)
        self.parent = parent
        self.count = 0 # 初始展示的图片数
        self.band = 0 # band数
        self.points=[]
        self.scaleds=[]
        self.image3D = image
        self.all_detalMessage={} #多通道图片整体信息
        self.part_detalMessage=[] #图片单通道信息，每一项都是一个字典
        self.select = False
        if len(image.shape)>2:
            self.band = image.shape[2]
        else:
            self.band = 1

        for i in range(self.band):
            self.points.append(None)
            self.scaleds.append(None)

        VBox = QVBoxLayout()
        self.imWidget = ImageWidget(image,self.parent)
        self.setContextMenuPolicy(1)
        self.imWidget.setContextMenuPolicy(2)
        # self.setFocus()
        # self.imWidget.customContextMenuRequested.disconnect(self.imWidget.showMenu) #断开信号连接
        # self.imWidget.customContextMenuRequested.connect(self.showMenu) #连接新的信号

        self.resize(600,600)

        VBox.addWidget(self.imWidget)


        HBox = QHBoxLayout()
        self.button_left = QPushButton("前一幅",self)
        self.lineEdit = QLineEdit('1',self)
        self.lineEdit.setValidator(QRegExpValidator(QRegExp("^[0-9]*[1-9][0-9]*$"), self)) #限制lineEdit输入
        self.label = QLabel("/"+str(self.band),self)
        self.button_skip = QPushButton("跳转", self)
        self.button_right = QPushButton("后一幅",self)
        self.lineEdit.setFixedWidth(40)
        self.label.setFixedWidth(40)
        self.button_left.setFixedWidth(60)
        self.button_skip.setFixedWidth(40)
        self.button_right.setFixedWidth(60)

        self.button_right.clicked.connect(self.next)
        self.button_left.clicked.connect(self.last)
        self.button_skip.clicked.connect(self.skip)

        HBox.addStretch(1)
        HBox.addWidget(self.button_left)
        HBox.addWidget(self.lineEdit)
        HBox.addWidget(self.label)
        HBox.addWidget(self.button_skip)
        HBox.addWidget(self.button_right)
        HBox.addStretch(1)
        # self.button_left.setFocusPolicy(Qt.NoFocus)
        # self.lineEdit.setFocusPolicy(Qt.NoFocus)
        # self.label.setFocusPolicy(Qt.NoFocus)
        # self.button_right.setFocusPolicy(Qt.NoFocus)

        VBox.addLayout(HBox)
        self.setLayout(VBox)


    def showMenu(self):
        self.contextMenu.exec_(QCursor.pos())  # 在鼠标位置显示

    def contextMenuEvent(self, event):
        # 创建QMenu信号事件
        contextMenu = QMenu(self)
        recover = contextMenu.addAction('复位')
        Mess = contextMenu.addAction('详细信息')
        Save = contextMenu.addAction('保存当前通道')
        Save_all = contextMenu.addAction('保存数据立方体')
        Expand = contextMenu.addAction('填充')
        Shear = contextMenu.addAction('裁剪')
        Color = contextMenu.addAction('合成彩色图像')
        Chart = contextMenu.addAction('画光谱曲线')
        correct = contextMenu.addAction('畸变矫正')
        register = contextMenu.addAction('通道配准')

        # 事件绑定
        recover.triggered.connect(self.Event)
        Mess.triggered.connect(self.Event)
        Save.triggered.connect(self.Event)
        Save_all.triggered.connect(self.Event)
        Expand.triggered.connect(self.Event)
        Shear.triggered.connect(self.Event)
        Color.triggered.connect(self.Event)
        Chart.triggered.connect(self.Event)
        correct.triggered.connect(self.Event)
        register.triggered.connect(self.Event)
        if not self.imWidget.ctrl:
            contextMenu.exec_(self.mapToGlobal(event.pos()))  # 在鼠标位置显示

    def Event(self):
        # sender()记录了发送信号的对象
        titleName = self.windowTitle()
        text = self.sender().text()
        if self.parent is None:return 0
        if text == '复位':
            for i in range(self.band):
                self.points[i]=None
                self.scaleds[i]=None
            self.imWidget.recover_state()

        if text == '详细信息':
            self.parent.message.setText("图像相关信息:")
            self.parent.messageLog.append("打开" + titleName + "的详细信息...")
            try:
                for k, v in self.all_detalMessage.items():
                    self.parent.message.append(k + ":" + v)
                if len(self.part_detalMessage)==0:return
                for key, value in self.part_detalMessage[self.count].items():
                    self.parent.message.append(str(key) + ":" + str(value))
            except:
                self.parent.message.append("无信息")
        if text == '保存当前通道':
            dict1 = self.part_detalMessage[self.count].copy()
            dict2 = self.all_detalMessage.copy()
            dict2.update(dict1)
            self.parent.saveFile(self.imWidget.currentImage,dict2)
        if text == '保存数据立方体':
            dict1 = self.part_detalMessage.copy()
            dict2 = self.all_detalMessage.copy()
            wavelengths = []
            for d in dict1:
                if d.keys().__contains__("central_wavelength"):
                    wavelengths.append(d["central_wavelength"])
            if len(wavelengths)>0:
                dict2.update({"central_wavelength":','.join(wavelengths)})
            if len(dict1)>0 and dict1[0].keys().__contains__("Window_Location"):
                dict2.update({"Window_Location":dict1[0]["Window_Location"]})
            self.parent.saveFile(self.image3D, dict2)
        if text == '填充':
            self.parent.messageLog.append("填充" + titleName + "...")
            expandEdit = ExpandEdit()
            image = self.imWidget.np_image[:,:,self.count]
            if expandEdit.exec_():
                width = int(expandEdit.lineEdit.text())
                height = int(expandEdit.lineEdit_2.text())
                pos_x = int(expandEdit.lineEdit_3.text())
                pos_y = int(expandEdit.lineEdit_4.text())
                new_image = np.zeros((height, width), dtype='uint16')
                try:
                    new_image[pos_y:pos_y + image.shape[0], pos_x:pos_x + image.shape[1]] = image
                    self.setImage(new_image)
                    self.parentWidget().resize(width + 30, height + 60) #改变QMdiSubWindow的大小
                except Exception as e:
                    self.parent.messageLog.append("填充失败！")
        if text == '裁剪':
            self.parent.messageLog.append("裁剪" + titleName + "...")
            shearEdit = ShearEdit()
            image = self.imWidget.currentImage
            if shearEdit.exec_():
                width_1 = int(shearEdit.lineEdit_1.text())
                width_2 = int(shearEdit.lineEdit_2.text())
                height_1 = int(shearEdit.lineEdit_3.text())
                height_2 = int(shearEdit.lineEdit_4.text())
                new_image = np.zeros((height_2-height_1,width_2-width_1),dtype='uint16')
                try:
                    new_image[:,:] = image[height_1:height_2,width_1:width_2]
                    self.setImage(new_image)
                except Exception as e:
                    self.parent.messageLog.append("裁剪失败！")
        if text == '合成彩色图像':
            labelNames = ["R:","G:","B:"]
            if len(self.imWidget.np_image.shape)>2:
                fileNames = ["band{0}".format(i+1) for i in range(self.imWidget.np_image.shape[2])]
            else:
                fileNames = ["band1"]
            mergeWidget = MergeDialog(fileNames, labelNames)
            mergeWidget.setWindowTitle("合成RGB彩色图像")
            if mergeWidget.exec_():
                fileNames_order = []
                for text in mergeWidget.box.texts:
                    if text.text() != '':
                        fileNames_order.append(text.text())  # 转变顺序
                if len(fileNames_order)!=3:return
                images = np.zeros((self.imWidget.np_image.shape[0], self.imWidget.np_image.shape[1], len(fileNames_order)), "uint16")
                for i,fileName_order in enumerate(fileNames_order):
                    images[:,:,i]=self.imWidget.np_image[:,:,int(fileName_order[4:])-1].copy()
                tabArea = QMdiArea()  # 添加页面窗口
                sub = QMdiSubWindow()
                sub.setWindowIcon(QIcon(os.path.join(LAST_DIR,"icon.png")))
                sub.setWindowFlags(Qt.Tool)
                sub.resize(images.shape[1] + 40, images.shape[0] + 60)
                imageWidget = ImageWidget(images, self.parent)
                imageWidget.detailMessage.update({"R":fileNames_order[0],"G":fileNames_order[1],"B":fileNames_order[2]})
                imageWidget.setImage(images.copy(),True)
                # imageWidget.setObjectName("other_add_imageWidget")
                imageWidget.setWindowTitle("合成彩色图像")
                sub.setWidget(imageWidget)
                tabArea.addSubWindow(sub)
                self.parent.__class__.tabCount += 1
                self.parent.tabWiget.addTab(tabArea, "页面" + str(self.parent.tabCount))
                self.parent.tabWiget.setCurrentWidget(tabArea)  # 设置为当前页面
                self.parent.messageLog.append("合成RGB彩色图像...")
        if text == '画光谱曲线':
            self.imWidget.relatedMarkPoints = [] #先清空
            for markPoint in self.imWidget.markPoints:
                self.imWidget.relatedMarkPoints.append(markPoint - self.imWidget.point) # 将绝对位置转化为图片像素位置
            points = self.imWidget.relatedMarkPoints
            ys = []
            band = 1
            normalImage = MyUtils.normalize(self.imWidget.np_image)
            if len(points)==0:QMessageBox.information(self, "提示：", '未选择标记点！')
            else:
                for point in points:
                    real_x = (point.x()/self.imWidget.scaled_img.width())*self.imWidget.np_image.shape[1]
                    real_y = (point.y()/self.imWidget.scaled_img.height())*self.imWidget.np_image.shape[0]
                    if len(self.imWidget.np_image.shape)>2:
                        band = self.imWidget.np_image.shape[2]
                    y = []
                    for i in range(band):
                        y.append(normalImage[int(real_y),int(real_x),i])
                    ys.append(y)

                if band==3:
                    x = [u'R', u'G', u'B']
                else:
                    x = ["band{0}".format(i+1) for i in range(band)]
                mpl = MyCanvas(self.parent, width=2, height=2, dpi=100)
                mpl_tool = ToolBar(mpl, self.parent)  # 添加完整工具栏
                mpl.draw_figure(x, ys,self.imWidget.color)
                # 初始化显示甘特图
                for i in range(self.parent.chartLayout.count()):
                    self.parent.chartLayout.itemAt(i).widget().deleteLater()
                self.parent.chartWidget.setHidden(False)
                self.parent.chartLayout.addWidget(mpl)
                self.parent.chartLayout.addWidget(mpl_tool)
        if text == "畸变矫正":
            if self.image3D.shape[2] != 8:
                QMessageBox.information(self.parent, "提示：", '操作失败,只针对8通道多光谱图像!')
            paraWidget = ParaWidget2()
            if MyUtils.cameraParam_addr is None:
                if paraWidget.exec_():
                    MyUtils.cameraParam_addr = paraWidget.lineEdit.text()
            else:
                paraWidget.loadmat(MyUtils.cameraParam_addr)

            if MyUtils.cameraParam_addr is not None: # 此处必须要写一个判断，否则第一次打开文件窗口后不会执行
                try:
                    params = paraWidget.mat_Info['Params']
                    # 补全窗口图像
                    new_image3D = np.zeros((2048, 2048, 8), dtype="uint16")
                    string = self.part_detalMessage[0]["Window_Location"]
                    string = string.replace(",", ":")
                    ranges = string.split(":")
                    for i in range(8):
                        param = params[0,i]
                        RadialDistortion = param[1]
                        TangentialDistortion = param[2]
                        IntrinsicMatrix = np.array(param[3]).T
                        # 畸变系数k1 k2 pq p2 k3
                        dist = np.array([RadialDistortion[0][0], RadialDistortion[0][1], TangentialDistortion[0][0],
                                         TangentialDistortion[0][1], 0])
                        n_image = np.zeros((2048, 2048), dtype="uint16")
                        n_image[int(ranges[0]):int(ranges[1]), int(ranges[2]):int(ranges[3])] = self.image3D[:, :, i].copy()
                        new_image3D[:,:,i] = cv2.undistort(n_image, IntrinsicMatrix, dist)
                    new_image3D = new_image3D[int(ranges[0]):int(ranges[1]), int(ranges[2]):int(ranges[3])].copy()
                    tabArea = QMdiArea()  # 添加页面窗口
                    sub = QMdiSubWindow()
                    sub.setWindowIcon(QIcon(os.path.join(LAST_DIR,"icon.png")))
                    sub.setWindowFlags(Qt.Tool)
                    sub.resize(new_image3D.shape[1] + 50, new_image3D.shape[0] + 80)
                    sub.setMaximumSize(1200, 800)
                    add_imageWidget = Add_ImageWidget(new_image3D, self.parent)
                    all_detalMessage = self.all_detalMessage.copy()
                    all_detalMessage.update({"correct": "True"})
                    add_imageWidget.all_detalMessage = all_detalMessage
                    add_imageWidget.part_detalMessage = self.part_detalMessage.copy()
                    add_imageWidget.setObjectName("add_imageWidget")
                    add_imageWidget.setWindowTitle("畸变矫正")
                    self.parent.messageLog.append("畸变矫正")
                    sub.setWidget(add_imageWidget)
                    tabArea.addSubWindow(sub)

                    self.parent.__class__.tabCount += 1
                    self.parent.tabWiget.addTab(tabArea, "页面" + str(self.parent.tabCount))
                    self.parent.tabWiget.setCurrentWidget(tabArea)  # 设置为当前页面
                except Exception as e:
                    QMessageBox.information(self.parent, "提示：", '参数错误！')
                    MyUtils.cameraParam_addr = None

        if text == "通道配准":
            paraWidget = ParaWidget()
            if MyUtils.translateTform_addr is None:
                if paraWidget.exec_():
                    MyUtils.translateTform_addr = paraWidget.lineEdit.text()
            else:
                paraWidget.loadmat(MyUtils.translateTform_addr)

            if MyUtils.translateTform_addr is not None:
                try:
                    addr_list = ["addr1", "addr2", "addr3", "addr4", "addr5", "addr6"]
                    Torms_list = []
                    for addr in addr_list:
                        Torms_list.append(paraWidget.mat_Info[addr])
                    new_image3D = np.zeros((2048, 2048,8), dtype="uint16")
                    string = self.part_detalMessage[0]["Window_Location"]
                    if not self.part_detalMessage[0].keys().__contains__("Defocusing_Compensation_Gear"):
                        addr = 6
                    else:
                        addr = int(self.part_detalMessage[0]["Defocusing_Compensation_Gear"][-1])
                    string = string.replace(",", ":")
                    ranges = string.split(":")
                    for i in range(self.image3D.shape[2]):
                        M = Torms_list[addr-1][:, 0:2, i]
                        M = M.T
                        n_image = np.zeros((2048,2048),dtype="uint16")
                        n_image[int(ranges[0]):int(ranges[1]),int(ranges[2]):int(ranges[3])] = self.image3D[:,:,i].copy()
                        res = cv2.warpAffine(n_image,M,(2048,2048),cv2.INTER_CUBIC)
                        new_image3D[:,:,i] = res
                    new_image3D = new_image3D[int(ranges[0]):int(ranges[1]),int(ranges[2]):int(ranges[3])].copy()
                    tabArea = QMdiArea()  # 添加页面窗口
                    sub = QMdiSubWindow()
                    sub.setWindowIcon(QIcon(os.path.join(LAST_DIR,"icon.png")))
                    sub.setWindowFlags(Qt.Tool)
                    sub.resize(new_image3D.shape[1] + 50, new_image3D.shape[0] + 80)
                    sub.setMaximumSize(1200, 800)
                    add_imageWidget = Add_ImageWidget(new_image3D, self.parent)
                    all_detalMessage = self.all_detalMessage.copy()
                    all_detalMessage.update({"register":"True"})
                    add_imageWidget.all_detalMessage = all_detalMessage
                    add_imageWidget.part_detalMessage = self.part_detalMessage.copy()
                    add_imageWidget.setObjectName("add_imageWidget")
                    add_imageWidget.setWindowTitle("图像配准")
                    self.parent.messageLog.append("图像配准")
                    sub.setWidget(add_imageWidget)
                    tabArea.addSubWindow(sub)

                    self.parent.__class__.tabCount += 1
                    self.parent.tabWiget.addTab(tabArea, "页面" + str(self.parent.tabCount))
                    self.parent.tabWiget.setCurrentWidget(tabArea) # 设置为当前页面
                except Exception as e:
                    QMessageBox.information(self.parent, "提示：", '参数错误！')
                    self.parent.messageLog.append("错误提示："+str(e))
                    MyUtils.translateTform_addr = None

    def next(self):
        if self.count<self.band-1:
            self.scaleds[self.count]=self.imWidget.endScaled
            self.points[self.count]=self.imWidget.endPoint
            self.count += 1
            self.lineEdit.setText(str(self.count+1))
            image = self.imWidget.np_image[:,:,self.count].copy()
            self.setImage(image,self.points[self.count],self.scaleds[self.count])

    def last(self):
        if self.count>0:
            self.scaleds[self.count] = self.imWidget.endScaled
            self.points[self.count] = self.imWidget.endPoint
            self.count -= 1
            self.lineEdit.setText(str(self.count+1))
            image = self.imWidget.np_image[:, :, self.count].copy()
            self.setImage(image,self.points[self.count],self.scaleds[self.count])

    def skip(self):
        count = int(self.lineEdit.text())-1
        if -1<count<self.band:
            self.scaleds[self.count] = self.imWidget.endScaled
            self.points[self.count] = self.imWidget.endPoint
            self.count = count
            image = self.imWidget.np_image[:, :, self.count].copy()
            self.setImage(image,self.points[self.count],self.scaleds[self.count])

    def setImage(self,image,point,scaled):
        self.imWidget.setImage(image,point,scaled)

# if __name__ == '__main__':
#     import cv2
#     app = QApplication(sys.argv)
#     img = cv2.imread("D:\Qt_project\mytest\icon.jpg") #BGR
#     # imag2=np.zeros((img.shape[0],img.shape[1],img.shape[2]),dtype="uint8")
#     # imag2[:,:,0]=img[:,:,2]
#     # imag2[:, :, 1] = img[:, :, 1]
#     # imag2[:, :, 2] = img[:, :, 0]
#     # imag2 = cv2.COLOR_RGB2BGR(img.copy())
#     # imag2 = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
#     ui = Add_ImageWidget(img)
#     # ui.setImage(img)
#     # ui.imWidget.setImage(img,color=True)
#     ui.show()
#     sys.exit(app.exec_())




