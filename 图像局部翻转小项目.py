#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立图像动画生成器 - 完整版
包含核心动画功能和GUI界面，无需外部依赖文件
"""

import sys
import os
import threading
import traceback
import random
from datetime import datetime

# 图像处理库
import cv2
import numpy as np

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QGroupBox, QPushButton, QLineEdit, QFileDialog, 
    QComboBox, QSpinBox, QProgressBar, QTextEdit, QMessageBox,
    QGridLayout, QFrame
)
from PySide6.QtCore import Qt, Signal, QObject, QThread
from PySide6.QtGui import QPixmap, QImage


# ==================== 核心动画功能 ====================

def alpha_blend(src, dst, alpha):
    """Alpha blending 两张图"""
    return cv2.addWeighted(src, 1 - alpha, dst, alpha, 0)


def create_animation(
    animation_mode: str,
    original_path: str,
    final_path: str = None,
    pool_folder: str = None,
    output_video: str = "animation_output.mp4",
    frame_rate: int = 20,
    grid_size: tuple = (4, 4),
    total_steps: int = None,
    blend_frames: int = 10,
    target_resolution: tuple = None,
    progress_callback=None,
    frame_callback=None
):
    """
    创建一个包含三种不同模式的图像过渡动画。
    """
    # --- 1. 参数验证 ---
    MODES = ['local_invert', 'scripted_invert', 'random_patch']
    if animation_mode not in MODES:
        raise ValueError(f"无效的动画模式: {animation_mode}. 可选模式: {MODES}")

    if not os.path.exists(original_path):
        raise FileNotFoundError(f"原始图像不存在: {original_path}")

    if animation_mode in ['local_invert', 'scripted_invert']:
        if not final_path:
            raise ValueError(f"模式 '{animation_mode}' 需要 'final_path' 参数.")
        if not os.path.exists(final_path):
            raise FileNotFoundError(f"最终图像不存在: {final_path}")
            
    if animation_mode in ['scripted_invert', 'random_patch']:
        if not pool_folder:
            raise ValueError(f"模式 '{animation_mode}' 需要 'pool_folder' 参数.")
        if not os.path.isdir(pool_folder):
            raise FileNotFoundError(f"图像池文件夹不存在: {pool_folder}")

    # --- 2. 图像加载与预处理 ---
    original = cv2.imread(original_path)
    if original is None:
        raise ValueError(f"原始图像读取失败: {original_path}")

    final_image = None
    if final_path:
        final_image = cv2.imread(final_path)
        if final_image is None:
            raise ValueError(f"最终图像读取失败: {final_path}")

    original_h, original_w = original.shape[:2]

    if target_resolution:
        target_w, target_h = target_resolution
    else:
        if original_h > original_w:
            target_h, target_w = 1080, 720
        else:
            target_h, target_w = 720, 1080
    
    original = cv2.resize(original, (target_w, target_h), interpolation=cv2.INTER_AREA)
    if final_image is not None:
        final_image = cv2.resize(final_image, (target_w, target_h), interpolation=cv2.INTER_AREA)

    h, w = original.shape[:2]
    canvas = original.copy()

    # --- 3. 加载图像池 ---
    pool_images = []
    if pool_folder:
        for f in os.listdir(pool_folder):
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                img_path = os.path.join(pool_folder, f)
                img = cv2.imread(img_path)
                if img is not None:
                    pool_images.append(img)
        if not pool_images:
            raise ValueError("图像池为空或所有图像无法读取")

    # --- 4. 视频和网格设置 ---
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_out = cv2.VideoWriter(output_video, fourcc, frame_rate, (w, h))

    grid_h = h // grid_size[0]
    grid_w = w // grid_size[1]
    
    grid_positions = [(j * grid_w, i * grid_h, grid_w, grid_h) for i in range(grid_size[0]) for j in range(grid_size[1])]
    random.shuffle(grid_positions)

    if total_steps is None:
        total_steps = len(grid_positions)
    else:
        total_steps = min(total_steps, len(grid_positions))

    # --- 5. 主循环和动画逻辑 ---
    for step in range(total_steps):
        if progress_callback:
            progress_callback(step, total_steps)
        
        x, y, width, height = grid_positions[step]

        # -- 模式: local_invert --
        if animation_mode == 'local_invert':
            current_region = canvas[y:y+height, x:x+width].copy()
            final_region = final_image[y:y+height, x:x+width].copy()
            for i in range(1, blend_frames + 1):
                alpha = i / blend_frames
                blended = alpha_blend(current_region, final_region, alpha)
                canvas[y:y+height, x:x+width] = blended
                video_out.write(canvas.copy())
                if frame_callback:
                    frame_callback(canvas.copy())
        
        # -- 模式: scripted_invert --
        elif animation_mode == 'scripted_invert':
            # 阶段一: 原始 -> 随机图
            old_region = canvas[y:y+height, x:x+width].copy()
            replacement = random.choice(pool_images)
            resized = cv2.resize(replacement, (width, height), interpolation=cv2.INTER_AREA)
            for i in range(1, blend_frames + 1):
                alpha = i / blend_frames
                blended = alpha_blend(old_region, resized, alpha)
                canvas[y:y+height, x:x+width] = blended
                video_out.write(canvas.copy())
                if frame_callback:
                    frame_callback(canvas.copy())
            
            # 阶段二: 随机图 -> 最终图
            current_region = canvas[y:y+height, x:x+width].copy()
            final_region = final_image[y:y+height, x:x+width].copy()
            for i in range(1, blend_frames + 1):
                alpha = i / blend_frames
                blended = alpha_blend(current_region, final_region, alpha)
                canvas[y:y+height, x:x+width] = blended
                video_out.write(canvas.copy())
                if frame_callback:
                    frame_callback(canvas.copy())

        # -- 模式: random_patch --
        elif animation_mode == 'random_patch':
            old_region = canvas[y:y+height, x:x+width].copy()
            replacement = random.choice(pool_images)
            resized = cv2.resize(replacement, (width, height), interpolation=cv2.INTER_AREA)
            for i in range(1, blend_frames + 1):
                alpha = i / blend_frames
                blended = alpha_blend(old_region, resized, alpha)
                canvas[y:y+height, x:x+width] = blended
                video_out.write(canvas.copy())
                if frame_callback:
                    frame_callback(canvas.copy())

    # --- 6. 结尾和清理 ---
    end_image = final_image if final_image is not None else original
    for _ in range(frame_rate):
        video_out.write(end_image)

    video_out.release()

    if progress_callback:
        progress_callback(total_steps, total_steps)


# ==================== 演示文件创建功能 ====================

def create_demo_files():
    """创建演示文件"""
    print("正在创建演示文件...")
    
    # 创建原始图像 - 蓝色背景
    original = np.zeros((400, 600, 3), dtype=np.uint8)
    original[:, :] = [200, 150, 100]  # 浅棕色
    cv2.rectangle(original, (150, 100), (450, 300), (100, 200, 255), -1)  # 浅橙色矩形
    cv2.putText(original, "Original Image", (200, 220), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.imwrite("demo_original.png", original)
    
    # 创建最终图像 - 绿色背景
    final = np.zeros((400, 600, 3), dtype=np.uint8)
    final[:, :] = [150, 200, 150]  # 浅绿色
    cv2.circle(final, (300, 200), 80, (100, 255, 200), -1)  # 浅青色圆形
    cv2.putText(final, "Final Image", (220, 220), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.imwrite("demo_final.png", final)
    
    # 创建图像池文件夹
    os.makedirs("demo_image_pool", exist_ok=True)
    
    # 创建多个池图像
    colors = [
        ([255, 200, 200], "Red"),      # 浅红色
        ([200, 255, 200], "Green"),    # 浅绿色
        ([200, 200, 255], "Blue"),     # 浅蓝色
        ([255, 255, 200], "Yellow"),   # 浅黄色
        ([255, 200, 255], "Magenta"),  # 浅洋红色
    ]
    
    for i, (color, name) in enumerate(colors):
        pool_img = np.zeros((200, 300, 3), dtype=np.uint8)
        pool_img[:, :] = color
        cv2.putText(pool_img, name, (80, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 100, 100), 2)
        cv2.imwrite(f"demo_image_pool/pool_{i+1}_{name.lower()}.png", pool_img)
    
    print("✓ 演示文件创建完成")
    return True


# ==================== GUI界面部分 ====================

class WorkerSignals(QObject):
    """工作线程信号"""
    progress = Signal(int, int)  # 当前步骤, 总步骤
    finished = Signal(str)       # 输出文件路径
    error = Signal(str)          # 错误信息
    frame_update = Signal(object)  # 当前帧图像数据


class AnimationWorker(QThread):
    """动画生成工作线程"""
    def __init__(self, params):
        super().__init__()
        self.params = params
        self.signals = WorkerSignals()

    def run(self):
        try:
            def progress_callback(step, total):
                self.signals.progress.emit(step, total)

            def frame_callback(frame_data):
                self.signals.frame_update.emit(frame_data)

            self.params['progress_callback'] = progress_callback
            self.params['frame_callback'] = frame_callback
            create_animation(**self.params)
            self.signals.finished.emit(self.params['output_video'])
        except Exception as e:
            self.signals.error.emit(f"生成失败: {str(e)}\n{traceback.format_exc()}")


class StandaloneAnimationStudio(QMainWindow):
    """独立图像动画生成器主界面"""

    def __init__(self):
        super().__init__()
        self.worker = None
        self.init_ui()
        self.setup_styles()

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("图像动画生成器 - 独立版")
        self.setGeometry(100, 100, 1000, 750)
        self.setMinimumSize(900, 650)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title_label = QLabel("🎬 图像动画生成器 - 独立版")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin: 10px;")
        main_layout.addWidget(title_label)

        # 创建主要内容区域
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # 左侧控制面板
        left_panel = self.create_control_panel()
        content_layout.addWidget(left_panel, 2)

        # 右侧状态面板
        right_panel = self.create_status_panel()
        content_layout.addWidget(right_panel, 1)

        main_layout.addLayout(content_layout)

    def create_control_panel(self):
        """创建左侧控制面板"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Box)
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)

        # 动画模式选择
        mode_group = QGroupBox("🎭 动画模式")
        mode_layout = QVBoxLayout(mode_group)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "局部反转 (local_invert)",
            "剧本翻转 (scripted_invert)",
            "随机补丁 (random_patch)"
        ])
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(self.mode_combo)

        # 模式说明
        self.mode_desc = QLabel()
        self.mode_desc.setWordWrap(True)
        self.mode_desc.setStyleSheet("color: #7f8c8d; font-size: 12px; padding: 5px;")
        mode_layout.addWidget(self.mode_desc)

        layout.addWidget(mode_group)

        # 文件设置
        file_group = QGroupBox("📁 文件设置")
        file_layout = QGridLayout(file_group)

        # 原始图像
        file_layout.addWidget(QLabel("原始图像:"), 0, 0)
        self.original_edit = QLineEdit()
        self.original_edit.setPlaceholderText("选择原始图像文件...")
        file_layout.addWidget(self.original_edit, 0, 1)
        self.original_btn = QPushButton("浏览")
        self.original_btn.clicked.connect(lambda: self.browse_file(self.original_edit, "图像"))
        file_layout.addWidget(self.original_btn, 0, 2)

        # 最终图像
        file_layout.addWidget(QLabel("最终图像:"), 1, 0)
        self.final_edit = QLineEdit()
        self.final_edit.setPlaceholderText("选择最终图像文件...")
        file_layout.addWidget(self.final_edit, 1, 1)
        self.final_btn = QPushButton("浏览")
        self.final_btn.clicked.connect(lambda: self.browse_file(self.final_edit, "图像"))
        file_layout.addWidget(self.final_btn, 1, 2)

        # 图像池文件夹
        file_layout.addWidget(QLabel("图像池:"), 2, 0)
        self.pool_edit = QLineEdit()
        self.pool_edit.setPlaceholderText("选择图像池文件夹...")
        file_layout.addWidget(self.pool_edit, 2, 1)
        self.pool_btn = QPushButton("浏览")
        self.pool_btn.clicked.connect(lambda: self.browse_folder(self.pool_edit))
        file_layout.addWidget(self.pool_btn, 2, 2)

        # 输出文件
        file_layout.addWidget(QLabel("输出视频:"), 3, 0)
        self.output_edit = QLineEdit()
        self.output_edit.setText("animation_output.mp4")
        file_layout.addWidget(self.output_edit, 3, 1)
        self.output_btn = QPushButton("保存为")
        self.output_btn.clicked.connect(lambda: self.save_file(self.output_edit))
        file_layout.addWidget(self.output_btn, 3, 2)

        layout.addWidget(file_group)

        # 参数设置
        param_group = QGroupBox("⚙️ 参数设置")
        param_layout = QGridLayout(param_group)

        # 帧率
        param_layout.addWidget(QLabel("帧率:"), 0, 0)
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 60)
        self.fps_spin.setValue(20)
        self.fps_spin.setSuffix(" fps")
        param_layout.addWidget(self.fps_spin, 0, 1)

        # 网格大小
        param_layout.addWidget(QLabel("网格 (行×列):"), 0, 2)
        grid_layout = QHBoxLayout()
        self.grid_rows = QSpinBox()
        self.grid_rows.setRange(1, 20)
        self.grid_rows.setValue(5)
        self.grid_cols = QSpinBox()
        self.grid_cols.setRange(1, 20)
        self.grid_cols.setValue(5)
        grid_layout.addWidget(self.grid_rows)
        grid_layout.addWidget(QLabel("×"))
        grid_layout.addWidget(self.grid_cols)
        param_layout.addLayout(grid_layout, 0, 3)

        # 动画步数
        param_layout.addWidget(QLabel("动画步数:"), 1, 0)
        self.steps_spin = QSpinBox()
        self.steps_spin.setRange(1, 400)
        self.steps_spin.setValue(25)
        param_layout.addWidget(self.steps_spin, 1, 1)

        # 过渡帧数
        param_layout.addWidget(QLabel("过渡帧数:"), 1, 2)
        self.blend_spin = QSpinBox()
        self.blend_spin.setRange(1, 60)
        self.blend_spin.setValue(12)
        param_layout.addWidget(self.blend_spin, 1, 3)

        layout.addWidget(param_group)

        # 操作按钮
        button_layout = QHBoxLayout()

        # 创建演示文件按钮
        self.demo_btn = QPushButton("🎨 创建演示文件")
        self.demo_btn.clicked.connect(self.create_demo_files)
        self.demo_btn.setStyleSheet("background-color: #f39c12; color: white;")

        self.generate_btn = QPushButton("🚀 开始生成动画")
        self.generate_btn.clicked.connect(self.start_generation)
        self.generate_btn.setMinimumHeight(40)

        self.stop_btn = QPushButton("⏹️ 停止")
        self.stop_btn.clicked.connect(self.stop_generation)
        self.stop_btn.setEnabled(False)

        button_layout.addWidget(self.demo_btn)
        button_layout.addWidget(self.generate_btn)
        button_layout.addWidget(self.stop_btn)
        layout.addLayout(button_layout)

        layout.addStretch()

        # 初始化模式
        self.on_mode_changed(0)

        return panel

    def create_status_panel(self):
        """创建右侧状态面板"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Box)
        layout = QVBoxLayout(panel)

        # 实时预览
        preview_group = QGroupBox("🖼️ 实时预览")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_label = QLabel()
        self.preview_label.setMinimumSize(300, 200)
        self.preview_label.setMaximumSize(400, 300)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #bdc3c7;
                border-radius: 8px;
                background-color: #f8f9fa;
                color: #7f8c8d;
                font-size: 14px;
            }
        """)
        self.preview_label.setText("预览窗口\n\n生成时将显示\n实时动画帧")
        self.preview_label.setScaledContents(True)
        preview_layout.addWidget(self.preview_label)

        layout.addWidget(preview_group)

        # 进度显示
        progress_group = QGroupBox("📊 生成进度")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(25)
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("准备就绪")
        self.progress_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.progress_label)

        layout.addWidget(progress_group)

        # 日志显示
        log_group = QGroupBox("📋 运行日志")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)

        # 帮助按钮
        help_btn = QPushButton("❓ 使用帮助")
        help_btn.clicked.connect(self.show_help)
        layout.addWidget(help_btn)

        layout.addStretch()

        return panel

    def setup_styles(self):
        """设置界面样式 - 浅色系主题"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }

            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #ffffff;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #495057;
                background-color: #ffffff;
            }

            QPushButton {
                background-color: #e3f2fd;
                border: 2px solid #bbdefb;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                color: #1565c0;
                font-weight: 500;
            }

            QPushButton:hover {
                background-color: #bbdefb;
                border-color: #90caf9;
            }

            QPushButton:pressed {
                background-color: #90caf9;
            }

            QPushButton:disabled {
                background-color: #f5f5f5;
                border-color: #e0e0e0;
                color: #9e9e9e;
            }

            QLineEdit {
                border: 2px solid #e0e0e0;
                border-radius: 4px;
                padding: 6px;
                background-color: #ffffff;
                font-size: 13px;
            }

            QLineEdit:focus {
                border-color: #2196f3;
            }

            QComboBox, QSpinBox {
                border: 2px solid #e0e0e0;
                border-radius: 4px;
                padding: 6px;
                background-color: #ffffff;
                font-size: 13px;
            }

            QComboBox:focus, QSpinBox:focus {
                border-color: #2196f3;
            }

            QProgressBar {
                border: 2px solid #e0e0e0;
                border-radius: 4px;
                text-align: center;
                background-color: #f5f5f5;
                font-weight: bold;
            }

            QProgressBar::chunk {
                background-color: #4caf50;
                border-radius: 2px;
            }

            QTextEdit {
                border: 2px solid #e0e0e0;
                border-radius: 4px;
                background-color: #ffffff;
                font-family: "Consolas", "Monaco", monospace;
                font-size: 12px;
            }

            QFrame {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: #ffffff;
                margin: 2px;
            }
        """)

    def on_mode_changed(self, index):
        """动画模式改变时的处理"""
        mode_descriptions = [
            "局部反转：将原始图像逐步过渡到最终图像，需要原始图像和最终图像。",
            "剧本翻转：先显示随机图像，再过渡到最终图像，需要原始图像、最终图像和图像池。",
            "随机补丁：随机替换图像区域，需要原始图像和图像池。"
        ]

        self.mode_desc.setText(mode_descriptions[index])

        # 根据模式启用/禁用控件
        if index == 0:  # local_invert
            self.final_edit.setEnabled(True)
            self.final_btn.setEnabled(True)
            self.pool_edit.setEnabled(False)
            self.pool_btn.setEnabled(False)
        elif index == 1:  # scripted_invert
            self.final_edit.setEnabled(True)
            self.final_btn.setEnabled(True)
            self.pool_edit.setEnabled(True)
            self.pool_btn.setEnabled(True)
        elif index == 2:  # random_patch
            self.final_edit.setEnabled(False)
            self.final_btn.setEnabled(False)
            self.pool_edit.setEnabled(True)
            self.pool_btn.setEnabled(True)

    def browse_file(self, line_edit, file_type):
        """浏览文件"""
        if file_type == "图像":
            file_path, _ = QFileDialog.getOpenFileName(
                self, f"选择{file_type}文件", "",
                "图像文件 (*.png *.jpg *.jpeg *.bmp *.tiff)"
            )
        else:
            file_path, _ = QFileDialog.getOpenFileName(self, f"选择{file_type}文件")

        if file_path:
            line_edit.setText(file_path)

    def browse_folder(self, line_edit):
        """浏览文件夹"""
        folder_path = QFileDialog.getExistingDirectory(self, "选择图像池文件夹")
        if folder_path:
            line_edit.setText(folder_path)

    def save_file(self, line_edit):
        """保存文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存动画视频", "animation_output.mp4",
            "MP4文件 (*.mp4);;AVI文件 (*.avi)"
        )
        if file_path:
            line_edit.setText(file_path)

    def create_demo_files(self):
        """创建演示文件"""
        try:
            create_demo_files()
            self.log("✅ 演示文件创建成功！")

            # 自动填充文件路径
            self.original_edit.setText("demo_original.png")
            self.final_edit.setText("demo_final.png")
            self.pool_edit.setText("demo_image_pool")

            QMessageBox.information(
                self, "演示文件创建成功",
                "演示文件已创建完成！\n\n已自动填充文件路径，您可以直接开始生成动画。"
            )
        except Exception as e:
            self.log(f"❌ 演示文件创建失败: {str(e)}", error=True)
            QMessageBox.warning(self, "创建失败", f"演示文件创建失败：{str(e)}")

    def start_generation(self):
        """开始生成动画"""
        try:
            # 验证输入
            if not self.validate_inputs():
                return

            # 准备参数
            params = self.get_generation_params()

            # 禁用生成按钮，启用停止按钮
            self.generate_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)

            # 重置进度
            self.progress_bar.setValue(0)
            self.progress_label.setText("开始生成...")
            self.log_text.clear()
            self.log("🚀 开始生成动画...")

            # 启动工作线程
            self.worker = AnimationWorker(params)
            self.worker.signals.progress.connect(self.on_progress)
            self.worker.signals.finished.connect(self.on_finished)
            self.worker.signals.error.connect(self.on_error)
            self.worker.signals.frame_update.connect(self.on_frame_update)
            self.worker.start()

        except Exception as e:
            self.log(f"❌ 启动失败: {str(e)}", error=True)
            self.generate_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

    def stop_generation(self):
        """停止生成"""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            self.log("⏹️ 生成已停止", error=True)

        self.generate_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_label.setText("已停止")

    def validate_inputs(self):
        """验证输入参数"""
        mode_index = self.mode_combo.currentIndex()

        # 检查原始图像
        if not self.original_edit.text().strip():
            QMessageBox.warning(self, "输入错误", "请选择原始图像文件")
            return False

        if not os.path.exists(self.original_edit.text().strip()):
            QMessageBox.warning(self, "文件错误", "原始图像文件不存在")
            return False

        # 根据模式检查其他输入
        if mode_index in [0, 1]:  # local_invert, scripted_invert
            if not self.final_edit.text().strip():
                QMessageBox.warning(self, "输入错误", "当前模式需要选择最终图像文件")
                return False
            if not os.path.exists(self.final_edit.text().strip()):
                QMessageBox.warning(self, "文件错误", "最终图像文件不存在")
                return False

        if mode_index in [1, 2]:  # scripted_invert, random_patch
            if not self.pool_edit.text().strip():
                QMessageBox.warning(self, "输入错误", "当前模式需要选择图像池文件夹")
                return False
            if not os.path.isdir(self.pool_edit.text().strip()):
                QMessageBox.warning(self, "文件错误", "图像池文件夹不存在")
                return False

        # 检查输出路径
        if not self.output_edit.text().strip():
            QMessageBox.warning(self, "输入错误", "请设置输出视频文件名")
            return False

        return True

    def get_generation_params(self):
        """获取生成参数"""
        mode_map = {
            0: 'local_invert',
            1: 'scripted_invert',
            2: 'random_patch'
        }

        params = {
            'animation_mode': mode_map[self.mode_combo.currentIndex()],
            'original_path': self.original_edit.text().strip(),
            'output_video': self.output_edit.text().strip(),
            'frame_rate': self.fps_spin.value(),
            'grid_size': (self.grid_rows.value(), self.grid_cols.value()),
            'total_steps': self.steps_spin.value(),
            'blend_frames': self.blend_spin.value()
        }

        # 根据模式添加额外参数
        if self.final_edit.isEnabled() and self.final_edit.text().strip():
            params['final_path'] = self.final_edit.text().strip()

        if self.pool_edit.isEnabled() and self.pool_edit.text().strip():
            params['pool_folder'] = self.pool_edit.text().strip()

        return params

    def on_progress(self, step, total):
        """更新进度"""
        progress = int((step / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(progress)
        self.progress_label.setText(f"进度: {step}/{total} ({progress}%)")
        self.log(f"📊 处理步骤 {step}/{total}")

    def on_frame_update(self, frame_data):
        """更新预览帧"""
        try:
            # 将OpenCV图像转换为Qt图像
            if frame_data is not None and len(frame_data.shape) == 3:
                height, width = frame_data.shape[:2]
                bytes_per_line = 3 * width

                # 转换BGR到RGB
                rgb_image = cv2.cvtColor(frame_data, cv2.COLOR_BGR2RGB)

                # 创建QImage
                qt_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)

                # 转换为QPixmap并缩放到预览窗口大小
                pixmap = QPixmap.fromImage(qt_image)
                scaled_pixmap = pixmap.scaled(
                    self.preview_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )

                # 更新预览标签
                self.preview_label.setPixmap(scaled_pixmap)

        except Exception:
            # 如果更新失败，不影响主要功能
            pass

    def on_finished(self, output_path):
        """生成完成"""
        self.progress_bar.setValue(100)
        self.progress_label.setText("生成完成!")
        self.log(f"🎉 动画生成完成: {output_path}")

        self.generate_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

        # 显示完成消息
        QMessageBox.information(
            self, "生成完成",
            f"🎬 动画已成功生成!\n\n📁 输出文件: {output_path}"
        )

    def on_error(self, error_msg):
        """处理错误"""
        self.log(error_msg, error=True)
        self.progress_label.setText("生成失败")

        self.generate_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

        # 显示错误消息
        QMessageBox.critical(self, "生成失败", error_msg)

    def log(self, message, error=False):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        if error:
            formatted_msg = f'<span style="color: #e74c3c;">[{timestamp}] ❌ {message}</span>'
        else:
            formatted_msg = f'<span style="color: #27ae60;">[{timestamp}] ✅ {message}</span>'

        self.log_text.append(formatted_msg)

        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def show_help(self):
        """显示帮助信息"""
        help_text = """
        <h3>🎬 图像动画生成器使用帮助</h3>

        <h4>🚀 快速开始：</h4>
        <ol>
        <li>点击 <b>"🎨 创建演示文件"</b> 按钮创建示例文件</li>
        <li>选择动画模式</li>
        <li>调整参数设置</li>
        <li>点击 <b>"🚀 开始生成动画"</b></li>
        <li>观看右侧实时预览</li>
        </ol>

        <h4>🎭 动画模式说明：</h4>
        <ul>
        <li><b>局部反转</b>：将原始图像逐步过渡到最终图像<br>
        需要：原始图像 + 最终图像</li>

        <li><b>剧本翻转</b>：先显示随机图像，再过渡到最终图像<br>
        需要：原始图像 + 最终图像 + 图像池文件夹</li>

        <li><b>随机补丁</b>：随机替换图像区域<br>
        需要：原始图像 + 图像池文件夹</li>
        </ul>

        <h4>⚙️ 参数说明：</h4>
        <ul>
        <li><b>帧率</b>：视频播放速度，建议 15-30 fps</li>
        <li><b>网格</b>：图像分割网格，影响动画细节</li>
        <li><b>动画步数</b>：动画变化的步骤数量</li>
        <li><b>过渡帧数</b>：每个变化的平滑帧数</li>
        </ul>

        <h4>✨ 特色功能：</h4>
        <ul>
        <li><b>实时预览</b>：右侧窗口实时显示生成过程</li>
        <li><b>一键演示</b>：自动创建示例文件</li>
        <li><b>独立运行</b>：无需外部依赖文件</li>
        </ul>
        """

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("📖 使用帮助")
        msg_box.setText(help_text)
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.exec()


def main():
    """主程序入口"""
    app = QApplication(sys.argv)

    # 设置应用程序信息
    app.setApplicationName("图像动画生成器")
    app.setApplicationVersion("独立版 v1.0")
    app.setOrganizationName("Animation Studio")

    # 显示启动信息
    print("🎬 图像动画生成器 - 独立版")
    print("=" * 50)
    print("✨ 特色功能:")
    print("  - 完全独立运行，无需外部依赖文件")
    print("  - 实时预览动画生成过程")
    print("  - 一键创建演示文件")
    print("  - 三种动画模式可选")
    print("=" * 50)

    # 创建并显示主窗口
    window = StandaloneAnimationStudio()
    window.show()

    # 运行应用程序
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
