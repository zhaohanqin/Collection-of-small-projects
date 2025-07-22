import cv2
import mediapipe as mp
import time
import numpy as np
import math
import ctypes
from ctypes import wintypes
import subprocess

# 尝试导入wmi，如果失败则使用备用方案
try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False
    print("警告: wmi模块未安装，将使用备用亮度控制方案")


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


class BrightnessController:#控制屏幕亮度的类
    def __init__(self):
        """初始化亮度控制器"""
        self.wmi_available = False
        self.api_available = False

        # 尝试使用WMI方式控制亮度
        if WMI_AVAILABLE:
            try:
                self.c = wmi.WMI(namespace='wmi')
                self.brightness_methods = self.c.WmiMonitorBrightnessMethods()[0]
                self.brightness_monitor = self.c.WmiMonitorBrightness()[0]
                self.wmi_available = True
                print("✅ 使用WMI方式控制亮度")
            except Exception as e:
                print(f"❌ WMI初始化失败: {e}")
                self.wmi_available = False

        # 备用方案：使用PowerShell命令
        if not self.wmi_available:
            try:
                # 测试PowerShell命令是否可用
                test_cmd = 'powershell.exe -Command "Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness"'
                result = subprocess.run(test_cmd, shell=True, capture_output=True, timeout=5)
                if result.returncode == 0:
                    self.api_available = True
                    print("✅ 使用PowerShell方式控制亮度")
                else:
                    print("❌ PowerShell亮度控制不可用")
            except Exception as e:
                print(f"❌ PowerShell测试失败: {e}")
                self.api_available = False

        if not self.wmi_available and not self.api_available:
            print("⚠️  警告: 所有亮度控制方案都不可用，程序将模拟亮度控制")
    
    def get_brightness(self):
        """获取当前屏幕亮度 (0-100)"""
        try:
            if self.wmi_available:
                return self.brightness_monitor.CurrentBrightness
            else:
                # 返回默认值
                return 50
        except Exception as e:
            print(f"获取亮度失败: {e}")
            return 50

    def set_brightness(self, brightness):
        """设置屏幕亮度 (0-100)"""
        try:
            brightness = max(1, min(100, int(brightness)))  # 确保在1-100范围内

            if self.wmi_available:
                self.brightness_methods.WmiSetBrightness(brightness, 0)
                return True
            elif self.api_available:
                # 使用PowerShell命令作为备用方案
                cmd = f'powershell.exe -Command "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{brightness})"'
                result = subprocess.run(cmd, shell=True, capture_output=True, timeout=3)
                return result.returncode == 0
            else:
                # 模拟模式 - 仅打印亮度值
                print(f"🔆 模拟设置亮度: {brightness}%")
                return True

        except Exception as e:
            print(f"设置亮度失败: {e}")
            return False


class BrightnessHandController:#手势控制亮度的主类
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
        
        # 初始化亮度控制
        self.brightness_controller = BrightnessController()
        
        # 添加平滑处理变量
        self.smoothBrightness = 50  # 默认亮度50%
        self.smoothingFactor = 0.3
        self.brightnessHistory = []
        self.historySize = 5
        self.brightnessBar = 400
        self.brightnessPer = 50
        
        # 获取当前系统亮度作为初始值
        try:
            self.currentBrightness = self.brightness_controller.get_brightness()
            self.smoothBrightness = self.currentBrightness
        except:
            self.currentBrightness = 50
            self.smoothBrightness = 50
        
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

        # 归一化距离，当距离为0时亮度为0，当距离等于脸宽时亮度为100%
        normalized_length = length_detailed / self.faceWidth

        # 映射到亮度范围（1-100，避免完全黑屏）
        target_brightness = np.interp(normalized_length, [0.05, 1.0], [1, 100])
        target_brightness = max(1, min(100, target_brightness))  # 确保在有效范围内

        # 添加平滑处理
        self.brightnessHistory.append(target_brightness)
        if len(self.brightnessHistory) > self.historySize:
            self.brightnessHistory.pop(0)

        # 使用中值滤波减少抖动
        median_brightness = np.median(self.brightnessHistory)

        # 平滑过渡
        self.smoothBrightness = self.smoothBrightness * (1 - self.smoothingFactor) + median_brightness * self.smoothingFactor

        # 设置系统亮度
        self.brightness_controller.set_brightness(self.smoothBrightness)

        # 更新UI显示值
        self.brightnessBar = np.interp(self.smoothBrightness, [0, 100], [400, 150])
        self.brightnessPer = self.smoothBrightness

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

        # 根据亮度大小改变中心点颜色深浅 - 在两个视图中都显示
        color_intensity = int(self.smoothBrightness * 255 / 100)
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
        """添加基本UI元素 - 亮度条和FPS计数器"""
        # 绘制亮度条
        cv2.rectangle(img, (50, 150), (85, 400), (255, 255, 0), 3)  # 黄色边框表示亮度
        cv2.rectangle(img, (50, int(self.brightnessBar)), (85, 400), (255, 255, 0), cv2.FILLED)
        cv2.putText(img, f'{int(self.brightnessPer)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX,
                    1, (255, 255, 0), 3)

        # 显示FPS - 使用传入的FPS值
        cv2.putText(img, f'FPS: {int(fps)}', (40, 50), cv2.FONT_HERSHEY_COMPLEX,
                    1, (0, 255, 0), 3)

        # 添加视图标题
        if is_detailed:
            cv2.putText(img, "Detailed View - Brightness Control", (img.shape[1] - 400, 50),
                        cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
        else:
            cv2.putText(img, "Clean View - Brightness Control", (img.shape[1] - 350, 50),
                        cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)

    def run(self):
        """运行应用程序并显示两个窗口"""
        print("手势亮度控制器启动中...")
        print("使用说明：")
        print("- 将拇指和食指靠近可降低亮度")
        print("- 将拇指和食指分开可提高亮度")
        print("- 按 'q' 键退出程序")

        while True:
            # 处理帧并获取两个视图
            result = self.process_frame(draw_details=True)
            if result is None:
                break

            img_detailed, img_clean = result

            # 显示两个窗口
            cv2.imshow("Detailed View - Brightness Control", img_detailed)
            cv2.imshow("Clean View - Brightness Control", img_clean)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()


def main():
    """主函数"""
    print("=" * 50)
    print("手势屏幕亮度控制器")
    print("=" * 50)
    print("依赖库要求：")
    print("- opencv-python")
    print("- mediapipe")
    print("- numpy")
    print("- wmi (用于Windows亮度控制)")
    print("=" * 50)

    try:
        controller = BrightnessHandController()
        controller.run()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")
        print("请确保已安装所有必需的依赖库：")
        print("pip install opencv-python mediapipe numpy wmi")


if __name__ == "__main__":
    main()
