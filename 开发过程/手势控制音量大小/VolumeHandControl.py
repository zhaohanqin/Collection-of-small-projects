# 改进后的手势音量控制程序（支持远近）
import cv2
import time
import numpy as np
import HandTrackingModule as htm
import math
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

wCam, hCam = 1080, 720#设置图像的分辨率
cap = cv2.VideoCapture(0)#初始化摄像头
cap.set(3, wCam)#设置摄像头宽度
cap.set(4, hCam)#设置摄像头高度
pTime = 0#初始化上一帧时间

detector = htm.handDetector(detectionCon=0.7)#初始化手部检测器

devices = AudioUtilities.GetSpeakers()#获取音频设备
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)#激活音频设备
volume = cast(interface, POINTER(IAudioEndpointVolume))#获取音频设备
volRange = volume.GetVolumeRange()#获取音量范围
minVol, maxVol = volRange[0], volRange[1]#获取最小音量和最大音量
vol = 0#初始化音量
volBar = 400#初始化音量条
volPer = 0#初始化音量百分比

while True:
    success, img = cap.read()
    img = detector.findHands(img)#获取图像中的手
    lmList = detector.findPosition(img, draw=False)#获取图像中的关键点
    
    if len(lmList) != 0:
        x1, y1 = lmList[4][1], lmList[4][2]#获取食指的x和y坐标
        x2, y2 = lmList[8][1], lmList[8][2]#获取拇指的x和y坐标
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2#计算两个点的中点

        cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)#在图像上绘制食指
        cv2.circle(img, (x2, y2), 15, (255, 0, 255), cv2.FILLED)#在图像上绘制拇指
        cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)#在图像上绘制两个点之间的线
        cv2.circle(img, (cx, cy), 15, (255, 0, 255), cv2.FILLED)#在图像上绘制中点

        # 添加手掌宽度参考（近远距离缩放因子）
        ref_x1, ref_y1 = lmList[0][1], lmList[0][2]#获取手掌的x和y坐标
        ref_x2, ref_y2 = lmList[17][1], lmList[17][2]#获取手掌的x和y坐标
        ref_length = math.hypot(ref_x2 - ref_x1, ref_y2 - ref_y1)#计算两个点之间的距离
        if ref_length == 0:
            ref_length = 1  # 避免除0错误

        # 原始食指与拇指间距离
        length = math.hypot(x2 - x1, y2 - y1)#计算两个点之间的距离
        scaling_factor = 80 / ref_length  # 归一化因子，80 为理想手掌宽度
        normalized_length = length * scaling_factor#计算归一化长度

        vol = np.interp(normalized_length, [30, 200], [minVol, maxVol])#计算音量
        volBar = np.interp(normalized_length, [30, 200], [400, 150])#计算音量条
        volPer = np.interp(normalized_length, [30, 200], [0, 100])#计算音量百分比

        volume.SetMasterVolumeLevel(vol, None)#设置音量

        if length < 30:
            cv2.circle(img, (cx, cy), 15, (0, 255, 0), cv2.FILLED)#在图像上绘制中点

    cv2.rectangle(img, (50, 150), (85, 400), (255, 0, 0), 3)#在图像上绘制音量条
    cv2.rectangle(img, (50, int(volBar)), (85, 400), (255, 0, 0), cv2.FILLED)#在图像上绘制音量条
    cv2.putText(img, f'{int(volPer)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX,
                1, (255, 0, 0), 3)#在图像上绘制音量百分比

    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (40, 50), cv2.FONT_HERSHEY_COMPLEX,
                1, (255, 0, 0), 3)

    cv2.imshow("Img", img)
    cv2.waitKey(1)
