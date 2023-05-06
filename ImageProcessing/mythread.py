#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
@author: Gao
@project: Qt_project
@file: mythread.py
@function:线程管理，子线程处理各级数据产品
@time: 2021/11/27 18:45
"""

from PyQt5.QtCore import QThread, pyqtSignal, QMutex
from utils.myUtils import MyUtils
import numpy as np
import traceback
import os


class Joint_01_Thread(QThread):
    finish = pyqtSignal(np.ndarray,int,str,dict,list,bool,str) #int是进度条完成度，str是窗口标题,dict1,list是图像信息和通道信息
    excepted = pyqtSignal(str) #发送一个异常信号

    def __init__(self,path,batchDic):
        super(Joint_01_Thread, self).__init__()
        self.path = path
        self.batchDic = batchDic # 用于存放批处理选项

    def readRaw(self,filepath):
        strings = filepath.split(".", 1)
        hdrPath = strings[0] + '.hdr'
        hdrDic, description = MyUtils.readHDR(hdrPath)
        source = description["sequence"] # 图片来源
        width = int(hdrDic["samples"])
        height = int(hdrDic["lines"])
        band = int(hdrDic["bands"])
        dataType = MyUtils.ENVIDateType[hdrDic["data type"]]
        byteOrder = hdrDic["byte order"]
        values = [e for e in MyUtils.dir2.values()]
        mode = values[int(byteOrder)] + MyUtils.dir1[dataType]
        images = MyUtils.read_other(filepath, width, height, band, mode)
        return images,hdrDic, description,source

    def splitImage(self):
        MyUtils.list_message_01 = []  # 将字典列表清空
        # 打开01文件
        MyUtils.readXML(self.path + 'L', fileType="01")
        MyUtils.width_01 = int(MyUtils.dir_message_01["Sample"])
        MyUtils.height_01 = int(MyUtils.dir_message_01["Line"])
        MyUtils.band_01 = int(MyUtils.dir_message_01["Time"])
        MyUtils.mode_01 = '>u2'
        images = MyUtils.read_01(self.path, MyUtils.width_01, MyUtils.height_01, MyUtils.band_01, MyUtils.mode_01)
        records = int(MyUtils.dir_message_01["records"])  # 开窗图像数

        messages_list = [] # 用于保存图像信息字典的列表
        for i in range(records):
            # 添加信息
            part_message = {}
            part_message.update(MyUtils.dir_message_01)
            part_message.update(MyUtils.list_message_01[i])
            # 更新window_location信息
            k = int(part_message["window_location"])
            x = (int(k) - 1) // 8
            y = (int(k) - 1) % 8
            x_1 = str(x * MyUtils.height_01)
            x_2 = str((x + 1) * MyUtils.height_01)
            y_1 = str(y * MyUtils.height_01)
            y_2 = str((y + 1) * MyUtils.height_01)
            part_message.update({"window_location": "{0}:{1},{2}:{3}".format(x_1, x_2, y_1, y_2)})
            # 更新product_id信息
            part_message.update({"product_id": part_message["file_name"][0:-5] + "-" +
                                               part_message["Defocusing_Compensation_Gear"] +
                                               "-" + str(x_1) + "_" + str(x_2) + "_" + str(y_1) + "_" + str(y_2) + "-" +
                                               part_message["Band_Number"] + "-S-01.raw"})
            # 更新波长信息
            band = int(part_message["Band_Number"][-1])
            part_message.update({"central_wavelength": MyUtils.CentralWavelength[band - 1]})
            MyUtils.saveFile(images[:, :, i], part_message, MyUtils.saveJoint_addr_tem)
            messages_list.append(part_message)
        return images,messages_list

    def jointImage(self,dic1):
        images_list = []  # 用于保存图像列表
        messages_list = []  # 用于保存图像信息字典的列表
        for key, values in dic1.items():  # key是场景，values是该场景的多谱段多个窗口位置的图像索引
            for bandCode in MyUtils.BandCode:
                file_list = os.listdir(MyUtils.saveJoint_addr_tem)  # 获取临时文件夹中的01拆分文件
                for file in file_list[::-1]:  # 逆序遍历
                    if file.endswith('-S-01.raw') and file[62:66] == key and file[-13:-9] == bandCode:  ## 判断文件的扩展名
                        continue
                    file_list.remove(file)  # 过滤文件
                # 拼接
                new_image = np.zeros((2048, 2048, 1), dtype='uint16')
                helpList_x = []
                helpList_y = []
                # 添加图像信息
                part_message = {}
                source_list = []  # 用于保存图像来源
                for j, file in enumerate(file_list):
                    file = os.path.join(MyUtils.saveJoint_addr_tem, file)
                    images,hdrDic, description,source = self.readRaw(file)
                    source_list.append(source)
                    if j == 0:
                        part_message = description.copy()
                    location = description["window_location"]
                    location = location.replace(",", ":")
                    ranges = location.split(":")
                    new_image[int(ranges[0]):int(ranges[1]), int(ranges[2]):int(ranges[3]), :] = images[:, :, :]
                    helpList_x.append(int(ranges[0]))
                    helpList_x.append(int(ranges[1]))
                    helpList_y.append(int(ranges[2]))
                    helpList_y.append(int(ranges[3]))
                # 图片主体范围
                x_min = min(helpList_x)
                x_max = max(helpList_x)
                y_min = min(helpList_y)
                y_max = max(helpList_y)
                new_image = new_image[x_min:x_max, y_min:y_max, :]
                # 更新product信息
                part_message.update(
                    {"window_location": "{0}:{1},{2}:{3}".format(str(x_min), str(x_max), str(y_min), str(y_max))})
                # 更新product_id信息,场景+位置+通道+J-01
                part_message.update({"product_id": part_message["product_id"][0:61] + "-" +
                                                   key + "-" + str(x_min) + "_" + str(x_max) + "_" + str(
                    y_min) + "_" + str(y_max) + "-" + bandCode + "-S-J-01.raw"})
                # 更新source
                part_message.update({"source": str(source_list)})
                MyUtils.saveFile(new_image, part_message, MyUtils.saveJoint_addr_tem)
                images_list.append(new_image)
                messages_list.append(part_message)
        return  images_list,messages_list

    def combineImage(self,dic1):
        images_list = []  # 用于保存图像列表
        # messages_list = []  # 用于保存图像信息字典的列表
        dir_messages_list = []  # 用于保存图像信息字典的列表
        part_messages_list = []
        for i, (key, values) in enumerate(dic1.items()):  # key是场景，values是该场景的多谱段多个窗口位置的图像索引
            location_list = []  # 窗口位置列表
            for value in values:
                location = MyUtils.list_message_01[value]["window_location"]
                x = (int(location) - 1) // 8  # 此处的8是原图像2048*2048被划分为8*8块位置
                y = (int(location) - 1) % 8
                locationString = "{0}_{1}_{2}_{3}".format(str(x * MyUtils.height_01),
                                                          str((x + 1) * MyUtils.height_01),
                                                          str(y * MyUtils.height_01),
                                                          str((y + 1) * MyUtils.height_01))

                if not location_list.__contains__(locationString):
                    location_list.append(locationString)
            for location in location_list:
                file_list = os.listdir(MyUtils.saveJoint_addr_tem)
                for file in file_list[::-1]:  # 逆序遍历
                    if file.endswith('-S-01.raw') and file[62:66] == key \
                            and file[67:-14] == location:  ## 判断文件的扩展名[31:-14]
                        continue
                    file_list.remove(file)  # 过滤文件
                # 同一位置通道合成
                ranges = location.split("_")
                width_ = int(ranges[1]) - int(ranges[0])
                height_ = int(ranges[3]) - int(ranges[2])
                new_image = np.zeros((width_, height_, len(file_list)), dtype='uint16')
                all_message = {}  # 保存多光谱图像整体信息
                part_message = [] # 用于保存多光谱通道信息
                source_list = []  # 用于保存图像来源
                central_wavelength_list = []  # 用于保存中心波长列表

                # 读取窗口文件并合成
                for j, file in enumerate(file_list):
                    file = os.path.join(MyUtils.saveJoint_addr_tem, file)
                    images, hdrDic, description, source = self.readRaw(file)
                    source_list.append(source)
                    if j == 0:
                        all_message = description
                    part_message.append(description)
                    central_wavelength_list.append(description["central_wavelength"])
                    new_image[:, :, j] = images[:, :, 0]
                # 更新product信息
                all_message.update({"window_location": "{0}:{1},{2}:{3}".format(ranges[0],ranges[1], ranges[2], ranges[3])})
                # 更新product_id信息,场景+位置+通道+J-01
                all_message.update({"product_id": all_message["product_id"][0:61] + "-" +
                                                   key +"-"+ location + "-WT" + "-S-C-01.raw"})
                # 更新source
                all_message.update({"source": str(source_list)})
                # 更新Band波段数
                all_message.update({"Band": str(len(file_list))})
                # 更新central_wavelength
                all_message.update({"central_wavelength": ','.join(central_wavelength_list)})
                MyUtils.saveFile(new_image, all_message, MyUtils.saveJoint_addr_tem)
                images_list.append(new_image)
                dir_messages_list.append(all_message)
                part_messages_list.append(part_message)
        return  images_list,dir_messages_list,part_messages_list

    def sceneClassify(self,records):
        # 将窗口图像集合按照场景分类
        sciene_list = []  # 存放场景分类
        dic1 = {}  # 初次分类：按场景分类图像，value是图像索引
        for record in range(records):
            SciName = MyUtils.list_message_01[record]["Defocusing_Compensation_Gear"]
            if not sciene_list.__contains__(SciName):
                sciene_list.append(SciName)  # 记录拍摄场景列表（以定焦轮位置区分场景）
        for sciene in sciene_list:
            dic1.update({sciene: []})
        for j in range(records):
            SciName = MyUtils.list_message_01[j]["Defocusing_Compensation_Gear"]
            dic1[SciName].append(j)  # 将同一SciName的文件索引放入同key字典的velue中
        return dic1,sciene_list

    # def joint_combineImage(self,dic1):
    #     images_list = []  # 用于保存图像列表
    #     messages_list = []  # 用于保存图像信息字典的列表
    #     for key in dic1.keys():
    #         file_list = os.listdir(MyUtils.saveJoint_addr_tem)  # 获取临时文件夹中的01拆分文件
    #         for file in file_list[::-1]:  # 逆序遍历
    #             if file.endswith('-S-J-01.raw') and file[26:30] == key :  # 根据场景区分图像
    #                 continue
    #             file_list.remove(file)  # 过滤文件
    #         # 拼接
    #         location = file_list[0][31:-16]
    #         ranges = location.split("_")
    #         width_ = int(ranges[1])-int(ranges[0])
    #         height_= int(ranges[3])-int(ranges[2])
    #         new_image = np.zeros((width_, height_, len(file_list)), dtype='uint16')
    #         # 添加图像信息
    #         part_message = {}
    #         source_list = []  # 用于保存图像来源
    #         central_wavelength_list = []  # 用于保存中心波长列表
    #         for j, file in enumerate(file_list):
    #             file = os.path.join(MyUtils.saveJoint_addr_tem, file)
    #             images, hdrDic, description, _ = self.readRaw(file)
    #             source_list.append(description["source"])
    #             central_wavelength_list.append(description["central_wavelength"])
    #             if j == 0:
    #                 part_message = description
    #             new_image[:,:,j] = images[:,:,0]
    #         # 更新product信息
    #         part_message.update(
    #             {"window_location": "{0}:{1},{2}:{3}".format(ranges[0],ranges[1], ranges[2], ranges[3])})
    #         # 更新product_id信息,场景+位置+通道+J-01
    #         part_message.update({"product_id": "HX1-Ro_GRAS_MSCam-W_SCI_N" + "-" +
    #                                            key + "-" + location  + "-WT" + "-S-J-C-01.raw"})
    #         # 更新source
    #         part_message.update({"source": str(source_list)})
    #         # 更新Band波段数
    #         part_message.update({"Band": str(len(file_list))})
    #         # 更新central_wavelength
    #         part_message.update({"central_wavelength": ','.join(central_wavelength_list)})
    #         MyUtils.saveFile(new_image, part_message, MyUtils.saveJoint_addr_tem)
    #         images_list.append(new_image)
    #         messages_list.append(part_message)
    #     return  images_list,messages_list

    def autoJointCombine(self,images,dic): # images是读取的01文件集合
        images_list = []  # 用于保存图像列表
        dir_messages_list = []  # 用于保存图像信息字典的列表
        part_messages_list = []

        # 对多个场景中的图像块进行拼接合成
        for i, (key, values) in enumerate(dic.items()):  # key是场景，values是该场景的多谱段多个窗口位置的图像索引
            dic2 = {}  # 位置：图片
            addrs = []  # 窗口位置列表
            for value in values:
                addr = MyUtils.list_message_01[value]["window_location"]
                if not addrs.__contains__(addr):
                    addrs.append(addr)
            for addr in addrs:
                dic2.update({addr: []})
            for value in values:
                # chanel = int(MyUtils.list_message_01[value]["Band_Number"][-1])
                addr = MyUtils.list_message_01[value]["window_location"]
                dic2[addr].append(value)  # key是窗口位置，value是该窗口位置的八个通道图像

            new_image = np.zeros((2048, 2048, len(dic2[addrs[0]])), dtype='uint16')
            helpList_x = []
            helpList_y = []

            # 各窗口位置进行通道合成和拼接
            for k, vs in dic2.items():  # k是窗口位置，vs是该位置的1-8通道图片集合
                x = (int(k) - 1) // 8  # 此处的8是原图像2048*2048被划分为8*8块位置
                y = (int(k) - 1) % 8
                helpList_x.append(x * MyUtils.height_01)
                helpList_x.append((x + 1) * MyUtils.height_01)
                helpList_y.append(y * MyUtils.height_01)
                helpList_y.append((y + 1) * MyUtils.height_01)
                # 遍历每一个窗口位置，对其进行合成
                for j, v in enumerate(vs):
                    new_image[x * MyUtils.height_01:(x + 1) * MyUtils.height_01,
                    y * MyUtils.width_01:(y + 1) * MyUtils.width_01, j] = images[:, :, v]
            # 图片主体范围
            x_min = min(helpList_x)
            x_max = max(helpList_x)
            y_min = min(helpList_y)
            y_max = max(helpList_y)
            new_image = new_image[x_min:x_max, y_min:y_max, :]

            # 为拼接合成好的图像整体添加信息
            tems_s = [elem for elem in dic2.values()]
            tems = tems_s[0]  # 第一个窗口位置的8个通道图像列表
            dir_message = MyUtils.dir_message_01.copy()
            dir_message["file_size"] = str((y_max - y_min) * (x_max - x_min) * len(tems) * 16 / 8)  # 更改"file_size"
            dir_message["Band"] = str(len(tems))
            dir_message.pop("records")
            dir_message.update({"product_level": "01", "source": self.path})

            # 为拼接合成好的图像各通道添加信息
            list_message = []
            for k, tem in enumerate(tems):
                tem_dic = MyUtils.list_message_01[tem].copy()
                tem_dic["window_location"] = "{0}:{1},{2}:{3}".format(x_min, x_max, y_min, y_max)
                tem_dic["sequence"] = str([elem[k] for elem in dic2.values()])
                tem_dic.update({"central_wavelength": MyUtils.CentralWavelength[k]})
                list_message.append(tem_dic)

            # 在保存的多光谱文件中添加保存格外的信息，此信息在list_message中有
            wavelengths = []
            for d in list_message:
                if d.keys().__contains__("central_wavelength"):
                    wavelengths.append(d["central_wavelength"])
            if len(wavelengths) > 0:
                dir_message.update({"central_wavelength": ','.join(wavelengths)})
            if len(list_message) > 0 and list_message[0].keys().__contains__("window_location"):
                dir_message.update({"window_location": list_message[0]["window_location"]})
            # 在头信息中添加更多信息
            dir_message.update({"product_id": dir_message["file_name"][0:-4] + "-" + str(x_max - x_min) + "_" + str(
                y_max - y_min) + "-JC_01.raw"})
            MyUtils.saveFile(new_image, dir_message, MyUtils.saveJoint_addr_tem)
            images_list.append(new_image)
            dir_messages_list.append(dir_message)
            part_messages_list.append(list_message)
        return images_list,dir_messages_list,part_messages_list

    def wavelengthSort(self,image,message,part_message):
        tem = image[:, :, 0].copy()
        image[:, :, 0] = image[:, :, 1]
        image[:, :, 1] = tem
        # 更新波段
        # 通道信息也排序
        tem_partmessage = part_message[0].copy()
        part_message[0] = part_message[1]
        part_message[1] = tem_partmessage

        band = message["Band"]
        central_wavelength_list = []
        for j in range(int(band)):
            central_wavelength_list.append(MyUtils.CentralWavelength_sort[j])
        message.update({"central_wavelength": ','.join(central_wavelength_list)})
        message.update({"wavelengthSort":"True"})
        message.update({"product_id":message["product_id"][:-4]+"-p.raw"})
        MyUtils.saveFile(image, message, MyUtils.saveJoint_addr_tem)
        return  image, message,part_message

    def geometryCorrect(self,image,message):
        new_image = MyUtils.geoCorrect(image, MyUtils.translateTform_addr, message, 31)
        message.update({"register": "True"})
        message.update({"product_id": message["product_id"][:-4] + "-j.raw"})
        MyUtils.saveFile(new_image, message, MyUtils.saveJoint_addr_tem)
        return new_image,message

    def falseColor(self,new_image,message_list,all_message):
        tem = np.zeros((new_image.shape[0], new_image.shape[1], 3), dtype=type(new_image.flatten()[0]))
        tem[:, :, 0] = new_image[:, :, 2]  # RGB 分别为 3 1 2 通道
        tem[:, :, 1] = new_image[:, :, 0]
        tem[:, :, 2] = new_image[:, :, 1]
        # 更新彩色通道信息
        tem_message = []
        tem_message.append(message_list[2])
        tem_message.append(message_list[0])
        tem_message.append(message_list[1])
        all_message.update({"Color":"True"})
        all_message.update({"product_id": all_message["product_id"][:-4] + "-c.raw"})
        all_message.update({"Band": str(len(tem_message))})
        MyUtils.saveFile(tem, all_message, MyUtils.saveJoint_addr_tem)
        return tem,tem_message,all_message

    def saveToPDS4(self,new_image,message_list):
        template = self.path+"L"
        outname = message_list["product_id"][:-4] + ".xml"
        outname = os.path.join(MyUtils.saveJoint_addr, outname)
        filename = os.path.join(MyUtils.saveJoint_addr_tem, message_list["product_id"])
        dataType = type(new_image.flatten()[0])
        MyUtils.save_PDS4(template, outname, filename, dataType)

    def run(self):
        try:
            # 选择将01图像流拆分
            images_s,messages_list_s = self.splitImage()

            # 将拆分的图像集合通过场景先进行分类
            dic1,_ = self.sceneClassify(images_s.shape[2])

            images_list_j=[]
            messages_list_j=[]
            if self.batchDic["jointCheck"] and not self.batchDic["combineCheck"]:  # 拼接
                images_list_j,messages_list_j = self.jointImage(dic1)

            images_list_c = []
            messages_list_c = []
            part_messages_list_c = []
            if self.batchDic["combineCheck"] and not self.batchDic["jointCheck"]:  # 合成
                images_list_c, messages_list_c,part_messages_list_c = self.combineImage(dic1)

            images_list_jc = []
            messages_list_jc = []
            part_messages_list_jc = []
            if self.batchDic["jointCheck"] and self.batchDic["combineCheck"]:  # 合成，拼接
                # images_list_jc, messages_list_jc = self.joint_combineImage(dic1)
                images_list_jc, messages_list_jc,part_messages_list_jc = self.autoJointCombine(images_s,dic1)

            if self.batchDic["geometryCheck"]: # 几何校正
                if self.batchDic["geometryCorrectSlect"] == 21 : # 使用参数进行校正
                    for i in range(len(images_list_c)):
                        images_list_c[i], messages_list_c[i] = self.geometryCorrect(images_list_c[i], messages_list_c[i])
                    for i in range(len(images_list_jc)):
                        images_list_jc[i], messages_list_jc[i] = self.geometryCorrect(images_list_jc[i], messages_list_jc[i])

            if self.batchDic["colorCheck"]:  # 色彩校正
                if self.batchDic["colorCorrectSlect"]==11: #伪彩色合成
                    for i in range(len(images_list_c)):
                        # messages_list_c[i].update({"product_id": messages_list_c[i]["product_id"][:-4] + "-c.raw"})
                        # messages_list_c[i].update({"Color":"True"})
                        images_list_c[i], part_messages_list_c[i],messages_list_c[i] = self.falseColor(images_list_c[i], part_messages_list_c[i],messages_list_c[i])
                    for i in range(len(images_list_jc)):
                        # messages_list_jc[i].update({"product_id": messages_list_jc[i]["product_id"][:-4] + "-c.raw"})
                        # messages_list_jc[i].update({"Color": "True"})
                        images_list_jc[i], part_messages_list_jc[i],messages_list_jc[i]= self.falseColor(images_list_jc[i], part_messages_list_jc[i],messages_list_jc[i])


            if self.batchDic["spectrumCheck"]: # 光谱校正
                if self.batchDic["wavelengthSortCheck"]:
                    for i in range(len(images_list_c)): # 图像集合中所有多光谱图像第1,2通道交换位置
                        images_list_c[i],messages_list_c[i],part_messages_list_c[i] = self.wavelengthSort(images_list_c[i],messages_list_c[i],part_messages_list_c[i])

                    for i in range(len(images_list_jc)):
                        images_list_jc[i], messages_list_jc[i],part_messages_list_jc[i] = self.wavelengthSort(images_list_jc[i], messages_list_jc[i],part_messages_list_jc[i])

            if self.batchDic["saveCheck"]: #保存
                if self.batchDic["saveType"] == "raw":
                    if self.batchDic["saveFile"] == "单文件":  # 只保存最终文件
                        for i in range(len(images_list_j)):
                            MyUtils.saveFile(images_list_j[i], messages_list_j[i], self.batchDic["saveDirectory"])
                        for i in range(len(images_list_c)):
                            MyUtils.saveFile(images_list_c[i], messages_list_c[i], self.batchDic["saveDirectory"])
                        for i in range(len(images_list_jc)):
                            MyUtils.saveFile(images_list_jc[i], messages_list_jc[i], self.batchDic["saveDirectory"])

                    if self.batchDic["saveFile"] == "多文件":  # 把分解的文件也进行保存
                        for i in range(images_s.shape[2]):
                            MyUtils.saveFile(images_s[:,:,i], messages_list_s[i], self.batchDic["saveDirectory"])
                        for i in range(len(images_list_j)):
                            MyUtils.saveFile(images_list_j[i], messages_list_j[i], self.batchDic["saveDirectory"])
                        for i in range(len(images_list_c)):
                            MyUtils.saveFile(images_list_c[i], messages_list_c[i], self.batchDic["saveDirectory"])
                        for i in range(len(images_list_jc)):
                            MyUtils.saveFile(images_list_jc[i], messages_list_jc[i], self.batchDic["saveDirectory"])
                if self.batchDic["saveType"] == "jpg":
                    for i in range(len(images_list_c)):
                        filename = messages_list_c[i]["product_id"][:-4] + ".jpg"
                        filepath = os.path.join(MyUtils.saveJoint_addr, filename)
                        MyUtils.save_RGB(filepath, images_list_c[i])
                    for i in range(len(images_list_jc)):
                        filename = messages_list_jc[i]["product_id"][:-4] + ".jpg"
                        filepath = os.path.join(MyUtils.saveJoint_addr, filename)
                        MyUtils.save_RGB(filepath, images_list_jc[i])

                if self.batchDic["saveType"] == "pds4":
                    if self.batchDic["saveFile"] == "单文件":  # 只保存最终文件
                        for i in range(len(images_list_j)):
                            self.saveToPDS4(images_list_j[i], messages_list_j[i])
                        for i in range(len(images_list_c)):
                            self.saveToPDS4(images_list_c[i], messages_list_c[i])
                        for i in range(len(images_list_jc)):
                            self.saveToPDS4(images_list_jc[i], messages_list_jc[i])
                    if self.batchDic["saveFile"] == "多文件":  # 把分解的文件也进行保存
                        for i in range(images_s.shape[2]):
                            self.saveToPDS4(images_s[:,:,i], messages_list_s[i])
                        for i in range(len(images_list_j)):
                            self.saveToPDS4(images_list_j[i], messages_list_j[i])
                        for i in range(len(images_list_c)):
                            self.saveToPDS4(images_list_c[i], messages_list_c[i])
                        for i in range(len(images_list_jc)):
                            self.saveToPDS4(images_list_jc[i], messages_list_jc[i])

            # 发送信号
            sum_len = len(images_list_j)+len(images_list_c)+len(images_list_jc)
            count = 0
            for i in range(len(images_list_j)):
                count+=1
                process = count/sum_len
                self.finish.emit(images_list_j[i], process*100, messages_list_j[i]["product_id"], messages_list_j[i], messages_list_j,self.batchDic["ToWindowCheck"],"01")
            for i in range(len(images_list_c)):
                count += 1
                process = count / sum_len
                self.finish.emit(images_list_c[i], process * 100, messages_list_c[i]["product_id"], messages_list_c[i], part_messages_list_c[i],self.batchDic["ToWindowCheck"],"01")
            for i in range(len(images_list_jc)):
                count += 1
                process = count / sum_len
                self.finish.emit(images_list_jc[i], process * 100, messages_list_jc[i]["product_id"], messages_list_jc[i], part_messages_list_jc[i],self.batchDic["ToWindowCheck"],"01")

            if sum_len == 0:
                for i in range(images_s.shape[2]):
                    count += 1
                    process = count / images_s.shape[2]
                    self.finish.emit(images_s[:,:,i], process * 100, messages_list_s[i]["product_id"],
                                     messages_list_s[i], messages_list_s, self.batchDic["ToWindowCheck"],"01")

        except Exception as e:
            exception = traceback.format_exc()
            self.excepted.emit(exception) # 将异常发送给UI进程


class Joint_2AThread(QThread):
    finish = pyqtSignal(np.ndarray, int, str,dict,list,bool,str) #int是进度条完成度，str是窗口标题,dict1,dict2是图像信息,最后一个是文件类型
    excepted = pyqtSignal(str) #发送一个异常信号

    def __init__(self,fileNames,paths,batchDic):
        # fileNames是文件名列表
        # paths是路径列表
        # dic —— key:窗口位置+场景名 value:属于该场景某一通道的图片列表
        # className_list "窗口位置+场景名"列表

        super(Joint_2AThread, self).__init__()
        self.fileNames = fileNames
        self.paths = paths
        self.batchDic = batchDic  # 用于存放批处理选项

    def readRaw(self, filepath):
        MyUtils.readXML(filepath + 'L', fileType="2A")
        dir_message = MyUtils.dir_message_2A
        band = 1
        mode = '<u2'
        source = filepath
        width = int(dir_message["Sample"])
        height = int(dir_message["Line"])
        image = MyUtils.read_type(filepath, width, height, band, "2A", mode)
        description = dir_message
        return image, description, source

    def sceneClassify(self):
        # 将窗口图像集合按照场景分类
        sciene_list = []
        dic = {}  # key:窗口位置+场景名+序列号 value:属于该场景某一通道的图片列表
        for text in self.fileNames:
            string = text[30:36] + text[-10:-5]  # 场景名+序列号
            if not sciene_list.__contains__(string):
                sciene_list.append(string)
        for className in sciene_list:
            dic.update({className: []})
        for text in self.fileNames:
            string = text[30:36] + text[-10:-5]  # 场景名+序列号
            dic[string].append(text)
        return dic, sciene_list

    def wavelengthSort(self,image,message,partMessage):
        tem = image[:, :, 0].copy()
        image[:, :, 0] = image[:, :, 1]
        image[:, :, 1] = tem

        # 通道信息也排序
        tem_partmessage = partMessage[0].copy()
        partMessage[0] =  partMessage[1]
        partMessage[1] = tem_partmessage

        for k,v in message.items():
            print(k,":",v)
        # 更新波段
        band = message["Band"]
        central_wavelength_list = []
        for j in range(int(band)):
            central_wavelength_list.append(MyUtils.CentralWavelength_sort[j])
        message.update({"central_wavelength": ','.join(central_wavelength_list)})
        message.update({"product_id": message["product_id"][:-4] + "-p.raw"})
        message.update({"wavelengthSort":"True"})
        MyUtils.saveFile(image, message, MyUtils.saveJoint_addr_tem)
        return  image, message,partMessage

    def geometryCorrect(self,image,message):
        new_image = MyUtils.geoCorrect(image, MyUtils.translateTform_addr, message, 31)
        message.update({"register": "True"})
        message.update({"product_id": message["product_id"][:-4] + "-j.raw"})
        MyUtils.saveFile(new_image, message, MyUtils.saveJoint_addr_tem)
        return new_image,message

    def falseColor(self,new_image,message_list,all_message):
        tem = np.zeros((new_image.shape[0], new_image.shape[1], 3), dtype=type(new_image.flatten()[0]))
        tem[:, :, 0] = new_image[:, :, 2]  # RGB 分别为 3 1 2 通道
        tem[:, :, 1] = new_image[:, :, 0]
        tem[:, :, 2] = new_image[:, :, 1]
        # 更新彩色通道信息
        tem_message = []
        tem_message.append(message_list[2])
        tem_message.append(message_list[0])
        tem_message.append(message_list[1])

        all_message.update({"Color": "True"})
        all_message.update({"product_id": all_message["product_id"][:-4] + "-c.raw"})
        all_message.update({"Band": str(len(tem_message))})
        MyUtils.saveFile(tem, all_message, MyUtils.saveJoint_addr_tem)
        return tem,tem_message,all_message

    def saveToPDS4(self,new_image,message_list):
        def isValid(string):
            validList = ["[","]","'"]
            if validList.__contains__(string):
                return False
            else:
                return True

        sources = message_list["source"].split(",")
        template = "".join(filter(isValid, sources[0]))
        template = template +"L"
        outname = message_list["product_id"][:-4] + ".xml"
        outname = os.path.join(MyUtils.saveJoint_addr, outname)
        filename = os.path.join(MyUtils.saveJoint_addr_tem, message_list["product_id"])
        dataType = type(new_image.flatten()[0])
        MyUtils.save_PDS4(template, outname, filename, dataType)

    def jointImage(self,dic1):
        images_list = []  # 用于保存图像列表
        messages_list = []  # 用于保存图像信息字典的列表
        for key, values in dic1.items(): # key是场景名，values是该场景的图像名
            for bandCode in range(len(MyUtils.BandCode)):
                file_list = values.copy()
                for file in file_list[::-1]:  # 逆序遍历
                    if int(file[20:21])-1 == bandCode:  # 寻找同一个场景同一个通道的图像
                        continue
                    file_list.remove(file)  # 过滤文件
                # 拼接
                new_image = np.zeros((2048, 2048,1), dtype='uint16')
                helpList_x = []
                helpList_y = []
                # 添加图像信息
                part_message = {}
                source_list = []  # 用于保存图像来源
                for j, file in enumerate(file_list):
                    filePath = self.paths[self.fileNames.index(file)]
                    images,description,source = self.readRaw(filePath)
                    source_list.append(source)
                    if j == 0:
                        part_message = description.copy()
                    location = description["window_location"]
                    location = location.strip("(")
                    location = location.strip(")")
                    ranges = location.split(",")
                    loc_x = int(ranges[0])-1
                    loc_y = int(ranges[1])-1
                    new_image[loc_x:loc_x+MyUtils.height_2A, loc_y:loc_y+MyUtils.width_2A,0] = images[:, :]
                    helpList_x.append(loc_x)
                    helpList_x.append(loc_x+MyUtils.height_2A)
                    helpList_y.append(loc_y)
                    helpList_y.append(loc_y+MyUtils.width_2A)
                # 图片主体范围
                x_min = min(helpList_x)
                x_max = max(helpList_x)
                y_min = min(helpList_y)
                y_max = max(helpList_y)
                new_image = new_image[x_min:x_max, y_min:y_max,:].copy()
                # 更新product信息
                part_message.update(
                    {"window_location": "{0}:{1},{2}:{3}".format(str(x_min), str(x_max), str(y_min), str(y_max))})
                # 更新product_id信息,场景+位置+通道+J-01
                part_message.update({"product_id": part_message["product_id"][0:-5] + "-"+str(x_min) + "_" + str(x_max) + "_" + str(
                    y_min) + "_" + str(y_max) + "-J-2A.raw"})
                # 更新source
                part_message.update({"source": str(source_list)})
                MyUtils.saveFile(new_image, part_message, MyUtils.saveJoint_addr_tem)
                images_list.append(new_image)
                messages_list.append(part_message)
        return  images_list,messages_list

    def combineImage(self,dic1):
        images_list = []  # 用于保存图像列表
        dir_messages_list = []  # 用于保存图像信息字典的列表
        part_messages_list = []
        for i, (key, values) in enumerate(dic1.items()):
            location_list = []  # 窗口位置列表
            for value in values:
                location = value[22:24]
                if not location_list.__contains__(location):
                    location_list.append(location)
            for location in location_list:
                file_list = values.copy()
                for file in file_list[::-1]:  # 逆序遍历
                    if file[22:24] == location:  ## 判断文件的名
                        continue
                    file_list.remove(file)  # 过滤文件
                # 同一位置通道合成
                new_image = np.zeros((MyUtils.height_2A,MyUtils.width_2A, len(file_list)), dtype='uint16')
                all_message = {}  # 保存多光谱图像整体信息
                part_message = [] # 用于保存多光谱通道信息
                source_list = []  # 用于保存图像来源
                central_wavelength_list = []  # 用于保存中心波长列表
                # 读取窗口文件并合成
                for j, file in enumerate(file_list):
                    filePath = self.paths[self.fileNames.index(file)]
                    images, description, source = self.readRaw(filePath)
                    source_list.append(source)
                    if j == 0:
                        all_message = description.copy()
                    part_message.append(description)
                    central_wavelength_list.append(description["central_wavelength"])
                    new_image[:, :, j] = images[:, :]
                # 更新product信息
                x = (int(location) - 1) // 8  # 此处的8是原图像2048*2048被划分为8*8块位置
                y = (int(location) - 1) % 8
                all_message.update({"window_location": "{0}:{1},{2}:{3}".format(str(x * MyUtils.height_2A),
                                                          str((x + 1) * MyUtils.height_2A),
                                                          str(y * MyUtils.width_2A),
                                                          str((y + 1) * MyUtils.width_2A))})
                # 更新product_id信息,场景+位置+通道+C-2A
                all_message.update({"product_id": all_message["product_id"][0:-5] + "-C-2A.raw"})
                # 更新source
                all_message.update({"source": str(source_list)})
                # 更新Band波段数
                all_message.update({"Band": str(len(file_list))})
                # 更新central_wavelength
                all_message.update({"central_wavelength": ','.join(central_wavelength_list)})
                MyUtils.saveFile(new_image, all_message, MyUtils.saveJoint_addr_tem)
                images_list.append(new_image)
                dir_messages_list.append(all_message)
                part_messages_list.append(part_message)
        return  images_list,dir_messages_list,part_messages_list

    def autoJointCombine(self):
        images_list = []  # 用于保存图像列表
        dir_messages_list = []  # 用于保存图像信息字典的列表
        part_messages_list = []
        MyUtils.readXML(self.paths[0] + 'L', fileType="2A")  # 读取了第一个文件的头信息
        MyUtils.width_2A = int(MyUtils.dir_message_2A["Sample"])
        MyUtils.height_2A = int(MyUtils.dir_message_2A["Line"])
        MyUtils.mode_2A = '<u2'

        # 将窗口图像集合按照场景分类
        sciene_list = []
        dic = {}  # key:窗口位置+场景名+序列号 value:属于该场景某一通道的图片列表
        for text in self.fileNames:
            string = text[22:24]+ text[30:36] + text[-10:-5]  # 场景名+序列号
            if not sciene_list.__contains__(string):
                sciene_list.append(string)
        for className in sciene_list:
            dic.update({className: []})
        for text in self.fileNames:
            string = text[22:24]+ text[30:36] + text[-10:-5]  # 场景名+序列号
            dic[string].append(text)

        dic2 = {}  # key代表窗口位置+场景名，value代表该场景窗口位置的数据立方体
        messages = {}
        sci_list = []  # 存放场景名列表
        for key, values in dic.items():
            if not sci_list.__contains__(key[2:]):
                sci_list.append(key[2:])
            band = len(values)  # 获取光谱通道数
            new_image = np.zeros((MyUtils.height_2A, MyUtils.height_2A, band), dtype='uint16')
            values = sorted(values)  # 将通道按顺序排列
            tems = []
            for i, v in enumerate(values):  # 通道叠加
                ind = self.fileNames.index(v)
                path = self.paths[ind]
                image = MyUtils.read_2A(path, MyUtils.width_2A, MyUtils.height_2A, MyUtils.mode_2A)
                MyUtils.readXML(path + 'L', fileType="2A")
                tem = MyUtils.dir_message_2A.copy()
                tems.append(tem)
                new_image[:, :, i] = image
            dic2.update({key: new_image})
            messages.update({key: tems})

        dic3 = {}  # key代表场景名，values是该场景的数据立方体列表
        dic3_dir = {}  # key代表场景名，values是该场景的数据立方体的窗口位置列表
        messages3 = {}  # 用于存放信息，key代表场景名，values是该场景通道信息集合的位置列表（value是二维列表）
        for sci in sci_list:  # 初始化dic3
            dic3.update({sci: []})
            dic3_dir.update({sci: []})
            messages3.update({sci: []})
        for sci_dir, image in dic2.items():  # 将数据立方体按照场景分类
            sci = sci_dir[2:]
            dic3[sci].append(image)  # 场景i对应数据立方体列表
            dic3_dir[sci].append(sci_dir[0:2])  # 场景i对应数据立方体位置
        for sci_dir, message in messages.items():
            sci = sci_dir[2:]
            messages3[sci].append(message)

        for i, (sci, images) in enumerate(dic3.items()):  # 遍历dic3中的图像对应关系
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
            new_image = new_image[x_min:x_max, y_min:y_max, :].copy()

            source = []
            for j, chanel_mess in enumerate(messages3[sci][0]):  # 用第一个位置的信息更新整幅图像的信息
                arrays = [elem[j] for elem in messages3[sci]]  # arrays是8个通道位置信息列表
                sequence = [array["product_id"] for array in arrays]
                for se in sequence:
                    source.append(self.paths[self.fileNames.index(se)])
                chanel_mess["file_size"] = str((y_max - y_min) * (x_max - x_min) * 8 * 16 / 8)
                chanel_mess["Sample"] = str(y_max - y_min)
                chanel_mess["Line"] = str(x_max - x_min)
                chanel_mess.update({"window_location": "{0}:{1},{2}:{3}".format(x_min, x_max, y_min, y_max)})
                chanel_mess.update({"Band_Number": str(j + 1)})
                chanel_mess.update({"Band": str(len(messages3[sci][0]))})
                chanel_mess.update({"sequence": str(sequence)})
                # if j==0:
                #     all_message_dic.update(chanel_mess)
                part_message_list.append(chanel_mess)

            # 更新信息
            all_message_dic.update({"SCI": sci, "product_level": "2A", "source": str(source)})
            all_message_dic.update({"Band": part_message_list[0]["Band"]})
            all_message_dic.update({"product_id": part_message_list[0]["product_id"][0:-3] +
                                                  part_message_list[0]["Sample"] + "_" + part_message_list[0][
                                                      "Line"] + "-JC_2A.raw"})

            # 将各通道一些信息整合到头信息中
            wavelengths = [] #波长
            absolute_radiation_calibration_parameter = []  # 辐射校正系数
            exposure_time = [] #曝光时间
            full_width_half_max = []
            maximum = []
            minimum = []
            mean = []
            standard_deviation = []
            for d in part_message_list:
                if d.keys().__contains__("central_wavelength"):
                    wavelengths.append(d["central_wavelength"])
                if d.keys().__contains__("absolute_radiation_calibration_parameter(W*m**-2*sr**-1*DN**-1)"):
                    absolute_radiation_calibration_parameter.append(d["absolute_radiation_calibration_parameter(W*m**-2*sr**-1*DN**-1)"])
                if d.keys().__contains__("exposure_time"):
                    exposure_time.append(d["exposure_time"])
                if d.keys().__contains__("full_width_half_max"):
                    full_width_half_max.append(d["full_width_half_max"])
                if d.keys().__contains__("maximum"):
                    maximum.append(d["maximum"])
                if d.keys().__contains__("minimum"):
                    minimum.append(d["minimum"])
                if d.keys().__contains__("mean"):
                    mean.append(d["mean"])
                if d.keys().__contains__("standard_deviation"):
                    standard_deviation.append(d["standard_deviation"])
            if len(wavelengths) > 0:
                all_message_dic.update({"central_wavelength": ','.join(wavelengths)})
            if len(absolute_radiation_calibration_parameter) > 0:
                all_message_dic.update({"absolute_radiation_calibration_parameter(W*m**-2*sr**-1*DN**-1)": ','.join(absolute_radiation_calibration_parameter)})
            if len(exposure_time) > 0:
                all_message_dic.update({"exposure_time": ','.join(exposure_time)})
            if len(full_width_half_max) > 0:
                all_message_dic.update({"full_width_half_max": ','.join(full_width_half_max)})

            if len(maximum) > 0:
                all_message_dic.update({"maximum": ','.join(maximum)})
            if len(minimum) > 0:
                all_message_dic.update({"minimum": ','.join(minimum)})
            if len(mean) > 0:
                all_message_dic.update({"mean": ','.join(mean)})
            if len(standard_deviation) > 0:
                all_message_dic.update({"standard_deviation": ','.join(standard_deviation)})

            if len(part_message_list) > 0 and part_message_list[0].keys().__contains__("window_location"):
                all_message_dic.update({"window_location": part_message_list[0]["window_location"]})

            MyUtils.saveFile(new_image, all_message_dic, MyUtils.saveJoint_addr_tem)
            images_list.append(new_image)
            dir_messages_list.append(all_message_dic)
            part_messages_list.append(part_message_list)

        return images_list,dir_messages_list,part_messages_list

    def absoluteRadiate(self,image,message,all_message):
        tem = np.zeros(image.shape, dtype="float64")
        if len(image.shape)>2 and image.shape[2]>1:
            for j in range(image.shape[2]): #数据立方体各通道分别辐射校正
                calibration_parameter = message[j]["absolute_radiation_calibration_parameter(W*m**-2*sr**-1*DN**-1)"]
                tem[:,:,j] = image[:,:,j]*float(calibration_parameter)

        else: # 单一通道图像
            calibration_parameter = message["absolute_radiation_calibration_parameter(W*m**-2*sr**-1*DN**-1)"]
            tem[:, :] = image[:, :] * float(calibration_parameter)

        all_message.update({"product_id": all_message["product_id"][:-4] + "-f.raw"})
        all_message.update({"absoluteRadiateCorrect": "True"})
        MyUtils.saveFile(tem, all_message, MyUtils.saveJoint_addr_tem)
        return tem,message,all_message

    def run(self):
        try:
            # 按照场景先进行初步分类
            dic, sciene_list=self.sceneClassify()

            images_list_j=[]
            messages_list_j=[]
            if self.batchDic["jointCheck"] and not self.batchDic["combineCheck"]:  # 拼接
                images_list_j, messages_list_j = self.jointImage(dic)

            images_list_c = []
            messages_list_c = []
            part_messages_list_c = []
            if self.batchDic["combineCheck"] and not self.batchDic["jointCheck"]:  # 合成
                images_list_c, messages_list_c, part_messages_list_c = self.combineImage(dic)

            images_list_jc = []
            messages_list_jc = []
            part_messages_list_jc = []
            if self.batchDic["jointCheck"] and self.batchDic["combineCheck"]:  # 合成，拼接
                images_list_jc, messages_list_jc, part_messages_list_jc = self.autoJointCombine()

            if self.batchDic["geometryCheck"]: # 几何校正
                if self.batchDic["geometryCorrectSlect"] == 21 : # 使用参数进行校正
                    for i in range(len(images_list_c)):
                        images_list_c[i], messages_list_c[i] = self.geometryCorrect(images_list_c[i], messages_list_c[i])
                    for i in range(len(images_list_jc)):
                        images_list_jc[i], messages_list_jc[i] = self.geometryCorrect(images_list_jc[i], messages_list_jc[i])

            if self.batchDic["colorCheck"]:  # 色彩校正
                if self.batchDic["colorCorrectSlect"]==11: #伪彩色合成
                    for i in range(len(images_list_c)):
                        images_list_c[i], part_messages_list_c[i],messages_list_c[i] = self.falseColor(images_list_c[i], part_messages_list_c[i],messages_list_c[i])
                    for i in range(len(images_list_jc)):
                        images_list_jc[i], part_messages_list_jc[i],messages_list_jc[i] = self.falseColor(images_list_jc[i], part_messages_list_jc[i],messages_list_jc[i])


            if self.batchDic["spectrumCheck"]: # 光谱校正
                if self.batchDic["wavelengthSortCheck"]: #光谱排序
                    for i in range(len(images_list_c)): # 图像集合中所有多光谱图像第1,2通道交换位置
                        images_list_c[i],messages_list_c[i],part_messages_list_c[i]= self.wavelengthSort(images_list_c[i],messages_list_c[i],part_messages_list_c[i])

                    for i in range(len(images_list_jc)):
                        images_list_jc[i], messages_list_jc[i] ,part_messages_list_jc[i]= self.wavelengthSort(images_list_jc[i], messages_list_jc[i],part_messages_list_jc[i])


            if self.batchDic["radiateCheck"]: #辐射校正
                if self.batchDic["absoluteRadiateCheck"]: #绝对辐射校正
                    for i in range(len(images_list_j)):
                        images_list_j[i], messages_list_j[i],_= self.absoluteRadiate(images_list_j[i], messages_list_j[i],messages_list_j[i])

                    for i in range(len(images_list_c)):
                        images_list_c[i], part_messages_list_c[i],messages_list_c[i] = self.absoluteRadiate(images_list_c[i], part_messages_list_c[i],messages_list_c[i])

                    for i in range(len(images_list_jc)):
                        images_list_jc[i], part_messages_list_jc[i],messages_list_jc[i] = self.absoluteRadiate(images_list_jc[i], part_messages_list_jc[i],messages_list_jc[i])


            if self.batchDic["saveCheck"]: #保存
                if self.batchDic["saveType"] == "raw":
                    if self.batchDic["saveFile"] == "单文件":  # 只保存最终文件
                        for i in range(len(images_list_j)):
                            MyUtils.saveFile(images_list_j[i], messages_list_j[i], self.batchDic["saveDirectory"])
                        for i in range(len(images_list_c)):
                            MyUtils.saveFile(images_list_c[i], messages_list_c[i], self.batchDic["saveDirectory"])
                        for i in range(len(images_list_jc)):
                            MyUtils.saveFile(images_list_jc[i], messages_list_jc[i], self.batchDic["saveDirectory"])

                    if self.batchDic["saveFile"] == "多文件":  # 把分解的文件也进行保存
                        raise Exception("Error")

                if self.batchDic["saveType"] == "jpg":
                    for i in range(len(images_list_c)):
                        filename = messages_list_c[i]["product_id"][:-4] + ".jpg"
                        filepath = os.path.join(MyUtils.saveJoint_addr, filename)
                        MyUtils.save_RGB(filepath, images_list_c[i])
                    for i in range(len(images_list_jc)):
                        filename = messages_list_jc[i]["product_id"][:-4] + ".jpg"
                        filepath = os.path.join(MyUtils.saveJoint_addr, filename)
                        MyUtils.save_RGB(filepath, images_list_jc[i])

                if self.batchDic["saveType"] == "pds4":
                    if self.batchDic["saveFile"] == "单文件":  # 只保存最终文件
                        for i in range(len(images_list_j)):
                            self.saveToPDS4(images_list_j[i], messages_list_j[i])
                        for i in range(len(images_list_c)):
                            self.saveToPDS4(images_list_c[i], messages_list_c[i])
                        for i in range(len(images_list_jc)):
                            self.saveToPDS4(images_list_jc[i], messages_list_jc[i])
                    if self.batchDic["saveFile"] == "多文件":  # 把分解的文件也进行保存
                        raise Exception("Error")

            # 发送信号
            sum_len = len(images_list_j)+len(images_list_c)+len(images_list_jc)
            count = 0
            for i in range(len(images_list_j)):
                count+=1
                process = count/sum_len
                self.finish.emit(images_list_j[i], process*100, messages_list_j[i]["product_id"], messages_list_j[i], messages_list_j,self.batchDic["ToWindowCheck"],"2A")
            for i in range(len(images_list_c)):
                count += 1
                process = count / sum_len
                self.finish.emit(images_list_c[i], process * 100, messages_list_c[i]["product_id"], messages_list_c[i], part_messages_list_c[i],self.batchDic["ToWindowCheck"],"2A")
            for i in range(len(images_list_jc)):
                count += 1
                process = count / sum_len
                self.finish.emit(images_list_jc[i], process * 100, messages_list_jc[i]["product_id"], messages_list_jc[i], part_messages_list_jc[i],self.batchDic["ToWindowCheck"],"2A")

            if sum_len == 0:
                raise Exception("未选择操作！")

        except Exception as e:
            exception = traceback.format_exc()
            self.excepted.emit(exception)  # 将异常发送给UI进程


class Joint_2BThread(QThread): # 和2A文件类似，修改变量名
    finish = pyqtSignal(np.ndarray, int, str, dict, list, bool, str)  # int是进度条完成度，str是窗口标题,dict1,dict2是图像信息,最后一个是文件类型
    excepted = pyqtSignal(str)  # 发送一个异常信号

    def __init__(self, fileNames, paths, batchDic):
        # fileNames是文件名列表
        # paths是路径列表
        # dic —— key:窗口位置+场景名 value:属于该场景某一通道的图片列表
        # className_list "窗口位置+场景名"列表

        super(Joint_2BThread, self).__init__()
        self.fileNames = fileNames
        self.paths = paths
        self.batchDic = batchDic  # 用于存放批处理选项

    def readRaw(self, filepath):
        MyUtils.readXML(filepath + 'L', fileType="2B")
        dir_message = MyUtils.dir_message_2B
        band = 1
        mode = '<u2'
        source = filepath
        width = int(dir_message["Sample"])
        height = int(dir_message["Line"])
        image = MyUtils.read_type(filepath, width, height, band, "2B", mode)
        description = dir_message
        return image, description, source

    def sceneClassify(self):
        # 将窗口图像集合按照场景分类
        sciene_list = []
        dic = {}  # key:窗口位置+场景名+序列号 value:属于该场景某一通道的图片列表
        for text in self.fileNames:
            string = text[30:36] + text[-10:-5]  # 场景名+序列号
            if not sciene_list.__contains__(string):
                sciene_list.append(string)
        for className in sciene_list:
            dic.update({className: []})
        for text in self.fileNames:
            string = text[30:36] + text[-10:-5]  # 场景名+序列号
            dic[string].append(text)
        return dic, sciene_list

    def wavelengthSort(self, image, message, partMessage):
        tem = image[:, :, 0].copy()
        image[:, :, 0] = image[:, :, 1]
        image[:, :, 1] = tem

        # 通道信息也排序
        tem_partmessage = partMessage[0].copy()
        partMessage[0] = partMessage[1]
        partMessage[1] = tem_partmessage

        # 更新波段
        band = message["Band"]
        central_wavelength_list = []
        for j in range(int(band)):
            central_wavelength_list.append(MyUtils.CentralWavelength_sort[j])
        message.update({"central_wavelength": ','.join(central_wavelength_list)})
        message.update({"wavelengthSort": "True"})
        message.update({"product_id": message["product_id"][:-4] + "-p.raw"})
        MyUtils.saveFile(image, message, MyUtils.saveJoint_addr_tem)
        return image, message, partMessage

    def geometryCorrect(self, image, message):
        new_image = MyUtils.geoCorrect(image, MyUtils.translateTform_addr, message, 31)
        message.update({"register": "True"})
        message.update({"product_id": message["product_id"][:-4] + "-j.raw"})
        MyUtils.saveFile(new_image, message, MyUtils.saveJoint_addr_tem)
        return new_image, message

    def falseColor(self, new_image, message_list,all_message):
        tem = np.zeros((new_image.shape[0], new_image.shape[1], 3), dtype=type(new_image.flatten()[0]))
        tem[:, :, 0] = new_image[:, :, 2]  # RGB 分别为 3 1 2 通道
        tem[:, :, 1] = new_image[:, :, 0]
        tem[:, :, 2] = new_image[:, :, 1]
        # 更新彩色通道信息
        tem_message = []
        tem_message.append(message_list[2])
        tem_message.append(message_list[0])
        tem_message.append(message_list[1])

        all_message.update({"Color": "True"})
        all_message.update({"product_id": all_message["product_id"][:-4] + "-c.raw"})
        all_message.update({"Band": str(len(tem_message))})
        MyUtils.saveFile(tem, all_message, MyUtils.saveJoint_addr_tem)
        return tem, tem_message,all_message

    def saveToPDS4(self, new_image, message_list):
        def isValid(string):
            validList = ["[", "]", "'"]
            if validList.__contains__(string):
                return False
            else:
                return True

        sources = message_list["source"].split(",")
        template = "".join(filter(isValid, sources[0]))
        template = template + "L"
        outname = message_list["product_id"][:-4] + ".xml"
        outname = os.path.join(MyUtils.saveJoint_addr, outname)
        filename = os.path.join(MyUtils.saveJoint_addr_tem, message_list["product_id"])
        dataType = type(new_image.flatten()[0])
        MyUtils.save_PDS4(template, outname, filename, dataType)

    def jointImage(self, dic1):
        images_list = []  # 用于保存图像列表
        messages_list = []  # 用于保存图像信息字典的列表
        for key, values in dic1.items():  # key是场景名，values是该场景的图像名
            for bandCode in range(len(MyUtils.BandCode)):
                file_list = values.copy()
                for file in file_list[::-1]:  # 逆序遍历
                    if int(file[20:21]) - 1 == bandCode:  # 寻找同一个场景同一个通道的图像
                        continue
                    file_list.remove(file)  # 过滤文件
                # 拼接
                new_image = np.zeros((2048, 2048, 1), dtype='uint16')
                helpList_x = []
                helpList_y = []
                # 添加图像信息
                part_message = {}
                source_list = []  # 用于保存图像来源
                for j, file in enumerate(file_list):
                    filePath = self.paths[self.fileNames.index(file)]
                    images, description, source = self.readRaw(filePath)
                    source_list.append(source)
                    if j == 0:
                        part_message = description.copy()
                    location = description["window_location"]
                    location = location.strip("(")
                    location = location.strip(")")
                    ranges = location.split(",")
                    loc_x = int(ranges[0]) - 1
                    loc_y = int(ranges[1]) - 1
                    new_image[loc_x:loc_x + MyUtils.height_2B, loc_y:loc_y + MyUtils.width_2B, 0] = images[:, :]
                    helpList_x.append(loc_x)
                    helpList_x.append(loc_x + MyUtils.height_2B)
                    helpList_y.append(loc_y)
                    helpList_y.append(loc_y + MyUtils.width_2B)
                # 图片主体范围
                x_min = min(helpList_x)
                x_max = max(helpList_x)
                y_min = min(helpList_y)
                y_max = max(helpList_y)
                new_image = new_image[x_min:x_max, y_min:y_max, :].copy()
                # 更新product信息
                part_message.update(
                    {"window_location": "{0}:{1},{2}:{3}".format(str(x_min), str(x_max), str(y_min), str(y_max))})
                # 更新product_id信息,场景+位置+通道+J-2B
                part_message.update(
                    {"product_id": part_message["product_id"][0:-5] + "-" + str(x_min) + "_" + str(x_max) + "_" + str(
                        y_min) + "_" + str(y_max) + "-J-2B.raw"})
                # 更新source
                part_message.update({"source": str(source_list)})
                MyUtils.saveFile(new_image, part_message, MyUtils.saveJoint_addr_tem)
                images_list.append(new_image)
                messages_list.append(part_message)
        return images_list, messages_list

    def combineImage(self, dic1):
        images_list = []  # 用于保存图像列表
        dir_messages_list = []  # 用于保存图像信息字典的列表
        part_messages_list = []
        for i, (key, values) in enumerate(dic1.items()):
            location_list = []  # 窗口位置列表
            for value in values:
                location = value[22:24]
                if not location_list.__contains__(location):
                    location_list.append(location)
            for location in location_list:
                file_list = values.copy()
                for file in file_list[::-1]:  # 逆序遍历
                    if file[22:24] == location:  ## 判断文件的名
                        continue
                    file_list.remove(file)  # 过滤文件
                # 同一位置通道合成
                new_image = np.zeros((MyUtils.height_2B, MyUtils.width_2B, len(file_list)), dtype='uint16')
                all_message = {}  # 保存多光谱图像整体信息
                part_message = []  # 用于保存多光谱通道信息
                source_list = []  # 用于保存图像来源
                central_wavelength_list = []  # 用于保存中心波长列表
                # 读取窗口文件并合成
                for j, file in enumerate(file_list):
                    filePath = self.paths[self.fileNames.index(file)]
                    images, description, source = self.readRaw(filePath)
                    source_list.append(source)
                    if j == 0:
                        all_message = description.copy()
                    part_message.append(description)
                    central_wavelength_list.append(description["central_wavelength"])
                    new_image[:, :, j] = images[:, :]
                # 更新product信息
                x = (int(location) - 1) // 8  # 此处的8是原图像2048*2048被划分为8*8块位置
                y = (int(location) - 1) % 8
                all_message.update({"window_location": "{0}:{1},{2}:{3}".format(str(x * MyUtils.height_2B),
                                                                                str((x + 1) * MyUtils.height_2B),
                                                                                str(y * MyUtils.width_2B),
                                                                                str((y + 1) * MyUtils.width_2B))})
                # 更新product_id信息,场景+位置+通道+C-2B
                all_message.update({"product_id": all_message["product_id"][0:-5] + "-C-2B.raw"})
                # 更新source
                all_message.update({"source": str(source_list)})
                # 更新Band波段数
                all_message.update({"Band": str(len(file_list))})
                # 更新central_wavelength
                all_message.update({"central_wavelength": ','.join(central_wavelength_list)})
                MyUtils.saveFile(new_image, all_message, MyUtils.saveJoint_addr_tem)
                images_list.append(new_image)
                dir_messages_list.append(all_message)
                part_messages_list.append(part_message)
        return images_list, dir_messages_list, part_messages_list

    def autoJointCombine(self):
        images_list = []  # 用于保存图像列表
        dir_messages_list = []  # 用于保存图像信息字典的列表
        part_messages_list = []
        MyUtils.readXML(self.paths[0] + 'L', fileType="2B")  # 读取了第一个文件的头信息
        MyUtils.width_2B = int(MyUtils.dir_message_2B["Sample"])
        MyUtils.height_2B = int(MyUtils.dir_message_2B["Line"])
        MyUtils.mode_2B = '<u2'

        # 将窗口图像集合按照场景分类
        sciene_list = []
        dic = {}  # key:窗口位置+场景名+序列号 value:属于该场景某一通道的图片列表
        for text in self.fileNames:
            string = text[22:24] + text[30:36] + text[-10:-5]  # 场景名+序列号
            if not sciene_list.__contains__(string):
                sciene_list.append(string)
        for className in sciene_list:
            dic.update({className: []})
        for text in self.fileNames:
            string = text[22:24] + text[30:36] + text[-10:-5]  # 场景名+序列号
            dic[string].append(text)

        dic2 = {}  # key代表窗口位置+场景名，value代表该场景窗口位置的数据立方体
        messages = {}
        sci_list = []  # 存放场景名列表
        for key, values in dic.items():
            if not sci_list.__contains__(key[2:]):
                sci_list.append(key[2:])
            band = len(values)  # 获取光谱通道数
            new_image = np.zeros((MyUtils.height_2B, MyUtils.height_2B, band), dtype='uint16')
            values = sorted(values)  # 将通道按顺序排列
            tems = []
            for i, v in enumerate(values):  # 通道叠加
                ind = self.fileNames.index(v)
                path = self.paths[ind]
                image = MyUtils.read_2B(path, MyUtils.width_2B, MyUtils.height_2B, MyUtils.mode_2B)
                MyUtils.readXML(path + 'L', fileType="2B")
                tem = MyUtils.dir_message_2B.copy()
                tem.update({"product_id": self.fileNames[ind]})  # 将product_id修改为文件名
                tems.append(tem)
                new_image[:, :, i] = image
            dic2.update({key: new_image})
            messages.update({key: tems})

        dic3 = {}  # key代表场景名，values是该场景的数据立方体列表
        dic3_dir = {}  # key代表场景名，values是该场景的数据立方体的窗口位置列表
        messages3 = {}  # 用于存放信息，key代表场景名，values是该场景通道信息集合的位置列表（value是二维列表）
        for sci in sci_list:  # 初始化dic3
            dic3.update({sci: []})
            dic3_dir.update({sci: []})
            messages3.update({sci: []})
        for sci_dir, image in dic2.items():  # 将数据立方体按照场景分类
            sci = sci_dir[2:]
            dic3[sci].append(image)  # 场景i对应数据立方体列表
            dic3_dir[sci].append(sci_dir[0:2])  # 场景i对应数据立方体位置
        for sci_dir, message in messages.items():
            sci = sci_dir[2:]
            messages3[sci].append(message)

        for i, (sci, images) in enumerate(dic3.items()):  # 遍历dic3中的图像对应关系
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
                y * MyUtils.width_2B:(y + 1) * MyUtils.width_2B, :] = image[:, :, :]

            x_min = min(helpList_x)
            x_max = max(helpList_x)
            y_min = min(helpList_y)
            y_max = max(helpList_y)
            new_image = new_image[x_min:x_max, y_min:y_max, :].copy()

            source = []
            for j, chanel_mess in enumerate(messages3[sci][0]):  # 用第一个位置的信息更新整幅图像的信息
                arrays = [elem[j] for elem in messages3[sci]]  # arrays是8个通道位置信息列表
                sequence = [array["product_id"] for array in arrays]
                for se in sequence:
                    source.append(self.paths[self.fileNames.index(se)])
                chanel_mess["file_size"] = str((y_max - y_min) * (x_max - x_min) * 8 * 16 / 8)
                chanel_mess["Sample"] = str(y_max - y_min)
                chanel_mess["Line"] = str(x_max - x_min)
                chanel_mess.update({"window_location": "{0}:{1},{2}:{3}".format(x_min, x_max, y_min, y_max)})
                chanel_mess.update({"Band_Number": str(j + 1)})
                chanel_mess.update({"Band": str(len(messages3[sci][0]))})
                chanel_mess.update({"sequence": str(sequence)})
                # if j == 0:
                #     all_message_dic.update(chanel_mess)
                part_message_list.append(chanel_mess)

            # 更新信息
            all_message_dic.update({"SCI": sci, "product_level": "2B", "source": str(source)})
            all_message_dic.update({"Band": part_message_list[0]["Band"]})
            all_message_dic.update({"product_id": part_message_list[0]["product_id"][0:-3] +
                                                  part_message_list[0]["Sample"] + "_" + part_message_list[0][
                                                      "Line"] + "-JC_2B.raw"})

            # 在保存的多光谱文件中添加保存格外的信息，此信息在list_message中有
            wavelengths = []  # 波长
            absolute_radiation_calibration_parameter = []  # 辐射校正系数
            exposure_time = []  # 曝光时间
            full_width_half_max = []
            maximum = []
            minimum = []
            mean = []
            standard_deviation = []
            for d in part_message_list:
                if d.keys().__contains__("central_wavelength"):
                    wavelengths.append(d["central_wavelength"])
                if d.keys().__contains__("absolute_radiation_calibration_parameter(W*m**-2*sr**-1*DN**-1)"):
                    absolute_radiation_calibration_parameter.append(
                        d["absolute_radiation_calibration_parameter(W*m**-2*sr**-1*DN**-1)"])
                if d.keys().__contains__("exposure_time"):
                    exposure_time.append(d["exposure_time"])
                if d.keys().__contains__("full_width_half_max"):
                    full_width_half_max.append(d["full_width_half_max"])
                if d.keys().__contains__("maximum"):
                    maximum.append(d["maximum"])
                if d.keys().__contains__("minimum"):
                    minimum.append(d["minimum"])
                if d.keys().__contains__("mean"):
                    mean.append(d["mean"])
                if d.keys().__contains__("standard_deviation"):
                    standard_deviation.append(d["standard_deviation"])
            if len(wavelengths) > 0:
                all_message_dic.update({"central_wavelength": ','.join(wavelengths)})
            if len(absolute_radiation_calibration_parameter) > 0:
                all_message_dic.update({"absolute_radiation_calibration_parameter(W*m**-2*sr**-1*DN**-1)": ','.join(
                    absolute_radiation_calibration_parameter)})
            if len(exposure_time) > 0:
                all_message_dic.update({"exposure_time": ','.join(exposure_time)})
            if len(full_width_half_max) > 0:
                all_message_dic.update({"full_width_half_max": ','.join(full_width_half_max)})

            if len(maximum) > 0:
                all_message_dic.update({"maximum": ','.join(maximum)})
            if len(minimum) > 0:
                all_message_dic.update({"minimum": ','.join(minimum)})
            if len(mean) > 0:
                all_message_dic.update({"mean": ','.join(mean)})
            if len(standard_deviation) > 0:
                all_message_dic.update({"standard_deviation": ','.join(standard_deviation)})

            if len(part_message_list) > 0 and part_message_list[0].keys().__contains__("window_location"):
                all_message_dic.update({"window_location": part_message_list[0]["window_location"]})

            MyUtils.saveFile(new_image, all_message_dic, MyUtils.saveJoint_addr_tem)
            images_list.append(new_image)
            dir_messages_list.append(all_message_dic)
            part_messages_list.append(part_message_list)

        return images_list, dir_messages_list, part_messages_list

    def absoluteRadiate(self, image, message,all_message):
        tem = np.zeros(image.shape, dtype="float64")
        if len(image.shape) > 2 and image.shape[2]>1:
            for j in range(image.shape[2]):
                calibration_parameter = message[j]["absolute_radiation_calibration_parameter(W*m**-2*sr**-1*DN**-1)"]
                tem[:, :, j] = image[:, :, j] * float(calibration_parameter)
        else:
            calibration_parameter = message["absolute_radiation_calibration_parameter(W*m**-2*sr**-1*DN**-1)"]
            tem[:, :] = image[:, :] * float(calibration_parameter)

        all_message.update({"product_id": all_message["product_id"][:-4] + "-f.raw"})
        all_message.update({"absoluteRadiateCorrect": "True"})
        MyUtils.saveFile(tem, all_message, MyUtils.saveJoint_addr_tem)
        return tem, message,all_message

    def run(self):
        try:
            # 按照场景先进行初步分类
            dic, sciene_list = self.sceneClassify()

            images_list_j = []
            messages_list_j = []
            if self.batchDic["jointCheck"] and not self.batchDic["combineCheck"]:  # 拼接
                images_list_j, messages_list_j = self.jointImage(dic)

            images_list_c = []
            messages_list_c = []
            part_messages_list_c = []
            if self.batchDic["combineCheck"] and not self.batchDic["jointCheck"]:  # 合成
                images_list_c, messages_list_c, part_messages_list_c = self.combineImage(dic)

            images_list_jc = []
            messages_list_jc = []
            part_messages_list_jc = []
            if self.batchDic["jointCheck"] and self.batchDic["combineCheck"]:  # 合成，拼接
                images_list_jc, messages_list_jc, part_messages_list_jc = self.autoJointCombine()

            if self.batchDic["geometryCheck"]:  # 几何校正
                if self.batchDic["geometryCorrectSlect"] == 21:  # 使用参数进行校正
                    for i in range(len(images_list_c)):
                        images_list_c[i], messages_list_c[i] = self.geometryCorrect(images_list_c[i],
                                                                                    messages_list_c[i])
                    for i in range(len(images_list_jc)):
                        images_list_jc[i], messages_list_jc[i] = self.geometryCorrect(images_list_jc[i],
                                                                                      messages_list_jc[i])

            if self.batchDic["colorCheck"]:  # 色彩校正
                if self.batchDic["colorCorrectSlect"] == 11:  # 伪彩色合成
                    for i in range(len(images_list_c)):
                        images_list_c[i], part_messages_list_c[i],messages_list_c[i] = self.falseColor(images_list_c[i],
                                                                                    part_messages_list_c[i],messages_list_c[i])

                    for i in range(len(images_list_jc)):
                        images_list_jc[i], part_messages_list_jc[i],messages_list_jc[i] = self.falseColor(images_list_jc[i],
                                                                                      part_messages_list_jc[i],messages_list_jc[i])

            if self.batchDic["spectrumCheck"]:  # 光谱校正
                if self.batchDic["wavelengthSortCheck"]:  # 光谱排序
                    for i in range(len(images_list_c)):  # 图像集合中所有多光谱图像第1,2通道交换位置
                        images_list_c[i], messages_list_c[i], part_messages_list_c[i] = self.wavelengthSort(
                            images_list_c[i], messages_list_c[i], part_messages_list_c[i])

                    for i in range(len(images_list_jc)):
                        images_list_jc[i], messages_list_jc[i], part_messages_list_jc[i] = self.wavelengthSort(
                            images_list_jc[i], messages_list_jc[i], part_messages_list_jc[i])

            if self.batchDic["radiateCheck"]:  # 辐射校正
                if self.batchDic["absoluteRadiateCheck"]:  # 绝对辐射校正
                    for i in range(len(images_list_j)):
                        images_list_j[i], messages_list_j[i],_= self.absoluteRadiate(images_list_j[i],
                                                                                    messages_list_j[i],messages_list_j[i])

                    for i in range(len(images_list_c)):
                        images_list_c[i], part_messages_list_c[i],messages_list_c[i] = self.absoluteRadiate(images_list_c[i],
                                                                                         part_messages_list_c[i],messages_list_c[i])

                    for i in range(len(images_list_jc)):
                        images_list_jc[i], part_messages_list_jc[i],messages_list_jc[i] = self.absoluteRadiate(images_list_jc[i],
                                                                                           part_messages_list_jc[i],messages_list_jc[i])

            if self.batchDic["saveCheck"]:  # 保存
                if self.batchDic["saveType"] == "raw":
                    if self.batchDic["saveFile"] == "单文件":  # 只保存最终文件
                        for i in range(len(images_list_j)):
                            MyUtils.saveFile(images_list_j[i], messages_list_j[i], self.batchDic["saveDirectory"])
                        for i in range(len(images_list_c)):
                            MyUtils.saveFile(images_list_c[i], messages_list_c[i], self.batchDic["saveDirectory"])
                        for i in range(len(images_list_jc)):
                            MyUtils.saveFile(images_list_jc[i], messages_list_jc[i], self.batchDic["saveDirectory"])

                    if self.batchDic["saveFile"] == "多文件":  # 把分解的文件也进行保存
                        raise Exception("Error")

                if self.batchDic["saveType"] == "jpg":
                    for i in range(len(images_list_c)):
                        filename = messages_list_c[i]["product_id"][:-4] + ".jpg"
                        filepath = os.path.join(MyUtils.saveJoint_addr, filename)
                        MyUtils.save_RGB(filepath, images_list_c[i])
                    for i in range(len(images_list_jc)):
                        filename = messages_list_jc[i]["product_id"][:-4] + ".jpg"
                        filepath = os.path.join(MyUtils.saveJoint_addr, filename)
                        MyUtils.save_RGB(filepath, images_list_jc[i])

                if self.batchDic["saveType"] == "pds4":
                    if self.batchDic["saveFile"] == "单文件":  # 只保存最终文件
                        for i in range(len(images_list_j)):
                            self.saveToPDS4(images_list_j[i], messages_list_j[i])
                        for i in range(len(images_list_c)):
                            self.saveToPDS4(images_list_c[i], messages_list_c[i])
                        for i in range(len(images_list_jc)):
                            self.saveToPDS4(images_list_jc[i], messages_list_jc[i])
                    if self.batchDic["saveFile"] == "多文件":  # 把分解的文件也进行保存
                        raise Exception("Error")

            # 发送信号
            sum_len = len(images_list_j) + len(images_list_c) + len(images_list_jc)
            count = 0
            for i in range(len(images_list_j)):
                count += 1
                process = count / sum_len
                self.finish.emit(images_list_j[i], process * 100, messages_list_j[i]["product_id"], messages_list_j[i],
                                 messages_list_j, self.batchDic["ToWindowCheck"], "2B")
            for i in range(len(images_list_c)):
                count += 1
                process = count / sum_len
                self.finish.emit(images_list_c[i], process * 100, messages_list_c[i]["product_id"], messages_list_c[i],
                                 part_messages_list_c[i], self.batchDic["ToWindowCheck"], "2B")
            for i in range(len(images_list_jc)):
                count += 1
                process = count / sum_len
                self.finish.emit(images_list_jc[i], process * 100, messages_list_jc[i]["product_id"],
                                 messages_list_jc[i], part_messages_list_jc[i], self.batchDic["ToWindowCheck"], "2B")

            if sum_len == 0:
                raise Exception("未选择操作！")

        except Exception as e:
            exception = traceback.format_exc()
            self.excepted.emit(exception)  # 将异常发送给UI进程
