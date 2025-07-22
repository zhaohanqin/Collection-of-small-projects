import cv2
import mediapipe as mp
import time
import numpy as np
import math
import subprocess
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from PIL import Image, ImageDraw, ImageFont
import os

# 尝试导入wmi，如果失败则使用备用方案
try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False
    print("警告: wmi模块未安装，将使用备用亮度控制方案")


def put_chinese_text(img, text, position, font_size=30, color=(255, 255, 255)):
    """
    在OpenCV图像上绘制中文文字

    Args:
        img: OpenCV图像
        text: 要显示的中文文字
        position: 文字位置 (x, y)
        font_size: 字体大小
        color: 文字颜色 (B, G, R)

    Returns:
        绘制了文字的图像
    """
    try:
        # 将OpenCV图像转换为PIL图像
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)

        # 尝试使用系统中文字体
        font_paths = [
            "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
            "C:/Windows/Fonts/simhei.ttf",  # 黑体
            "C:/Windows/Fonts/simsun.ttc",  # 宋体
            "C:/Windows/Fonts/arial.ttf",   # Arial (备用)
        ]

        font = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    font = ImageFont.truetype(font_path, font_size)
                    break
                except:
                    continue

        if font is None:
            # 如果没有找到字体，使用默认字体
            font = ImageFont.load_default()

        # 绘制文字 (PIL使用RGB颜色)
        rgb_color = (color[2], color[1], color[0])  # BGR转RGB
        draw.text(position, text, font=font, fill=rgb_color)

        # 转换回OpenCV格式
        img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        return img_cv

    except Exception as e:
        # 如果出错，使用英文替代
        cv2.putText(img, text.encode('ascii', 'ignore').decode('ascii'),
                   position, cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        return img


class HandDetector:
    """手部检测类"""
    def __init__(self, mode=False, maxHands=2, detectionCon=0.2, trackCon=0.2):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(static_image_mode=mode, max_num_hands=maxHands,
                                      min_detection_confidence=detectionCon, min_tracking_confidence=trackCon)
        self.mpDraw = mp.solutions.drawing_utils
        self.tipIds = [4, 8, 12, 16, 20]

    def findHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)

        if draw and self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)

        return img

    def findAllHands(self, img, draw=True):
        """检测所有手部并返回每只手的信息，修正左右手识别"""
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)

        allHands = []

        if self.results.multi_hand_landmarks:
            for handLms, handInfo in zip(self.results.multi_hand_landmarks, self.results.multi_handedness):
                # 修正左右手识别 - MediaPipe返回的是镜像结果，需要反转
                original_handType = handInfo.classification[0].label
                handType = "Right" if original_handType == "Left" else "Left"

                # 获取关键点
                lmList = []
                xList = []
                yList = []

                for id, lm in enumerate(handLms.landmark):
                    h, w, c = img.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lmList.append([id, cx, cy])
                    xList.append(cx)
                    yList.append(cy)

                # 计算边界框
                xmin, xmax = min(xList), max(xList)
                ymin, ymax = min(yList), max(yList)
                bbox = xmin, ymin, xmax, ymax

                # 绘制手部
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)
                    cv2.rectangle(img, (bbox[0] - 20, bbox[1] - 20),
                                  (bbox[2] + 20, bbox[3] + 20), (0, 255, 0), 2)
                    # 在手部上方显示左右手标识（中文）
                    hand_text = "左手" if handType == "Left" else "右手"
                    img = put_chinese_text(img, hand_text, (bbox[0] - 20, bbox[1] - 30),
                                         font_size=25, color=(0, 255, 0))

                allHands.append({
                    'lmList': lmList,
                    'bbox': bbox,
                    'handType': handType
                })

        return allHands, img

    def findDistance(self, p1, p2, img, lmList=None, draw=True):
        """计算两个关键点之间的距离"""
        if lmList is None:
            lmList = self.lmList

        if len(lmList) == 0:
            return 0, img, [0, 0, 0, 0, 0, 0]

        x1, y1 = lmList[p1][1], lmList[p1][2]
        x2, y2 = lmList[p2][1], lmList[p2][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        if draw:
            cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 15, (255, 0, 255), cv2.FILLED)
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
            cv2.circle(img, (cx, cy), 15, (255, 0, 255), cv2.FILLED)

        length = math.hypot(x2 - x1, y2 - y1)
        return length, img, [x1, y1, x2, y2, cx, cy]


class VolumeController:
    """音量控制器类"""
    def __init__(self):
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self.volume = cast(interface, POINTER(IAudioEndpointVolume))
            volRange = self.volume.GetVolumeRange()
            self.minVol, self.maxVol = volRange[0], volRange[1]
            self.smoothVolume = 0.5
            self.smoothingFactor = 0.3
            self.volHistory = []
            self.historySize = 5
            self.volBar = 400
            self.volPer = 50
            print("✅ 音量控制器初始化成功")
        except Exception as e:
            print(f"❌ 音量控制器初始化失败: {e}")
            self.volume = None

    def update_volume_from_distance(self, finger_distance, face_width):
        """根据手指距离和人脸宽度更新音量"""
        if self.volume is None or face_width == 0:
            return

        # 使用人脸宽度进行归一化
        normalized_length = finger_distance / face_width

        # 映射到音量范围 (0.0-1.0)
        target_volume = np.interp(normalized_length, [0.05, 1.0], [0.0, 1.0])
        target_volume = max(0.0, min(1.0, target_volume))

        # 平滑处理
        self.volHistory.append(target_volume)
        if len(self.volHistory) > self.historySize:
            self.volHistory.pop(0)

        median_vol = np.median(self.volHistory)
        self.smoothVolume = self.smoothVolume * (1 - self.smoothingFactor) + median_vol * self.smoothingFactor

        # 设置系统音量
        self.volume.SetMasterVolumeLevelScalar(self.smoothVolume, None)

        # 更新UI显示值
        self.volBar = np.interp(self.smoothVolume, [0.0, 1.0], [400, 150])
        self.volPer = np.interp(self.smoothVolume, [0.0, 1.0], [0, 100])


class BrightnessController:
    """亮度控制器类"""
    
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
        
        # 初始化亮度相关变量
        self.currentBrightness = 50    # 当前亮度 (1-100)
        self.smoothBrightness = 50     # 平滑后的亮度
        self.smoothingFactor = 0.3     # 平滑因子
        self.brightnessHistory = []    # 亮度历史记录
        self.historySize = 5           # 历史记录大小
        
        # UI相关变量
        self.brightnessBar = 400       # 亮度条位置
        self.brightnessPer = 50        # 亮度百分比
        
        # 获取当前系统亮度作为初始值
        try:
            self.currentBrightness = self.get_brightness()
            self.smoothBrightness = self.currentBrightness
        except:
            self.currentBrightness = 50
            self.smoothBrightness = 50

        # 更新UI显示值
        self.brightnessBar = np.interp(self.smoothBrightness, [0, 100], [400, 150])
        self.brightnessPer = self.smoothBrightness

    def get_brightness(self):
        """获取当前屏幕亮度 (1-100)"""
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
        """设置屏幕亮度 (1-100)"""
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

    def calculate_brightness_from_distance(self, finger_distance, reference_length):
        """
        根据手指距离计算亮度 - 使用与音量控制相同的逻辑

        Args:
            finger_distance: 拇指和食指之间的距离
            reference_length: 人脸宽度，用于归一化

        Returns:
            计算出的亮度值 (1-100)
        """
        if reference_length == 0:
            reference_length = 1  # 避免除零错误

        # 计算手指距离与人脸宽度的比例
        distance_ratio = finger_distance / reference_length

        # 将距离比例映射到亮度范围 (1-100)
        # 当手指距离等于人脸宽度时，亮度为100%
        # 距离比例范围 [0.0, 1.0] 映射到亮度范围 [1, 100]
        target_brightness = np.interp(distance_ratio, [0.0, 1.0], [1, 100])
        target_brightness = max(1, min(100, target_brightness))  # 确保在有效范围内

        return target_brightness

    def update_brightness(self, target_brightness):
        """
        更新亮度，包含平滑处理

        Args:
            target_brightness: 目标亮度 (1-100)
        """
        try:
            # 添加到历史记录
            self.brightnessHistory.append(target_brightness)
            if len(self.brightnessHistory) > self.historySize:
                self.brightnessHistory.pop(0)

            # 使用中值滤波减少抖动
            median_brightness = np.median(self.brightnessHistory)

            # 平滑过渡
            self.smoothBrightness = self.smoothBrightness * (1 - self.smoothingFactor) + median_brightness * self.smoothingFactor

            # 设置系统亮度
            self.set_brightness(self.smoothBrightness)

            # 更新UI显示值
            self.brightnessBar = np.interp(self.smoothBrightness, [0, 100], [400, 150])
            self.brightnessPer = self.smoothBrightness

            return True

        except Exception as e:
            print(f"更新亮度失败: {e}")
            return False


class DualHandController:
    """双手手势控制器 - 左手控制音量，右手控制亮度"""

    def __init__(self, wCam=1280, hCam=960, detectionCon=0.7):
        """
        初始化双手控制器

        Args:
            wCam: 摄像头宽度 (增大显示尺寸)
            hCam: 摄像头高度 (增大显示尺寸)
            detectionCon: 手部检测置信度
        """
        self.wCam = wCam
        self.hCam = hCam

        # 初始化摄像头
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, self.wCam)
        self.cap.set(4, self.hCam)
        self.pTime = 0

        # 初始化手部检测器
        self.detector = HandDetector(detectionCon=detectionCon, maxHands=2)

        # 初始化人脸检测 - 使用Face Mesh获得精确的人脸宽度
        self.mpFaceMesh = mp.solutions.face_mesh
        self.faceMesh = self.mpFaceMesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5)
        self.mpDraw = mp.solutions.drawing_utils
        self.drawSpec = self.mpDraw.DrawingSpec(thickness=1, circle_radius=1)

        # 人脸宽度相关变量
        self.faceWidth = 200  # 默认人脸宽度
        self.faceDetected = False

        # 定义脸部关键点索引 - 用于计算精确的脸部宽度
        self.LEFT_CHEEK = 234   # 左脸颊关键点
        self.RIGHT_CHEEK = 454  # 右脸颊关键点

        # 初始化音量和亮度控制器
        self.volume_controller = VolumeController()
        self.brightness_controller = BrightnessController()

        # 状态变量
        self.left_hand_detected = False
        self.right_hand_detected = False
        self.left_hand_distance = 0
        self.right_hand_distance = 0

        print("=" * 60)
        print("🎮 双手手势控制器启动")
        print("=" * 60)
        print("📋 使用说明：")
        print("👈 左手控制音量：拇指食指靠近降低音量，分开提高音量")
        print("👉 右手控制亮度：拇指食指靠近降低亮度，分开提高亮度")
        print("🚪 按 'q' 键退出程序")
        print("=" * 60)

    def update_brightness_from_distance(self, finger_distance, face_width):
        """根据手指距离和人脸宽度更新亮度"""
        if face_width == 0:
            return

        # 计算目标亮度
        target_brightness = self.brightness_controller.calculate_brightness_from_distance(finger_distance, face_width)

        # 使用亮度控制器的更新方法
        self.brightness_controller.update_brightness(target_brightness)

    def detect_face(self, img, draw=True):
        """使用Face Mesh检测人脸并计算精确的人脸宽度"""
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.faceMesh.process(imgRGB)

        self.faceDetected = False

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

                    # 更新人脸宽度
                    if face_width > 50:  # 确保检测到的是有效的人脸宽度
                        self.faceWidth = face_width
                        self.faceDetected = True

                    # 绘制脸部边界框，只有在draw=True时
                    if draw:
                        cv2.line(img, tuple(left_cheek), tuple(right_cheek), (0, 255, 0), 2)
                        img = put_chinese_text(img, f'人脸宽度: {int(face_width)}',
                                             (left_cheek[0], left_cheek[1] - 10),
                                             font_size=20, color=(0, 255, 0))

                break  # 只处理第一个检测到的人脸

    def process_frame(self, draw_details=True):
        """处理单帧图像，返回详细视图和简洁视图"""
        success, img = self.cap.read()
        if not success:
            return None, None

        # 创建两个视图的副本
        img_detailed = img.copy()
        img_clean = img.copy()

        # 检测人脸 - 详细视图显示所有标记，简洁视图不显示
        self.detect_face(img_detailed, draw=draw_details)
        self.detect_face(img_clean, draw=False)

        # 检测所有手部
        allHands_detailed, img_detailed = self.detector.findAllHands(img_detailed, draw=draw_details)
        allHands_clean, img_clean = self.detector.findAllHands(img_clean, draw=False)

        # 重置检测状态
        self.left_hand_detected = False
        self.right_hand_detected = False

        # 处理检测到的每只手
        for hand in allHands_detailed:
            handType = hand['handType']
            lmList = hand['lmList']
            bbox = hand['bbox']

            if len(lmList) == 0:
                continue

            # 计算拇指和食指之间的距离
            length_detailed, img_detailed, line_info_detailed = self.detector.findDistance(4, 8, img_detailed, lmList, draw=True)

            # 在简洁视图中也绘制手指连线
            for hand_clean in allHands_clean:
                if hand_clean['handType'] == handType:
                    length_clean, img_clean, line_info_clean = self.detector.findDistance(4, 8, img_clean, hand_clean['lmList'], draw=True)
                    break

            # 根据手的类型进行不同的控制
            if handType == "Left":  # 左手控制音量
                self.left_hand_detected = True
                self.left_hand_distance = length_detailed

                # 使用人脸宽度更新音量
                self.volume_controller.update_volume_from_distance(length_detailed, self.faceWidth)

                # 在左手附近显示音量信息（中文）
                cx, cy = line_info_detailed[4], line_info_detailed[5]
                img_detailed = put_chinese_text(img_detailed, f'音量: {int(self.volume_controller.volPer)}%',
                                               (cx - 50, cy - 50), font_size=25, color=(0, 255, 0))

                # 在详细视图中显示距离信息
                if self.faceWidth > 0:
                    normalized_length = length_detailed / self.faceWidth
                    cv2.putText(img_detailed, f'Distance: {int(length_detailed)}',
                               (cx - 50, cy - 80), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 2)
                    cv2.putText(img_detailed, f'Normalized: {normalized_length:.2f}',
                               (cx - 50, cy - 100), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 2)

            elif handType == "Right":  # 右手控制亮度
                self.right_hand_detected = True
                self.right_hand_distance = length_detailed

                # 使用人脸宽度更新亮度
                self.update_brightness_from_distance(length_detailed, self.faceWidth)

                # 在右手附近显示亮度信息（中文）
                cx, cy = line_info_detailed[4], line_info_detailed[5]
                img_detailed = put_chinese_text(img_detailed, f'亮度: {int(self.brightness_controller.brightnessPer)}%',
                                               (cx - 50, cy - 50), font_size=25, color=(0, 255, 255))

                # 在详细视图中显示距离信息
                if self.faceWidth > 0:
                    normalized_length = length_detailed / self.faceWidth
                    cv2.putText(img_detailed, f'Distance: {int(length_detailed)}',
                               (cx - 50, cy - 80), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 255), 2)
                    cv2.putText(img_detailed, f'Normalized: {normalized_length:.2f}',
                               (cx - 50, cy - 100), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 255), 2)

        # 添加UI元素
        self._add_ui_elements(img_detailed, True)
        self._add_ui_elements(img_clean, False)

        return img_detailed, img_clean

    def _add_ui_elements(self, img, is_detailed):
        """添加UI元素到图像"""
        # 计算FPS
        cTime = time.time()
        fps = 1 / max(cTime - self.pTime, 0.001)
        self.pTime = cTime

        # 显示FPS（使用原项目样式）
        cv2.putText(img, f'FPS: {int(fps)}', (40, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 3)

        # 只在详细视图中显示控制条
        if is_detailed:
            # 音量控制条（左侧，绿色）- 使用原项目样式
            vol_bar_pos = self.volume_controller.volBar
            vol_per = self.volume_controller.volPer

            # 确保音量控制条位置在有效范围内
            vol_bar_pos = max(150, min(400, vol_bar_pos))

            # 绘制音量控制条边框（更粗的边框，更明显）
            cv2.rectangle(img, (50, 150), (85, 400), (0, 255, 0), 4)  # 绿色边框，更粗

            # 绘制音量控制条填充（从底部向上填充）
            # 计算填充高度，确保填充正确显示
            bar_height = 400 - 150  # 控制条总高度
            fill_height = int((vol_per / 100.0) * bar_height)  # 根据百分比计算填充高度
            fill_top = 400 - fill_height  # 从底部开始填充
            fill_top = max(fill_top, 150)  # 确保不超出边界

            # 绘制填充（确保至少有一点填充显示）
            if fill_height > 0:
                cv2.rectangle(img, (52, fill_top), (83, 398), (0, 255, 0), cv2.FILLED)

            # 添加一个更明显的边框内部轮廓
            cv2.rectangle(img, (51, 151), (84, 399), (255, 255, 255), 1)  # 白色内边框

            cv2.putText(img, f'{int(vol_per)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 3)
            img = put_chinese_text(img, '音量', (40, 130), font_size=25, color=(0, 255, 0))

            # 亮度控制条（音量控制条右侧，紫色）
            brightness_bar_pos = self.brightness_controller.brightnessBar
            brightness_per = self.brightness_controller.brightnessPer

            # 确保亮度控制条位置在有效范围内
            brightness_bar_pos = max(150, min(400, brightness_bar_pos))

            # 亮度控制条位置：音量控制条右侧，间隔20像素
            brightness_left = 85 + 20  # 音量控制条右边界(85) + 间隔(20) = 105
            brightness_right = brightness_left + 35  # 控制条宽度35像素

            # 定义紫色颜色 (BGR格式: 蓝色, 绿色, 红色)
            purple_color = (255, 0, 255)  # 紫色 (高蓝色 + 高红色)

            # 绘制亮度控制条边框（更粗的边框，更明显）
            cv2.rectangle(img, (brightness_left, 150), (brightness_right, 400), purple_color, 4)  # 紫色边框，更粗

            # 绘制亮度控制条填充（从底部向上填充）
            # 计算填充高度，确保填充正确显示
            bar_height = 400 - 150  # 控制条总高度
            fill_height = int((brightness_per / 100.0) * bar_height)  # 根据百分比计算填充高度
            fill_top = 400 - fill_height  # 从底部开始填充
            fill_top = max(fill_top, 150)  # 确保不超出边界

            # 绘制填充（确保至少有一点填充显示）
            if fill_height > 0:
                cv2.rectangle(img, (brightness_left + 2, fill_top), (brightness_right - 2, 398), purple_color, cv2.FILLED)
            else:
                # 即使是0%也显示一个小的底部区域
                cv2.rectangle(img, (brightness_left + 2, 395), (brightness_right - 2, 398), purple_color, cv2.FILLED)

            # 添加一个更明显的边框内部轮廓
            cv2.rectangle(img, (brightness_left + 1, 151), (brightness_right - 1, 399), (255, 255, 255), 1)  # 白色内边框

            # 显示亮度百分比（位置调整到亮度控制条下方）
            cv2.putText(img, f'{int(brightness_per)} %', (brightness_left - 10, 450), cv2.FONT_HERSHEY_COMPLEX, 1, purple_color, 3)

            # 显示亮度标签（位置调整到亮度控制条上方）
            img = put_chinese_text(img, '亮度', (brightness_left - 10, 130), font_size=25, color=purple_color)

            # 显示亮度控制条的调试信息
            cv2.putText(img, f'Brightness: {int(brightness_per)}% Pos: {int(brightness_bar_pos)}',
                       (200, 100), cv2.FONT_HERSHEY_PLAIN, 1, purple_color, 2)

        # 显示手部检测状态（中文）
        left_status = "✓ 左手" if self.left_hand_detected else "✗ 左手"
        right_status = "✓ 右手" if self.right_hand_detected else "✗ 右手"

        left_color = (0, 255, 0) if self.left_hand_detected else (0, 0, 255)
        right_color = (0, 255, 255) if self.right_hand_detected else (0, 0, 255)

        img = put_chinese_text(img, left_status, (40, 80), font_size=25, color=left_color)
        img = put_chinese_text(img, right_status, (40, 110), font_size=25, color=right_color)

        # 显示人脸检测状态（仅在详细视图中）
        if is_detailed:
            face_status = "人脸已检测" if self.faceDetected else "未检测到人脸"
            face_color = (0, 255, 0) if self.faceDetected else (0, 0, 255)
            img = put_chinese_text(img, face_status, (40, 140), font_size=25, color=face_color)

            # 显示人脸宽度信息
            if self.faceDetected:
                img = put_chinese_text(img, f'人脸宽度: {int(self.faceWidth)}',
                                     (40, 170), font_size=20, color=(0, 255, 0))

        # 添加视图标题（使用原项目样式，但保持中文）
        if is_detailed:
            # 使用英文标题避免中文显示问题，但在下方添加中文说明
            cv2.putText(img, "Detailed View", (img.shape[1] - 250, 50),
                        cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
            img = put_chinese_text(img, "详细视图", (img.shape[1] - 250, 80),
                                 font_size=20, color=(0, 0, 255))
        else:
            cv2.putText(img, "Clean View", (img.shape[1] - 200, 50),
                        cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
            img = put_chinese_text(img, "简洁视图", (img.shape[1] - 200, 80),
                                 font_size=20, color=(0, 0, 255))

        # 显示控制说明（中文）
        img = put_chinese_text(img, "左手控制音量 | 右手控制亮度",
                             (img.shape[1] // 2 - 200, img.shape[0] - 30),
                             font_size=25, color=(255, 255, 255))

    def run(self):
        """运行应用程序并显示两个窗口"""
        print("手势双重控制器启动中...")
        print("使用说明：")
        print("- 左手拇指和食指靠近可降低音量，分开可提高音量")
        print("- 右手拇指和食指靠近可降低亮度，分开可提高亮度")
        print("- 按 'q' 键退出程序")

        while True:
            # 处理帧并获取两个视图
            result = self.process_frame(draw_details=True)
            if result is None or result[0] is None:
                break

            img_detailed, img_clean = result

            # 显示两个窗口（使用英文标题避免乱码）
            cv2.imshow("Detailed View - Dual Hand Controller", img_detailed)
            cv2.imshow("Clean View - Dual Hand Controller", img_clean)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()
        print("\n👋 程序已退出")


def main():
    """主函数"""
    print("=" * 60)
    print("🎮 手势双重控制器 - 独立版本")
    print("=" * 60)
    print("🔧 检查依赖库...")

    # 检查必要的依赖库
    required_modules = ['cv2', 'mediapipe', 'numpy', 'pycaw', 'comtypes', 'PIL']

    missing_modules = []

    for module in required_modules:
        try:
            if module == 'cv2':
                import cv2
            elif module == 'mediapipe':
                import mediapipe
            elif module == 'numpy':
                import numpy
            elif module == 'pycaw':
                import pycaw
            elif module == 'comtypes':
                import comtypes
            elif module == 'PIL':
                import PIL
        except ImportError:
            missing_modules.append(module)

    if missing_modules:
        print(f"❌ 缺少必要的依赖库: {', '.join(missing_modules)}")
        print("请运行以下命令安装：")
        print("pip install opencv-python mediapipe numpy pycaw comtypes Pillow")
        print("pip install wmi  # 可选，用于更好的亮度控制")
        return

    print("✅ 所有必要依赖库已安装")
    print("=" * 60)

    try:
        controller = DualHandController()
        controller.run()
    except KeyboardInterrupt:
        print("\n⚠️ 程序被用户中断")
    except Exception as e:
        print(f"❌ 程序运行出错: {e}")
        import traceback
        traceback.print_exc()
        print("请确保已安装所有必需的依赖库：")
        print("pip install opencv-python mediapipe numpy pycaw comtypes wmi")


if __name__ == "__main__":
    main()
