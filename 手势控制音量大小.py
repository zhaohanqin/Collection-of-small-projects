import cv2
import mediapipe as mp
import time
import numpy as np
import math
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume


class HandDetector:#手部检测类
    def __init__(self, mode=False, maxHands=2, detectionCon=0.2, trackCon=0.2):#初始化参数
        self.mode = mode#是否使用静态图像模式
        self.maxHands = maxHands#最大检测手部数量
        self.detectionCon = detectionCon#检测置信度
        self.trackCon = trackCon#跟踪置信度

        self.mpHands = mp.solutions.hands#手部检测模型
        self.hands = self.mpHands.Hands(static_image_mode=mode, max_num_hands=maxHands,
                                      min_detection_confidence=detectionCon, min_tracking_confidence=trackCon)#初始化手部检测模型
        self.mpDraw = mp.solutions.drawing_utils#绘制工具
        self.tipIds = [4, 8, 12, 16, 20]#手指关键点ID

    def findHands(self, img, draw=True):#检测手部
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)#将图像转换为RGB格式
        self.results = self.hands.process(imgRGB)#处理图像

        # 只在需要时绘制全部手部关键点
        if draw and self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)
                
        return img

    def findPosition(self, img, handNo=0, draw=True):#检测手部位置
        xList = []#x坐标列表
        yList = []#y坐标列表
        bbox = []#边界框
        self.lmList = []#手部关键点列表
        if self.results.multi_hand_landmarks:#如果检测到手部
            myHand = self.results.multi_hand_landmarks[handNo]#获取指定手部
            for id, lm in enumerate(myHand.landmark):#遍历每个关键点
                h, w, c = img.shape#获取图像尺寸
                cx, cy = int(lm.x * w), int(lm.y * h)#计算关键点在图像中的位置
                xList.append(cx)#添加到x坐标列表
                yList.append(cy)#添加到y坐标列表
                self.lmList.append([id, cx, cy])#添加到手部关键点列表
                
                # 只在需要时绘制所有关键点
                if draw:
                    cv2.circle(img, (cx, cy), 5, (0, 255, 0), cv2.FILLED)

            xmin, xmax = min(xList), max(xList)#计算边界框
            ymin, ymax = min(yList), max(yList)
            bbox = xmin, ymin, xmax, ymax

            if draw:#如果需要绘制边界框
                cv2.rectangle(img, (bbox[0] - 20, bbox[1] - 20),#绘制边界框
                              (bbox[2] + 20, bbox[3] + 20), (0, 255, 0), 2)

        return self.lmList

    def fingersUp(self):#检测手指状态
        fingers = []#手指状态列表
        # Thumb
        if self.lmList[self.tipIds[0]][1] > self.lmList[self.tipIds[0] - 1][1]:#拇指状态
            fingers.append(1)#拇指状态为1
        else:
            fingers.append(0)#拇指状态为0
        # 4 Fingers
        for id in range(1, 5):#遍历其他手指
            if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id] - 2][2]:#如果手指状态为1
                fingers.append(1)#拇指状态为1
            else:
                fingers.append(0)#拇指状态为0
        return fingers

    def findDistance(self, p1, p2, img, draw=True):#检测手指距离
        x1, y1 = self.lmList[p1][1], self.lmList[p1][2]#获取手指1的坐标
        x2, y2 = self.lmList[p2][1], self.lmList[p2][2]#获取手指2的坐标
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2#计算中心点坐标

        if draw:#如果需要绘制
            cv2.circle(img, (x1, y1), 10, (0, 255, 0), cv2.FILLED)#绘制手指1
            cv2.circle(img, (x2, y2), 10, (0, 255, 0), cv2.FILLED)#绘制手指2
            cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 3)
            cv2.circle(img, (cx, cy), 10, (0, 255, 0), cv2.FILLED)

        length = math.hypot(x2 - x1, y2 - y1)#计算手指距离
        return length, img, [x1, y1, x2, y2, cx, cy]#返回距离、图像和中心点坐标
        
        
class VolumeController:#控制音量的类
    def __init__(self, wCam=1080, hCam=720, detectionCon=0.7):#初始化参数
        self.wCam = wCam#摄像头宽度
        self.hCam = hCam#摄像头高度
        self.cap = cv2.VideoCapture(0)#打开摄像头
        self.cap.set(3, self.wCam)#设置摄像头宽度
        self.cap.set(4, self.hCam)#设置摄像头高度
        self.pTime = 0#初始化时间
        
        self.detector = HandDetector(detectionCon=detectionCon)
        
        # 初始化人脸检测 - 使用Face Mesh代替简单的Face Detection以获得更精确的人脸轮廓
        self.mpFaceMesh = mp.solutions.face_mesh
        self.faceMesh = self.mpFaceMesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5)
        self.mpDraw = mp.solutions.drawing_utils
        self.drawSpec = self.mpDraw.DrawingSpec(thickness=1, circle_radius=1)
        
        # 初始化音频控制
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(interface, POINTER(IAudioEndpointVolume))
        volRange = self.volume.GetVolumeRange()
        self.minVol, self.maxVol = volRange[0], volRange[1]
        
        # 添加平滑处理变量
        self.smoothVolume = 0
        self.smoothingFactor = 0.3
        self.volHistory = []
        self.historySize = 5
        self.volBar = 400
        self.volPer = 0
        
        # 获取当前系统音量作为初始值
        self.currentVol = self.volume.GetMasterVolumeLevelScalar()
        self.smoothVolume = self.currentVol
        
        # 人脸宽度相关变量
        self.faceWidth = 200  # 默认人脸宽度（如果未检测到人脸）
        self.faceDetected = False
        
        # 定义脸部关键点索引 - 用于计算精确的脸部宽度
        # 左脸颊点和右脸颊点的索引
        self.LEFT_CHEEK = 234  # 左脸颊关键点
        self.RIGHT_CHEEK = 454  # 右脸颊关键点
    
    def detect_face(self, img, draw=True):
        """使用Face Mesh检测人脸并计算更精确的人脸宽度，可选是否显示网格"""
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.faceMesh.process(imgRGB)
        
        self.faceDetected = False
        face_landmarks = []
        
        if results.multi_face_landmarks:
            for faceLms in results.multi_face_landmarks:
                # 收集所有脸部关键点坐标
                face_points = []
                for id, lm in enumerate(faceLms.landmark):
                    ih, iw, ic = img.shape
                    x, y = int(lm.x * iw), int(lm.y * ih)
                    face_points.append([x, y])
                    
                    # 在特定关键点上绘制，只有在draw=True时
                    if draw and id in [self.LEFT_CHEEK, self.RIGHT_CHEEK]:
                        cv2.circle(img, (x, y), 5, (255, 0, 0), cv2.FILLED)
                
                face_landmarks = face_points
                
                # 绘制完整的脸部网格，只有在draw=True时
                if draw:
                    self.mpDraw.draw_landmarks(
                        img, 
                        faceLms, 
                        self.mpFaceMesh.FACEMESH_TESSELATION,
                        self.drawSpec, 
                        self.drawSpec
                    )
                
                # 计算精确的脸部宽度 - 使用两侧脸颊点
                if len(face_points) > max(self.LEFT_CHEEK, self.RIGHT_CHEEK):
                    left_cheek = face_points[self.LEFT_CHEEK]
                    right_cheek = face_points[self.RIGHT_CHEEK]
                    
                    # 计算脸颊之间的距离
                    face_width = math.hypot(right_cheek[0] - left_cheek[0], 
                                           right_cheek[1] - left_cheek[1])
                    
                    # 创建自定义的脸部边界框
                    min_x = min(left_cheek[0], right_cheek[0])
                    max_x = max(left_cheek[0], right_cheek[0])
                    min_y = min(left_cheek[1], right_cheek[1])
                    max_y = max(left_cheek[1], right_cheek[1])
                    
                    # 调整边界框以适应整个脸部
                    padding_x = int((max_x - min_x) * 0.2)
                    padding_y = int((max_y - min_y) * 0.2)
                    
                    face_bbox = [
                        max(0, min_x - padding_x),
                        max(0, min_y - padding_y),
                        min(iw, max_x + padding_x),
                        min(ih, max_y + padding_y)
                    ]
                    
                    # 绘制精确的脸部边界框，只有在draw=True时
                    if draw:
                        cv2.rectangle(img, 
                                     (face_bbox[0], face_bbox[1]),
                                     (face_bbox[2], face_bbox[3]),
                                     (0, 255, 0), 2)
                    
                        # 连接两个脸颊点
                        cv2.line(img, 
                                (left_cheek[0], left_cheek[1]), 
                                (right_cheek[0], right_cheek[1]), 
                                (0, 0, 255), 3)
                    
                    # 更新人脸宽度
                    self.faceWidth = face_width
                    self.faceDetected = True
                    
                    # 显示人脸宽度信息，只有在draw=True时
                    if draw:
                        cv2.putText(img, f'Face Width: {int(self.faceWidth)}', 
                                   (face_bbox[0], face_bbox[1] - 20),
                                   cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 2)
                
                # 只处理第一张检测到的脸
                break
                
        return img
    
    def process_frame(self, draw_details=True):
        """处理一帧图像，可选是否显示详细信息"""
        success, img = self.cap.read()
        if not success:
            return None
            
        # 计算FPS - 只在这里计算一次，然后传递给UI函数
        cTime = time.time()
        fps = 1 / max(cTime - self.pTime, 0.001)  # 确保不会除以零
        self.pTime = cTime
            
        # 创建原始图像的副本，以便分别处理两个视图
        img_detailed = img.copy()
        img_clean = img.copy()
            
        # 检测人脸 - 详细视图显示所有标记，简洁视图不显示
        self.detect_face(img_detailed, draw=draw_details)
        self.detect_face(img_clean, draw=False)
        
        # 检测手部 - 详细视图显示所有标记，简洁视图不显示
        self.detector.findHands(img_detailed, draw=draw_details)
        self.detector.findHands(img_clean, draw=False)
        
        # 获取手部位置 - 对两个视图都需要，但只在详细视图绘制
        lmList = self.detector.findPosition(img_detailed, draw=draw_details)
        if len(lmList) == 0:
            # 如果没有检测到手，返回当前帧
            # 添加基本UI元素
            self._add_basic_ui(img_detailed, True, fps)
            self._add_basic_ui(img_clean, False, fps)
            return img_detailed, img_clean
        
        # 使用findDistance方法来获取拇指和食指之间的距离
        # 详细视图
        length_detailed, img_detailed, line_info_detailed = self.detector.findDistance(4, 8, img_detailed, draw=True)
        # 简洁视图 - 仅显示拇指、食指和连线
        length_clean, img_clean, line_info_clean = self.detector.findDistance(4, 8, img_clean, draw=True)
        
        # 使用人脸宽度进行归一化
        if self.faceWidth < 1:  # 避免除零错误
            self.faceWidth = 1
            
        # 归一化距离，当距离为0时音量为0，当距离等于脸宽时音量为100%
        normalized_length = length_detailed / self.faceWidth
        
        # 映射到音量范围（使用标量值0.0-1.0更直观）
        target_vol = np.interp(normalized_length, [0.05, 1.0], [0.0, 1.0])
        target_vol = max(0.0, min(1.0, target_vol))  # 确保在有效范围内
        
        # 添加平滑处理
        self.volHistory.append(target_vol)
        if len(self.volHistory) > self.historySize:
            self.volHistory.pop(0)
        
        # 使用中值滤波减少抖动
        median_vol = np.median(self.volHistory)
        
        # 平滑过渡
        self.smoothVolume = self.smoothVolume * (1 - self.smoothingFactor) + median_vol * self.smoothingFactor
        
        # 设置系统音量（使用标量值而不是分贝值）
        self.volume.SetMasterVolumeLevelScalar(self.smoothVolume, None)
        
        # 更新UI显示值
        self.volBar = np.interp(self.smoothVolume, [0.0, 1.0], [400, 150])
        self.volPer = np.interp(self.smoothVolume, [0.0, 1.0], [0, 100])
        
        # 在画面上显示当前手指距离 - 仅在详细视图中
        cx_detailed, cy_detailed = line_info_detailed[4], line_info_detailed[5]
        cx_clean, cy_clean = line_info_clean[4], line_info_clean[5]
        
        # 在详细视图中显示距离信息
        if draw_details:
            cv2.putText(img_detailed, f'Fingers Dist: {int(length_detailed)}', 
                        (cx_detailed-20, cy_detailed-40), 
                        cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 2)
            cv2.putText(img_detailed, f'Normalized: {normalized_length:.2f}', 
                        (cx_detailed-20, cy_detailed-20), 
                        cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 2)
        
        # 根据音量大小改变中心点颜色深浅 - 在两个视图中都显示
        color_intensity = int(self.smoothVolume * 255)
        cv2.circle(img_detailed, (cx_detailed, cy_detailed), 12, (0, color_intensity, 0), cv2.FILLED)
        cv2.circle(img_clean, (cx_clean, cy_clean), 12, (0, color_intensity, 0), cv2.FILLED)

        # 显示人脸检测状态 - 仅在详细视图中
        if draw_details:
            face_status = "Face Detected" if self.faceDetected else "No Face Detected"
            cv2.putText(img_detailed, face_status, (40, 80), cv2.FONT_HERSHEY_COMPLEX,
                        1, (0, 0, 255) if not self.faceDetected else (0, 255, 0), 2)
        
        # 添加基本UI元素
        self._add_basic_ui(img_detailed, True, fps)
        self._add_basic_ui(img_clean, False, fps)

        return img_detailed, img_clean
    
    def _add_basic_ui(self, img, is_detailed, fps):
        """添加基本UI元素 - 音量条和FPS计数器"""
        # 绘制音量条
        cv2.rectangle(img, (50, 150), (85, 400), (0, 255, 0), 3)
        cv2.rectangle(img, (50, int(self.volBar)), (85, 400), (0, 255, 0), cv2.FILLED)
        cv2.putText(img, f'{int(self.volPer)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX,
                    1, (0, 255, 0), 3)

        # 显示FPS - 使用传入的FPS值
        cv2.putText(img, f'FPS: {int(fps)}', (40, 50), cv2.FONT_HERSHEY_COMPLEX,
                    1, (0, 255, 0), 3)
        
        # 添加视图标题
        if is_detailed:
            cv2.putText(img, "Detailed View", (img.shape[1] - 250, 50), 
                        cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
        else:
            cv2.putText(img, "Clean View", (img.shape[1] - 200, 50), 
                        cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
    
    def run(self):
        """运行应用程序并显示两个窗口"""
        while True:
            # 处理帧并获取两个视图
            result = self.process_frame(draw_details=True)
            if result is None:
                break
                
            img_detailed, img_clean = result
            
            # 显示两个窗口
            cv2.imshow("Detailed View", img_detailed)
            cv2.imshow("Clean View", img_clean)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        self.cap.release()
        cv2.destroyAllWindows()


def main():
    controller = VolumeController()
    controller.run()


if __name__ == "__main__":
    main() 