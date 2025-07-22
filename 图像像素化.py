import cv2
import os
import sys
import numpy as np
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QFileDialog, QSlider, QStackedWidget, 
                             QFrame, QSplitter)
from PySide6.QtCore import Qt, QTimer, Signal, Slot, QSize
from PySide6.QtGui import QImage, QPixmap, QIcon, QColor, QPalette, QFont, QFontDatabase

class PixelateApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 设置应用风格
        self.setWindowTitle("清新像素化工具")
        self.setMinimumSize(1000, 600)
        
        # 设置应用颜色方案
        self.COLORS = {
            "primary": "#4ECCA3",    # 薄荷绿
            "secondary": "#E4F1FE",  # 浅蓝
            "light_gray": "#EAEAEA", # 浅灰
            "accent": "#2C786C",     # 深绿
            "text_dark": "#333333",  # 深灰
            "text_medium": "#666666",# 中灰
            "background": "#F5F8FA"  # 背景色
        }
        
        # 设置应用背景色
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(self.COLORS["background"]))
        self.setPalette(palette)
        
        # 初始化UI
        self.setup_ui()
        
        # 初始化变量
        self.pixel_size = 16
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.current_frame = None
        self.pixelated_frame = None
        self.image_path = None
        
    def setup_ui(self):
        # 创建主窗口部件
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # 创建标题
        title_label = QLabel("清新像素化工具")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            color: {self.COLORS["accent"]};
            margin-bottom: 10px;
        """)
        
        # 创建功能选择区域
        self.stacked_widget = QStackedWidget()
        
        # 创建主菜单页面
        menu_page = QWidget()
        menu_layout = QHBoxLayout(menu_page)
        menu_layout.setSpacing(16)
        
        # 创建三个功能卡片
        self.create_feature_card(menu_layout, "处理图片", "打开并像素化图片文件", self.open_image_page)
        self.create_feature_card(menu_layout, "处理视频", "打开并像素化视频文件", self.open_video_page)
        self.create_feature_card(menu_layout, "摄像头", "实时像素化摄像头画面", self.open_webcam_page)
        
        # 添加主菜单到堆叠窗口
        self.stacked_widget.addWidget(menu_page)
        
        # 创建图片处理页面
        self.image_page = self.create_processing_page("图片")
        self.stacked_widget.addWidget(self.image_page)
        
        # 创建视频处理页面
        self.video_page = self.create_processing_page("视频")
        self.stacked_widget.addWidget(self.video_page)
        
        # 创建摄像头处理页面
        self.webcam_page = self.create_processing_page("摄像头")
        self.stacked_widget.addWidget(self.webcam_page)
        
        # 添加堆叠窗口到主布局
        main_layout.addWidget(title_label)
        main_layout.addWidget(self.stacked_widget)
        
        # 设置中央窗口部件
        self.setCentralWidget(central_widget)
    
    def create_feature_card(self, parent_layout, title, description, callback):
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 10px;
                border: 1px solid {self.COLORS["light_gray"]};
            }}
            QFrame:hover {{
                border: 1px solid {self.COLORS["primary"]};
                background-color: {self.COLORS["secondary"]};
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        
        # 标题
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {self.COLORS["accent"]};
            padding: 10px;
        """)
        
        # 描述
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"""
            font-size: 14px;
            color: {self.COLORS["text_medium"]};
            padding: 5px 15px;
        """)
        
        # 按钮
        button = QPushButton("选择")
        button.setCursor(Qt.PointingHandCursor)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.COLORS["primary"]};
                color: white;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.COLORS["accent"]};
            }}
            QPushButton:pressed {{
                margin: 1px;
            }}
        """)
        button.clicked.connect(callback)
        
        # 添加到卡片布局
        card_layout.addWidget(title_label)
        card_layout.addWidget(desc_label)
        card_layout.addWidget(button, 0, Qt.AlignCenter)
        card_layout.addStretch()
        
        # 添加到父布局
        parent_layout.addWidget(card)
        return card
    
    def create_processing_page(self, mode):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # 创建预览区域
        preview_splitter = QSplitter(Qt.Horizontal)
        
        # 原始图像/视频显示
        original_frame = QFrame()
        original_frame.setFrameShape(QFrame.StyledPanel)
        original_frame.setStyleSheet(f"""
            background-color: white;
            border-radius: 8px;
            border: 1px solid {self.COLORS["light_gray"]};
        """)
        original_layout = QVBoxLayout(original_frame)
        
        original_title = QLabel("原始" + mode)
        original_title.setAlignment(Qt.AlignCenter)
        original_title.setStyleSheet(f"color: {self.COLORS['text_dark']}; font-weight: bold;")
        
        original_display = QLabel()
        original_display.setAlignment(Qt.AlignCenter)
        original_display.setMinimumSize(400, 300)
        original_display.setStyleSheet("background-color: black;")
        
        original_layout.addWidget(original_title)
        original_layout.addWidget(original_display)
        
        # 像素化图像/视频显示
        pixelated_frame = QFrame()
        pixelated_frame.setFrameShape(QFrame.StyledPanel)
        pixelated_frame.setStyleSheet(f"""
            background-color: white;
            border-radius: 8px;
            border: 1px solid {self.COLORS["light_gray"]};
        """)
        pixelated_layout = QVBoxLayout(pixelated_frame)
        
        pixelated_title = QLabel("像素化" + mode)
        pixelated_title.setAlignment(Qt.AlignCenter)
        pixelated_title.setStyleSheet(f"color: {self.COLORS['text_dark']}; font-weight: bold;")
        
        pixelated_display = QLabel()
        pixelated_display.setAlignment(Qt.AlignCenter)
        pixelated_display.setMinimumSize(400, 300)
        pixelated_display.setStyleSheet("background-color: black;")
        
        pixelated_layout.addWidget(pixelated_title)
        pixelated_layout.addWidget(pixelated_display)
        
        # 添加到分割器
        preview_splitter.addWidget(original_frame)
        preview_splitter.addWidget(pixelated_frame)
        
        # 控制面板
        control_panel = QFrame()
        control_panel.setFrameShape(QFrame.StyledPanel)
        control_panel.setStyleSheet(f"""
            background-color: white;
            border-radius: 8px;
            border: 1px solid {self.COLORS["light_gray"]};
            padding: 10px;
        """)
        control_layout = QVBoxLayout(control_panel)
        
        # 像素大小控制
        pixel_control_layout = QHBoxLayout()
        pixel_size_label = QLabel("像素大小:")
        pixel_size_label.setStyleSheet(f"color: {self.COLORS['text_dark']};")
        
        pixel_slider = QSlider(Qt.Horizontal)
        pixel_slider.setMinimum(2)
        pixel_slider.setMaximum(64)
        pixel_slider.setValue(16)
        pixel_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 1px solid {self.COLORS["light_gray"]};
                height: 8px;
                background: {self.COLORS["secondary"]};
                margin: 2px 0;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {self.COLORS["primary"]};
                border: 1px solid {self.COLORS["accent"]};
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }}
        """)
        
        pixel_value = QLabel("16")
        pixel_value.setMinimumWidth(30)
        pixel_value.setAlignment(Qt.AlignCenter)
        pixel_value.setStyleSheet(f"""
            color: {self.COLORS["accent"]};
            font-weight: bold;
            background-color: {self.COLORS["secondary"]};
            border-radius: 4px;
            padding: 2px 8px;
        """)
        
        pixel_control_layout.addWidget(pixel_size_label)
        pixel_control_layout.addWidget(pixel_slider)
        pixel_control_layout.addWidget(pixel_value)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 打开文件按钮
        open_button = QPushButton("打开" + mode)
        if mode == "摄像头":
            open_button.setText("启动摄像头")
        open_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.COLORS["primary"]};
                color: white;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.COLORS["accent"]};
            }}
            QPushButton:pressed {{
                margin: 1px;
            }}
        """)
        
        # 保存按钮
        save_button = QPushButton("保存")
        save_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.COLORS["accent"]};
                color: white;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.COLORS["text_dark"]};
            }}
            QPushButton:pressed {{
                margin: 1px;
            }}
        """)
        
        # 返回按钮
        back_button = QPushButton("返回")
        back_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.COLORS["light_gray"]};
                color: {self.COLORS["text_dark"]};
                border-radius: 8px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {self.COLORS["text_medium"]};
                color: white;
            }}
            QPushButton:pressed {{
                margin: 1px;
            }}
        """)
        back_button.clicked.connect(self.back_to_menu)
        
        button_layout.addWidget(open_button)
        button_layout.addWidget(save_button)
        button_layout.addWidget(back_button)
        button_layout.addStretch()
        
        # 添加到控制面板
        control_layout.addLayout(pixel_control_layout)
        control_layout.addLayout(button_layout)
        
        # 添加到主布局
        layout.addWidget(preview_splitter, 1)
        layout.addWidget(control_panel, 0)
        
        # 存储页面中的控件引用
        if mode == "图片":
            self.image_original_display = original_display
            self.image_pixelated_display = pixelated_display
            self.image_pixel_slider = pixel_slider
            self.image_pixel_value = pixel_value
            self.image_open_button = open_button
            self.image_save_button = save_button
            
            # 连接信号
            self.image_pixel_slider.valueChanged.connect(self.update_image_pixel_size)
            self.image_open_button.clicked.connect(self.open_image)
            self.image_save_button.clicked.connect(self.save_image)
            
        elif mode == "视频":
            self.video_original_display = original_display
            self.video_pixelated_display = pixelated_display
            self.video_pixel_slider = pixel_slider
            self.video_pixel_value = pixel_value
            self.video_open_button = open_button
            self.video_save_button = save_button
            
            # 连接信号
            self.video_pixel_slider.valueChanged.connect(self.update_video_pixel_size)
            self.video_open_button.clicked.connect(self.open_video)
            self.video_save_button.clicked.connect(self.save_video_frame)
            
        elif mode == "摄像头":
            self.webcam_original_display = original_display
            self.webcam_pixelated_display = pixelated_display
            self.webcam_pixel_slider = pixel_slider
            self.webcam_pixel_value = pixel_value
            self.webcam_open_button = open_button
            self.webcam_save_button = save_button
            
            # 连接信号
            self.webcam_pixel_slider.valueChanged.connect(self.update_webcam_pixel_size)
            self.webcam_open_button.clicked.connect(self.toggle_webcam)
            self.webcam_save_button.clicked.connect(self.save_webcam_frame)
        
        return page
    
    def back_to_menu(self):
        # 停止任何正在进行的处理
        if self.cap is not None:
            self.timer.stop()
            self.cap.release()
            self.cap = None
        
        # 返回主菜单
        self.stacked_widget.setCurrentIndex(0)
    
    def open_image_page(self):
        self.stacked_widget.setCurrentIndex(1)
    
    def open_video_page(self):
        self.stacked_widget.setCurrentIndex(2)
    
    def open_webcam_page(self):
        self.stacked_widget.setCurrentIndex(3)
    
    def pixelate_frame(self, frame, pixel_size):
        """对图像进行像素化处理"""
        if frame is None:
            return None
        
        h, w = frame.shape[:2]
        temp = cv2.resize(frame, (w // pixel_size, h // pixel_size), interpolation=cv2.INTER_LINEAR)
        return cv2.resize(temp, (w, h), interpolation=cv2.INTER_NEAREST)
    
    def convert_cv_to_pixmap(self, cv_img):
        """将OpenCV图像转换为QPixmap"""
        if cv_img is None:
            return QPixmap()
        
        h, w, ch = cv_img.shape
        bytes_per_line = ch * w
        convert_to_qt_format = QImage(cv_img.data, w, h, bytes_per_line, QImage.Format_BGR888)
        return QPixmap.fromImage(convert_to_qt_format)
    
    def display_image(self, label, image):
        """在QLabel上显示图像，保持纵横比"""
        if image is None:
            return
        
        pixmap = self.convert_cv_to_pixmap(image)
        label_size = label.size()
        scaled_pixmap = pixmap.scaled(label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label.setPixmap(scaled_pixmap)
    
    # 图片处理功能
    def open_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if file_path:
            self.image_path = file_path
            self.current_frame = cv2.imread(file_path)
            self.update_image_pixel_size(self.image_pixel_slider.value())
    
    def update_image_pixel_size(self, value):
        self.pixel_size = value
        self.image_pixel_value.setText(str(value))
        
        if self.current_frame is not None:
            self.pixelated_frame = self.pixelate_frame(self.current_frame, self.pixel_size)
            self.display_image(self.image_original_display, self.current_frame)
            self.display_image(self.image_pixelated_display, self.pixelated_frame)
    
    def save_image(self):
        if self.pixelated_frame is None:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存像素化图片", "", "JPEG (*.jpg);;PNG (*.png)"
        )
        
        if file_path:
            cv2.imwrite(file_path, self.pixelated_frame)
    
    # 视频处理功能
    def open_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频", "", "视频文件 (*.mp4 *.avi *.mkv *.mov)"
        )
        
        if file_path:
            # 停止之前的视频
            if self.cap is not None:
                self.timer.stop()
                self.cap.release()
            
            # 打开新视频
            self.cap = cv2.VideoCapture(file_path)
            if self.cap.isOpened():
                self.timer.start(33)  # ~30fps
    
    def update_video_pixel_size(self, value):
        self.pixel_size = value
        self.video_pixel_value.setText(str(value))
    
    def save_video_frame(self):
        if self.pixelated_frame is None:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存当前帧", "", "JPEG (*.jpg);;PNG (*.png)"
        )
        
        if file_path:
            cv2.imwrite(file_path, self.pixelated_frame)
    
    # 摄像头功能
    def toggle_webcam(self):
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)
            if self.cap.isOpened():
                self.webcam_open_button.setText("停止摄像头")
                self.timer.start(33)  # ~30fps
        else:
            self.timer.stop()
            self.cap.release()
            self.cap = None
            self.webcam_open_button.setText("启动摄像头")
            # 清空显示
            self.webcam_original_display.clear()
            self.webcam_pixelated_display.clear()
    
    def update_webcam_pixel_size(self, value):
        self.pixel_size = value
        self.webcam_pixel_value.setText(str(value))
    
    def save_webcam_frame(self):
        if self.pixelated_frame is None:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存当前帧", "", "JPEG (*.jpg);;PNG (*.png)"
        )
        
        if file_path:
            cv2.imwrite(file_path, self.pixelated_frame)
    
    # 通用视频/摄像头帧更新
    def update_frame(self):
        if self.cap is None or not self.cap.isOpened():
            return
        
        ret, frame = self.cap.read()
        if not ret:
            # 视频结束
            self.timer.stop()
            if self.stacked_widget.currentIndex() == 3:  # 如果是摄像头页面
                self.toggle_webcam()
            return
        
        self.current_frame = frame
        self.pixelated_frame = self.pixelate_frame(frame, self.pixel_size)
        
        # 根据当前页面更新显示
        current_index = self.stacked_widget.currentIndex()
        if current_index == 2:  # 视频页面
            self.display_image(self.video_original_display, frame)
            self.display_image(self.video_pixelated_display, self.pixelated_frame)
        elif current_index == 3:  # 摄像头页面
            self.display_image(self.webcam_original_display, frame)
            self.display_image(self.webcam_pixelated_display, self.pixelated_frame)

def main():
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 创建并显示主窗口
    window = PixelateApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 