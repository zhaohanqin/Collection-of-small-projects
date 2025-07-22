import sys
import os
import base64
import random
import string
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                              QHBoxLayout, QLabel, QRadioButton, QComboBox,
                              QPushButton, QTextEdit, QFrame, QFileDialog,
                              QMessageBox, QButtonGroup, QLineEdit, QGraphicsDropShadowEffect,
                              QSizePolicy, QStackedWidget, QGridLayout)
from PySide6.QtCore import Qt, Signal, Slot, QObject, QPropertyAnimation, QEasingCurve, QSize, QTimer
from PySide6.QtGui import QFont, QColor, QIcon, QPixmap, QPainter, QPainterPath, QLinearGradient


class RoundedTextEdit(QTextEdit):
    """自定义圆角文本框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("RoundedTextEdit")
        
    def paintEvent(self, event):
        # 使用QPainter绘制圆角背景
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 创建圆角路径
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 8, 8)
        
        # 设置裁剪区域为圆角矩形
        painter.setClipPath(path)
        
        # 调用原始绘制方法
        super().paintEvent(event)


class ModernButton(QPushButton):
    """现代风格按钮，带有悬停效果"""
    def __init__(self, text, parent=None, primary=False):
        super().__init__(text, parent)
        self.primary = primary
        self.setObjectName("ModernButton")
        self.setCursor(Qt.PointingHandCursor)
        
        # 创建阴影效果
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QColor(0, 0, 0, 30))
        self.shadow.setOffset(0, 2)
        self.setGraphicsEffect(self.shadow)
        
        # 设置固定高度
        self.setFixedHeight(40)
        
        # 初始化动画
        self._setup_animations()
        
    def _setup_animations(self):
        # 阴影动画
        self.shadow_anim = QPropertyAnimation(self.shadow, b"blurRadius")
        self.shadow_anim.setDuration(200)
        
    def enterEvent(self, event):
        # 鼠标悬停时增加阴影
        self.shadow_anim.setStartValue(15)
        self.shadow_anim.setEndValue(25)
        self.shadow_anim.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        # 鼠标离开时恢复阴影
        self.shadow_anim.setStartValue(25)
        self.shadow_anim.setEndValue(15)
        self.shadow_anim.start()
        super().leaveEvent(event)


class ModernGroupBox(QFrame):
    """现代风格分组框 - 修复布局稳定性问题"""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.setObjectName("ModernGroupBox")

        # 设置固定的尺寸策略，防止布局抖动，增加高度确保字体显示完整
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(100)  # 增加最小高度，确保字体有足够显示空间

        # 创建阴影效果
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(20)
        self.shadow.setColor(QColor(0, 0, 0, 15))
        self.shadow.setOffset(0, 3)
        self.setGraphicsEffect(self.shadow)

        # 创建标题标签并设置父级
        self.title_label = QLabel(title, self)
        self.title_label.setObjectName("GroupBoxTitle")
        # 设置标题标签的固定位置和尺寸策略
        self.title_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # 创建内部布局，增加更多边距确保字体显示完整
        self.inner_layout = QVBoxLayout(self)
        self.inner_layout.setContentsMargins(25, 40, 25, 25)  # 增大边距，为标题和内容留更多空间
        self.inner_layout.setSpacing(15)  # 增加间距，避免内容拥挤

        # 确保标题标签在正确位置
        self._position_title_label()

    def _position_title_label(self):
        """精确定位标题标签"""
        # 计算标题标签的理想位置
        title_width = self.title_label.fontMetrics().boundingRect(self.title).width() + 20
        self.title_label.setFixedSize(title_width, 20)
        self.title_label.move(25, 5)  # 固定位置，避免动态计算

    def resizeEvent(self, event):
        """重写resize事件，确保标题标签位置稳定"""
        super().resizeEvent(event)
        # 重新定位标题标签，但使用固定的计算方式
        self._position_title_label()

    def sizeHint(self):
        """提供尺寸提示，帮助布局管理器做出更好的决策"""
        hint = super().sizeHint()
        # 确保最小高度
        hint.setHeight(max(hint.height(), 80))
        return hint


class ModernCryptoApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # 设置窗口属性 - 增大尺寸确保字体显示完整
        self.setWindowTitle("🔒 加密解密器 v3.0 🔓")
        self.resize(1000, 800)  # 增大默认尺寸，确保有足够空间
        self.setMinimumSize(900, 700)  # 增大最小尺寸，防止字体被挤压

        # 颜色方案 - 优化浅色系配色
        self.colors = {
            "bg": "#f8fafc",           # 背景色
            "card_bg": "#ffffff",      # 卡片背景色
            "primary": "#3b82f6",      # 主色 - 调整为更深的蓝色
            "primary_light": "#93c5fd", # 主色浅色
            "primary_dark": "#1d4ed8", # 主色深色 - 增加对比度
            "secondary": "#10b981",    # 次色 - 改为绿色系
            "secondary_light": "#6ee7b7", # 次色浅色
            "secondary_dark": "#059669", # 次色深色
            "text": "#1e293b",         # 文字颜色 - 增加对比度
            "text_light": "#64748b",   # 浅色文字
            "border": "#e2e8f0",       # 边框颜色
            "error": "#ef4444",        # 错误颜色 - 增加对比度
            "success": "#10b981"       # 成功颜色
        }
        
        # 设置字体
        self.fonts = {
            "title": QFont("Microsoft YaHei", 18, QFont.Bold),
            "heading": QFont("Microsoft YaHei", 14, QFont.DemiBold),
            "normal": QFont("Microsoft YaHei", 12),
            "small": QFont("Microsoft YaHei", 10)
        }
        
        # 初始化变量
        self.mode = "加密"
        self.algorithm = "Unicode偏移"
        self.shift_value = "3"
        self.key_value = ""
        
        # 设置主窗口样式
        self.setStyleSheet(self._get_main_stylesheet())
        
        # 创建主窗口部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        # 设置中央部件的尺寸策略
        self.central_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 创建主布局 - 增加更多空间确保字体显示完整
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(40, 40, 40, 40)  # 增大边距，给组件更多空间
        self.main_layout.setSpacing(25)  # 增加间距，避免组件拥挤

        # 创建界面组件
        self.create_widgets()

        # 初始设置
        self.update_input_options()

        # 随机生成密钥
        self.generate_random_key()

    def _get_main_stylesheet(self):
        """获取主样式表 - 优化布局稳定性和视觉效果"""
        return f"""
            QMainWindow, QWidget {{
                background-color: {self.colors['bg']};
                color: {self.colors['text']};
            }}

            QLabel {{
                color: {self.colors['text']};
                background: transparent;
                /* 确保标签稳定 */
                min-height: 20px;
            }}

            QRadioButton {{
                color: {self.colors['text']};
                background: transparent;
                spacing: 15px;
                /* 增加高度确保字体显示完整 */
                min-height: 35px;
                font-size: 14px;
                padding: 5px;
            }}

            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid {self.colors['border']};
            }}

            QRadioButton::indicator:checked {{
                background-color: {self.colors['primary']};
                border: 2px solid {self.colors['primary']};
            }}

            QRadioButton::indicator:unchecked {{
                background-color: white;
                border: 2px solid {self.colors['border']};
            }}

            QRadioButton::indicator:hover {{
                border-color: {self.colors['primary_light']};
            }}

            QComboBox {{
                background-color: white;
                color: {self.colors['text']};
                border: 2px solid {self.colors['border']};
                border-radius: 8px;
                padding: 12px 18px;
                min-height: 30px;
                /* 确保下拉框稳定且字体显示完整 */
                min-width: 200px;
                font-size: 14px;
            }}

            QComboBox:hover {{
                border-color: {self.colors['primary_light']};
            }}

            QComboBox:focus {{
                border-color: {self.colors['primary']};
                outline: none;
            }}

            QComboBox::drop-down {{
                border: none;
                width: 30px;
                subcontrol-origin: padding;
                subcontrol-position: top right;
            }}

            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {self.colors['text']};
                margin-right: 8px;
            }}

            QLineEdit {{
                background-color: white;
                color: {self.colors['text']};
                border: 2px solid {self.colors['border']};
                border-radius: 6px;
                padding: 12px 18px;
                selection-background-color: {self.colors['primary_light']};
                /* 增加高度确保字体显示完整 */
                min-height: 25px;
                font-size: 14px;
            }}

            QLineEdit:focus {{
                border-color: {self.colors['primary']};
                outline: none;
            }}

            QLineEdit:hover {{
                border-color: {self.colors['primary_light']};
            }}

            #RoundedTextEdit {{
                background-color: white;
                color: {self.colors['text']};
                border: 2px solid {self.colors['border']};
                border-radius: 8px;
                padding: 20px;
                selection-background-color: {self.colors['primary_light']};
                /* 增加高度确保文本显示完整 */
                min-height: 140px;
                font-size: 14px;
                line-height: 1.5;
            }}

            #RoundedTextEdit:focus {{
                border-color: {self.colors['primary']};
                outline: none;
            }}

            #ModernButton {{
                background-color: {self.colors['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-weight: 600;
                font-size: 14px;
                /* 增加按钮尺寸确保字体显示完整 */
                min-height: 35px;
                min-width: 100px;
            }}

            #ModernButton:hover {{
                background-color: {self.colors['primary_dark']};
            }}

            #ModernButton:pressed {{
                background-color: {self.colors['primary_light']};
            }}

            #ModernButton:disabled {{
                background-color: {self.colors['border']};
                color: {self.colors['text_light']};
            }}

            #SecondaryButton {{
                background-color: {self.colors['secondary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 25px;
                font-weight: 600;
                font-size: 14px;
                min-height: 35px;
                min-width: 100px;
            }}

            #SecondaryButton:hover {{
                background-color: {self.colors['secondary_dark']};
            }}

            #ModernGroupBox {{
                background-color: {self.colors['card_bg']};
                border-radius: 12px;
                border: 2px solid {self.colors['border']};
                margin: 8px;
                /* 增加最小尺寸确保内容显示完整 */
                min-height: 100px;
            }}

            #GroupBoxTitle {{
                background-color: {self.colors['primary']};
                color: white;
                padding: 8px 20px;
                border-radius: 12px;
                font-weight: 600;
                font-size: 14px;
                /* 增加尺寸确保标题显示完整 */
                min-width: 80px;
                min-height: 28px;
            }}

            /* 滚动条样式 */
            QScrollBar:vertical {{
                background-color: {self.colors['bg']};
                width: 12px;
                border-radius: 6px;
            }}

            QScrollBar::handle:vertical {{
                background-color: {self.colors['border']};
                border-radius: 6px;
                min-height: 20px;
            }}

            QScrollBar::handle:vertical:hover {{
                background-color: {self.colors['primary_light']};
            }}
        """

    def create_widgets(self):
        """创建界面组件"""
        # 顶部标题
        title_layout = QHBoxLayout()
        title_label = QLabel("加密解密工具")
        title_label.setFont(self.fonts["title"])
        title_label.setStyleSheet(f"color: {self.colors['text']}; margin-bottom: 10px;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        self.main_layout.addLayout(title_layout)
        
        # 模式选择区域 - 优化布局稳定性
        mode_group = ModernGroupBox("操作模式")
        mode_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        mode_layout = QHBoxLayout()
        mode_layout.setContentsMargins(15, 10, 15, 10)  # 增加边距
        mode_layout.setSpacing(50)  # 增加间距，避免拥挤

        self.encrypt_radio = QRadioButton("加密")
        self.encrypt_radio.setFont(self.fonts["normal"])
        self.encrypt_radio.setChecked(True)
        self.encrypt_radio.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.encrypt_radio.toggled.connect(self.on_mode_changed)

        self.decrypt_radio = QRadioButton("解密")
        self.decrypt_radio.setFont(self.fonts["normal"])
        self.decrypt_radio.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.decrypt_radio.toggled.connect(self.on_mode_changed)

        # 创建按钮组
        mode_button_group = QButtonGroup(self)
        mode_button_group.addButton(self.encrypt_radio)
        mode_button_group.addButton(self.decrypt_radio)

        mode_layout.addWidget(self.encrypt_radio)
        mode_layout.addWidget(self.decrypt_radio)
        mode_layout.addStretch()

        mode_group.inner_layout.addLayout(mode_layout)
        self.main_layout.addWidget(mode_group)
        
        # 算法选择区域 - 优化布局稳定性
        algo_group = ModernGroupBox("加密算法")
        algo_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        algo_layout = QHBoxLayout()
        algo_layout.setContentsMargins(15, 10, 15, 10)  # 增加边距
        algo_layout.setSpacing(20)  # 增加间距

        algo_label = QLabel("选择算法:")
        algo_label.setFont(self.fonts["normal"])
        algo_label.setFixedWidth(100)  # 增加标签宽度，确保文字显示完整

        self.algo_combo = QComboBox()
        self.algo_combo.setFont(self.fonts["normal"])
        self.algo_combo.addItems(["Unicode偏移", "Base64编码", "凯撒密码", "异或加密"])
        self.algo_combo.currentTextChanged.connect(self.on_algorithm_changed)
        self.algo_combo.setMinimumWidth(250)  # 增加最小宽度
        self.algo_combo.setMinimumHeight(40)  # 增加最小高度
        self.algo_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        algo_layout.addWidget(algo_label)
        algo_layout.addWidget(self.algo_combo)
        algo_layout.addStretch()

        algo_group.inner_layout.addLayout(algo_layout)
        self.main_layout.addWidget(algo_group)
        
        # 参数设置区域 - 优化布局稳定性，增加空间
        self.params_group = ModernGroupBox("参数设置")
        self.params_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.params_group.setMinimumHeight(100)  # 增加最小高度，确保字体显示完整

        self.params_layout = QHBoxLayout()
        self.params_layout.setContentsMargins(15, 10, 15, 10)  # 增加边距
        self.params_layout.setSpacing(20)  # 增加间距

        self.params_group.inner_layout.addLayout(self.params_layout)
        self.main_layout.addWidget(self.params_group)

        # 输入区域 - 优化布局稳定性
        input_group = ModernGroupBox("输入文本")
        input_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        input_layout = QVBoxLayout()
        input_layout.setContentsMargins(10, 10, 10, 10)  # 增加边距

        self.input_text = RoundedTextEdit()
        self.input_text.setFont(self.fonts["normal"])
        self.input_text.setMinimumHeight(150)  # 增加最小高度
        self.input_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        input_layout.addWidget(self.input_text)

        input_group.inner_layout.addLayout(input_layout)
        self.main_layout.addWidget(input_group)
        
        # 按钮区域 - 优化布局稳定性，增加空间
        button_layout = QHBoxLayout()
        button_layout.setSpacing(25)  # 增加间距
        button_layout.setContentsMargins(15, 15, 15, 15)  # 增加边距

        self.process_button = ModernButton("执行操作", primary=True)
        self.process_button.setFont(self.fonts["normal"])
        self.process_button.setObjectName("ModernButton")
        self.process_button.clicked.connect(self.process_text)
        self.process_button.setMinimumWidth(140)  # 增加最小宽度
        self.process_button.setFixedHeight(45)  # 增加高度
        self.process_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.clear_button = ModernButton("清空")
        self.clear_button.setFont(self.fonts["normal"])
        self.clear_button.setObjectName("SecondaryButton")
        self.clear_button.clicked.connect(self.clear_text)
        self.clear_button.setMinimumWidth(100)  # 增加最小宽度
        self.clear_button.setFixedHeight(45)  # 增加高度
        self.clear_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.save_button = ModernButton("保存结果")
        self.save_button.setFont(self.fonts["normal"])
        self.save_button.setObjectName("SecondaryButton")
        self.save_button.clicked.connect(self.save_result)
        self.save_button.setMinimumWidth(120)  # 增加最小宽度
        self.save_button.setFixedHeight(45)  # 增加高度
        self.save_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        button_layout.addWidget(self.process_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()

        self.main_layout.addLayout(button_layout)
        
        # 结果区域 - 优化布局稳定性
        output_group = ModernGroupBox("结果输出")
        output_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        output_layout = QVBoxLayout()
        output_layout.setContentsMargins(10, 10, 10, 10)  # 增加边距

        self.output_text = RoundedTextEdit()
        self.output_text.setFont(self.fonts["normal"])
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(150)  # 增加最小高度
        self.output_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        output_layout.addWidget(self.output_text)

        output_group.inner_layout.addLayout(output_layout)
        self.main_layout.addWidget(output_group)
        
        # 状态栏 - 优化布局稳定性
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(10, 5, 10, 5)

        self.status_label = QLabel("就绪")
        self.status_label.setFont(self.fonts["small"])
        self.status_label.setStyleSheet(f"color: {self.colors['text_light']};")
        self.status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        version_label = QLabel("v3.0 - 布局优化版")
        version_label.setFont(self.fonts["small"])
        version_label.setStyleSheet(f"color: {self.colors['text_light']};")
        version_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(version_label)

        self.main_layout.addLayout(status_layout)

    def on_mode_changed(self):
        """模式变更处理"""
        if self.encrypt_radio.isChecked():
            self.mode = "加密"
        else:
            self.mode = "解密"

    def on_algorithm_changed(self, algorithm):
        """算法变更处理"""
        self.algorithm = algorithm
        self.update_input_options()

    def update_input_options(self):
        """根据选择的算法更新输入选项 - 修复布局稳定性问题"""
        # 使用更安全的方式清除现有控件，避免布局抖动
        self._clear_params_safely()

        # 使用延迟更新避免布局闪烁
        QTimer.singleShot(0, self._create_params_widgets)

    def _clear_params_safely(self):
        """安全地清除参数控件，避免布局抖动"""
        # 先隐藏所有控件
        for i in range(self.params_layout.count()):
            item = self.params_layout.itemAt(i)
            if item and item.widget():
                item.widget().hide()

        # 然后删除控件
        for i in reversed(range(self.params_layout.count())):
            item = self.params_layout.takeAt(i)
            if item and item.widget():
                item.widget().deleteLater()

    def _create_params_widgets(self):
        """创建参数控件"""
        if self.algorithm == "Unicode偏移":
            self._create_unicode_params()
        elif self.algorithm == "Base64编码":
            self._create_base64_params()
        elif self.algorithm == "凯撒密码":
            self._create_caesar_params()
        elif self.algorithm == "异或加密":
            self._create_xor_params()

        # 强制更新布局
        self.params_layout.update()

    def _create_unicode_params(self):
        """创建Unicode偏移参数"""
        container = self._create_param_container()
        layout = QHBoxLayout(container)

        shift_label = QLabel("偏移量:")
        shift_label.setFont(self.fonts["normal"])
        shift_label.setFixedWidth(100)  # 增加标签宽度

        self.shift_entry = QLineEdit(self.shift_value)
        self.shift_entry.setFont(self.fonts["normal"])
        self.shift_entry.setFixedWidth(150)  # 增加输入框宽度
        self.shift_entry.setFixedHeight(35)  # 增加高度
        self.shift_entry.textChanged.connect(self.on_shift_changed)

        layout.addWidget(shift_label)
        layout.addWidget(self.shift_entry)
        layout.addStretch()

        self.params_layout.addWidget(container)

    def _create_base64_params(self):
        """创建Base64参数"""
        container = self._create_param_container()
        layout = QHBoxLayout(container)

        info_label = QLabel("Base64编码不需要额外参数")
        info_label.setFont(self.fonts["normal"])
        info_label.setStyleSheet(f"color: {self.colors['text_light']};")

        layout.addWidget(info_label)
        layout.addStretch()

        self.params_layout.addWidget(container)

    def _create_caesar_params(self):
        """创建凯撒密码参数"""
        container = self._create_param_container()
        layout = QHBoxLayout(container)

        shift_label = QLabel("偏移量:")
        shift_label.setFont(self.fonts["normal"])
        shift_label.setFixedWidth(100)  # 增加标签宽度

        self.shift_entry = QLineEdit(self.shift_value)
        self.shift_entry.setFont(self.fonts["normal"])
        self.shift_entry.setFixedWidth(150)  # 增加输入框宽度
        self.shift_entry.setFixedHeight(35)  # 增加高度
        self.shift_entry.textChanged.connect(self.on_shift_changed)

        layout.addWidget(shift_label)
        layout.addWidget(self.shift_entry)
        layout.addStretch()

        self.params_layout.addWidget(container)

    def _create_xor_params(self):
        """创建异或加密参数"""
        container = self._create_param_container()
        layout = QHBoxLayout(container)

        key_label = QLabel("密钥:")
        key_label.setFont(self.fonts["normal"])
        key_label.setFixedWidth(100)  # 增加标签宽度

        self.key_entry = QLineEdit(self.key_value)
        self.key_entry.setFont(self.fonts["normal"])
        self.key_entry.setFixedWidth(300)  # 增加输入框宽度
        self.key_entry.setFixedHeight(35)  # 增加高度
        self.key_entry.textChanged.connect(self.on_key_changed)

        generate_button = QPushButton("生成随机密钥")
        generate_button.setFont(self.fonts["normal"])
        generate_button.setObjectName("SecondaryButton")
        generate_button.setFixedHeight(35)  # 增加高度
        generate_button.setFixedWidth(140)  # 增加按钮宽度
        generate_button.setCursor(Qt.PointingHandCursor)
        generate_button.clicked.connect(self.generate_random_key)

        layout.addWidget(key_label)
        layout.addWidget(self.key_entry)
        layout.addWidget(generate_button)
        layout.addStretch()

        self.params_layout.addWidget(container)

    def _create_param_container(self):
        """创建参数容器，确保布局稳定，增加高度确保字体显示完整"""
        container = QWidget()
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        container.setFixedHeight(50)  # 增加高度，确保字体显示完整
        return container

    def on_shift_changed(self, text):
        """偏移量变更处理"""
        self.shift_value = text

    def on_key_changed(self, text):
        """密钥变更处理"""
        self.key_value = text

    def generate_random_key(self):
        """生成随机密钥"""
        # 生成16位随机字符串作为密钥
        key = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        self.key_value = key
        
        # 如果密钥输入框存在，则更新其值
        if hasattr(self, 'key_entry'):
            self.key_entry.setText(key)

    def unicode_encrypt(self, text, shift):
        """Unicode偏移加密"""
        return ''.join([chr(ord(c) + shift) for c in text])
        
    def unicode_decrypt(self, text, shift):
        """Unicode偏移解密"""
        return ''.join([chr(ord(c) - shift) for c in text])
        
    def base64_encrypt(self, text):
        """Base64加密"""
        return base64.b64encode(text.encode('utf-8')).decode('utf-8')
        
    def base64_decrypt(self, text):
        """Base64解密"""
        try:
            return base64.b64decode(text.encode('utf-8')).decode('utf-8')
        except Exception:
            raise ValueError("无效的Base64编码")
            
    def caesar_encrypt(self, text, shift):
        """凯撒密码加密"""
        result = ""
        # 对字母进行偏移
        for char in text:
            if char.isalpha():
                ascii_offset = ord('a') if char.islower() else ord('A')
                # 计算偏移后的字符
                result += chr((ord(char) - ascii_offset + shift) % 26 + ascii_offset)
            else:
                result += char
        return result
        
    def caesar_decrypt(self, text, shift):
        """凯撒密码解密"""
        return self.caesar_encrypt(text, 26 - (shift % 26))
        
    def xor_encrypt(self, text, key):
        """异或加密"""
        result = ""
        for i in range(len(text)):
            result += chr(ord(text[i]) ^ ord(key[i % len(key)]))
        return result
        
    def xor_decrypt(self, text, key):
        """异或解密 (与加密相同)"""
        return self.xor_encrypt(text, key)

    def process_text(self):
        """处理文本"""
        try:
            text = self.input_text.toPlainText().strip()
            if not text:
                self.show_status("请输入要处理的文本", "error")
                return
                
            # 根据算法和模式处理文本
            if self.algorithm == "Unicode偏移":
                try:
                    shift = int(self.shift_value)
                except ValueError:
                    self.show_status("偏移量必须为整数", "error")
                    return
                    
                if self.mode == "加密":
                    result = self.unicode_encrypt(text, shift)
                else:
                    result = self.unicode_decrypt(text, shift)
                    
            elif self.algorithm == "Base64编码":
                if self.mode == "加密":
                    result = self.base64_encrypt(text)
                else:
                    result = self.base64_decrypt(text)
                    
            elif self.algorithm == "凯撒密码":
                try:
                    shift = int(self.shift_value)
                except ValueError:
                    self.show_status("偏移量必须为整数", "error")
                    return
                    
                if self.mode == "加密":
                    result = self.caesar_encrypt(text, shift)
                else:
                    result = self.caesar_decrypt(text, shift)
                    
            elif self.algorithm == "异或加密":
                key = self.key_value
                if not key:
                    self.show_status("请输入密钥", "error")
                    return
                    
                if self.mode == "加密":
                    result = self.xor_encrypt(text, key)
                else:
                    result = self.xor_decrypt(text, key)
            
            self.show_result(result)
            self.show_status(f"{self.mode}完成", "success")
            
        except ValueError as e:
            self.show_status(str(e), "error")
        except Exception as e:
            self.show_status(f"处理错误: {str(e)}", "error")

    def show_result(self, text):
        """显示结果"""
        self.output_text.setPlainText(text)

    def clear_text(self):
        """清空输入和输出"""
        self.input_text.clear()
        self.output_text.clear()
        self.show_status("已清空", "info")

    def save_result(self):
        """保存结果到文件"""
        content = self.output_text.toPlainText().strip()
        if not content:
            self.show_status("没有可保存的内容", "error")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存文件",
            "",
            "文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.show_status(f"文件已保存: {os.path.basename(file_path)}", "success")
            except Exception as e:
                self.show_status(f"保存失败: {str(e)}", "error")

    def show_status(self, message, status_type="info"):
        """显示状态信息"""
        if status_type == "error":
            color = self.colors["error"]
        elif status_type == "success":
            color = self.colors["success"]
        else:
            color = self.colors["text_light"]
            
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color};")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModernCryptoApp()
    window.show()
    sys.exit(app.exec()) 