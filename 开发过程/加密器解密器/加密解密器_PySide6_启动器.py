import os
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt


class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 设置窗口属性
        self.setWindowTitle("加密解密器启动器")
        self.resize(400, 200)
        self.setStyleSheet("background-color: #f5f7fa;")
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题标签
        title_label = QLabel("加密解密工具启动器")
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        title_label.setStyleSheet("color: #495057;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 添加间距
        layout.addSpacing(20)
        
        # 启动按钮
        start_button = QPushButton("启动加密解密器 v3.0 (PySide6)")
        start_button.setFont(QFont("Microsoft YaHei", 12))
        start_button.setStyleSheet("""
            QPushButton {
                background-color: #91c4f8;
                color: #495057;
                border: none;
                padding: 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #74b3f8;
            }
        """)
        start_button.clicked.connect(self.start_app)
        layout.addWidget(start_button)
        
        # 添加伸缩空间
        layout.addStretch()

    def start_app(self):
        try:
            # 尝试导入PySide6版本
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "crypto_app_pyside6", 
                os.path.join(os.path.dirname(__file__), "加密解密器_PySide6.py")
            )
            crypto_app = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(crypto_app)
            
            # 关闭启动器窗口
            self.close()
            
            # 启动应用
            self.app_window = crypto_app.ModernCryptoApp()
            self.app_window.show()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "启动错误",
                f"无法启动加密解密器 PySide6 版本: {str(e)}"
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LauncherWindow()
    window.show()
    sys.exit(app.exec()) 