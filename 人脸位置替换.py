import cv2
import mediapipe as mp
import os
import random
import numpy as np
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFileDialog, QSlider, QRadioButton,
                             QFrame, QButtonGroup, QLineEdit, QComboBox, QMessageBox)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap, QPalette, QColor

class FaceProcessingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("人脸处理工具")
        self.setMinimumSize(1200, 700)  # 减小最小高度
        
        # 设置应用颜色方案
        self.COLORS = {
            "primary": "#4ECCA3",    # 薄荷绿
            "secondary": "#E4F1FE",  # 浅蓝
            "light_gray": "#EAEAEA", # 浅灰
            "accent": "#2C786C",     # 深绿
            "text_dark": "#333333",  # 深灰
            "background": "#F5F8FA"  # 背景色
        }
        
        # 初始化MediaPipe
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1,
            min_detection_confidence=0.5
        )
        
        # 初始化变量
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.current_frame = None
        self.processed_frame = None
        self.replacement_images = []
        self.pixel_size = 16
        self.mode = "replace"  # 'replace' or 'pixelate'
        self.fps = 0
        self.frame_count = 0
        self.last_time = cv2.getTickCount()
        self.face_count = 0
        
        # 初始化跟踪变量
        self.tracked_faces = []
        self.face_to_image_map = {}
        
        # 添加新的变量
        self.source_type = "camera"  # 'camera', 'image', 'video'
        self.video_path = None
        self.image_path = None
        self.video_writer = None
        self.total_frames = 0
        self.current_frame_pos = 0
        
        # 设置UI
        self.setup_ui()
        
    def setup_ui(self):
        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)  # 减小组件间距
        main_layout.setContentsMargins(10, 10, 10, 10)  # 减小边距
        
        # 创建顶部控制面板
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)
        
        # 创建显示区域
        display_frame = QFrame()
        display_frame.setFrameShape(QFrame.StyledPanel)
        display_frame.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 8px;
                border: 1px solid {self.COLORS['light_gray']};
                padding: 10px;
            }}
        """)
        
        display_layout = QHBoxLayout(display_frame)
        display_layout.setSpacing(10)  # 减小视频显示间距
        
        # 原始视频显示
        original_container = QFrame()
        original_container.setStyleSheet("background-color: black; border-radius: 4px;")
        original_layout = QVBoxLayout(original_container)
        original_layout.setContentsMargins(0, 0, 0, 0)
        
        original_title = QLabel("原始画面")
        original_title.setStyleSheet(f"""
            color: white;
            padding: 5px;
            background-color: {self.COLORS['accent']};
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        """)
        original_title.setAlignment(Qt.AlignCenter)
        
        self.original_display = QLabel()
        self.original_display.setMinimumSize(560, 420)
        self.original_display.setAlignment(Qt.AlignCenter)
        
        original_layout.addWidget(original_title)
        original_layout.addWidget(self.original_display, 1)
        
        # 处理后视频显示
        processed_container = QFrame()
        processed_container.setStyleSheet("background-color: black; border-radius: 4px;")
        processed_layout = QVBoxLayout(processed_container)
        processed_layout.setContentsMargins(0, 0, 0, 0)
        
        processed_title = QLabel("处理后画面")
        processed_title.setStyleSheet(f"""
            color: white;
            padding: 5px;
            background-color: {self.COLORS['accent']};
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        """)
        processed_title.setAlignment(Qt.AlignCenter)
        
        self.processed_display = QLabel()
        self.processed_display.setMinimumSize(560, 420)
        self.processed_display.setAlignment(Qt.AlignCenter)
        
        processed_layout.addWidget(processed_title)
        processed_layout.addWidget(self.processed_display, 1)
        
        display_layout.addWidget(original_container)
        display_layout.addWidget(processed_container)
        
        main_layout.addWidget(display_frame, 1)  # 设置拉伸因子为1
        
        # 创建底部状态栏
        status_frame = QFrame()
        status_frame.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 8px;
                border: 1px solid {self.COLORS['light_gray']};
                padding: 5px;
            }}
        """)
        status_layout = QHBoxLayout(status_frame)
        
        self.status_label = QLabel()
        self.progress_label = QLabel()
        self.status_label.setStyleSheet(f"color: {self.COLORS['text_dark']};")
        self.progress_label.setStyleSheet(f"color: {self.COLORS['text_dark']};")
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.progress_label)
        
        main_layout.addWidget(status_frame)
    
    def create_control_panel(self):
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 8px;
                border: 1px solid {self.COLORS['light_gray']};
                padding: 10px;
            }}
        """)
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)  # 减小控件间距
        
        # 创建两行控制区域
        top_row = QHBoxLayout()
        bottom_row = QHBoxLayout()
        
        # 第一行：输入源和模式选择
        # 输入源选择
        source_group = QFrame()
        source_layout = QHBoxLayout(source_group)
        source_layout.setContentsMargins(0, 0, 0, 0)
        source_label = QLabel("输入源:")
        self.source_combo = QComboBox()
        self.source_combo.addItems(["摄像头", "图片", "视频"])
        self.source_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {self.COLORS['light_gray']};
                border-radius: 4px;
                padding: 4px;
                min-width: 100px;
            }}
        """)
        self.source_combo.currentTextChanged.connect(self.change_source)
        source_layout.addWidget(source_label)
        source_layout.addWidget(self.source_combo)
        
        # 模式选择
        mode_group = QFrame()
        mode_layout = QHBoxLayout(mode_group)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_button_group = QButtonGroup(self)
        
        replace_radio = QRadioButton("人脸替换")
        replace_radio.setChecked(True)
        pixelate_radio = QRadioButton("人脸像素化")
        
        mode_button_group.addButton(replace_radio)
        mode_button_group.addButton(pixelate_radio)
        
        replace_radio.toggled.connect(lambda: self.change_mode("replace"))
        pixelate_radio.toggled.connect(lambda: self.change_mode("pixelate"))
        
        mode_layout.addWidget(replace_radio)
        mode_layout.addWidget(pixelate_radio)
        
        top_row.addWidget(source_group)
        top_row.addStretch()
        top_row.addWidget(mode_group)
        
        # 第二行：文件夹选择和像素大小控制
        # 文件夹选择
        folder_group = QFrame()
        folder_layout = QHBoxLayout(folder_group)
        folder_layout.setContentsMargins(0, 0, 0, 0)
        self.folder_path_input = QLineEdit()
        self.folder_path_input.setPlaceholderText("选择替换图片文件夹...")
        self.folder_path_input.setReadOnly(True)
        self.folder_path_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {self.COLORS['light_gray']};
                border-radius: 4px;
                padding: 4px;
            }}
        """)
        
        folder_button = QPushButton("浏览文件夹")
        folder_button.clicked.connect(self.select_folder)
        folder_button.setStyleSheet(self.get_button_style())
        
        folder_layout.addWidget(self.folder_path_input)
        folder_layout.addWidget(folder_button)
        
        # 像素大小控制
        pixel_group = QFrame()
        pixel_layout = QHBoxLayout(pixel_group)
        pixel_layout.setContentsMargins(0, 0, 0, 0)
        pixel_label = QLabel("像素大小:")
        self.pixel_slider = QSlider(Qt.Horizontal)
        self.pixel_slider.setMinimum(2)
        self.pixel_slider.setMaximum(64)
        self.pixel_slider.setValue(16)
        self.pixel_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 1px solid {self.COLORS['light_gray']};
                height: 8px;
                background: {self.COLORS['secondary']};
                margin: 2px 0;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {self.COLORS['primary']};
                border: 1px solid {self.COLORS['accent']};
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }}
        """)
        self.pixel_slider.valueChanged.connect(self.update_pixel_size)
        
        self.pixel_value_label = QLabel("16")
        self.pixel_value_label.setMinimumWidth(30)
        self.pixel_value_label.setAlignment(Qt.AlignCenter)
        
        pixel_layout.addWidget(pixel_label)
        pixel_layout.addWidget(self.pixel_slider)
        pixel_layout.addWidget(self.pixel_value_label)
        
        bottom_row.addWidget(folder_group)
        bottom_row.addWidget(pixel_group)
        
        # 控制按钮
        button_row = QHBoxLayout()
        
        self.source_button = QPushButton("选择文件")
        self.source_button.clicked.connect(self.select_source)
        self.source_button.setStyleSheet(self.get_button_style())
        self.source_button.hide()  # 默认隐藏
        
        self.start_button = QPushButton("启动摄像头")
        self.start_button.clicked.connect(self.toggle_processing)
        self.start_button.setStyleSheet(self.get_button_style())
        
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.save_output)
        self.save_button.setStyleSheet(self.get_button_style())
        
        button_row.addWidget(self.source_button)
        button_row.addWidget(self.start_button)
        button_row.addWidget(self.save_button)
        button_row.addStretch()
        
        # 添加所有行到主布局
        layout.addLayout(top_row)
        layout.addLayout(bottom_row)
        layout.addLayout(button_row)
        
        return panel
    
    def get_button_style(self):
        return f"""
            QPushButton {{
                background-color: {self.COLORS['primary']};
                color: white;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.COLORS['accent']};
            }}
            QPushButton:pressed {{
                margin: 1px;
            }}
        """
    
    def change_mode(self, mode):
        self.mode = mode
        self.folder_path_input.setEnabled(mode == "replace")
    
    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "选择替换图片文件夹")
        if folder_path:
            self.folder_path_input.setText(folder_path)
            self.load_replacement_images(folder_path)
    
    def load_replacement_images(self, folder_path):
        self.replacement_images = []
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        
        try:
            for filename in os.listdir(folder_path):
                ext = os.path.splitext(filename.lower())[1]
                if ext in valid_extensions:
                    img_path = os.path.join(folder_path, filename)
                    img = cv2.imread(img_path)
                    if img is not None:
                        self.replacement_images.append(img)
            
            if not self.replacement_images:
                raise ValueError("没有找到有效的图片")
                
        except Exception as e:
            self.status_label.setText(f"错误: {str(e)}")
    
    def update_pixel_size(self, value):
        self.pixel_size = value
        self.pixel_value_label.setText(str(value))
    
    def change_source(self, source_text):
        if source_text == "摄像头":
            self.source_type = "camera"
            self.source_button.hide()
            self.start_button.setText("启动摄像头")
        elif source_text == "图片":
            self.source_type = "image"
            self.source_button.show()
            self.source_button.setText("选择图片")
            self.start_button.setText("处理图片")
        else:  # 视频
            self.source_type = "video"
            self.source_button.show()
            self.source_button.setText("选择视频")
            self.start_button.setText("开始处理")
        
        # 停止当前处理
        self.stop_processing()
    
    def select_source(self):
        if self.source_type == "image":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp)"
            )
            if file_path:
                self.image_path = file_path
                self.load_image()
        
        elif self.source_type == "video":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择视频", "", "视频文件 (*.mp4 *.avi *.mkv *.mov)"
            )
            if file_path:
                self.video_path = file_path
                self.prepare_video()
    
    def load_image(self):
        if self.image_path:
            self.current_frame = cv2.imread(self.image_path)
            if self.current_frame is not None:
                self.display_image(self.original_display, self.current_frame)
                self.status_label.setText("图片加载成功")
            else:
                QMessageBox.warning(self, "错误", "无法加载图片")
    
    def prepare_video(self):
        if self.video_path:
            cap = cv2.VideoCapture(self.video_path)
            if cap.isOpened():
                self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                self.current_frame_pos = 0
                cap.release()
                self.status_label.setText(f"视频加载成功: {self.total_frames} 帧")
            else:
                QMessageBox.warning(self, "错误", "无法加载视频")
    
    def toggle_processing(self):
        if self.source_type == "camera":
            self.toggle_camera()
        elif self.source_type == "image":
            self.process_image()
        else:  # video
            if self.timer.isActive():
                self.stop_processing()
            else:
                self.start_video_processing()
    
    def process_image(self):
        if self.current_frame is None:
            return
            
        # 处理图片
        frame_rgb = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(frame_rgb)
        
        processed = self.current_frame.copy()
        self.face_count = 0
        
        if results.detections:
            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box
                h, w = processed.shape[:2]
                
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                width = int(bbox.width * w)
                height = int(bbox.height * h)
                
                # 扩大检测框
                expand_ratio = 0.4
                new_x = max(int(x - width * expand_ratio * 0.5), 0)
                new_y = max(int(y - height * expand_ratio), 0)
                new_w = min(int(width * (1 + expand_ratio)), w - new_x)
                new_h = min(int(height * (1 + expand_ratio)), h - new_y)
                
                if new_w <= 0 or new_h <= 0:
                    continue
                
                self.face_count += 1
                
                if self.mode == "replace" and self.replacement_images:
                    # 随机选择替换图片
                    replacement_image = random.choice(self.replacement_images)
                    
                    # 调整替换图片大小
                    replacement_resized = cv2.resize(replacement_image, (new_w, new_h))
                    
                    # 创建圆角蒙版
                    corner_radius = int(min(new_w, new_h) * 0.2)
                    mask = self.create_rounded_mask(new_w, new_h, corner_radius)
                    mask_3channel = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) / 255.0
                    
                    # 调整颜色
                    replacement_resized = self.match_color_with_background(
                        replacement_resized, processed, new_x, new_y, new_w, new_h
                    )
                    
                    # 混合图像
                    roi = processed[new_y:new_y + new_h, new_x:new_x + new_w]
                    blended = cv2.convertScaleAbs(
                        replacement_resized * mask_3channel + roi * (1 - mask_3channel)
                    )
                    processed[new_y:new_y + new_h, new_x:new_x + new_w] = blended
                    
                elif self.mode == "pixelate":
                    processed = self.pixelate_region(
                        processed, new_x, new_y, new_w, new_h, self.pixel_size
                    )
        
        self.processed_frame = processed
        self.display_image(self.processed_display, processed)
        self.status_label.setText(f"检测到的人脸数: {self.face_count} | "
                                f"模式: {'人脸替换' if self.mode == 'replace' else '人脸像素化'}")
    
    def start_video_processing(self):
        if not self.video_path:
            return
            
        self.cap = cv2.VideoCapture(self.video_path)
        if self.cap.isOpened():
            self.start_button.setText("停止处理")
            self.timer.start(33)  # ~30fps
            self.frame_count = 0
            self.last_time = cv2.getTickCount()
    
    def stop_processing(self):
        if self.timer.isActive():
            self.timer.stop()
        
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None
        
        if self.source_type == "camera":
            self.start_button.setText("启动摄像头")
        elif self.source_type == "video":
            self.start_button.setText("开始处理")
        
        self.original_display.clear()
        self.processed_display.clear()
        self.status_label.setText("")
        self.progress_label.setText("")
    
    def save_output(self):
        if self.processed_frame is None:
            return
        
        if self.source_type == "image":
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存图片", "", "JPEG (*.jpg);;PNG (*.png)"
            )
            if file_path:
                cv2.imwrite(file_path, self.processed_frame)
                
        elif self.source_type == "video":
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存视频", "", "MP4 (*.mp4);;AVI (*.avi)"
            )
            if file_path:
                # 获取原视频的属性
                cap = cv2.VideoCapture(self.video_path)
                fps = cap.get(cv2.CAP_PROP_FPS)
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                cap.release()
                
                # 创建视频写入器
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                self.video_writer = cv2.VideoWriter(file_path, fourcc, fps, (width, height))
                
                # 重新处理视频
                self.process_video_for_saving()
        else:
            # 摄像头模式下保存当前帧
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存当前帧", "", "JPEG (*.jpg);;PNG (*.png)"
            )
            if file_path:
                cv2.imwrite(file_path, self.processed_frame)
    
    def process_video_for_saving(self):
        if not self.video_path or not self.video_writer:
            return
            
        cap = cv2.VideoCapture(self.video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        progress = QMessageBox(self)
        progress.setWindowTitle("处理中")
        progress.setText("正在处理视频...")
        progress.setStandardButtons(QMessageBox.NoButton)
        progress.show()
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # 处理帧
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_detection.process(frame_rgb)
            
            processed = frame.copy()
            if results.detections:
                for detection in results.detections:
                    bbox = detection.location_data.relative_bounding_box
                    h, w = frame.shape[:2]
                    
                    x = int(bbox.xmin * w)
                    y = int(bbox.ymin * h)
                    width = int(bbox.width * w)
                    height = int(bbox.height * h)
                    
                    expand_ratio = 0.4
                    new_x = max(int(x - width * expand_ratio * 0.5), 0)
                    new_y = max(int(y - height * expand_ratio), 0)
                    new_w = min(int(width * (1 + expand_ratio)), w - new_x)
                    new_h = min(int(height * (1 + expand_ratio)), h - new_y)
                    
                    if new_w <= 0 or new_h <= 0:
                        continue
                    
                    if self.mode == "replace" and self.replacement_images:
                        replacement_image = random.choice(self.replacement_images)
                        replacement_resized = cv2.resize(replacement_image, (new_w, new_h))
                        
                        corner_radius = int(min(new_w, new_h) * 0.2)
                        mask = self.create_rounded_mask(new_w, new_h, corner_radius)
                        mask_3channel = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) / 255.0
                        
                        replacement_resized = self.match_color_with_background(
                            replacement_resized, processed, new_x, new_y, new_w, new_h
                        )
                        
                        roi = processed[new_y:new_y + new_h, new_x:new_x + new_w]
                        blended = cv2.convertScaleAbs(
                            replacement_resized * mask_3channel + roi * (1 - mask_3channel)
                        )
                        processed[new_y:new_y + new_h, new_x:new_x + new_w] = blended
                        
                    elif self.mode == "pixelate":
                        processed = self.pixelate_region(
                            processed, new_x, new_y, new_w, new_h, self.pixel_size
                        )
            
            self.video_writer.write(processed)
            frame_count += 1
            
            # 更新进度
            progress.setText(f"正在处理视频... {frame_count}/{total_frames} 帧")
            QApplication.processEvents()
        
        cap.release()
        self.video_writer.release()
        self.video_writer = None
        
        progress.close()
        QMessageBox.information(self, "完成", "视频处理完成！")
    
    def update_frame(self):
        if self.cap is None or not self.cap.isOpened():
            return
            
        ret, frame = self.cap.read()
        if not ret:
            if self.source_type == "video":
                self.stop_processing()
                return
            else:
                self.toggle_camera()
                return
        
        # 更新进度（仅视频模式）
        if self.source_type == "video":
            self.current_frame_pos += 1
            progress = (self.current_frame_pos / self.total_frames) * 100
            self.progress_label.setText(f"进度: {progress:.1f}% ({self.current_frame_pos}/{self.total_frames})")
        
        # 计算FPS
        self.frame_count += 1
        if self.frame_count >= 30:
            current_time = cv2.getTickCount()
            time_diff = (current_time - self.last_time) / cv2.getTickFrequency()
            self.fps = self.frame_count / time_diff
            self.frame_count = 0
            self.last_time = current_time
        
        # 处理帧
        self.current_frame = frame
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(frame_rgb)
        
        processed = frame.copy()
        current_faces = []
        self.face_count = 0
        
        if results.detections:
            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box
                h, w = frame.shape[:2]
                
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                width = int(bbox.width * w)
                height = int(bbox.height * h)
                
                expand_ratio = 0.4
                new_x = max(int(x - width * expand_ratio * 0.5), 0)
                new_y = max(int(y - height * expand_ratio), 0)
                new_w = min(int(width * (1 + expand_ratio)), w - new_x)
                new_h = min(int(height * (1 + expand_ratio)), h - new_y)
                
                if new_w <= 0 or new_h <= 0:
                    continue
                    
                current_faces.append((new_x, new_y, new_w, new_h))
                self.face_count += 1
        
        # 处理检测到的人脸
        matched_faces = []
        unmatched_current_faces = list(range(len(current_faces)))
        new_tracked_faces = []
        
        for i, (face_id, old_face_box) in enumerate(self.tracked_faces):
            best_match = -1
            best_iou = 0.3
            
            for j in unmatched_current_faces:
                iou = self.calculate_iou(old_face_box, current_faces[j])
                if iou > best_iou:
                    best_iou = iou
                    best_match = j
            
            if best_match >= 0:
                matched_faces.append((face_id, best_match))
                unmatched_current_faces.remove(best_match)
                new_tracked_faces.append((face_id, current_faces[best_match]))
        
        for j in unmatched_current_faces:
            new_face_id = len(self.face_to_image_map) + 1
            if new_face_id not in self.face_to_image_map and self.replacement_images:
                self.face_to_image_map[new_face_id] = random.randint(0, len(self.replacement_images) - 1)
            new_tracked_faces.append((new_face_id, current_faces[j]))
        
        self.tracked_faces = new_tracked_faces
        
        # 应用处理效果
        for face_id, (new_x, new_y, new_w, new_h) in self.tracked_faces:
            if self.mode == "replace" and self.replacement_images:
                if face_id not in self.face_to_image_map:
                    self.face_to_image_map[face_id] = random.randint(0, len(self.replacement_images) - 1)
                
                replacement_idx = self.face_to_image_map[face_id]
                replacement_image = self.replacement_images[replacement_idx % len(self.replacement_images)]
                
                replacement_resized = cv2.resize(replacement_image, (new_w, new_h))
                
                corner_radius = int(min(new_w, new_h) * 0.2)
                mask = self.create_rounded_mask(new_w, new_h, corner_radius)
                mask_3channel = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) / 255.0
                
                replacement_resized = self.match_color_with_background(
                    replacement_resized, processed, new_x, new_y, new_w, new_h
                )
                
                roi = processed[new_y:new_y + new_h, new_x:new_x + new_w]
                blended = cv2.convertScaleAbs(
                    replacement_resized * mask_3channel + roi * (1 - mask_3channel)
                )
                processed[new_y:new_y + new_h, new_x:new_x + new_w] = blended
                
            elif self.mode == "pixelate":
                processed = self.pixelate_region(
                    processed, new_x, new_y, new_w, new_h, self.pixel_size
                )
        
        # 更新状态信息
        status_text = f"FPS: {self.fps:.1f} | 检测到的人脸数: {self.face_count} | "
        status_text += f"模式: {'人脸替换' if self.mode == 'replace' else '人脸像素化'} | "
        status_text += f"像素大小: {self.pixel_size}"
        
        if self.source_type == "video":
            status_text += f" | 帧: {self.current_frame_pos}/{self.total_frames}"
        
        self.status_label.setText(status_text)
        
        # 显示图像
        self.display_image(self.original_display, frame)
        self.display_image(self.processed_display, processed)
        self.processed_frame = processed
    
    def display_image(self, label, image):
        if image is None:
            return
            
        h, w = image.shape[:2]
        bytes_per_line = 3 * w
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        qt_image = QImage(image_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label.setPixmap(scaled_pixmap)

    def toggle_camera(self):
        if self.cap is None or not self.cap.isOpened():
            try:
                self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # 使用DirectShow后端
                if not self.cap.isOpened():
                    raise Exception("无法打开摄像头")
                    
                self.start_button.setText("停止摄像头")
                self.timer.start(33)  # ~30fps
                self.frame_count = 0
                self.last_time = cv2.getTickCount()
                self.status_label.setText("摄像头已启动")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"摄像头启动失败: {str(e)}")
                self.cap = None
        else:
            self.stop_processing()
            self.start_button.setText("启动摄像头")
            self.status_label.setText("摄像头已停止")

    def calculate_iou(self, box1, box2):
        """计算两个边界框的IoU（交并比）"""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        
        # 计算交集区域
        xx1 = max(x1, x2)
        yy1 = max(y1, y2)
        xx2 = min(x1 + w1, x2 + w2)
        yy2 = min(y1 + h1, y2 + h2)
        
        # 计算交集面积
        intersection_area = max(0, xx2 - xx1) * max(0, yy2 - yy1)
        
        # 计算并集面积
        box1_area = w1 * h1
        box2_area = w2 * h2
        union_area = box1_area + box2_area - intersection_area
        
        if union_area == 0:
            return 0
        
        return intersection_area / union_area
    
    def pixelate_region(self, image, x, y, w, h, pixel_size):
        """对指定区域进行像素化处理"""
        region = image[y:y+h, x:x+w]
        temp = cv2.resize(region, (w // pixel_size, h // pixel_size), interpolation=cv2.INTER_LINEAR)
        pixelated = cv2.resize(temp, (w, h), interpolation=cv2.INTER_NEAREST)
        result = image.copy()
        result[y:y+h, x:x+w] = pixelated
        return result
    
    def create_rounded_mask(self, width, height, radius):
        """创建圆角蒙版"""
        mask = np.zeros((height, width), dtype=np.uint8)
        cv2.rectangle(mask, (radius, 0), (width-radius, height), 255, -1)
        cv2.rectangle(mask, (0, radius), (width, height-radius), 255, -1)
        cv2.circle(mask, (radius, radius), radius, 255, -1)
        cv2.circle(mask, (width-radius, radius), radius, 255, -1)
        cv2.circle(mask, (radius, height-radius), radius, 255, -1)
        cv2.circle(mask, (width-radius, height-radius), radius, 255, -1)
        return mask
    
    def match_color_with_background(self, replacement_img, background_img, x, y, w, h):
        """调整替换图片的颜色以匹配背景"""
        background_region = background_img[max(0, y-10):min(background_img.shape[0], y+h+10),
                                        max(0, x-10):min(background_img.shape[1], x+w+10)]
        background_mean = np.mean(background_region, axis=(0, 1))
        replacement_mean = np.mean(replacement_img, axis=(0, 1))
        color_diff = background_mean - replacement_mean
        adjusted_img = replacement_img.astype(np.float32)
        adjusted_img += color_diff * 0.3
        return np.clip(adjusted_img, 0, 255).astype(np.uint8)

def main():
    app = QApplication([])
    window = FaceProcessingApp()
    window.show()
    app.exec()

if __name__ == "__main__":
    main()
