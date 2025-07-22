import sys
import os
import base64
import random
import string
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                              QHBoxLayout, QLabel, QRadioButton, QComboBox,
                              QPushButton, QTextEdit, QFrame, QFileDialog,
                              QMessageBox, QButtonGroup, QLineEdit)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class SimpleCryptoApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # 设置窗口属性
        self.setWindowTitle("加密解密器")
        self.resize(800, 600)
        self.setMinimumSize(700, 500)

        # 简洁的颜色方案
        self.colors = {
            "bg": "#ffffff",           # 纯白背景
            "primary": "#2563eb",      # 蓝色主色
            "text": "#374151",         # 深灰色文字
            "text_light": "#6b7280",   # 浅灰色文字
            "border": "#d1d5db",       # 边框颜色
            "input_bg": "#f9fafb",     # 输入框背景
            "button_hover": "#1d4ed8", # 按钮悬停色
            "success": "#059669",      # 成功色
            "error": "#dc2626"         # 错误色
        }

        # 设置字体
        self.font_normal = QFont("Microsoft YaHei", 10)
        self.font_title = QFont("Microsoft YaHei", 14, QFont.Bold)

        # 初始化变量
        self.mode = "加密"
        self.algorithm = "Unicode偏移"
        self.shift_value = "3"
        self.key_value = ""

        # 设置样式
        self.setStyleSheet(self._get_stylesheet())

        # 创建界面
        self.setup_ui()

        # 初始设置
        self.update_params()
        self.generate_random_key()

    def _get_stylesheet(self):
        """获取简洁的样式表"""
        return f"""
            QMainWindow {{
                background-color: {self.colors['bg']};
            }}

            QLabel {{
                color: {self.colors['text']};
                background: transparent;
            }}

            QRadioButton {{
                color: {self.colors['text']};
                spacing: 8px;
                padding: 5px;
            }}

            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 2px solid {self.colors['border']};
                background-color: white;
            }}

            QRadioButton::indicator:checked {{
                background-color: {self.colors['primary']};
                border-color: {self.colors['primary']};
            }}

            QComboBox {{
                background-color: {self.colors['input_bg']};
                border: 1px solid {self.colors['border']};
                border-radius: 4px;
                padding: 8px 12px;
                min-height: 20px;
            }}

            QComboBox:focus {{
                border-color: {self.colors['primary']};
            }}

            QLineEdit {{
                background-color: {self.colors['input_bg']};
                border: 1px solid {self.colors['border']};
                border-radius: 4px;
                padding: 8px 12px;
                min-height: 20px;
            }}

            QLineEdit:focus {{
                border-color: {self.colors['primary']};
            }}

            QTextEdit {{
                background-color: {self.colors['input_bg']};
                border: 1px solid {self.colors['border']};
                border-radius: 4px;
                padding: 12px;
            }}

            QTextEdit:focus {{
                border-color: {self.colors['primary']};
            }}

            QPushButton {{
                background-color: {self.colors['primary']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
            }}

            QPushButton:hover {{
                background-color: {self.colors['button_hover']};
            }}

            QPushButton:pressed {{
                background-color: {self.colors['primary']};
            }}

            #secondary_button {{
                background-color: {self.colors['input_bg']};
                color: {self.colors['text']};
                border: 1px solid {self.colors['border']};
            }}

            #secondary_button:hover {{
                background-color: {self.colors['border']};
            }}
        """

    def setup_ui(self):
        """创建简洁的界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # 标题
        title_label = QLabel("加密解密器")
        title_label.setFont(self.font_title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"color: {self.colors['text']}; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        # 模式选择
        mode_frame = QFrame()
        mode_frame.setStyleSheet(f"background-color: {self.colors['input_bg']}; border: 1px solid {self.colors['border']}; border-radius: 6px; padding: 10px;")
        mode_layout = QHBoxLayout(mode_frame)

        mode_label = QLabel("操作模式:")
        mode_label.setFont(self.font_normal)

        self.encrypt_radio = QRadioButton("加密")
        self.encrypt_radio.setFont(self.font_normal)
        self.encrypt_radio.setChecked(True)
        self.encrypt_radio.toggled.connect(self.on_mode_changed)

        self.decrypt_radio = QRadioButton("解密")
        self.decrypt_radio.setFont(self.font_normal)
        self.decrypt_radio.toggled.connect(self.on_mode_changed)

        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.encrypt_radio)
        mode_layout.addWidget(self.decrypt_radio)
        mode_layout.addStretch()

        main_layout.addWidget(mode_frame)

        # 算法选择
        algo_frame = QFrame()
        algo_frame.setStyleSheet(f"background-color: {self.colors['input_bg']}; border: 1px solid {self.colors['border']}; border-radius: 6px; padding: 10px;")
        algo_layout = QHBoxLayout(algo_frame)

        algo_label = QLabel("加密算法:")
        algo_label.setFont(self.font_normal)

        self.algo_combo = QComboBox()
        self.algo_combo.setFont(self.font_normal)
        self.algo_combo.addItems(["Unicode偏移", "Base64编码", "凯撒密码", "异或加密"])
        self.algo_combo.currentTextChanged.connect(self.on_algorithm_changed)

        algo_layout.addWidget(algo_label)
        algo_layout.addWidget(self.algo_combo)
        algo_layout.addStretch()

        main_layout.addWidget(algo_frame)

        # 参数设置区域
        self.params_frame = QFrame()
        self.params_frame.setStyleSheet(f"background-color: {self.colors['input_bg']}; border: 1px solid {self.colors['border']}; border-radius: 6px; padding: 10px;")
        self.params_layout = QHBoxLayout(self.params_frame)
        main_layout.addWidget(self.params_frame)

        # 输入文本
        input_label = QLabel("输入文本:")
        input_label.setFont(self.font_normal)
        main_layout.addWidget(input_label)

        self.input_text = QTextEdit()
        self.input_text.setFont(self.font_normal)
        self.input_text.setMinimumHeight(120)
        self.input_text.setPlaceholderText("请输入要加密或解密的文本...")
        main_layout.addWidget(self.input_text)

        # 按钮区域
        button_layout = QHBoxLayout()

        self.process_button = QPushButton("执行操作")
        self.process_button.setFont(self.font_normal)
        self.process_button.clicked.connect(self.process_text)

        self.clear_button = QPushButton("清空")
        self.clear_button.setFont(self.font_normal)
        self.clear_button.setObjectName("secondary_button")
        self.clear_button.clicked.connect(self.clear_text)

        self.save_button = QPushButton("保存结果")
        self.save_button.setFont(self.font_normal)
        self.save_button.setObjectName("secondary_button")
        self.save_button.clicked.connect(self.save_result)

        button_layout.addWidget(self.process_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()

        main_layout.addLayout(button_layout)

        # 输出文本
        output_label = QLabel("输出结果:")
        output_label.setFont(self.font_normal)
        main_layout.addWidget(output_label)

        self.output_text = QTextEdit()
        self.output_text.setFont(self.font_normal)
        self.output_text.setMinimumHeight(120)
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("处理结果将显示在这里...")
        main_layout.addWidget(self.output_text)

        # 状态栏
        self.status_label = QLabel("就绪")
        self.status_label.setFont(self.font_normal)
        self.status_label.setStyleSheet(f"color: {self.colors['text_light']};")
        main_layout.addWidget(self.status_label)

    def on_mode_changed(self):
        """模式变更处理"""
        if self.encrypt_radio.isChecked():
            self.mode = "加密"
        else:
            self.mode = "解密"

    def on_algorithm_changed(self, algorithm):
        """算法变更处理"""
        self.algorithm = algorithm
        self.update_params()

    def update_params(self):
        """根据选择的算法更新参数设置"""
        # 清除现有参数控件
        for i in reversed(range(self.params_layout.count())):
            item = self.params_layout.takeAt(i)
            if item.widget():
                item.widget().deleteLater()

        # 根据算法添加相应参数
        if self.algorithm == "Unicode偏移" or self.algorithm == "凯撒密码":
            shift_label = QLabel("偏移量:")
            shift_label.setFont(self.font_normal)

            self.shift_entry = QLineEdit(self.shift_value)
            self.shift_entry.setFont(self.font_normal)
            self.shift_entry.textChanged.connect(self.on_shift_changed)

            self.params_layout.addWidget(shift_label)
            self.params_layout.addWidget(self.shift_entry)

        elif self.algorithm == "异或加密":
            key_label = QLabel("密钥:")
            key_label.setFont(self.font_normal)

            self.key_entry = QLineEdit(self.key_value)
            self.key_entry.setFont(self.font_normal)
            self.key_entry.textChanged.connect(self.on_key_changed)

            generate_button = QPushButton("生成随机密钥")
            generate_button.setFont(self.font_normal)
            generate_button.setObjectName("secondary_button")
            generate_button.clicked.connect(self.generate_random_key)

            self.params_layout.addWidget(key_label)
            self.params_layout.addWidget(self.key_entry)
            self.params_layout.addWidget(generate_button)

        elif self.algorithm == "Base64编码":
            info_label = QLabel("Base64编码不需要额外参数")
            info_label.setFont(self.font_normal)
            info_label.setStyleSheet(f"color: {self.colors['text_light']};")

            self.params_layout.addWidget(info_label)

        self.params_layout.addStretch()

    def on_shift_changed(self, text):
        """偏移量变更处理"""
        self.shift_value = text

    def on_key_changed(self, text):
        """密钥变更处理"""
        self.key_value = text

    def generate_random_key(self):
        """生成随机密钥"""
        key = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        self.key_value = key
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
    window = SimpleCryptoApp()
    window.show()
    sys.exit(app.exec())