import sys
import math
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QLineEdit, QComboBox, QSizePolicy, QSpacerItem,
                             QFrame, QGridLayout, QMessageBox)
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QPolygonF, QLinearGradient
from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QTimer

# === 算盘配置 ===
NUM_RODS = 13  # 算盘档数（支持万亿级别）
NUM_UPPER_BEADS_PER_ROD = 1  # 每档上珠数量（代表5）
NUM_LOWER_BEADS_PER_ROD = 4  # 每档下珠数量（每颗代表1）

# === 颜色配置 ===
COLOR_BACKGROUND = QColor("#F8F8F8")  # 背景色（浅灰白）
COLOR_FRAME = QColor("#8B4513")  # 外框色（深棕色木框）
COLOR_ROD = QColor("#A0522D")  # 杆颜色（红棕色木杆）
COLOR_BEAM = QColor("#654321")  # 梁颜色（深棕色木梁）
COLOR_BEAD_ACTIVE = QColor("#D2691E")  # 激活珠子颜色（橙棕色）
COLOR_BEAD_INACTIVE = QColor("#DEB887")  # 非激活珠子颜色（浅棕色）
COLOR_BEAD_BORDER = QColor("#8B4513")  # 珠子边框（深棕色）
COLOR_TEXT = QColor("#333333")  # 文本颜色
COLOR_HIGHLIGHT = QColor("#FFD700")  # 高亮颜色（金色）

# 位值标签（从左到右：高位到低位）
PLACE_VALUE_LABELS = ["万亿", "千亿", "百亿", "十亿", "亿", "千万", "百万", "十万", "万", "千", "百", "十", "个"]


class AbacusWidget(QWidget):
    """改进的算盘部件"""
    valueChanged = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.num_rods = NUM_RODS
        self.num_upper_beads = NUM_UPPER_BEADS_PER_ROD
        self.num_lower_beads = NUM_LOWER_BEADS_PER_ROD
        
        # 算盘状态：每档包含上珠和下珠的激活数量
        # abacus_state[rod_index] = {'upper_active': 0或1, 'lower_active': 0-4}
        self.abacus_state = []
        self.init_abacus_state()
        
        # 鼠标悬停状态
        self.hover_rod = -1
        self.hover_bead_type = None  # 'upper' 或 'lower'
        self.hover_bead_index = -1
        
        self.setMinimumSize(800, 400)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)  # 启用鼠标跟踪以支持悬停效果
        
    def init_abacus_state(self):
        """初始化算盘状态"""
        self.abacus_state = [{'upper_active': 0, 'lower_active': 0} for _ in range(self.num_rods)]
        self.update_display_value()
        
    def get_rod_value(self, rod_idx):
        """获取指定档的数值"""
        if 0 <= rod_idx < len(self.abacus_state):
            state = self.abacus_state[rod_idx]
            return state['upper_active'] * 5 + state['lower_active']
        return 0
        
    def get_total_value(self):
        """获取算盘总数值"""
        total = 0
        # 从左到右计算，左边是高位
        for i in range(self.num_rods):
            rod_value = self.get_rod_value(i)
            power = self.num_rods - 1 - i  # 位权
            total += rod_value * (10 ** power)
        return total
        
    def update_display_value(self):
        """更新显示数值"""
        self.valueChanged.emit(self.get_total_value())
        self.update()  # 触发重绘
        
    def clear_abacus(self):
        """清空算盘"""
        self.init_abacus_state()
        
    def set_value(self, number_to_set):
        """设置算盘数值"""
        self.clear_abacus()
        
        if not isinstance(number_to_set, int):
            try:
                number_to_set = int(number_to_set)
            except ValueError:
                return False
                
        if number_to_set < 0:
            number_to_set = 0
            
        # 检查是否超出算盘容量
        max_value = 10 ** self.num_rods - 1
        if number_to_set > max_value:
            number_to_set = max_value
            
        # 将数字转换为字符串并从右到左设置
        s_num = str(number_to_set).zfill(self.num_rods)
        
        for i, digit_char in enumerate(s_num):
            digit = int(digit_char)
            rod_idx = i  # 从左到右对应高位到低位
            
            if digit >= 5:
                self.abacus_state[rod_idx]['upper_active'] = 1
                self.abacus_state[rod_idx]['lower_active'] = digit - 5
            else:
                self.abacus_state[rod_idx]['upper_active'] = 0
                self.abacus_state[rod_idx]['lower_active'] = digit
                
        self.update_display_value()
        return True
        
    def calculate_dimensions(self):
        """计算绘制尺寸"""
        width = self.width()
        height = self.height()
        
        frame_thickness = min(width, height) * 0.03
        drawable_width = width - 2 * frame_thickness
        drawable_height = height - 2 * frame_thickness
        
        rod_area_width = drawable_width / self.num_rods
        rod_width = rod_area_width * 0.08
        bead_diameter = min(rod_area_width * 0.6, drawable_height * 0.08)
        
        beam_height = drawable_height * 0.06
        beam_y = frame_thickness + drawable_height * 0.35
        
        upper_area_height = beam_y - frame_thickness
        lower_area_height = frame_thickness + drawable_height - (beam_y + beam_height)
        
        return {
            'width': width, 'height': height,
            'frame_thickness': frame_thickness,
            'drawable_width': drawable_width, 'drawable_height': drawable_height,
            'rod_area_width': rod_area_width, 'rod_width': rod_width,
            'bead_diameter': bead_diameter, 'beam_height': beam_height,
            'beam_y': beam_y, 'upper_area_height': upper_area_height,
            'lower_area_height': lower_area_height
        }
        
    def get_bead_position(self, rod_idx, bead_type, bead_idx, is_active, dims):
        """计算珠子位置"""
        rod_x_center = dims['frame_thickness'] + (rod_idx + 0.5) * dims['rod_area_width']
        
        if bead_type == 'upper':
            if is_active:
                # 激活的上珠靠近梁
                y = dims['beam_y'] - dims['bead_diameter'] * 0.7
            else:
                # 非激活的上珠远离梁
                y = dims['frame_thickness'] + dims['bead_diameter'] * 0.7
        else:  # lower
            if is_active:
                # 激活的下珠靠近梁，从下往上排列
                y = dims['beam_y'] + dims['beam_height'] + (bead_idx + 0.7) * dims['bead_diameter'] * 1.2
            else:
                # 非激活的下珠远离梁，在底部
                inactive_idx = bead_idx - self.abacus_state[rod_idx]['lower_active']
                y = dims['frame_thickness'] + dims['drawable_height'] - (inactive_idx + 0.7) * dims['bead_diameter'] * 1.2
                
        return QPointF(rod_x_center, y)
        
    def draw_bead(self, painter, center, diameter, is_active, is_hover=False):
        """绘制珠子"""
        # 选择颜色
        if is_hover:
            color = COLOR_HIGHLIGHT
        elif is_active:
            color = COLOR_BEAD_ACTIVE
        else:
            color = COLOR_BEAD_INACTIVE
            
        # 创建渐变效果
        gradient = QLinearGradient(center.x() - diameter/4, center.y() - diameter/4,
                                 center.x() + diameter/4, center.y() + diameter/4)
        gradient.setColorAt(0, color.lighter(120))
        gradient.setColorAt(1, color.darker(120))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(COLOR_BEAD_BORDER, 2))
        painter.drawEllipse(center, diameter/2, diameter/2)
        
        # 添加高光效果
        highlight_center = QPointF(center.x() - diameter/6, center.y() - diameter/6)
        painter.setBrush(QBrush(QColor(255, 255, 255, 100)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(highlight_center, diameter/8, diameter/8)

    def paintEvent(self, event):
        """绘制算盘"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        dims = self.calculate_dimensions()

        # 绘制背景
        painter.fillRect(self.rect(), COLOR_BACKGROUND)

        # 绘制外框
        painter.setPen(QPen(COLOR_FRAME, dims['frame_thickness'] * 0.8))
        painter.setBrush(COLOR_FRAME)
        painter.drawRect(0, 0, dims['width'], dims['height'])

        # 清空内部区域
        painter.fillRect(QRectF(dims['frame_thickness'], dims['frame_thickness'],
                               dims['drawable_width'], dims['drawable_height']), COLOR_BACKGROUND)

        # 绘制梁
        painter.setBrush(COLOR_BEAM)
        painter.setPen(Qt.NoPen)
        painter.drawRect(QRectF(dims['frame_thickness'], dims['beam_y'],
                               dims['drawable_width'], dims['beam_height']))

        # 绘制位值标签
        painter.setPen(COLOR_TEXT)
        label_font = QFont()
        label_font.setPointSize(max(8, int(dims['rod_area_width'] * 0.15)))
        painter.setFont(label_font)

        for i in range(self.num_rods):
            if i < len(PLACE_VALUE_LABELS):
                rod_x_center = dims['frame_thickness'] + (i + 0.5) * dims['rod_area_width']
                label_y = dims['height'] - dims['frame_thickness'] * 0.3

                painter.drawText(QRectF(rod_x_center - dims['rod_area_width']/2, label_y - 20,
                                      dims['rod_area_width'], 20),
                                Qt.AlignCenter, PLACE_VALUE_LABELS[i])

        # 绘制算档（杆）
        painter.setBrush(COLOR_ROD)
        painter.setPen(Qt.NoPen)

        for i in range(self.num_rods):
            rod_x_center = dims['frame_thickness'] + (i + 0.5) * dims['rod_area_width']
            rod_x_start = rod_x_center - dims['rod_width'] / 2
            painter.drawRect(QRectF(rod_x_start, dims['frame_thickness'],
                                   dims['rod_width'], dims['drawable_height']))

        # 绘制珠子
        for rod_idx in range(self.num_rods):
            rod_state = self.abacus_state[rod_idx]

            # 绘制上珠
            for bead_idx in range(self.num_upper_beads):
                is_active = bead_idx < rod_state['upper_active']
                is_hover = (self.hover_rod == rod_idx and
                           self.hover_bead_type == 'upper' and
                           self.hover_bead_index == bead_idx)

                center = self.get_bead_position(rod_idx, 'upper', bead_idx, is_active, dims)
                self.draw_bead(painter, center, dims['bead_diameter'], is_active, is_hover)

            # 绘制下珠
            for bead_idx in range(self.num_lower_beads):
                is_active = bead_idx < rod_state['lower_active']
                is_hover = (self.hover_rod == rod_idx and
                           self.hover_bead_type == 'lower' and
                           self.hover_bead_index == bead_idx)

                center = self.get_bead_position(rod_idx, 'lower', bead_idx, is_active, dims)
                self.draw_bead(painter, center, dims['bead_diameter'], is_active, is_hover)

    def get_clicked_bead(self, pos):
        """获取点击的珠子信息"""
        dims = self.calculate_dimensions()

        # 检查是否在有效区域内
        if not (dims['frame_thickness'] < pos.x() < dims['width'] - dims['frame_thickness'] and
                dims['frame_thickness'] < pos.y() < dims['height'] - dims['frame_thickness']):
            return None

        # 确定点击的档
        rod_idx = int((pos.x() - dims['frame_thickness']) / dims['rod_area_width'])
        if rod_idx >= self.num_rods:
            return None

        # 检查点击区域（上珠区域、梁区域、下珠区域）
        if pos.y() < dims['beam_y']:
            # 上珠区域
            bead_type = 'upper'
            # 检查是否点击了上珠
            for bead_idx in range(self.num_upper_beads):
                is_active = bead_idx < self.abacus_state[rod_idx]['upper_active']
                center = self.get_bead_position(rod_idx, 'upper', bead_idx, is_active, dims)
                distance = math.sqrt((pos.x() - center.x())**2 + (pos.y() - center.y())**2)
                if distance <= dims['bead_diameter'] * 0.6:  # 增大点击区域
                    return {'rod': rod_idx, 'type': 'upper', 'index': bead_idx}

        elif pos.y() > dims['beam_y'] + dims['beam_height']:
            # 下珠区域
            bead_type = 'lower'
            # 检查是否点击了下珠
            for bead_idx in range(self.num_lower_beads):
                is_active = bead_idx < self.abacus_state[rod_idx]['lower_active']
                center = self.get_bead_position(rod_idx, 'lower', bead_idx, is_active, dims)
                distance = math.sqrt((pos.x() - center.x())**2 + (pos.y() - center.y())**2)
                if distance <= dims['bead_diameter'] * 0.6:  # 增大点击区域
                    return {'rod': rod_idx, 'type': 'lower', 'index': bead_idx}

        return None

    def mousePressEvent(self, event):
        """处理鼠标点击事件"""
        if event.button() != Qt.LeftButton:
            return

        bead_info = self.get_clicked_bead(event.position())
        if not bead_info:
            return

        rod_idx = bead_info['rod']
        bead_type = bead_info['type']
        bead_idx = bead_info['index']

        rod_state = self.abacus_state[rod_idx]

        if bead_type == 'upper':
            # 上珠简单切换
            rod_state['upper_active'] = 1 - rod_state['upper_active']
        else:
            # 下珠智能切换
            current_active = rod_state['lower_active']
            if bead_idx < current_active:
                # 点击已激活的珠子，将其及以下珠子设为非激活
                rod_state['lower_active'] = bead_idx
            else:
                # 点击非激活的珠子，将其及以上珠子设为激活
                rod_state['lower_active'] = bead_idx + 1

        self.update_display_value()

    def mouseMoveEvent(self, event):
        """处理鼠标移动事件（悬停效果）"""
        bead_info = self.get_clicked_bead(event.position())

        if bead_info:
            self.hover_rod = bead_info['rod']
            self.hover_bead_type = bead_info['type']
            self.hover_bead_index = bead_info['index']
        else:
            self.hover_rod = -1
            self.hover_bead_type = None
            self.hover_bead_index = -1

        self.update()  # 触发重绘以显示悬停效果


class AbacusApp(QMainWindow):
    """改进的算盘应用程序"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("改进的中国算盘模拟器")
        self.setGeometry(100, 100, 1000, 700)

        # 设置应用样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F8F8F8;
            }
            QLabel {
                color: #333333;
                font-size: 12pt;
                padding: 5px;
            }
            QPushButton {
                background-color: #4682B4;
                color: white;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11pt;
                border: none;
            }
            QPushButton:hover {
                background-color: #5792C4;
            }
            QPushButton:pressed {
                background-color: #3672A4;
            }
            QLineEdit {
                border: 2px solid #CCCCCC;
                border-radius: 6px;
                padding: 8px;
                background-color: white;
                font-size: 11pt;
            }
            QLineEdit:focus {
                border-color: #4682B4;
            }
            QComboBox {
                border: 2px solid #CCCCCC;
                border-radius: 6px;
                padding: 6px;
                background-color: white;
                font-size: 11pt;
            }
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #DDDDDD;
            }
        """)

        self.setup_ui()

    def setup_ui(self):
        """设置用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title_label = QLabel("改进的中国算盘模拟器")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2C3E50; padding: 10px;")
        main_layout.addWidget(title_label)

        # 算盘部件
        self.abacus_widget = AbacusWidget()
        main_layout.addWidget(self.abacus_widget, 1)

        # 数值显示区域
        display_frame = QFrame()
        display_layout = QHBoxLayout(display_frame)
        display_layout.setContentsMargins(15, 10, 15, 10)

        display_layout.addWidget(QLabel("当前数值:"))

        self.display_label = QLabel("0")
        self.display_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        display_font = QFont()
        display_font.setPointSize(24)
        display_font.setBold(True)
        self.display_label.setFont(display_font)
        self.display_label.setStyleSheet("color: #2C3E50; background-color: #ECF0F1; padding: 10px; border-radius: 5px;")
        display_layout.addWidget(self.display_label, 1)

        main_layout.addWidget(display_frame)

        # 连接值变化信号
        self.abacus_widget.valueChanged.connect(self.update_display)

        # 控制面板
        control_frame = QFrame()
        control_layout = QVBoxLayout(control_frame)
        control_layout.setContentsMargins(15, 15, 15, 15)
        control_layout.setSpacing(10)

        # 数字设置行
        set_layout = QHBoxLayout()
        set_layout.addWidget(QLabel("设置数字:"))

        self.num_input = QLineEdit()
        self.num_input.setPlaceholderText("输入要设置到算盘的数字")
        self.num_input.returnPressed.connect(self.set_abacus_value)
        set_layout.addWidget(self.num_input, 1)

        btn_set = QPushButton("设置")
        btn_set.clicked.connect(self.set_abacus_value)
        set_layout.addWidget(btn_set)

        btn_clear = QPushButton("清空")
        btn_clear.clicked.connect(self.clear_abacus)
        set_layout.addWidget(btn_clear)

        control_layout.addLayout(set_layout)

        # 计算行
        calc_layout = QHBoxLayout()
        calc_layout.addWidget(QLabel("计算:"))

        self.op_combo = QComboBox()
        self.op_combo.addItems(["+", "-", "×", "÷"])
        calc_layout.addWidget(self.op_combo)

        self.operand_input = QLineEdit()
        self.operand_input.setPlaceholderText("输入操作数")
        self.operand_input.returnPressed.connect(self.perform_calculation)
        calc_layout.addWidget(self.operand_input, 1)

        btn_calc = QPushButton("计算")
        btn_calc.clicked.connect(self.perform_calculation)
        calc_layout.addWidget(btn_calc)

        control_layout.addLayout(calc_layout)

        # 结果显示
        self.result_label = QLabel("结果将显示在这里")
        self.result_label.setStyleSheet("color: #27AE60; font-weight: bold;")
        control_layout.addWidget(self.result_label)

        main_layout.addWidget(control_frame)

        # 使用说明
        help_text = ("使用说明:\n"
                    "• 点击上珠切换激活状态（代表5）\n"
                    "• 点击下珠智能设置数值（每颗代表1）\n"
                    "• 可以直接输入数字设置到算盘\n"
                    "• 支持基本四则运算")
        help_label = QLabel(help_text)
        help_label.setStyleSheet("color: #7F8C8D; font-size: 10pt; padding: 10px;")
        main_layout.addWidget(help_label)

    def update_display(self, value):
        """更新数值显示"""
        self.display_label.setText(f"{value:,}")

    def set_abacus_value(self):
        """设置算盘数值"""
        try:
            text = self.num_input.text().strip()
            if not text:
                return

            # 移除逗号分隔符
            text = text.replace(',', '')
            value = int(text)

            if value < 0:
                self.show_message("错误", "请输入非负整数！", "error")
                return

            max_value = 10 ** NUM_RODS - 1
            if value > max_value:
                self.show_message("警告", f"数值超出算盘容量！最大支持 {max_value:,}", "warning")
                value = max_value

            success = self.abacus_widget.set_value(value)
            if success:
                self.result_label.setText(f"已设置数值: {value:,}")
                self.result_label.setStyleSheet("color: #27AE60; font-weight: bold;")
            else:
                self.show_message("错误", "设置数值失败！", "error")

        except ValueError:
            self.show_message("错误", "请输入有效的数字！", "error")

    def clear_abacus(self):
        """清空算盘"""
        self.abacus_widget.clear_abacus()
        self.num_input.clear()
        self.operand_input.clear()
        self.result_label.setText("算盘已清空")
        self.result_label.setStyleSheet("color: #27AE60; font-weight: bold;")

    def perform_calculation(self):
        """执行计算"""
        try:
            current_value = self.abacus_widget.get_total_value()
            operator = self.op_combo.currentText()

            operand_text = self.operand_input.text().strip()
            if not operand_text:
                self.show_message("错误", "请输入操作数！", "error")
                return

            # 移除逗号分隔符
            operand_text = operand_text.replace(',', '')
            operand = int(operand_text)

            # 执行计算
            if operator == "+":
                result = current_value + operand
            elif operator == "-":
                result = current_value - operand
            elif operator == "×":
                result = current_value * operand
            elif operator == "÷":
                if operand == 0:
                    self.show_message("错误", "除数不能为零！", "error")
                    return
                result = current_value // operand  # 整数除法
            else:
                self.show_message("错误", "未知的运算符！", "error")
                return

            # 检查结果范围
            if result < 0:
                self.show_message("警告", "结果为负数，将设置为0", "warning")
                result = 0

            max_value = 10 ** NUM_RODS - 1
            if result > max_value:
                self.show_message("警告", f"结果超出算盘容量！将设置为最大值 {max_value:,}", "warning")
                result = max_value

            # 设置结果到算盘
            self.abacus_widget.set_value(result)
            self.num_input.setText(str(result))

            # 显示计算过程
            expression = f"{current_value:,} {operator} {operand:,} = {result:,}"
            self.result_label.setText(expression)
            self.result_label.setStyleSheet("color: #27AE60; font-weight: bold;")

        except ValueError:
            self.show_message("错误", "请输入有效的数字！", "error")
        except Exception as e:
            self.show_message("错误", f"计算出错: {str(e)}", "error")

    def show_message(self, title, message, msg_type="info"):
        """显示消息框"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)

        if msg_type == "error":
            msg_box.setIcon(QMessageBox.Critical)
        elif msg_type == "warning":
            msg_box.setIcon(QMessageBox.Warning)
        else:
            msg_box.setIcon(QMessageBox.Information)

        msg_box.exec()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # 设置应用程序信息
    app.setApplicationName("改进的中国算盘模拟器")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("算盘模拟器")

    # 创建并显示主窗口
    main_window = AbacusApp()
    main_window.show()

    sys.exit(app.exec())
