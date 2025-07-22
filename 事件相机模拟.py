import cv2
import numpy as np
import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QSlider, QPushButton, QRadioButton, QButtonGroup, QFrame,
    QSizePolicy, QSpacerItem, QFileDialog, QGridLayout, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QImage, QPixmap, QFont, QKeyEvent


class EventOverlayFusionUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 修改配色方案
        self.colors = {
            "light_bg": "#FFFFFF",     # 白色（背景）
            "light_blue": "#A8D8F3",   # 浅蓝色（按钮）
            "light_yellow": "#FFE0A8", # 浅黄色（高亮）
            "light_purple": "#E0D8F0"  # 浅紫色（强调，替代浅粉色）
        }
        
        # 初始化变量
        self.cap = None
        self.old_frame_gray = None
        self.video_path = "2.mp4"  # 默认视频文件
        self.output_path = ""  # 默认为空，让用户选择
        self.video_writer = None
        self.is_recording = False
        self.is_direct_fusion = True  # 默认使用直接融合模式
        self.alpha = 0.7  # 默认透明度
        self.frame_id = 0
        self.threshold = 30
        self.ratio_threshold = 1.0
        self.visualization_mode = 0  # 默认可视化模式 (0: RGB, 1: HSV, 2: 热力图)
        self.resolution = (1024, 512)  # 默认分辨率
        self.fps = 30  # 默认帧率
        self.is_portrait = False  # 默认为横屏模式
        self.particle_size = 1  # 默认粒子大小为1
        
        # 初始化视频处理定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.process_frame)
        
        # 设置快捷键
        self.shortcut_keys = {}
        
        # 初始化界面 - 确保在变量初始化之后调用
        self.setWindowTitle("事件图像融合器")
        self.setMinimumSize(1200, 800)
        self.setup_ui()
        
    def setup_ui(self):
        # 修改整体样式
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {self.colors['light_bg']};
            }}
            QLabel {{
                color: #000000;
                font-size: 14px;
            }}
            QPushButton {{
                background-color: {self.colors['light_blue']};
                color: #000000;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.colors['light_yellow']};
            }}
            QPushButton:pressed {{
                background-color: {self.colors['light_purple']};
            }}
            QRadioButton {{
                color: #000000;
                font-size: 14px;
                spacing: 8px;
            }}
            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 2px solid {self.colors['light_blue']};
            }}
            QRadioButton::indicator:checked {{
                background-color: {self.colors['light_purple']};
                border: 2px solid {self.colors['light_blue']};
            }}
            QSlider::groove:horizontal {{
                border: 1px solid #BBBBBB;
                height: 10px;
                background: #FFFFFF;
                margin: 0px;
                border-radius: 5px;
            }}
            QSlider::handle:horizontal {{
                background: {self.colors['light_purple']};
                border: 1px solid #BBBBBB;
                width: 18px;
                margin: -4px 0;
                border-radius: 9px;
            }}
            QFrame#video_frame {{
                background-color: #FFFFFF;
                border: 2px solid {self.colors['light_blue']};
                border-radius: 10px;
            }}
        """)
        
        # 主窗口布局
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # 视频显示区域 - 使用网格布局
        video_section = QWidget()
        video_layout = QGridLayout(video_section)
        video_layout.setContentsMargins(0, 0, 0, 0)
        video_layout.setSpacing(15)
        
        # 原始视频帧
        original_frame = QFrame()
        original_frame.setObjectName("video_frame")
        original_layout = QVBoxLayout(original_frame)
        original_layout.setContentsMargins(5, 5, 5, 5)
        
        original_title = QLabel("原始视频")
        original_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        original_title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: #000000;")
        
        self.original_view = QLabel()
        self.original_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.original_view.setMinimumSize(300, 300)
        self.original_view.setStyleSheet("background-color: #000000;")
        
        original_layout.addWidget(original_title, 0)
        original_layout.addWidget(self.original_view, 1)
        
        # 灰度事件图像
        gray_event_frame = QFrame()
        gray_event_frame.setObjectName("video_frame")
        gray_event_layout = QVBoxLayout(gray_event_frame)
        gray_event_layout.setContentsMargins(5, 5, 5, 5)
        
        gray_event_title = QLabel("灰度事件图像")
        gray_event_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gray_event_title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: #000000;")
        
        self.gray_event_view = QLabel()
        self.gray_event_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gray_event_view.setMinimumSize(300, 300)
        self.gray_event_view.setStyleSheet("background-color: #000000;")
        
        gray_event_layout.addWidget(gray_event_title, 0)
        gray_event_layout.addWidget(self.gray_event_view, 1)
        
        # 彩色事件图像
        event_frame = QFrame()
        event_frame.setObjectName("video_frame")
        event_layout = QVBoxLayout(event_frame)
        event_layout.setContentsMargins(5, 5, 5, 5)
        
        event_title = QLabel("彩色事件图像")
        event_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        event_title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: #000000;")
        
        self.event_view = QLabel()
        self.event_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.event_view.setMinimumSize(300, 300)
        self.event_view.setStyleSheet("background-color: #000000;")
        
        event_layout.addWidget(event_title, 0)
        event_layout.addWidget(self.event_view, 1)
        
        # 融合结果
        fusion_frame = QFrame()
        fusion_frame.setObjectName("video_frame")
        fusion_layout = QVBoxLayout(fusion_frame)
        fusion_layout.setContentsMargins(5, 5, 5, 5)
        
        fusion_title = QLabel("融合结果")
        fusion_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fusion_title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: #000000;")
        
        self.fusion_view = QLabel()
        self.fusion_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fusion_view.setMinimumSize(300, 300)
        self.fusion_view.setStyleSheet("background-color: #000000;")
        
        fusion_layout.addWidget(fusion_title, 0)
        fusion_layout.addWidget(self.fusion_view, 1)
        
        # 将视频窗口添加到网格布局
        video_layout.addWidget(original_frame, 0, 0)
        video_layout.addWidget(gray_event_frame, 0, 1)
        video_layout.addWidget(event_frame, 1, 0)
        video_layout.addWidget(fusion_frame, 1, 1)
        
        # 控制区域
        control_section = QWidget()
        control_layout = QVBoxLayout(control_section)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(15)
        
        # 文件选择区域
        file_frame = QWidget()
        file_layout = QHBoxLayout(file_frame)
        file_layout.setContentsMargins(0, 0, 0, 0)
        
        self.select_video_btn = QPushButton("选择视频文件")
        self.select_video_btn.clicked.connect(self.select_video)
        
        # 添加摄像头选择按钮
        self.camera_btn = QPushButton("使用摄像头")
        self.camera_btn.clicked.connect(self.use_camera)
        
        self.select_output_btn = QPushButton("选择输出位置")
        self.select_output_btn.clicked.connect(self.select_output)
        
        self.video_path_label = QLabel("当前视频: 2.mp4")
        self.output_path_label = QLabel("输出文件: 未选择")
        
        # 添加组件到文件布局
        file_layout.addWidget(self.select_video_btn)
        file_layout.addWidget(self.camera_btn)
        file_layout.addWidget(self.video_path_label)
        file_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        file_layout.addWidget(self.select_output_btn)
        file_layout.addWidget(self.output_path_label)
        
        # 添加事件阈值控制
        threshold_frame = QWidget()
        threshold_layout = QHBoxLayout(threshold_frame)
        threshold_layout.setContentsMargins(0, 0, 0, 0)
        
        threshold_label = QLabel("事件阈值:")
        threshold_label.setStyleSheet("font-weight: bold;")
        
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(5, 100)
        self.threshold_slider.setValue(30)
        self.threshold_slider.valueChanged.connect(self.update_threshold)
        
        self.threshold_value_label = QLabel("30")
        
        threshold_layout.addWidget(threshold_label)
        threshold_layout.addWidget(self.threshold_slider)
        threshold_layout.addWidget(self.threshold_value_label)
        
        # 添加粒子大小控制
        particle_frame = QWidget()
        particle_layout = QHBoxLayout(particle_frame)
        particle_layout.setContentsMargins(0, 0, 0, 0)
        
        particle_label = QLabel("粒子大小:")
        particle_label.setStyleSheet("font-weight: bold;")
        
        self.particle_slider = QSlider(Qt.Orientation.Horizontal)
        self.particle_slider.setRange(1, 10)
        self.particle_slider.setValue(1)
        self.particle_slider.valueChanged.connect(self.update_particle_size)
        
        self.particle_value_label = QLabel("1")
        
        particle_layout.addWidget(particle_label)
        particle_layout.addWidget(self.particle_slider)
        particle_layout.addWidget(self.particle_value_label)
        
        # 添加分辨率选择
        resolution_frame = QWidget()
        resolution_layout = QHBoxLayout(resolution_frame)
        resolution_layout.setContentsMargins(0, 0, 0, 0)
        
        resolution_label = QLabel("分辨率:")
        resolution_label.setStyleSheet("font-weight: bold;")
        
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItem("1024 x 512 (默认)")
        self.resolution_combo.addItem("640 x 360 (流畅)")
        self.resolution_combo.addItem("1280 x 720 (高清)")
        self.resolution_combo.addItem("1920 x 1080 (全高清)")
        self.resolution_combo.currentIndexChanged.connect(self.change_resolution)
        
        fps_label = QLabel("帧率:")
        fps_label.setStyleSheet("font-weight: bold;")
        
        self.fps_combo = QComboBox()
        self.fps_combo.addItem("30 FPS")
        self.fps_combo.addItem("15 FPS (省电)")
        self.fps_combo.addItem("60 FPS (高流畅)")
        self.fps_combo.currentIndexChanged.connect(self.change_fps)
        
        resolution_layout.addWidget(resolution_label)
        resolution_layout.addWidget(self.resolution_combo)
        resolution_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        resolution_layout.addWidget(fps_label)
        resolution_layout.addWidget(self.fps_combo)
        
        # 融合模式选择
        mode_frame = QWidget()
        mode_layout = QHBoxLayout(mode_frame)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        
        mode_label = QLabel("融合模式:")
        mode_label.setStyleSheet("font-weight: bold;")
        
        self.direct_mode_radio = QRadioButton("直接叠加")
        self.direct_mode_radio.setChecked(True)
        self.direct_mode_radio.toggled.connect(self.mode_changed)
        
        self.alpha_mode_radio = QRadioButton("半透明叠加")
        self.alpha_mode_radio.toggled.connect(self.mode_changed)
        
        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.direct_mode_radio)
        self.mode_group.addButton(self.alpha_mode_radio)
        
        # 添加事件可视化模式选择
        viz_label = QLabel("可视化方式:")
        viz_label.setStyleSheet("font-weight: bold;")
        
        self.viz_mode_combo = QComboBox()
        self.viz_mode_combo.addItem("RGB颜色编码")
        self.viz_mode_combo.addItem("HSV颜色编码")
        self.viz_mode_combo.addItem("热力图编码")
        self.viz_mode_combo.currentIndexChanged.connect(self.change_visualization_mode)
        
        # 透明度滑块
        self.alpha_label = QLabel("透明度:")
        self.alpha_label.setStyleSheet("font-weight: bold;")
        
        self.alpha_slider = QSlider(Qt.Orientation.Horizontal)
        self.alpha_slider.setRange(0, 100)
        self.alpha_slider.setValue(70)
        self.alpha_slider.valueChanged.connect(self.update_alpha)
        
        self.alpha_value_label = QLabel("70%")
        
        # 添加到模式布局
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.direct_mode_radio)
        mode_layout.addWidget(self.alpha_mode_radio)
        mode_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        mode_layout.addWidget(viz_label)
        mode_layout.addWidget(self.viz_mode_combo)
        mode_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        mode_layout.addWidget(self.alpha_label)
        mode_layout.addWidget(self.alpha_slider)
        mode_layout.addWidget(self.alpha_value_label)
        
        # 播放控制区域
        playback_frame = QWidget()
        playback_layout = QHBoxLayout(playback_frame)
        playback_layout.setContentsMargins(0, 0, 0, 0)
        
        self.play_btn = QPushButton("播放")
        self.play_btn.clicked.connect(self.toggle_playback)
        self.play_btn.setStyleSheet(f"""
            background-color: {self.colors['light_blue']};
            min-width: 120px;
        """)
        
        self.record_btn = QPushButton("开始录制")
        self.record_btn.clicked.connect(self.toggle_recording)
        self.record_btn.setStyleSheet(f"""
            background-color: {self.colors['light_purple']};
            min-width: 120px;
        """)
        
        self.status_label = QLabel("状态: 就绪")
        self.status_label.setStyleSheet("font-weight: bold;")
        
        playback_layout.addWidget(self.play_btn)
        playback_layout.addWidget(self.record_btn)
        playback_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        playback_layout.addWidget(self.status_label)
        
        # 添加控制区域组件
        control_layout.addWidget(file_frame)
        control_layout.addWidget(threshold_frame)
        control_layout.addWidget(particle_frame)
        control_layout.addWidget(resolution_frame)
        control_layout.addWidget(mode_frame)
        control_layout.addWidget(playback_frame)
        
        # 添加到主布局
        main_layout.addWidget(video_section, 3)  # 视频区域占3份
        main_layout.addWidget(control_section, 1)  # 控制区域占1份
        
        # 设置中央窗口
        self.setCentralWidget(central_widget)
        
        # 更新UI状态
        self.update_ui_state()
    
    def keyPressEvent(self, event: QKeyEvent):
        # ESC键退出程序
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
    
    def select_video(self):
        """选择视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择视频文件", 
            "", 
            "视频文件 (*.mp4 *.avi *.mov *.mkv);;所有文件 (*)"
        )
        
        if file_path:
            self.video_path = file_path
            self.video_path_label.setText(f"当前视频: {os.path.basename(file_path)}")
            self.status_label.setText("状态: 已加载视频")
            
            # 如果视频正在播放，重新开始
            if self.timer.isActive():
                self.stop_playback()
                self.start_playback()
            
            self.frame_id = 0
    
    def use_camera(self):
        """使用摄像头作为输入源"""
        self.video_path = 0  # OpenCV中0表示默认摄像头
        self.video_path_label.setText("当前输入: 摄像头")
        self.status_label.setText("状态: 已选择摄像头")
        
        # 如果视频正在播放，重新开始
        if self.timer.isActive():
            self.stop_playback()
            self.start_playback()
        
        self.frame_id = 0
    
    def select_output(self):
        """选择输出文件位置"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "选择输出位置", 
            "", 
            "视频文件 (*.mp4 *.avi)"
        )
        
        if file_path:
            if not (file_path.lower().endswith('.mp4') or file_path.lower().endswith('.avi')):
                file_path += '.mp4'  # 默认使用MP4格式
            
            self.output_path = file_path
            self.output_path_label.setText(f"输出文件: {os.path.basename(file_path)}")
            
            # 如果正在录制，更新视频写入器
            if self.is_recording and self.video_writer is not None:
                self.video_writer.release()
                self.video_writer = None
                self.setup_video_writer()
                
            self.status_label.setText(f"状态: 已设置输出到 {os.path.basename(file_path)}")
            return True
        return False
    
    def update_threshold(self, value):
        """更新事件阈值"""
        self.threshold = value
        self.threshold_value_label.setText(str(value))
    
    def update_particle_size(self, value):
        """更新事件粒子大小"""
        self.particle_size = value
        self.particle_value_label.setText(str(value))
    
    def mode_changed(self):
        """融合模式变更"""
        self.is_direct_fusion = self.direct_mode_radio.isChecked()
        self.alpha_slider.setEnabled(not self.is_direct_fusion)
        self.alpha_label.setEnabled(not self.is_direct_fusion)
        self.alpha_value_label.setEnabled(not self.is_direct_fusion)
    
    def update_alpha(self, value):
        """更新透明度值"""
        self.alpha = value / 100.0
        self.alpha_value_label.setText(f"{value}%")
    
    def toggle_playback(self):
        """切换播放/暂停状态"""
        if self.timer.isActive():
            self.stop_playback()
        else:
            self.start_playback()
    
    def start_playback(self):
        """开始播放"""
        # 初始化摄像头或视频源
        if self.cap is not None:
            self.cap.release()
        
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            self.status_label.setText("状态: 无法打开视频文件")
            return
        
        # 读取第一帧作为参考
        ret, old_frame = self.cap.read()
        if not ret:
            self.status_label.setText("状态: 无法读取视频帧")
            self.cap.release()
            self.cap = None
            return
        
        # 检测视频方向，判断是否为竖屏视频
        height, width = old_frame.shape[:2]
        self.is_portrait = height > width
        
        # 根据视频方向设置合适的分辨率
        if self.is_portrait:
            # 竖屏视频，交换宽高
            index = self.resolution_combo.currentIndex()
            portrait_resolutions = [
                (512, 1024),    # 默认竖屏
                (360, 640),     # 流畅竖屏
                (720, 1280),    # 高清竖屏
                (1080, 1920)    # 全高清竖屏
            ]
            if 0 <= index < len(portrait_resolutions):
                self.resolution = portrait_resolutions[index]
        
        # 调整尺寸并转为灰度图
        old_frame = cv2.resize(old_frame, self.resolution)
        self.old_frame_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
        
        # 重置帧计数
        self.frame_id = 0
        
        # 启动定时器，使用当前帧率设置
        interval = int(1000 / self.fps)
        self.timer.start(interval)
        
        # 更新UI
        self.play_btn.setText("暂停")
        self.status_label.setText(f"状态: 播放中 ({'竖屏' if self.is_portrait else '横屏'})")
    
    def stop_playback(self):
        """停止播放"""
        self.timer.stop()
        self.play_btn.setText("播放")
        self.status_label.setText("状态: 已暂停")
    
    def toggle_recording(self):
        """切换录制状态"""
        if self.is_recording:
            self.stop_recording()
        else:
            # 检查是否已选择输出文件
            if not self.output_path:
                # 提示用户选择输出文件
                QMessageBox.warning(self, "未选择输出文件", "请先选择一个输出文件位置再开始录制。")
                self.select_output()
                # 如果用户取消或仍未选择，则不继续录制
                if not self.output_path:
                    return
            
            self.start_recording()
    
    def start_recording(self):
        """开始录制"""
        self.is_recording = True
        self.setup_video_writer()
        
        self.record_btn.setText("停止录制")
        self.record_btn.setStyleSheet(f"""
            background-color: {self.colors['light_purple']};
            min-width: 120px;
        """)
        
        # 如果没有播放，开始播放
        if not self.timer.isActive():
            self.start_playback()
        
        self.status_label.setText(f"状态: 录制中... ({os.path.basename(self.output_path)})")
    
    def stop_recording(self):
        """停止录制"""
        self.is_recording = False
        
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None
        
        self.record_btn.setText("开始录制")
        self.record_btn.setStyleSheet(f"""
            background-color: {self.colors['light_purple']};
            min-width: 120px;
        """)
        
        self.status_label.setText("状态: 录制已停止")
    
    def setup_video_writer(self):
        """设置视频写入器"""
        if self.video_writer is not None:
            self.video_writer.release()
        
        # 初始化视频写入器
        if self.output_path.lower().endswith('.mp4'):
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # MP4格式
        else:
            fourcc = cv2.VideoWriter_fourcc(*'XVID')  # AVI格式
            
        # 使用当前分辨率和帧率
        self.video_writer = cv2.VideoWriter(self.output_path, fourcc, self.fps, self.resolution)
    
    def change_visualization_mode(self, index):
        """更改事件可视化模式"""
        self.visualization_mode = index
    
    def change_resolution(self, index):
        """更改视频处理分辨率"""
        # 横屏分辨率
        landscape_resolutions = [
            (1024, 512),  # 默认
            (640, 360),   # 流畅
            (1280, 720),  # 高清
            (1920, 1080)  # 全高清
        ]
        
        # 竖屏分辨率
        portrait_resolutions = [
            (512, 1024),  # 默认竖屏
            (360, 640),   # 流畅竖屏
            (720, 1280),  # 高清竖屏
            (1080, 1920)  # 全高清竖屏
        ]
        
        if 0 <= index < len(landscape_resolutions):
            # 根据当前视频方向选择合适的分辨率
            if self.is_portrait:
                self.resolution = portrait_resolutions[index]
            else:
                self.resolution = landscape_resolutions[index]
            
            # 重新启动播放以应用新分辨率
            if self.timer.isActive():
                self.stop_playback()
                self.start_playback()
    
    def change_fps(self, index):
        """更改视频处理帧率"""
        fps_values = [30, 15, 60]
        
        if 0 <= index < len(fps_values):
            self.fps = fps_values[index]
            
            # 更新定时器间隔
            if self.timer.isActive():
                self.timer.stop()
                # 计算毫秒间隔 (1000ms / fps)
                interval = int(1000 / self.fps)
                self.timer.start(interval)
    
    def process_frame(self):
        """处理当前帧并更新显示"""
        if self.cap is None or not self.cap.isOpened():
            self.stop_playback()
            return
        
        # 读取当前帧
        ret, frame = self.cap.read()
        if not ret:
            # 如果是视频文件(不是摄像头)，则循环播放
            if isinstance(self.video_path, str):
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                if not ret:
                    self.stop_playback()
                    return
            else:
                self.stop_playback()
                return
        
        # 检测视频方向
        height, width = frame.shape[:2]
        current_is_portrait = height > width
        
        # 如果视频方向发生变化，调整分辨率
        if current_is_portrait != self.is_portrait:
            self.is_portrait = current_is_portrait
            # 更新分辨率
            index = self.resolution_combo.currentIndex()
            if self.is_portrait:
                portrait_resolutions = [(512, 1024), (360, 640), (720, 1280), (1080, 1920)]
                if 0 <= index < len(portrait_resolutions):
                    self.resolution = portrait_resolutions[index]
            else:
                landscape_resolutions = [(1024, 512), (640, 360), (1280, 720), (1920, 1080)]
                if 0 <= index < len(landscape_resolutions):
                    self.resolution = landscape_resolutions[index]
        
        # 调整尺寸以优化性能
        frame = cv2.resize(frame, self.resolution)
        
        # 转为灰度图用于事件检测
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 计算帧间差异
        diff = frame_gray.astype(int) - self.old_frame_gray.astype(int)
        increase = np.clip(diff, 0, 255).astype(np.uint8)
        decrease = np.clip(-diff, 0, 255).astype(np.uint8)

        # 阈值判断 - 使用用户设定的阈值
        increase_event = (increase > self.threshold).astype(np.uint8) * 255
        decrease_event = (decrease > self.threshold).astype(np.uint8) * 255

        # 应用粒子大小参数 - 使用形态学操作来调整粒子大小
        if self.particle_size > 1:
            kernel = np.ones((self.particle_size, self.particle_size), np.uint8)
            increase_event = cv2.dilate(increase_event, kernel, iterations=1)
            decrease_event = cv2.dilate(decrease_event, kernel, iterations=1)

        # 创建灰度事件图像 (类似于event_camera_demo函数中的实现)
        gray_event_img = (frame_gray.astype(int) - self.old_frame_gray.astype(int)) + 50
        gray_event_img = np.clip(gray_event_img, 0, 255).astype(np.uint8)
        
        # 根据选择的可视化模式创建事件图像
        event_img = np.zeros_like(frame)
        
        if self.visualization_mode == 0:  # RGB模式
            # 构造彩色事件图像（红：增强，蓝：减弱，绿：同时变化）
            event_img[:, :, 2] = increase_event  # R通道
            event_img[:, :, 0] = decrease_event  # B通道
            event_img[:, :, 1] = ((increase_event > 0) & (decrease_event > 0)).astype(np.uint8) * 255  # G通道
        
        elif self.visualization_mode == 1:  # HSV模式
            # 使用HSV颜色空间进行事件编码
            event_hsv = np.zeros_like(frame)
            
            # 正向事件: 色调设为红色范围 (0-30)
            # 负向事件: 色调设为蓝色范围 (210-240)
            # 同时发生: 色调设为绿色范围 (120-150)
            event_hsv[:, :, 0] = np.zeros_like(increase_event)  # 初始化H通道
            event_hsv[:, :, 1] = np.ones_like(increase_event) * 255  # S通道最大
            event_hsv[:, :, 2] = np.zeros_like(increase_event)  # 初始化V通道
            
            # 设置正向事件
            pos_mask = (increase_event > 0)
            event_hsv[pos_mask, 0] = 0  # 红色
            event_hsv[pos_mask, 2] = 255  # 亮度最大
            
            # 设置负向事件
            neg_mask = (decrease_event > 0)
            event_hsv[neg_mask, 0] = 120  # 蓝色
            event_hsv[neg_mask, 2] = 255  # 亮度最大
            
            # 设置同时发生事件
            both_mask = (increase_event > 0) & (decrease_event > 0)
            event_hsv[both_mask, 0] = 60  # 绿色
            event_hsv[both_mask, 2] = 255  # 亮度最大
            
            # 转换回BGR
            event_img = cv2.cvtColor(event_hsv, cv2.COLOR_HSV2BGR)
        
        elif self.visualization_mode == 2:  # 热力图模式
            # 创建热力图可视化
            # 正向变化用暖色调，负向变化用冷色调
            combined_event = np.zeros_like(increase)
            combined_event = increase - decrease + 128  # 中性值为128
            
            # 应用伪彩色映射
            heatmap = cv2.applyColorMap(combined_event, cv2.COLORMAP_JET)
            
            # 只在有事件的地方显示热力图
            event_mask = (increase > self.threshold) | (decrease > self.threshold)
            event_img = np.zeros_like(frame)
            event_img[event_mask] = heatmap[event_mask]

        # 事件像素数统计
        increase_count = np.sum(increase_event) / 255.0
        decrease_count = np.sum(decrease_event) / 255.0
        total_pixels = frame.shape[0] * frame.shape[1]

        # 创建融合图像
        event_mask = (event_img[:,:,0] > 0) | (event_img[:,:,1] > 0) | (event_img[:,:,2] > 0)
        fusion_img = frame.copy()
        
        # 确保mask非空才进行操作
        if np.any(event_mask):
            if self.is_direct_fusion:
                # 直接叠加模式
                fusion_img[event_mask] = event_img[event_mask]
            else:
                # 半透明叠加模式
                mask_indices = np.where(event_mask)
                frame_masked = frame[mask_indices]
                event_masked = event_img[mask_indices]
                
                if len(frame_masked) > 0 and len(event_masked) > 0:
                    blended = cv2.addWeighted(
                        frame_masked, 1.0 - self.alpha,
                        event_masked, self.alpha,
                        0
                    )
                    fusion_img[mask_indices] = blended

        # 添加提示信息
        if increase_count > decrease_count * self.ratio_threshold:
            cv2.putText(fusion_img, '++!Event!++', (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 2)
        elif decrease_count > increase_count * self.ratio_threshold:
            cv2.putText(fusion_img, '--!Event!--', (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 0, 0), 2)
        elif (increase_count + decrease_count) / total_pixels > 0.05:
            cv2.putText(fusion_img, 'Significant Change', (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        # 添加帧序号和阈值信息
        self.frame_id += 1
        cv2.putText(fusion_img, f'Frame: {self.frame_id} | Threshold: {self.threshold} | Particle: {self.particle_size}', 
                    (30, frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 1)
        
        # 更新显示
        self.update_display(frame, gray_event_img, event_img, fusion_img)
        
        # 保存融合结果
        if self.is_recording and self.video_writer is not None:
            self.video_writer.write(fusion_img)
        
        # 当前帧更新为旧帧
        self.old_frame_gray = frame_gray.copy()
    
    def update_display(self, frame, gray_event_img, event_img, fusion_img):
        """更新界面上的图像显示"""
        # 转换为RGB格式用于显示
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 将灰度事件图像转为彩色用于显示
        gray_event_rgb = cv2.cvtColor(gray_event_img, cv2.COLOR_GRAY2RGB)
        
        event_rgb = cv2.cvtColor(event_img, cv2.COLOR_BGR2RGB)
        fusion_rgb = cv2.cvtColor(fusion_img, cv2.COLOR_BGR2RGB)
        
        # 创建QImage
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        
        q_img_frame = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        q_img_gray_event = QImage(gray_event_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        q_img_event = QImage(event_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        q_img_fusion = QImage(fusion_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        
        # 更新标签显示
        self.original_view.setPixmap(QPixmap.fromImage(q_img_frame).scaled(
            self.original_view.width(), self.original_view.height(),
            Qt.AspectRatioMode.KeepAspectRatio
        ))
        
        self.gray_event_view.setPixmap(QPixmap.fromImage(q_img_gray_event).scaled(
            self.gray_event_view.width(), self.gray_event_view.height(),
            Qt.AspectRatioMode.KeepAspectRatio
        ))
        
        self.event_view.setPixmap(QPixmap.fromImage(q_img_event).scaled(
            self.event_view.width(), self.event_view.height(),
            Qt.AspectRatioMode.KeepAspectRatio
        ))
        
        self.fusion_view.setPixmap(QPixmap.fromImage(q_img_fusion).scaled(
            self.fusion_view.width(), self.fusion_view.height(),
            Qt.AspectRatioMode.KeepAspectRatio
        ))
    
    def update_ui_state(self):
        """更新UI控件状态"""
        # 初始状态下，透明度控制禁用
        self.alpha_slider.setEnabled(not self.is_direct_fusion)
        self.alpha_label.setEnabled(not self.is_direct_fusion)
        self.alpha_value_label.setEnabled(not self.is_direct_fusion)
    
    def closeEvent(self, event):
        """程序关闭时的处理"""
        # 停止播放和录制
        if self.timer.isActive():
            self.timer.stop()
        
        if self.cap is not None:
            self.cap.release()
        
        if self.video_writer is not None:
            self.video_writer.release()
        
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EventOverlayFusionUI()
    window.show()
    sys.exit(app.exec()) 