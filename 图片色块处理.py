import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton, 
                              QVBoxLayout, QHBoxLayout, QLabel, QFileDialog, 
                              QListWidget, QSlider, QCheckBox, QFrame, 
                              QScrollArea, QMessageBox, QSplitter, QStyle, QSizePolicy,
                              QListWidgetItem, QDialog)
from PySide6.QtGui import QImage, QPixmap, QColor, QPainter, QPalette, QFont, QBrush
from PySide6.QtCore import Qt, QSize, Signal, QPoint, QRect
import numpy as np
from PIL import Image
import os

class ColorDisplay(QFrame):
    """自定义颜色显示组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.color = QColor(240, 240, 240)
        self.setMinimumSize(100, 50)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("border-radius: 8px;")
        
        # 添加文本标签
        layout = QVBoxLayout(self)
        self.text_label = QLabel("RGB: 无")
        self.text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.text_label)
        
    def set_color(self, color, text):
        self.color = color
        self.text_label.setText(text)
        self.setStyleSheet(f"background-color: {color.name()}; border-radius: 8px; border: 1px solid #e0e0e0;")
        
    def paintEvent(self, event):
        super().paintEvent(event)
        
class ImageViewer(QLabel):
    """自定义图片显示组件，支持点击事件"""
    pixel_clicked = Signal(QPoint, QColor)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(500, 400)  # 增大最小尺寸
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 设置尺寸策略为扩展
        self.setStyleSheet("background-color: #f8f9fa; border-radius: 12px;")
        self.setText("点击'加载图片'开始")
        self.pixmap = None
        self.scale_factor = 1.0
        self.original_pixmap = None
        
    def set_image(self, pixmap):
        """设置图片并自动调整大小"""
        self.original_pixmap = pixmap
        self.adjust_pixmap()
        
    def adjust_pixmap(self):
        """根据控件大小调整图片"""
        if not self.original_pixmap:
            return
            
        # 获取控件大小
        view_width = self.width()
        view_height = self.height()
        
        if view_width <= 1 or view_height <= 1:
            return
            
        # 获取图片原始大小
        img_width = self.original_pixmap.width()
        img_height = self.original_pixmap.height()
        
        # 计算缩放比例
        scale_x = view_width / img_width if img_width > 0 else 1
        scale_y = view_height / img_height if img_height > 0 else 1
        self.scale_factor = min(scale_x, scale_y)
        
        # 如果图片小于控件，不放大
        if img_width < view_width and img_height < view_height:
            self.scale_factor = 1.0
            
        # 缩放图片
        if self.scale_factor != 1.0:
            scaled_width = int(img_width * self.scale_factor)
            scaled_height = int(img_height * self.scale_factor)
            self.pixmap = self.original_pixmap.scaled(
                scaled_width, scaled_height, 
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        else:
            self.pixmap = self.original_pixmap
            
        # 设置图片
        self.setPixmap(self.pixmap)
        
    def resizeEvent(self, event):
        """窗口大小改变时重新调整图片"""
        super().resizeEvent(event)
        self.adjust_pixmap()
        
    def mousePressEvent(self, event):
        if self.pixmap and event.button() == Qt.LeftButton:
            # 计算实际图像中的位置
            pos = self.get_image_position(event.position().toPoint())
            if pos:
                color = self.get_pixel_color(pos)
                self.pixel_clicked.emit(pos, color)
        super().mousePressEvent(event)
        
    def get_image_position(self, pos):
        """转换鼠标位置到图像坐标"""
        if not self.pixmap or not self.original_pixmap:
            return None
            
        # 获取图像在标签中的位置
        img_rect = self.get_image_rect()
        if not img_rect.contains(pos):
            return None
            
        # 计算相对位置并应用缩放
        x = int((pos.x() - img_rect.left()) / self.scale_factor)
        y = int((pos.y() - img_rect.top()) / self.scale_factor)
        
        # 确保在图像范围内
        if 0 <= x < self.original_pixmap.width() and 0 <= y < self.original_pixmap.height():
            return QPoint(x, y)
        return None
        
    def get_image_rect(self):
        """获取图像在标签中的实际矩形区域"""
        if not self.pixmap:
            return QRect()
            
        # 计算居中位置
        pos = QPoint(
            (self.width() - self.pixmap.width()) // 2,
            (self.height() - self.pixmap.height()) // 2
        )
        
        return QRect(pos, self.pixmap.size())
        
    def get_pixel_color(self, pos):
        """获取指定位置的像素颜色"""
        if not self.original_pixmap:
            return QColor()
            
        # 创建一个临时图像来获取像素颜色
        img = self.original_pixmap.toImage()
        return QColor(img.pixel(pos))

class ColorListItem(QWidget):
    """自定义颜色列表项，包含颜色预览和文本"""
    def __init__(self, color_info, parent=None):
        super().__init__(parent)
        
        # 获取颜色信息
        r, g, b, a = color_info['rgb']
        hex_color = color_info['hex']
        
        # 创建布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # 创建颜色预览块
        color_preview = QFrame()
        color_preview.setFixedSize(20, 20)
        color_preview.setStyleSheet(f"background-color: {hex_color}; border-radius: 3px; border: 1px solid #e0e0e0;")
        layout.addWidget(color_preview)
        
        # 创建文本标签
        text = f"RGB({r},{g},{b}) Alpha:{a}"
        label = QLabel(text)
        layout.addWidget(label)
        
        # 存储颜色信息
        self.color_info = color_info

class PixelColorTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图片像素颜色选择器")
        self.resize(1100, 700)
        
        # 初始化变量
        self.original_image = None
        self.current_image = None
        self.clicked_colors = []  # 存储点击的颜色
        self.tolerance = 15
        self.use_advanced_matching = True
        
        # 设置应用样式
        self.setup_style()
        
        # 创建UI
        self.setup_ui()
        
    def setup_style(self):
        """设置应用整体样式"""
        # 设置应用字体
        font = QFont("Segoe UI", 9)
        QApplication.setFont(font)
        
        # 设置应用样式表
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QPushButton {
                background-color: #f0f4f8;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                color: #4a6fa5;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #e1ebf2;
            }
            QPushButton:pressed {
                background-color: #d4e2ed;
            }
            QLabel {
                color: #4a5568;
            }
            QListWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
                padding: 5px;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: #e0e0e0;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #4a6fa5;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background: #a3c4e9;
                border-radius: 2px;
            }
            QCheckBox {
                color: #4a5568;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #a0aec0;
            }
            QCheckBox::indicator:checked {
                background-color: #4a6fa5;
                border: 1px solid #4a6fa5;
            }
        """)
        
    def setup_ui(self):
        """创建UI界面"""
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # 顶部按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 加载图片按钮
        self.load_btn = QPushButton("加载图片")
        self.load_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.load_btn.clicked.connect(self.load_image)
        button_layout.addWidget(self.load_btn)
        
        # 保存图片按钮
        self.save_btn = QPushButton("保存图片")
        self.save_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.save_btn.clicked.connect(self.save_image)
        button_layout.addWidget(self.save_btn)
        
        # 重置按钮
        self.reset_btn = QPushButton("重置图片")
        self.reset_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogResetButton))
        self.reset_btn.clicked.connect(self.reset_image)
        button_layout.addWidget(self.reset_btn)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        # 创建分割器，分隔图像区域和控制区域
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        
        # 左侧 - 图片显示区域
        image_container = QWidget()
        image_layout = QVBoxLayout(image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)
        
        # 图片显示区
        self.image_viewer = ImageViewer()
        self.image_viewer.pixel_clicked.connect(self.on_image_click)
        image_layout.addWidget(self.image_viewer)
        
        # 状态标签
        self.status_label = QLabel("状态: 等待加载图片")
        self.status_label.setAlignment(Qt.AlignLeft)
        image_layout.addWidget(self.status_label)
        
        # 右侧 - 颜色控制区域
        control_container = QWidget()
        control_container.setMaximumWidth(280)  # 限制控制面板宽度
        control_layout = QVBoxLayout(control_container)
        control_layout.setContentsMargins(15, 5, 5, 5)
        
        # 当前颜色显示
        color_title = QLabel("当前点击颜色:")
        color_title.setStyleSheet("font-weight: bold; margin-top: 5px;")
        control_layout.addWidget(color_title)
        
        self.current_color_display = ColorDisplay()
        control_layout.addWidget(self.current_color_display)
        
        # 已保存的颜色列表
        saved_colors_label = QLabel("已保存的颜色:")
        saved_colors_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        control_layout.addWidget(saved_colors_label)
        
        # 颜色列表
        self.color_list = QListWidget()
        self.color_list.setAlternatingRowColors(True)
        self.color_list.setMaximumHeight(150)  # 限制列表高度
        control_layout.addWidget(self.color_list)
        
        # 透明化按钮
        self.transparent_btn = QPushButton("将选中颜色设为透明")
        self.transparent_btn.clicked.connect(self.make_color_transparent)
        control_layout.addWidget(self.transparent_btn)
        
        # 颜色容差设置
        tolerance_layout = QHBoxLayout()
        tolerance_label = QLabel("颜色容差:")
        tolerance_layout.addWidget(tolerance_label)
        
        self.tolerance_slider = QSlider(Qt.Horizontal)
        self.tolerance_slider.setRange(0, 50)
        self.tolerance_slider.setValue(self.tolerance)
        self.tolerance_slider.valueChanged.connect(self.update_tolerance)
        tolerance_layout.addWidget(self.tolerance_slider)
        
        self.tolerance_value_label = QLabel(str(self.tolerance))
        tolerance_layout.addWidget(self.tolerance_value_label)
        
        control_layout.addLayout(tolerance_layout)
        
        # 高级匹配选项
        self.advanced_checkbox = QCheckBox("使用高级颜色匹配")
        self.advanced_checkbox.setChecked(self.use_advanced_matching)
        self.advanced_checkbox.stateChanged.connect(self.toggle_advanced_matching)
        control_layout.addWidget(self.advanced_checkbox)
        
        # 分析按钮
        self.analyze_btn = QPushButton("分析相似颜色")
        self.analyze_btn.clicked.connect(self.analyze_similar_colors)
        control_layout.addWidget(self.analyze_btn)
        
        # 批量透明化按钮
        self.batch_btn = QPushButton("批量透明化相似颜色")
        self.batch_btn.clicked.connect(self.batch_make_transparent)
        control_layout.addWidget(self.batch_btn)
        
        # 添加伸缩空间
        control_layout.addStretch()
        
        # 将左右两部分添加到分割器
        splitter.addWidget(image_container)
        splitter.addWidget(control_container)
        
        # 设置分割比例 (图片区域:控制区域 = 4:1)
        splitter.setSizes([800, 200])
        
        main_layout.addWidget(splitter, 1)  # 给予分割器更大的垂直空间
        
    def load_image(self):
        """加载图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", 
            "图片文件 (*.png *.jpg *.jpeg *.gif *.bmp);;所有文件 (*.*)"
        )
        
        if not file_path:
            return
            
        try:
            # 使用PIL加载图片
            pil_image = Image.open(file_path)
            
            # 如果图片没有alpha通道，添加一个
            if pil_image.mode != 'RGBA':
                pil_image = pil_image.convert('RGBA')
                
            # 保存原始图片和当前图片
            self.original_image = pil_image
            self.current_image = pil_image.copy()
            
            # 显示图片
            self.display_image()
            
            # 清空之前的颜色记录
            self.clicked_colors.clear()
            self.color_list.clear()
            
            self.status_label.setText("状态: 图片已加载，点击像素查看颜色")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法加载图片: {str(e)}")
            
    def display_image(self):
        """显示当前图片"""
        if self.current_image is None:
            return
            
        # 将PIL图像转换为QPixmap
        img_data = self.current_image.tobytes("raw", "RGBA")
        qimg = QImage(img_data, self.current_image.width, self.current_image.height, 
                     QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimg)
        
        # 计算缩放比例
        viewer_width = self.image_viewer.width()
        viewer_height = self.image_viewer.height()
        
        if viewer_width <= 1 or viewer_height <= 1:
            # 如果尺寸还未初始化，延迟显示
            QApplication.processEvents()
            self.display_image()
            return
            
        # 设置图像
        self.image_viewer.set_image(pixmap)
        
        # 更新状态
        self.status_label.setText(f"状态: 图片已加载 ({self.current_image.width}x{self.current_image.height})")
        
    def on_image_click(self, pos, color):
        """处理图片点击事件"""
        if self.current_image is None:
            return
            
        # 获取RGB和Alpha值
        r, g, b, a = color.red(), color.green(), color.blue(), color.alpha()
        
        # 显示当前颜色
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        color_text = f"RGB: ({r}, {g}, {b})\nAlpha: {a}\nPos: ({pos.x()}, {pos.y()})"
        self.current_color_display.set_color(color, color_text)
        
        # 保存颜色到列表
        color_info = {
            'rgb': (r, g, b, a),
            'hex': hex_color,
            'pos': (pos.x(), pos.y())
        }
        
        # 检查是否已存在该颜色
        if not any(c['hex'] == hex_color for c in self.clicked_colors):
            self.clicked_colors.append(color_info)
            
            # 创建自定义列表项
            item = QListWidgetItem()
            custom_widget = ColorListItem(color_info)
            item.setSizeHint(custom_widget.sizeHint())
            
            self.color_list.addItem(item)
            self.color_list.setItemWidget(item, custom_widget)
            
            self.status_label.setText(f"状态: 添加颜色 {hex_color}")
            
    def update_tolerance(self, value):
        """更新容差值"""
        self.tolerance = value
        self.tolerance_value_label.setText(str(value))
        
    def toggle_advanced_matching(self, state):
        """切换高级匹配模式"""
        self.use_advanced_matching = (state == Qt.Checked)
        
    def color_distance(self, color1, color2):
        """计算两个颜色之间的距离（欧几里得距离）"""
        r1, g1, b1 = color1[:3]
        r2, g2, b2 = color2[:3]
        return np.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)
        
    def advanced_color_match(self, img_array, target_color, tolerance):
        """高级颜色匹配算法"""
        target_rgb = np.array(target_color[:3])
        
        # 方法1: 欧几里得距离
        img_rgb = img_array[:, :, :3].astype(np.float32)
        distances = np.sqrt(np.sum((img_rgb - target_rgb) ** 2, axis=2))
        euclidean_mask = distances <= tolerance
        
        # 方法2: 加权颜色差异（人眼对绿色更敏感）
        weights = np.array([0.299, 0.587, 0.114])  # RGB权重
        weighted_diff = np.abs(img_rgb - target_rgb) * weights
        weighted_distance = np.sum(weighted_diff, axis=2)
        weighted_mask = weighted_distance <= tolerance * 0.5
        
        # 组合掩码
        combined_mask = euclidean_mask | weighted_mask
        
        return combined_mask
        
    def simple_color_match(self, img_array, target_color, tolerance):
        """简单颜色匹配（原始方法）"""
        target_rgb = target_color[:3]
        mask = (
            (np.abs(img_array[:, :, 0] - target_rgb[0]) <= tolerance) &
            (np.abs(img_array[:, :, 1] - target_rgb[1]) <= tolerance) &
            (np.abs(img_array[:, :, 2] - target_rgb[2]) <= tolerance)
        )
        return mask
        
    def analyze_similar_colors(self):
        """分析图片中与选中颜色相似的所有颜色"""
        selected_items = self.color_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择一个颜色")
            return
            
        if self.current_image is None:
            QMessageBox.warning(self, "警告", "请先加载图片")
            return
            
        selected_index = self.color_list.row(selected_items[0])
        selected_color = self.clicked_colors[selected_index]
        target_rgb = selected_color['rgb'][:3]
        
        # 转换图片为numpy数组
        img_array = np.array(self.current_image)
        
        # 获取匹配的像素
        if self.use_advanced_matching:
            mask = self.advanced_color_match(img_array, target_rgb, self.tolerance)
        else:
            mask = self.simple_color_match(img_array, target_rgb, self.tolerance)
            
        # 统计匹配的像素数量
        matched_pixels = np.sum(mask)
        total_pixels = img_array.shape[0] * img_array.shape[1]
        percentage = (matched_pixels / total_pixels) * 100
        
        # 获取所有匹配颜色的统计信息
        matched_colors = img_array[mask]
        if len(matched_colors) > 0:
            unique_colors = np.unique(matched_colors.reshape(-1, matched_colors.shape[-1]), axis=0)
            
            # 创建带颜色预览的分析结果对话框
            analysis_dialog = QDialog(self)
            analysis_dialog.setWindowTitle("颜色分析")
            analysis_dialog.setMinimumWidth(400)
            
            dialog_layout = QVBoxLayout(analysis_dialog)
            
            # 添加颜色预览
            preview_frame = QFrame()
            preview_frame.setFixedSize(60, 60)
            preview_frame.setStyleSheet(f"background-color: {selected_color['hex']}; border-radius: 5px; border: 1px solid #e0e0e0;")
            
            preview_layout = QHBoxLayout()
            preview_layout.addWidget(preview_frame)
            preview_layout.addStretch()
            dialog_layout.addLayout(preview_layout)
            
            # 添加分析结果文本
            info_text = f"目标颜色: RGB{target_rgb}\n"
            info_text += f"容差设置: {self.tolerance}\n"
            info_text += f"匹配像素: {matched_pixels:,} 个\n"
            info_text += f"占比: {percentage:.2f}%\n"
            info_text += f"发现 {len(unique_colors)} 种相似颜色"
            
            result_label = QLabel(info_text)
            result_label.setStyleSheet("margin: 10px 0;")
            dialog_layout.addWidget(result_label)
            
            # 添加确定按钮
            ok_button = QPushButton("确定")
            ok_button.clicked.connect(analysis_dialog.accept)
            dialog_layout.addWidget(ok_button)
            
            analysis_dialog.exec()
            self.status_label.setText(f"状态: 找到 {matched_pixels:,} 个匹配像素")
        else:
            QMessageBox.information(self, "颜色分析", "在当前容差下未找到匹配的颜色")
            
    def batch_make_transparent(self):
        """批量透明化相似颜色"""
        selected_items = self.color_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择一个颜色")
            return
            
        if self.current_image is None:
            QMessageBox.warning(self, "警告", "请先加载图片")
            return
            
        # 创建确认对话框
        confirm_dialog = QDialog(self)
        confirm_dialog.setWindowTitle("确认操作")
        confirm_dialog.setMinimumWidth(350)
        
        dialog_layout = QVBoxLayout(confirm_dialog)
        
        selected_index = self.color_list.row(selected_items[0])
        selected_color = self.clicked_colors[selected_index]
        
        # 添加颜色预览
        preview_frame = QFrame()
        preview_frame.setFixedSize(50, 50)
        preview_frame.setStyleSheet(f"background-color: {selected_color['hex']}; border-radius: 5px; border: 1px solid #e0e0e0;")
        
        preview_layout = QHBoxLayout()
        preview_layout.addWidget(preview_frame)
        preview_layout.addStretch()
        dialog_layout.addLayout(preview_layout)
        
        # 添加确认文本
        confirm_text = f"将使用容差 {self.tolerance} 批量透明化所有相似颜色。\n此操作可能影响大量像素，是否继续？"
        confirm_label = QLabel(confirm_text)
        confirm_label.setWordWrap(True)
        dialog_layout.addWidget(confirm_label)
        
        # 添加按钮
        button_layout = QHBoxLayout()
        yes_button = QPushButton("确定")
        no_button = QPushButton("取消")
        
        button_layout.addWidget(yes_button)
        button_layout.addWidget(no_button)
        
        yes_button.clicked.connect(confirm_dialog.accept)
        no_button.clicked.connect(confirm_dialog.reject)
        
        dialog_layout.addLayout(button_layout)
        
        # 显示对话框并获取结果
        result = confirm_dialog.exec()
        
        if result != QDialog.Accepted:
            return
            
        target_rgb = selected_color['rgb'][:3]
        
        # 转换图片为numpy数组
        img_array = np.array(self.current_image)
        
        # 获取匹配的像素
        if self.use_advanced_matching:
            mask = self.advanced_color_match(img_array, target_rgb, self.tolerance)
        else:
            mask = self.simple_color_match(img_array, target_rgb, self.tolerance)
            
        # 统计处理前的像素数量
        matched_pixels = np.sum(mask)
        
        if matched_pixels == 0:
            QMessageBox.information(self, "提示", "在当前容差下未找到匹配的颜色")
            return
            
        # 将匹配的像素设为透明
        img_array[mask, 3] = 0  # 设置alpha通道为0（透明）
        
        # 转换回PIL Image
        self.current_image = Image.fromarray(img_array, 'RGBA')
        
        # 重新显示图片
        self.display_image()
        
        hex_color = selected_color['hex']
        self.status_label.setText(f"状态: 已透明化 {matched_pixels:,} 个相似像素")
        
        QMessageBox.information(self, "完成", f"已将 {matched_pixels:,} 个相似颜色像素设为透明")
        
    def make_color_transparent(self):
        """将选中的颜色设为透明"""
        selected_items = self.color_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择一个颜色")
            return
            
        if self.current_image is None:
            QMessageBox.warning(self, "警告", "请先加载图片")
            return
            
        # 获取选中的颜色
        selected_index = self.color_list.row(selected_items[0])
        selected_color = self.clicked_colors[selected_index]
        target_rgb = selected_color['rgb'][:3]
        
        # 转换图片为numpy数组进行处理
        img_array = np.array(self.current_image)
        
        # 根据用户选择使用不同的匹配算法
        if self.use_advanced_matching:
            mask = self.advanced_color_match(img_array, target_rgb, self.tolerance)
        else:
            mask = self.simple_color_match(img_array, target_rgb, self.tolerance)
            
        # 统计匹配的像素数量
        matched_pixels = np.sum(mask)
        
        if matched_pixels == 0:
            QMessageBox.warning(self, "提示", f"在容差 {self.tolerance} 下未找到匹配的颜色，请尝试增加容差值")
            return
            
        # 将匹配的像素设为透明
        img_array[mask, 3] = 0  # 设置alpha通道为0（透明）
        
        # 转换回PIL Image
        self.current_image = Image.fromarray(img_array, 'RGBA')
        
        # 重新显示图片
        self.display_image()
        
        hex_color = selected_color['hex']
        self.status_label.setText(f"状态: 颜色 {hex_color} 已设为透明 ({matched_pixels} 像素)")
        
        QMessageBox.information(self, "完成", f"颜色 {hex_color} 已设为透明\n处理了 {matched_pixels} 个像素")
        
    def save_image(self):
        """保存当前图片"""
        if self.current_image is None:
            QMessageBox.warning(self, "警告", "没有图片可保存")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存图片", "", "PNG文件 (*.png);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                self.current_image.save(file_path, "PNG")
                QMessageBox.information(self, "成功", f"图片已保存到: {file_path}")
                self.status_label.setText("状态: 图片保存成功")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
                
    def reset_image(self):
        """重置图片到原始状态"""
        if self.original_image is None:
            QMessageBox.warning(self, "警告", "没有原始图片可重置")
            return
            
        self.current_image = self.original_image.copy()
        self.display_image()
        self.status_label.setText("状态: 图片已重置到原始状态")
        
    def resizeEvent(self, event):
        """窗口大小改变时重新显示图片"""
        super().resizeEvent(event)
        if self.current_image:
            self.display_image()


def main():
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 创建窗口
    window = PixelColorTool()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()