import os
import re

import numpy as np
import xml.dom.minidom
import scipy.io as sio
import cv2
from osgeo import gdal


class MyUtils:
    fileNames = []
    paths = []
    width_01 = 256  # samples:width lines:height
    height_01 = 256
    band_01 = 144
    mode_01 = '>u2'

    width_2A = 256
    height_2A = 256
    band_2A = 1
    mode_2A = '<u2'

    width_2B = 256
    height_2B = 256
    band_2B = 1
    mode_2B = '<u2'

    width_2CS = 2048
    height_2CS = 2048
    band_2CS = 3
    mode_2CS = '<u2'

    width_other = 2048
    height_other = 2048
    band_other = 3
    mode_other = '<u2'

    dir1 = {"uint8": "u1", "int8": "i1", "uint16": "u2", "int16": "i2", "uint32": "u4", "int32": "i4","float32":"f","float64":"d"} #python的数据类型表示
    ENVIDateType = {"1":"uint8","2":"int16","12":"uint16","3":"int32","13":"uint32","4":"float32","5":"float64"} # envi软件data type=1代表 uint8,2代表uint16
    dir1_re = {v:k for k,v in dir1.items()}
    ENVIDateType_re = {v:k for k,v in ENVIDateType.items()}
    dir2 = {"little-end": "<", "big-end": ">"}

    dir_message_01 = {} # 存放01文件的头文件信息
    list_message_01 = [] # 存放01文件图像块信息
    dir_message_2A = {} # 存放2A文件的头文件信息
    dir_message_2B = {} # 存放2B文件的头文件信息


    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    LAST_DIR = os.path.abspath(os.path.dirname(BASE_DIR))

    cameraParam_addr = None  # 用于存放畸变参数的路径
    translateTform_addr = os.path.join(LAST_DIR,"para\\translateTforms.mat")  # 用于存放仿射变换的路径

    saveJoint_addr = os.path.join(LAST_DIR,"JointImages")
    saveJoint_addr_tem = os.path.join(LAST_DIR, "tem")
    CentralWavelength = ["525nm","480nm","650nm","700nm","800nm","900nm","950nm","1000nm","panchromatic"]
    CentralWavelength_sort = ["480nm","525nm","650nm","700nm","800nm","900nm","950nm","1000nm"]
    BandCode = ["0x11","0x22","0x33","0x44","0x55","0x66","0x77","0x88"]

    # 通过递归的方式获取文件夹下所有的文件路径
    @staticmethod
    def get_all(cwd):
        get_dir = os.listdir(cwd)
        for i in get_dir:
            sub_dir = os.path.join(cwd, i)
            if os.path.isdir(sub_dir):
                MyUtils.get_all(sub_dir)
            else:
                MyUtils.fileNames.append(i)
                MyUtils.paths.append(sub_dir)

    @staticmethod
    def get_fileSize(cwd):
        size = os.path.getsize(cwd)
        if size < 2**10:
            return '%i' % size + 'Byte'
        elif 2**10 <= size < 2**20:
            return '%.1f' % float(size / 2**10) + 'KB'
        elif 2**20 <= size < 2**30:
            return '%.1f' % float(size / 2**20) + 'MB'
        elif 2**30 <= size < 2**40:
            return '%.1f' % float(size / 2**30 ) + 'GB'

    @staticmethod
    def read_01(string,width,height,band,mode='>u2'):
        date_type = MyUtils.dir1_re[mode[1:]]
        imgData = np.fromfile(string, mode, count=-1)
        imgData = np.resize(imgData, (band, height, width))
        img = np.zeros((height, width,band),dtype=date_type)
        for i in range(band):
            # tem = imgData[i,:,:]
            # tem -= tem.min()
            # tem = tem / (tem.max() - tem.min())*1.0
            # tem *= 255
            # img[:,:,i] = np.uint8(tem)
            img[:, :, i] = imgData[i,:,:]
        return img # 三维图片数据

    @staticmethod
    def read_other(string, width, height, band, mode='>u2'):
        date_type = MyUtils.dir1_re[mode[1:]]
        imgData = np.fromfile(string, mode, count=-1)
        imgData = np.resize(imgData, (band,height,width))
        img = np.zeros((height, width, band), dtype=date_type)
        for i in range(band):
            img[:, :, i] = imgData[i,:,:]
        return img  # 三维图片数据

    @staticmethod
    def read_2A(string,width,height,mode='<u2'):
        imgData = np.fromfile(string, mode, count=-1)
        imgData = np.resize(imgData, (height, width))
        # uint16转化为uint8，需要进行像素值归一化操作
        # imgData -= imgData.min()
        # imgData = imgData / (imgData.max() - imgData.min())*1.0
        # imgData *= 255
        # imgData = np.uint8(imgData)
        return imgData

    @staticmethod
    def read_2B(string,width,height,mode='<u2'):
        imgData = MyUtils.read_2A(string,width,height,mode='<u2')
        return imgData

    @staticmethod
    def read_type(string,width,height,band,type,mode):
        if type == "01":
            imgData = MyUtils.read_01(string,width,height,band,mode)
        if type == "2A":
            imgData = MyUtils.read_2A(string,width,height,mode)
        if type == "2B":
            imgData = MyUtils.read_2B(string,width,height,mode)
        return imgData

    @staticmethod
    def normalize(img): # 归一化到0-255
        if len(img.shape)>2:
            image = np.zeros(img.shape,dtype=np.uint8)
            for i in range(img.shape[2]):
                im = img[:,:,i]
                im -= np.min(im)
                try:
                    im = im / (np.max(im) - np.min(im))
                except Exception as e:
                    print("最大值&最小值",np.max(im) ,np.min(im))
                im *= 255
                im = im.astype(np.uint8)
                image[:,:,i] = im
            return image
        else:
            img -= np.min(img)
            try:
                img = img / (np.max(img) - np.min(img))
            except Exception as e:
                print("最大值&最小值", np.max(img), np.min(img))
            img *= 255
            img = img.astype(np.uint8)
            return img

    @staticmethod
    def geoCorrect(image3D,string,part_detalMessage,mode): #使用参数几何矫正
        # string是参数路径
        # part_detalMessage=[]图片单通道信息，每一项都是一个字典
        # image3D是uint16多光谱图像
        # mode表示填充方式
        mat_Info = sio.loadmat(string)
        addr_list = ["addr1", "addr2", "addr3", "addr4", "addr5", "addr6","addrD"]
        Torms_list = []
        for addr in addr_list:
            Torms_list.append(mat_Info[addr])
        dataType = type(image3D[0, 0, 0])
        new_image3D = np.zeros((2048, 2048, 8), dtype=dataType)
        if isinstance(part_detalMessage,list):
            if len(part_detalMessage) == 0:
                string = "0:2048,0:2048"
                addr = 7
            else:
                string = part_detalMessage[0]["window_location"]
                if not part_detalMessage[0].keys().__contains__("Defocusing_Compensation_Gear"):
                    addr = 7
                else:
                    addr = int(part_detalMessage[0]["Defocusing_Compensation_Gear"][-1])
        if isinstance(part_detalMessage,dict):
            string = part_detalMessage["window_location"]
            if not part_detalMessage.keys().__contains__("Defocusing_Compensation_Gear"):
                addr = 7
            else:
                addr = int(part_detalMessage["Defocusing_Compensation_Gear"][-1])
        string = string.replace(",", ":")
        ranges = string.split(":")
        for i in range(image3D.shape[2]):
            M = Torms_list[addr - 1][:, 0:2, i]
            M = M.T
            t = int(ranges[0])
            b = 2048 - int(ranges[1])
            l = int(ranges[2])
            r = 2048 - int(ranges[3])
            if mode == 31:
                tem = image3D[:, :, i].copy()
                n_image = cv2.copyMakeBorder(tem,t,b,l,r,cv2.BORDER_REFLECT)
                res = cv2.warpAffine(n_image, M, (2048, 2048),borderMode=cv2.BORDER_REFLECT,flags=cv2.INTER_CUBIC)
            else:
                n_image = cv2.copyMakeBorder(image3D[:, :, i], t, b, l, r,cv2.BORDER_CONSTANT)
                res = cv2.warpAffine(n_image, M, (2048, 2048), borderMode=cv2.BORDER_CONSTANT, flags=cv2.INTER_CUBIC)

            new_image3D[:, :, i] = res
        new_image3D = new_image3D[int(ranges[0]):int(ranges[1]), int(ranges[2]):int(ranges[3]),:].copy()
        return new_image3D

    @staticmethod
    def saveFile(image,message_dic,dir_path):
        dataType = type(image.flatten()[0])
        if len(image.shape)>2:
            bsqImage = np.zeros((image.shape[2], image.shape[0],image.shape[1]),dtype=dataType) #转变为bsq
            for i in range(image.shape[2]):
                bsqImage[i,:,:] = image[:,:,i]
        else:
            bsqImage = image
        dataType = str(dataType)
        datatype = dataType[dataType.find(".") + 1:-2]
        dataNum = MyUtils.ENVIDateType_re[datatype]  # 将类型转换为ENVI的数字表示
        # 确定保存的文件名
        filename = os.path.join(dir_path,message_dic["product_id"])
        bsqImage.tofile(filename)
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
        h9 = 'data type = ' + dataNum  # 数据格式
        h10 = 'interleave = bsq'  # 存储格式
        h11 = 'sensor type = Unknown'
        h12 = 'byte order = 0'
        if not message_dic.keys().__contains__("central_wavelength"):
            h13 = 'wavelength units = Unknown'
        else:
            h13 = 'wavelength = {'+message_dic["central_wavelength"]+'}'
        h = [h1, h2, h3, h4, h5, h6, h7, h8, h9, h10, h11, h12, h13]
        doc = open(filename[:-4]+".hdr", 'w')
        for i in range(len(h)):
            print(h[i], end='\n', file=doc)
            # print('\n', end='', file=doc)
        doc.close()

    @staticmethod
    def save_RGB(filename,image3D):
        new_image = MyUtils.normalize(image3D)
        new_image = cv2.cvtColor(new_image, cv2.COLOR_RGB2BGR)
        cv2.imwrite(filename, new_image)

    @staticmethod
    def save_PDS4(templePath,outname,filename,dataType):
        gdalType = gdal.GDT_UInt16
        dataType = str(dataType)
        if dataType == "<class 'numpy.float64'>":
            gdalType = gdal.GDT_Float64
        if dataType == "<class 'numpy.uint8'>":
            gdalType = gdal.GDT_Byte
        gdal.Translate(outname, filename, format='PDS4', creationOptions=[
            'TEMPLATE='+templePath],
                       outputType=gdalType)

    @staticmethod #用于解析PDS4工具箱传回的json文件
    def dict_generator(indict, pre=None):
        pre = pre[:] if pre else []
        if isinstance(indict, dict):
            for key, value in indict.items():
                if isinstance(value, dict):
                    if len(value) == 0:
                        yield pre + [key, '{}']
                    else:
                        for d in MyUtils.dict_generator(value, pre + [key]):
                            yield d
                elif isinstance(value, list):
                    if len(value) == 0:
                        yield pre + [key, '[]']
                    else:
                        for v in value:
                            for d in MyUtils.dict_generator(v, pre + [key]):
                                yield d
                elif isinstance(value, tuple):
                    if len(value) == 0:
                        yield pre + [key, '()']
                    else:
                        for v in value:
                            for d in MyUtils.dict_generator(v, pre + [key]):
                                yield d
                else:
                    yield pre + [key, value]
        else:
            yield indict

    @staticmethod
    def readXML(path,fileType="01"):
        # 打开xml文档
        dom = xml.dom.minidom.parse(path)
        # 得到文档元素对象
        root = dom.documentElement
        if fileType=="01":
            # 1.获取标签
            label_fileNames = root.getElementsByTagName("file_name")
            label_fileName_createTimes = root.getElementsByTagName("creation_date_time")
            label_fileSizes = root.getElementsByTagName("file_size")
            label_records = root.getElementsByTagName("records")

            label_instrument_names = root.getElementsByTagName("instrument_name")
            label_instrument_ids = root.getElementsByTagName("instrument_id")
            label_sequence_ids = root.getElementsByTagName("sequence_id")
            label_Axis_Array = root.getElementsByTagName("Axis_Array")

            MyUtils.dir_message_01.update({"file_name":label_fileNames[0].firstChild.data,
                         "creation_date_time":label_fileName_createTimes[0].firstChild.data,
                         "file_size":label_fileSizes[0].firstChild.data,
                         "records" : label_records[0].firstChild.data,
                         "instrument_name":label_instrument_names[0].firstChild.data,
                         "instrument_id": label_instrument_ids[0].firstChild.data,
                         "sequence_id" :label_sequence_ids[0].firstChild.data,
                         "Time":label_Axis_Array[0].getElementsByTagName("elements")[0].firstChild.data,
                         "Line":label_Axis_Array[1].getElementsByTagName("elements")[0].firstChild.data,
                         "Sample":label_Axis_Array[2].getElementsByTagName("elements")[0].firstChild.data
            })
            messageFile = path[:-1]
            messageFile = messageFile.replace("SCI","AUX")
            file = open(messageFile)
            while 1:
                lines = file.readlines()
                if not lines:
                    break
                for i,line in enumerate(lines):
                    strs = re.split(r"[ ]+", line)
                    imageMessage = {}
                    imageMessage.update({"sequence" : str(i),
                                         "Time":strs[0],
                                         "Rover_Pitch":strs[1],
                                         "Rover_Yaw":strs[3],
                                         "Mast_Roll":strs[4],
                                         "Mast_Pitch":strs[5],
                                         "Mast_Yaw":strs[6],
                                         "Image_Mode" : strs[7],
                                         "window_location" : strs[8],
                                         "Compress_Mode" : strs[9],
                                         "Compress_Ratio" : strs[10],
                                         "Band_Number" : strs[11],
                                         "Exposure_Time": strs[12],
                                         "Defocusing_Compensation_Gear" : strs[13],
                                         "MSCam_Temperature" : strs[14],
                                         "Exposure_Mode" : strs[15],
                                         "Focusing_Mode" : strs[16],
                                         "Frame_Count":strs[17],
                                         "Quality_Information":strs[18].strip()
                                         })
                    MyUtils.list_message_01.append(imageMessage)
            file.close()

        if fileType == "2A":

            label_product_ids = root.getElementsByTagName("product_id")
            label_product_levels = root.getElementsByTagName("product_level")
            label_instrument_names = root.getElementsByTagName("instrument_name")
            label_instrument_ids = root.getElementsByTagName("instrument_id")
            label_sequence_ids = root.getElementsByTagName("sequence_id")


            label_Work_Mode_Parms = root.getElementsByTagName("Work_Mode_Parm")
            label_image_mode = label_Work_Mode_Parms[0].getElementsByTagName("image_mode")
            label_sample_interval = label_Work_Mode_Parms[0].getElementsByTagName("sample_interval")
            label_window_location = label_Work_Mode_Parms[0].getElementsByTagName("window_location")
            label_compress_mode = label_Work_Mode_Parms[0].getElementsByTagName("compress_mode")
            label_compress_ratio = label_Work_Mode_Parms[0].getElementsByTagName("compress_ratio")
            label_exposure_time = label_Work_Mode_Parms[0].getElementsByTagName("exposure_time")
            label_exposure_time_unit = label_exposure_time[0].getAttribute("unit")
            label_MSCcam_temperature = label_Work_Mode_Parms[0].getElementsByTagName("MSCcam_temperature")
            label_MSCcam_temperature_unit =label_MSCcam_temperature[0].getAttribute("unit")
            label_exposure_mode = label_Work_Mode_Parms[0].getElementsByTagName("exposure_mode")
            label_focusing_mode = label_Work_Mode_Parms[0].getElementsByTagName("focusing_mode")


            label_Instrument_Parm = root.getElementsByTagName("Instrument_Parm")
            label_central_wavelength = label_Instrument_Parm[0].getElementsByTagName("central_wavelength")
            label_central_wavelength_unit = label_central_wavelength[0].getAttribute("unit")
            label_full_width_half_max = label_Instrument_Parm[0].getElementsByTagName("full_width_half_max")
            label_full_width_half_max_unit = label_full_width_half_max[0].getAttribute("unit")
            label_focal_length = label_Instrument_Parm[0].getElementsByTagName("focal_length")
            label_focal_length_unit = label_focal_length[0].getAttribute("unit")
            label_pixel_size = label_Instrument_Parm[0].getElementsByTagName("pixel_size")
            label_pixel_size_unit = label_pixel_size[0].getAttribute("unit")



            label_absolute_radiation_calibration_parameter = root.getElementsByTagName("absolute_radiation_calibration_parameter")
            label_absolute_radiation_calibration_parameter_unit = label_absolute_radiation_calibration_parameter[0].getAttribute("unit")



            label_file_size = root.getElementsByTagName("file_size")
            label_Axis_Array = root.getElementsByTagName("Axis_Array")

            label_maximum = root.getElementsByTagName("maximum")
            label_minimum = root.getElementsByTagName("minimum")
            label_mean = root.getElementsByTagName("mean")
            label_standard_deviation = root.getElementsByTagName("standard_deviation")

            MyUtils.dir_message_2A.update({"product_id": label_product_ids[0].firstChild.data,
                         "product_level": label_product_levels[0].firstChild.data,
                         "instrument_name": label_instrument_names[0].firstChild.data,
                         "instrument_id": label_instrument_ids[0].firstChild.data,
                         "sequence_id": label_sequence_ids[0].firstChild.data,
                         "image_mode": label_image_mode[0].firstChild.data,
                         "sample_interval": label_sample_interval[0].firstChild.data,
                         "window_location": label_window_location[0].firstChild.data,
                         "compress_mode": label_compress_mode[0].firstChild.data,
                         "compress_ratio": label_compress_ratio[0].firstChild.data,
                         "exposure_time": label_exposure_time[0].firstChild.data + label_exposure_time_unit,
                         "MSCcam_temperature": label_MSCcam_temperature[
                                                   0].firstChild.data + label_MSCcam_temperature_unit,
                         "exposure_mode": label_exposure_mode[0].firstChild.data,
                         "focusing_mode": label_focusing_mode[0].firstChild.data,
                         "central_wavelength": label_central_wavelength[
                                                   0].firstChild.data + label_central_wavelength_unit,
                         "full_width_half_max": label_full_width_half_max[
                                                    0].firstChild.data + label_full_width_half_max_unit,
                         "focal_length": label_focal_length[0].firstChild.data + label_focal_length_unit,
                         "pixel_size": label_pixel_size[0].firstChild.data + label_pixel_size_unit,
                         "absolute_radiation_calibration_parameter" + "(" + label_absolute_radiation_calibration_parameter_unit + ")":
                             label_absolute_radiation_calibration_parameter[0].firstChild.data,
                         "file_size":label_file_size[0].firstChild.data,
                         "Line": label_Axis_Array[0].getElementsByTagName("elements")[0].firstChild.data,
                         "Sample": label_Axis_Array[1].getElementsByTagName("elements")[0].firstChild.data,
                         "maximum":label_maximum[0].firstChild.data,
                         "minimum":label_minimum[0].firstChild.data,
                         "mean":label_mean[0].firstChild.data,
                         "standard_deviation":label_standard_deviation[0].firstChild.data
                         })
        if fileType == "2B":
            label_product_ids = root.getElementsByTagName("product_id")
            label_product_levels = root.getElementsByTagName("product_level")
            label_instrument_names = root.getElementsByTagName("instrument_name")
            label_instrument_ids = root.getElementsByTagName("instrument_id")
            label_sequence_ids = root.getElementsByTagName("sequence_id")

            label_Work_Mode_Parms = root.getElementsByTagName("Work_Mode_Parm")
            label_image_mode = label_Work_Mode_Parms[0].getElementsByTagName("image_mode")
            label_sample_interval = label_Work_Mode_Parms[0].getElementsByTagName("sample_interval")
            label_window_location = label_Work_Mode_Parms[0].getElementsByTagName("window_location")
            label_compress_mode = label_Work_Mode_Parms[0].getElementsByTagName("compress_mode")
            label_compress_ratio = label_Work_Mode_Parms[0].getElementsByTagName("compress_ratio")
            label_exposure_time = label_Work_Mode_Parms[0].getElementsByTagName("exposure_time")
            label_exposure_time_unit = label_exposure_time[0].getAttribute("unit")
            label_MSCcam_temperature = label_Work_Mode_Parms[0].getElementsByTagName("MSCcam_temperature")
            label_MSCcam_temperature_unit = label_MSCcam_temperature[0].getAttribute("unit")
            label_exposure_mode = label_Work_Mode_Parms[0].getElementsByTagName("exposure_mode")
            label_focusing_mode = label_Work_Mode_Parms[0].getElementsByTagName("focusing_mode")

            label_Instrument_Parm = root.getElementsByTagName("Instrument_Parm")
            label_central_wavelength = label_Instrument_Parm[0].getElementsByTagName("central_wavelength")
            label_central_wavelength_unit = label_central_wavelength[0].getAttribute("unit")
            label_full_width_half_max = label_Instrument_Parm[0].getElementsByTagName("full_width_half_max")
            label_full_width_half_max_unit = label_full_width_half_max[0].getAttribute("unit")
            label_focal_length = label_Instrument_Parm[0].getElementsByTagName("focal_length")
            label_focal_length_unit = label_focal_length[0].getAttribute("unit")
            label_pixel_size = label_Instrument_Parm[0].getElementsByTagName("pixel_size")
            label_pixel_size_unit = label_pixel_size[0].getAttribute("unit")

            label_absolute_radiation_calibration_parameter = root.getElementsByTagName(
                "absolute_radiation_calibration_parameter")
            label_absolute_radiation_calibration_parameter_unit = label_absolute_radiation_calibration_parameter[
                0].getAttribute("unit")

            label_Mast_Rotation_Angle = root.getElementsByTagName("Mast_Rotation_Angle")
            label_Mast_Rotation_Angle_roll = label_Mast_Rotation_Angle[0].getElementsByTagName("roll")
            label_Mast_Rotation_Angle_roll_unit = label_Mast_Rotation_Angle_roll[0].getAttribute("unit")
            label_Mast_Rotation_Angle_pitch = label_Mast_Rotation_Angle[0].getElementsByTagName("pitch")
            label_Mast_Rotation_Angle_pitch_unit = label_Mast_Rotation_Angle_pitch[0].getAttribute("unit")
            label_Mast_Rotation_Angle_yaw = label_Mast_Rotation_Angle[0].getElementsByTagName("yaw")
            label_Mast_Rotation_Angle_yaw_unit = label_Mast_Rotation_Angle_yaw[0].getAttribute("unit")

            label_Rover_Location = root.getElementsByTagName("Rover_Location")
            label_Rover_Location_reference_frame = label_Rover_Location[0].getElementsByTagName("reference_frame")
            label_Rover_Location_longitude = label_Rover_Location[0].getElementsByTagName("longitude")
            label_Rover_Location_longitude_unit = label_Rover_Location_longitude[0].getAttribute("unit")
            label_Rover_Location_latitude = label_Rover_Location[0].getElementsByTagName("latitude")
            label_Rover_Location_latitude_unit = label_Rover_Location_latitude[0].getAttribute("unit")
            label_Rover_Location_altitude = label_Rover_Location[0].getElementsByTagName("altitude")
            label_Rover_Location_altitude_unit = label_Rover_Location_altitude[0].getAttribute("unit")

            label_Rover_Location_xyz = root.getElementsByTagName("Rover_Location_xyz")
            label_Rover_Location_xyz_reference_frame = label_Rover_Location_xyz[0].getElementsByTagName("reference_frame")
            label_Rover_Location_xyz_x = label_Rover_Location_xyz[0].getElementsByTagName("x")
            label_Rover_Location_xyz_y = label_Rover_Location_xyz[0].getElementsByTagName("y")
            label_Rover_Location_xyz_z = label_Rover_Location_xyz[0].getElementsByTagName("z")
            label_Rover_Location_xyz_unit = label_Rover_Location_xyz_x[0].getAttribute("unit")

            # 剩余信息根据后期需要再添加


            label_file_size = root.getElementsByTagName("file_size")
            label_Axis_Array = root.getElementsByTagName("Axis_Array")

            label_maximum = root.getElementsByTagName("maximum")
            label_minimum = root.getElementsByTagName("minimum")
            label_mean = root.getElementsByTagName("mean")
            label_standard_deviation = root.getElementsByTagName("standard_deviation")

            MyUtils.dir_message_2B.update({"product_id": label_product_ids[0].firstChild.data,
                                           "product_level": label_product_levels[0].firstChild.data,
                                           "instrument_name": label_instrument_names[0].firstChild.data,
                                           "instrument_id": label_instrument_ids[0].firstChild.data,
                                           "sequence_id": label_sequence_ids[0].firstChild.data,
                                           "image_mode": label_image_mode[0].firstChild.data,
                                           "sample_interval": label_sample_interval[0].firstChild.data,
                                           "window_location": label_window_location[0].firstChild.data,
                                           "compress_mode": label_compress_mode[0].firstChild.data,
                                           "compress_ratio": label_compress_ratio[0].firstChild.data,
                                           "exposure_time": label_exposure_time[
                                                                0].firstChild.data + label_exposure_time_unit,
                                           "MSCcam_temperature": label_MSCcam_temperature[
                                                                     0].firstChild.data + label_MSCcam_temperature_unit,
                                           "exposure_mode": label_exposure_mode[0].firstChild.data,
                                           "focusing_mode": label_focusing_mode[0].firstChild.data,
                                           "central_wavelength": label_central_wavelength[
                                                                     0].firstChild.data + label_central_wavelength_unit,
                                           "full_width_half_max": label_full_width_half_max[
                                                                      0].firstChild.data + label_full_width_half_max_unit,
                                           "focal_length": label_focal_length[
                                                               0].firstChild.data + label_focal_length_unit,
                                           "pixel_size": label_pixel_size[0].firstChild.data + label_pixel_size_unit,
                                           "absolute_radiation_calibration_parameter" + "(" + label_absolute_radiation_calibration_parameter_unit + ")":
                                               label_absolute_radiation_calibration_parameter[0].firstChild.data,
                                           "file_size": label_file_size[0].firstChild.data,
                                           "Line": label_Axis_Array[0].getElementsByTagName("elements")[
                                               0].firstChild.data,
                                           "Sample": label_Axis_Array[1].getElementsByTagName("elements")[
                                               0].firstChild.data,
                                           "maximum": label_maximum[0].firstChild.data,
                                           "minimum": label_minimum[0].firstChild.data,
                                           "mean": label_mean[0].firstChild.data,
                                           "standard_deviation": label_standard_deviation[0].firstChild.data
                                           })

    @staticmethod
    def readHDR(path):
        keyValues = []
        description = []
        with open(path) as file:
            while True:
                line = file.readline()
                if not line:
                    break
                if line.__contains__("="):
                    keyValues.append(line.strip())
                else:
                    description.append(line.strip())
        dic1 = {}
        for keyValue in keyValues:
            strings = keyValue.split("=")
            dic1.update({strings[0].strip():strings[1].strip()})
        dic2 = {}
        for des in description:
            if des.__contains__(":"):
                strings = des.split(":",1)
                dic2.update(({strings[0].strip():strings[1].strip()}))

        return dic1,dic2 #dic1是头文件信息，dic2是文件描述信息

    @staticmethod
    def del_file(path): #用于清除文件夹子文件
        ls = os.listdir(path)
        for i in ls:
            c_path = os.path.join(path, i)
            if os.path.isdir(c_path):
                MyUtils.del_file(c_path)
            else:
                os.remove(c_path)

    @staticmethod
    def save_file(oldpath,newpath):
        import shutil
        nameList=[]
        def listDir(dirTemp):
            if None == dirTemp:
                return
            if not os.path.exists(dirTemp):
                print("file or directory isn't exist")
                return
            if os.path.isfile(dirTemp):
                nameList.append(dirTemp)
                return
            resultList = os.listdir(dirTemp)  # os.listdir()方法用于返回指定文件夹包含的文件或文件夹的名字的列表
            for fileOrDir in resultList:
                listDir(dirTemp + "\\" + fileOrDir)  # 递归调用，搜查子文件夹下的文件
            return nameList

        list = listDir(oldpath)
        for item in list:
            shutil.copy(item, newpath)  # 将文件复制到设定的文件夹中


if __name__ == '__main__':
    from pds4_tools import pds4_read
    all_detalMessage = {}
    xmlPath = r"D:\MSCam_Processing\test\HX1-Ro_GRAS_MSCam-W-1-28-0001-02_SCI_N_20210625030542_20210625030542_00041_A_J0.xml"
    d = pds4_read(xmlPath, quiet=True)
    images = np.array(d[0].data)
    root = d.label.to_dict()['Product_Observational']  # 读取图像说明文件
    for j in MyUtils.dict_generator(root):
        all_detalMessage.update({'.'.join(j[0:-1]): j[-1]})
    for k,v in all_detalMessage.items():
        print(k,v)