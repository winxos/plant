#!/usr/bin/env python
# -- coding: utf-8 --

import os.path
import sys
print(os.environ)
#os imigrade
if os.path.exists("/opt/MVS/Samples/armhf"):
    #can't use relative path
    sys.path.append("/opt/MVS/Samples/armhf/Python/MvImport")
elif os.path.exists("/opt/MVS/Samples/aarch64"):
    sys.path.append("/opt/MVS/Samples/aarch64/Python/MvImport")
else:
    print("camara driver package is missing, system exit.")
    exit

import time
import json
import threading
import cv2
import numpy as np
from ctypes import *
import datetime
from time import sleep

from gps import gps_init, gpsInfo
from inout import io_init, btns
from filenum import get_cur_num
from sensor import sensor_init,sensorInfo
from cam import cam_init, camInfo
from printer import print_info

save_path = "/home/pi/Desktop/data/"

if not os.path.exists(save_path):
    os.makedirs(save_path)

# first need to set the cam image format to rgb8 24bit, default is yuv 16bit
# img_w=3072
# img_h=2048
SCREEN_WIDTH=800
SCREEN_HEIGHT=480

def data_save(file):
    cv2.imwrite(save_path + file + ".jpg", camInfo["raw"])
    j = {}
    j["device_id"] = sensorInfo["cpuid"]
    j["record_time"] = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    j["east"] = gpsInfo["east"]
    j["north"] = gpsInfo["north"]
    j["temperature(C)"] = sensorInfo["temp"]
    j["humidity(%)"] = sensorInfo["humid"]
    j["image_name"] = file + ".jpg"
    with open("%s%s.txt"%(save_path,file),"w") as f:
        json.dump(j, f, indent=2)

def app_init():
    io_init()
    gps_init()
    sensor_init()
    cam_init()
#opencv转换显示
def work_thread():
    NORTH_Y = 150
    EAST_Y = 200
    TEMP_Y = 250
    HUMID_Y = 300
    INFO_Y = 300
    cur_num = get_cur_num()
    cv2.namedWindow("preview", cv2.WINDOW_NORMAL)
    # cv2.resizeWindow("preview", 800, 480)
    cv2.setWindowProperty("preview",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN) #fullscreen
    while True:
        preview = np.zeros((SCREEN_HEIGHT,SCREEN_WIDTH, 3), np.uint8)
        file = '%s%04d'%(datetime.datetime.now().strftime("%Y%m%d"),cur_num)
        cv2.putText(preview, file, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0xff, 0xff, 0xff), 2)

        if sensorInfo["error"].is_set():
            cv2.putText(preview, ' SENSOR ERR', (500, TEMP_Y), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0x00, 0x00, 0xcc), 2)
        else:
            cv2.putText(preview, ' TEMP:%.1f C'%sensorInfo["temp"], (500, TEMP_Y), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 0xcc, 0x99), 2)
            cv2.putText(preview, 'Humid:%.1f %%'%sensorInfo["humid"], (500, HUMID_Y), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 0xcc, 0x99), 2)
        if gpsInfo["error"].is_set():
            cv2.putText(preview, '     GPS ERR', (500, NORTH_Y), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0x00, 0x00, 0xcc), 2)
        else:
            if gpsInfo["connected"]:
                cv2.putText(preview, '    N:%.3f'%gpsInfo["north"], (500, NORTH_Y), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 0xcc, 0x99), 2)
                cv2.putText(preview, '    E:%.3f'%gpsInfo["east"], (500, EAST_Y), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 0xcc, 0x99), 2)
            else:
                cv2.putText(preview, 'GPS MISS', (500, NORTH_Y), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0xff, 0xcc, 0x00), 1)
        if camInfo["error"].is_set():
            cv2.putText(preview, ' CAMERA ERR', (50, INFO_Y), cv2.FONT_HERSHEY_SIMPLEX, 2, (0x00, 0x00, 0xcc), 4)
        else:
            preview =cv2.addWeighted(preview,0.4,camInfo["preview"],0.6,0)
        if btns[1].is_set():
            cv2.putText(preview, 'captured!', (200, INFO_Y), cv2.FONT_HERSHEY_SIMPLEX, 3, (50, 50, 255), 5)
            data_save(file)
            cur_num+=1
            btns[1].clear()
        if btns[2].is_set():
            cv2.putText(preview, 'print!', (200, INFO_Y), cv2.FONT_HERSHEY_SIMPLEX, 3, (50, 50, 255), 5)
            print_info(file, file)
            btns[2].clear()

        cv2.imshow('preview', preview)
        k = cv2.waitKey(500) & 0xff
        if k == ord('q'):
            cv2.destroyAllWindows()
            break

if __name__ == "__main__":
    print("plant system start at %s"%datetime.datetime.now().strftime("%c"))
    app_init()
    hThreadHandle = threading.Thread(target=work_thread)
    hThreadHandle.start()
    hThreadHandle.join()
    print("system exit")
