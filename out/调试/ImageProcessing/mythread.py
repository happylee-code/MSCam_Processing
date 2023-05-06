#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
@author: Gao
@project: Qt_project
@file: mythread.py
@function:线程管理
@time: 2021/11/27 18:45
"""
from PyQt5.QtCore import QThread, pyqtSignal, QMutex
from utils.myUtils import MyUtils
import numpy as np


class Joint_01_Thread(QThread):
    finish = pyqtSignal(np.ndarray,int,str,dict,list) #int是进度条完成度，str是窗口标题,dict1,dict2是图像信息
    mutex = QMutex()
    # def __del__(self):
    #     self.wait()

    def __init__(self,path):
        super(Joint_01_Thread, self).__init__()
        self.path = path
        self.stop_flag = False
        self.exitcode = 0  # 如果线程异常退出，将该标志位设置为1，正常退出为0
        self.exception = None

    def run(self):
        Joint_01_Thread.mutex.lock()
        try:
            #处理数据
            MyUtils.list_message_01 = []  # 将字典列表清空
            # 打开01文件
            MyUtils.readXML(self.path + 'L', fileType="01")
            MyUtils.width_01 = int(MyUtils.dir_message_01["Sample"])
            MyUtils.height_01 = int(MyUtils.dir_message_01["Line"])
            MyUtils.band_01 = int(MyUtils.dir_message_01["Time"])
            MyUtils.mode_01 = '>u2'
            images = MyUtils.read_01(self.path, MyUtils.width_01, MyUtils.height_01, MyUtils.band_01,
                                     MyUtils.mode_01)
            records = int(MyUtils.dir_message_01["records"])
            className_list = []
            dic = {}  # 存放场景分类

            for record in range(records):
                SciName = MyUtils.list_message_01[record]["Defocusing_Compensation_Gear"]
                if not className_list.__contains__(SciName):
                    className_list.append(SciName)
            for className in className_list:
                dic.update({className: []})

            for j in range(records):
                SciName = MyUtils.list_message_01[j]["Defocusing_Compensation_Gear"]
                dic[SciName].append(j)  # 将同一SciName的文件索引放入同key字典的velue中

            for i,(key, values) in enumerate(dic.items()):  # key是场景，values是该场景的图像
                dic2 = {}  # 位置：图片
                addrs = []  # 位置列表
                for value in values:
                    addr = MyUtils.list_message_01[value]["Window_Location"]
                    if not addrs.__contains__(addr):
                        addrs.append(addr)
                for addr in addrs:
                    dic2.update({addr: []})
                for value in values:
                    # chanel = int(MyUtils.list_message_01[value]["Band_Number"][-1])
                    addr = MyUtils.list_message_01[value]["Window_Location"]
                    dic2[addr].append(value)

                new_image = np.zeros((2048, 2048, len(dic2[addrs[0]])), dtype='uint16')
                helpList_x = []
                helpList_y = []
                for k, vs in dic2.items():  # k是窗口位置，vs是该位置的1-8通道图片集合
                    x = (int(k) - 1) // 8
                    y = (int(k) - 1) % 8
                    helpList_x.append(x * MyUtils.height_01)
                    helpList_x.append((x + 1) * MyUtils.height_01)
                    helpList_y.append(y * MyUtils.height_01)
                    helpList_y.append((y + 1) * MyUtils.height_01)
                    for j, v in enumerate(vs):
                        new_image[x * MyUtils.height_01:(x + 1) * MyUtils.height_01,
                        y * MyUtils.width_01:(y + 1) * MyUtils.width_01, j] = images[:, :, v]
                #图片主体范围
                x_min = min(helpList_x)
                x_max = max(helpList_x)
                y_min = min(helpList_y)
                y_max = max(helpList_y)
                new_image=new_image[x_min:x_max,y_min:y_max,:]
                process = i/(len(dic)-1)

                tems_s = [elem for elem in dic2.values()]
                tems = tems_s[0]  # 第一个窗口位置的8个通道图像列表
                dir_message = MyUtils.dir_message_01.copy()
                dir_message["file_size"] = str((y_max-y_min)*(x_max-x_min)*len(tems)*16/8) #更改"file_size"
                dir_message["Time"]=str(len(tems))
                dir_message.pop("records")
                dir_message.update({"product_level":"01","source":self.path})

                list_message = []
                for k,tem in enumerate(tems):
                    tem_dic = MyUtils.list_message_01[tem].copy()
                    tem_dic["Window_Location"] = "{0}:{1},{2}:{3}".format(x_min,x_max,y_min,y_max)
                    tem_dic["sequence"] = str([elem[k] for elem in dic2.values()])
                    tem_dic.update({"central_wavelength":MyUtils.CentralWavelength[k]})
                    list_message.append(tem_dic)

                self.finish.emit(new_image, process*100, key,dir_message,list_message)  # 发送信号,key是标题

        except Exception as e:
            self.exitcode = 1  # 如果线程异常退出，将该标志位设置为1，正常退出为0
            self.exception = e

        Joint_01_Thread.mutex.unlock()


class Joint_2AThread(QThread):
    finish = pyqtSignal(np.ndarray, int, str,dict,list) #int是进度条完成度，str是窗口标题,dict1,dict2是图像信息
    mutex = QMutex()
    # def __del__(self):
    #     self.wait()

    def __init__(self,fileNames_2A,paths_2A,dic,className_list):
        self.exitcode = 0
        self.exception = None #记录异常状态
        # fileNames_2A是文件名列表
        # paths_2A是路径列表
        # dic —— key:窗口位置+场景名 value:属于该场景某一通道的图片列表
        # className_list "窗口位置+场景名"列表

        super(Joint_2AThread, self).__init__()
        self.fileNames_2A = fileNames_2A
        self.paths_2A = paths_2A
        self.dic = dic
        self.className_list = className_list

    def run(self):
        Joint_2AThread.mutex.lock()
        try:
            ind = self.fileNames_2A.index(self.dic[self.className_list[0]][0])
            path = self.paths_2A[ind]
            MyUtils.readXML(path + 'L', fileType="2A") #读取了第一个文件的头信息
            MyUtils.width_2A = int(MyUtils.dir_message_2A["Sample"])
            MyUtils.height_2A = int(MyUtils.dir_message_2A["Line"])
            MyUtils.mode_2A = '<u2'
            dic2 = {}  # key代表窗口位置+场景名，value代表该场景窗口位置的数据立方体
            messages = {}
            sci_list = []  # 存放场景名列表
            for key, values in self.dic.items():
                if not sci_list.__contains__(key[2:]):
                    sci_list.append(key[2:])
                band = len(values)  # 获取光谱通道数
                new_image = np.zeros((MyUtils.height_2A, MyUtils.height_2A, band), dtype='uint16')
                values = sorted(values)  # 将通道按顺序排列
                tems = []
                for i, v in enumerate(values):  # 通道叠加
                    ind = self.fileNames_2A.index(v)
                    path = self.paths_2A[ind]
                    image = MyUtils.read_2A(path, MyUtils.width_2A, MyUtils.height_2A, MyUtils.mode_2A)
                    MyUtils.readXML(path + 'L', fileType="2A")
                    tem = MyUtils.dir_message_2A.copy()
                    tems.append(tem)
                    new_image[:, :, i] = image
                dic2.update({key: new_image})
                messages.update({key:tems})

            dic3 = {}  # key代表场景名，values是该场景的数据立方体列表
            dic3_dir = {}  # key代表场景名，values是该场景的数据立方体的窗口位置列表
            messages3 ={} # 用于存放信息，key代表场景名，values是该场景通道信息集合的位置列表（value是二维列表）
            for sci in sci_list:  # 初始化dic3
                dic3.update({sci: []})
                dic3_dir.update({sci: []})
                messages3.update({sci:[]})
            for sci_dir, image in dic2.items(): #将数据立方体按照场景分类
                sci = sci_dir[2:]
                dic3[sci].append(image) # 场景i对应数据立方体列表
                dic3_dir[sci].append(sci_dir[0:2]) # 场景i对应数据立方体位置
            for sci_dir,message in messages.items():
                sci = sci_dir[2:]
                messages3[sci].append(message)

            for i,(sci, images) in enumerate(dic3.items()):  # 遍历dic3中的图像对应关系
                part_message_list = []
                all_message_dic = {}
                new_image = np.ones((2048, 2048, images[0].shape[2]), dtype="uint16")
                helpList_x = []
                helpList_y = []
                for j, image in enumerate(images):
                    dir = int(dic3_dir[sci][j])
                    x = (dir - 1) // 8
                    y = (dir - 1) % 8
                    helpList_x.append(x * MyUtils.height_2A)
                    helpList_x.append((x + 1) * MyUtils.height_2A)
                    helpList_y.append(y * MyUtils.height_2A)
                    helpList_y.append((y + 1) * MyUtils.height_2A)
                    new_image[x * MyUtils.height_2A:(x + 1) * MyUtils.height_2A,
                    y * MyUtils.width_2A:(y + 1) * MyUtils.width_2A, :] = image[:, :, :]

                x_min = min(helpList_x)
                x_max = max(helpList_x)
                y_min = min(helpList_y)
                y_max = max(helpList_y)
                new_image = new_image[x_min:x_max, y_min:y_max, :]
                process = i / (len(dic3) - 1)

                source = []
                for j,chanel_mess in enumerate(messages3[sci][0]): #用第一个位置的信息更新整幅图像的信息
                    arrays = [elem[j] for elem in messages3[sci]] # arrays是8个通道位置信息列表
                    sequence = [array["product_id"] for array in arrays]
                    source += sequence
                    chanel_mess["file_size"] = str((y_max-y_min)*(x_max-x_min)*8*16/8)
                    chanel_mess["Sample"] = str(y_max - y_min)
                    chanel_mess["Line"] = str(x_max-x_min)
                    chanel_mess.update({"Window_Location": "{0}:{1},{2}:{3}".format(x_min,x_max,y_min,y_max)})
                    chanel_mess.update({"Band_Number":str(j)})
                    chanel_mess.update({"sequence":str(sequence)})
                    # chanel_mess.pop("product_id")
                    part_message_list.append(chanel_mess)
                for part_message in part_message_list:
                    part_message.pop("product_id")
                # print(messages3[sci])
                # print(len(messages3[sci]))
                # print(len(messages3[sci][0]))
                all_message_dic.update({"SCI":sci,"product_level":"2A","source":str(source)})
                self.finish.emit(new_image, process * 100, sci,all_message_dic,part_message_list)  # 发送信号
        except Exception as e:
            self.exitcode = 1  # 如果线程异常退出，将该标志位设置为1，正常退出为0
            self.exception = e
        Joint_2AThread.mutex.unlock()


class Joint_2BThread(QThread): # 和2A文件类似，修改变量名
    finish = pyqtSignal(np.ndarray, int, str,dict,list) #int是进度条完成度，str是窗口标题,dict1,dict2是图像信息
    mutex = QMutex()
    # def __del__(self):
    #     self.wait()

    def __init__(self,fileNames_2B,paths_2B,dic,className_list):
        self.exitcode = 0
        self.exception = None #记录异常状态
        # fileNames_2B是文件名列表
        # paths_2B是路径列表
        # dic —— key:窗口位置+场景名 value:属于该场景某一通道的图片列表
        # className_list "窗口位置+场景名"列表

        super(Joint_2BThread, self).__init__()
        self.fileNames_2B = fileNames_2B
        self.paths_2B = paths_2B
        self.dic = dic
        self.className_list = className_list

    def run(self):
        Joint_2BThread.mutex.lock()
        try:
            ind = self.fileNames_2B.index(self.dic[self.className_list[0]][0])
            path = self.paths_2B[ind]
            MyUtils.readXML(path + 'L', fileType="2B") #读取了第一个文件的头信息
            MyUtils.width_2B = int(MyUtils.dir_message_2B["Sample"])
            MyUtils.height_2B = int(MyUtils.dir_message_2B["Line"])
            MyUtils.mode_2B = '<u2'
            dic2 = {}  # key代表窗口位置+场景名+序列号，value代表该场景窗口位置的数据立方体
            messages = {}
            sci_list = []  # 存放场景名列表
            for key, values in self.dic.items():
                if not sci_list.__contains__(key[2:]):
                    sci_list.append(key[2:])
                band = len(values)  # 获取光谱通道数
                new_image = np.zeros((MyUtils.height_2B, MyUtils.height_2B, band), dtype='uint16')
                values = sorted(values)  # 将通道按顺序排列
                tems = []
                for i, v in enumerate(values):  # 通道叠加
                    ind = self.fileNames_2B.index(v)
                    path = self.paths_2B[ind]
                    image = MyUtils.read_2B(path, MyUtils.width_2B, MyUtils.height_2B, MyUtils.mode_2B)
                    MyUtils.readXML(path + 'L', fileType="2B")
                    tem = MyUtils.dir_message_2B.copy()
                    tems.append(tem)
                    new_image[:, :, i] = image
                dic2.update({key: new_image})
                messages.update({key:tems})

            dic3 = {}  # key代表场景名，values是该场景的数据立方体列表
            dic3_dir = {}  # key代表场景名，values是该场景的数据立方体的窗口位置列表
            messages3 ={} # 用于存放信息，key代表场景名，values是该场景通道信息集合的位置列表（value是二维列表）
            for sci in sci_list:  # 初始化dic3
                dic3.update({sci: []})
                dic3_dir.update({sci: []})
                messages3.update({sci:[]})
            for sci_dir, image in dic2.items(): #将数据立方体按照场景分类
                sci = sci_dir[2:]
                dic3[sci].append(image) # 场景i对应数据立方体列表
                dic3_dir[sci].append(sci_dir[0:2]) # 场景i对应数据立方体位置
            for sci_dir,message in messages.items():
                sci = sci_dir[2:]
                messages3[sci].append(message)

            for i,(sci, images) in enumerate(dic3.items()):  # 遍历dic3中的图像对应关系
                part_message_list = []
                all_message_dic = {}
                new_image = np.ones((2048, 2048, images[0].shape[2]), dtype="uint16")
                helpList_x = []
                helpList_y = []
                for j, image in enumerate(images):
                    dir = int(dic3_dir[sci][j])
                    x = (dir - 1) // 8
                    y = (dir - 1) % 8
                    helpList_x.append(x * MyUtils.height_2B)
                    helpList_x.append((x + 1) * MyUtils.height_2B)
                    helpList_y.append(y * MyUtils.height_2B)
                    helpList_y.append((y + 1) * MyUtils.height_2B)
                    new_image[x * MyUtils.height_2B:(x + 1) * MyUtils.height_2B,
                    y * MyUtils.width_2B:(y + 1) * MyUtils.width_2B, :] = image[:,:,:].copy()
                x_min = min(helpList_x)
                x_max = max(helpList_x)
                y_min = min(helpList_y)
                y_max = max(helpList_y)
                new_image = new_image[x_min:x_max, y_min:y_max, :]
                process = i / (len(dic3) - 1)

                source = []

                for j,chanel_mess in enumerate(messages3[sci][0]): #用第一个位置的信息更新整幅图像的信息
                    arrays = [elem[j] for elem in messages3[sci]] # arrays是8个通道位置信息列表
                    sequence = [array["product_id"] for array in arrays]
                    source += sequence
                    chanel_mess["file_size"] = str((y_max-y_min)*(x_max-x_min)*8*16/8)
                    chanel_mess["Sample"] = str(y_max - y_min)
                    chanel_mess["Line"] = str(x_max-x_min)
                    chanel_mess.update({"Window_Location": "{0}:{1},{2}:{3}".format(x_min,x_max,y_min,y_max)})
                    chanel_mess.update({"Band_Number":str(j)})
                    chanel_mess.update({"sequence":str(sequence)})
                    # chanel_mess.pop("product_id")
                    part_message_list.append(chanel_mess)
                for part_message in part_message_list:
                    part_message.pop("product_id")
                # print(messages3[sci])
                # print(len(messages3[sci]))
                # print(len(messages3[sci][0]))
                all_message_dic.update({"SCI":sci,"product_level":"2B","source":str(source)})
                self.finish.emit(new_image, process * 100, sci,all_message_dic,part_message_list)  # 发送信号
        except Exception as e:
            self.exitcode = 1  # 如果线程异常退出，将该标志位设置为1，正常退出为0
            self.exception = e
        Joint_2BThread.mutex.unlock()
