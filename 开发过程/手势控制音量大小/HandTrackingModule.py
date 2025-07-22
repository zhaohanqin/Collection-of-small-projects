import cv2
import mediapipe as mp
import time
import math


class handDetector():
    def __init__(self, mode=False, maxHands=2, detectionCon=0.2, trackCon=0.2):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands# 初始化手部检测模型
        self.hands = self.mpHands.Hands(static_image_mode=mode,max_num_hands=maxHands,min_detection_confidence=detectionCon,min_tracking_confidence=trackCon)# 初始化手部检测器
        self.mpDraw = mp.solutions.drawing_utils# 初始化手部绘制工具
        self.tipIds = [4, 8, 12, 16, 20]# 初始化手指关键点ID


    def findHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)#将图像从BGR格式转换为RGB格式
        self.results = self.hands.process(imgRGB)#处理图像
        # print(results.multi_hand_landmarks)

        if self.results.multi_hand_landmarks:# 如果检测到手
            for handLms in self.results.multi_hand_landmarks:# 遍历所有手
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)# 绘制手部关键点
        return img


    def findPosition(self, img, handNo=0, draw=True):
        xList = []# 初始化x坐标列表
        yList = []# 初始化y坐标列表
        bbox = []# 初始化边界框
        self.lmList = []# 初始化关键点列表
        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNo]# 获取当前手
            for id, lm in enumerate(myHand.landmark):# 遍历所有关键点
                # print(id, lm)
                h, w, c = img.shape# 获取图像高度、宽度和通道数
                cx, cy = int(lm.x * w), int(lm.y * h)
                xList.append(cx)# 将x坐标添加到列表中
                yList.append(cy)# 将y坐标添加到列表中
                # print(id, cx, cy)
                self.lmList.append([id, cx, cy])# 将关键点坐标添加到列表中
                if draw:
                    cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)# 在图像上绘制关键点
            xmin, xmax = min(xList), max(xList)# 获取边界框
            ymin, ymax = min(yList), max(yList)# 获取边界框
            bbox = xmin, ymin, xmax, ymax# 设置边界框

            if draw:
                cv2.rectangle(img, (bbox[0] - 20, bbox[1] - 20),
                              (bbox[2] + 20, bbox[3] + 20), (0, 255, 0), 2)# 在图像上绘制边界框

        return self.lmList# 返回关键点列表


    def fingersUp(self):
        fingers = []# 初始化手指列表
        # Thumb
        if self.lmList[self.tipIds[0]][1] > self.lmList[self.tipIds[0] - 1][1]:# 如果拇指的x坐标大于食指的x坐标
            fingers.append(1)# 将拇指状态添加到列表中
        else:
            fingers.append(0)# 将拇指状态添加到列表中
        # 4 Fingers
        for id in range(1, 5):# 遍历所有手指
            if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id] - 2][2]:# 如果手指的y坐标小于食指的y坐标
                fingers.append(1)# 将手指状态添加到列表中
            else:
                fingers.append(0)# 将手指状态添加到列表中
        return fingers# 返回手指列表


    def findDistance(self, p1, p2, img, draw=True):
        x1, y1 = self.lmList[p1][1], self.lmList[p1][2]# 获取第一个点的x和y坐标
        x2, y2 = self.lmList[p2][1], self.lmList[p2][2]# 获取第二个点的x和y坐标
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2# 计算两个点的中点

        if draw:
            cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)# 在图像上绘制第一个点
            cv2.circle(img, (x2, y2), 15, (255, 0, 255), cv2.FILLED)# 在图像上绘制第二个点
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)# 在图像上绘制两个点之间的线
            cv2.circle(img, (cx, cy), 15, (255, 0, 255), cv2.FILLED)# 在图像上绘制中点

        length = math.hypot(x2 - x1, y2 - y1)# 计算两个点之间的距离
        return length, img, [x1, y1, x2, y2, cx, cy]# 返回距离、图像和两个点之间的坐标


def main():
    pTime = 0# 初始化上一帧时间
    cap = cv2.VideoCapture(0)# 初始化摄像头
    detector = handDetector()# 初始化一个手部识别器
    while True:
        success, img = cap.read()# 读取图像
        img = detector.findHands(img)# 找到手
        lmList = detector.findPosition(img)# 找到关键点
        if len(lmList) != 0:
            print(lmList[4])# 打印第4个关键点的坐标

        cTime = time.time()# 获取当前时间   
        fps = 1 / (cTime - pTime)# 计算帧率
        pTime = cTime# 更新上一帧时间

        cv2.putText(img, f'FPS: {int(fps)}', (10, 70), cv2.FONT_HERSHEY_PLAIN, 3,
                    (255, 0, 255), 3)# 在图像上显示帧率

        cv2.imshow("Image", img)# 显示图像
        cv2.waitKey(1)# 等待1毫秒


if __name__ == "__main__":
    main()