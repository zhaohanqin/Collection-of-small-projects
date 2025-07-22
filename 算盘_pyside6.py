import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QLineEdit, QComboBox, QSizePolicy, QSpacerItem)
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QPolygonF
from PySide6.QtCore import Qt, QPointF, QRectF, Signal

# --- 算盘配置 ---
NUM_RODS = 17  # 算盘的档数（增加到17档）
NUM_UPPER_BEADS_PER_ROD = 2  # 每档上珠数量 (每颗代表5)
NUM_LOWER_BEADS_PER_ROD = 5  # 每档下珠数量 (每颗代表1)

# --- 颜色配置 ---
COLOR_BACKGROUND = QColor("#F5F5F5")  # 背景色 (米白色)
COLOR_FRAME = QColor("#8B4513")  # 外框色 (棕色木框)
COLOR_ROD = QColor("#A0522D")  # 杆颜色 (红棕色木杆)
COLOR_BEAM = QColor("#8B4513")  # 梁颜色 (棕色木梁)
COLOR_BEAD_UPPER = QColor("#654321")  # 上珠颜色 (深褐色)
COLOR_BEAD_LOWER = QColor("#654321")  # 下珠颜色 (深褐色)
COLOR_BEAD_BORDER = QColor("#333333")  # 珠子边框
COLOR_TEXT = QColor("#333333")  # 文本颜色

# 位值标签
PLACE_VALUE_LABELS = ["十兆", "兆", "千亿", "百亿", "十亿", "亿", "千万", "百万", "十万", "万", "千", "百", "十", "个", "分", "厘", "毫"]


class AbacusWidget(QWidget):
    valueChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.num_rods = NUM_RODS
        self.num_upper_beads = NUM_UPPER_BEADS_PER_ROD
        self.num_lower_beads = NUM_LOWER_BEADS_PER_ROD

        # abacus_state[rod_index] = {'upper_active': count, 'lower_active': count}
        # 'upper_active': 靠梁的上珠数量 (0 to NUM_UPPER_BEADS_PER_ROD)
        # 'lower_active': 靠梁的下珠数量 (0 to NUM_LOWER_BEADS_PER_ROD)
        self.abacus_state = []
        self.init_abacus_state()

        self.setMinimumSize(600, 300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def init_abacus_state(self):
        self.abacus_state = [{'upper_active': 0, 'lower_active': 0} for _ in range(self.num_rods)]
        self.update_display_value()

    def get_rod_value(self, rod_idx):
        state = self.abacus_state[rod_idx]
        return state['upper_active'] * 5 + state['lower_active'] * 1

    def get_total_value(self):
        total = 0
        # 从右到左计算，个位在最右边
        for i in range(self.num_rods):
            rod_idx = self.num_rods - 1 - i  # 反转索引，最右边是个位
            rod_value = self.get_rod_value(rod_idx)
            total += rod_value * (10 ** i)
        return total

    def update_display_value(self):
        self.valueChanged.emit(self.get_total_value())
        self.update()  # 触发重绘

    def clear_abacus(self):
        self.init_abacus_state()

    def set_value(self, number_to_set):
        self.clear_abacus()
        if not isinstance(number_to_set, int):
            try:
                number_to_set = int(number_to_set)
            except ValueError:
                print("无效的数字输入")
                return

        if number_to_set < 0:  # 简化处理，仅支持正数
            number_to_set = 0

        s_num = str(number_to_set)

        # 如果数字太长，只显示最右边的位数
        if len(s_num) > self.num_rods:
            s_num = s_num[-self.num_rods:]

        # 从右到左设置珠子状态
        for i, digit_char in enumerate(reversed(s_num)):
            digit = int(digit_char)
            rod_idx = self.num_rods - 1 - i  # 从右到左，个位在最右边

            if rod_idx < 0 or rod_idx >= self.num_rods:
                continue

            upper_active = 0
            lower_active = 0

            if digit >= 5:
                upper_active = 1
                lower_active = digit - 5
            else:
                upper_active = 0
                lower_active = digit

            if upper_active > self.num_upper_beads:
                upper_active = self.num_upper_beads
            if lower_active > self.num_lower_beads:
                lower_active = self.num_lower_beads

            self.abacus_state[rod_idx]['upper_active'] = upper_active
            self.abacus_state[rod_idx]['lower_active'] = lower_active

        self.update_display_value()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        painter.fillRect(self.rect(), COLOR_BACKGROUND)

        # --- 计算尺寸 ---
        frame_thickness = min(width, height) * 0.03

        drawable_width = width - 2 * frame_thickness
        drawable_height = height - 2 * frame_thickness

        rod_area_width = drawable_width / self.num_rods
        rod_width = rod_area_width * 0.1
        bead_diameter = rod_area_width * 0.7  # 圆形珠子直径

        beam_height = drawable_height * 0.05

        # 上下珠子区域的垂直划分
        total_bead_space_v = drawable_height - beam_height
        upper_bead_area_height = total_bead_space_v * 0.3  # 上珠区域占30%
        lower_bead_area_height = total_bead_space_v * 0.7  # 下珠区域占70%

        bead_v_spacing_upper = upper_bead_area_height / (self.num_upper_beads + 1)
        bead_v_spacing_lower = lower_bead_area_height / (self.num_lower_beads + 1)

        # --- 绘制外框 ---
        painter.setPen(QPen(COLOR_FRAME, frame_thickness * 0.8))
        painter.setBrush(COLOR_FRAME)
        painter.drawRect(0, 0, width, height)  # 外边框
        # 内部清空区域:
        painter.fillRect(QRectF(frame_thickness, frame_thickness, drawable_width, drawable_height), COLOR_BACKGROUND)

        # --- 绘制梁 ---
        beam_y = frame_thickness + upper_bead_area_height
        painter.setBrush(COLOR_BEAM)
        painter.setPen(Qt.NoPen)
        painter.drawRect(QRectF(frame_thickness, beam_y, drawable_width, beam_height))

        # --- 绘制位值标签 ---
        painter.setPen(COLOR_TEXT)
        label_font = QFont()
        label_font.setPointSize(10)
        painter.setFont(label_font)
        
        for i in range(self.num_rods):
            rod_x_center = frame_thickness + (i + 0.5) * rod_area_width
            label_y = height - frame_thickness * 0.5
            
            # 确保标签索引不会越界
            label_idx = i
            if label_idx < len(PLACE_VALUE_LABELS):
                label = PLACE_VALUE_LABELS[label_idx]
                painter.drawText(QRectF(rod_x_center - rod_area_width/2, label_y - 15, 
                                      rod_area_width, 20), 
                                Qt.AlignCenter, label)

        # --- 绘制算档和珠子 ---
        for i in range(self.num_rods):
            rod_x_center = frame_thickness + (i + 0.5) * rod_area_width
            rod_x_start = rod_x_center - rod_width / 2

            # 绘制算档
            painter.setBrush(COLOR_ROD)
            painter.drawRect(QRectF(rod_x_start, frame_thickness, rod_width, drawable_height))

            rod_state = self.abacus_state[i]

            # 绘制上珠
            painter.setBrush(COLOR_BEAD_UPPER)
            painter.setPen(QPen(COLOR_BEAD_BORDER, 1))
            
            for j in range(self.num_upper_beads):
                bead_center_x = rod_x_center
                
                # 修改上珠位置逻辑，使每颗珠子可以独立移动
                # 每颗珠子的状态: 0=未激活(远离梁), 1=激活(靠近梁)
                is_active = (j < rod_state['upper_active'])
                
                if is_active:  # 激活的珠子（靠近梁）
                    bead_center_y = beam_y - (j + 0.5) * bead_v_spacing_upper
                else:  # 未激活的珠子（远离梁）
                    bead_center_y = frame_thickness + (j + 0.5) * bead_v_spacing_upper

                # 绘制圆形珠子
                painter.drawEllipse(QPointF(bead_center_x, bead_center_y), 
                                   bead_diameter/2, bead_diameter/2)

            # 绘制下珠 - 修改下珠的显示逻辑，使其与传统算盘一致
            painter.setBrush(COLOR_BEAD_LOWER)
            
            for j in range(self.num_lower_beads):
                bead_center_x = rod_x_center
                
                # 修改：下珠的激活状态与上珠相反
                # 下珠激活表示向上移动（远离底部）
                is_active = (j < rod_state['lower_active'])
                
                if is_active:  # 激活的下珠（靠近梁）
                    # 从下往上数，最靠近梁的珠子位置
                    bead_center_y = beam_y + beam_height + (j + 0.5) * bead_v_spacing_lower
                else:  # 未激活的下珠（远离梁，靠近底部）
                    # 从下往上数，最远离梁的珠子位置
                    bead_center_y = height - frame_thickness - (self.num_lower_beads - j - 0.5) * bead_v_spacing_lower

                # 绘制圆形珠子
                painter.drawEllipse(QPointF(bead_center_x, bead_center_y), 
                                   bead_diameter/2, bead_diameter/2)

    def mousePressEvent(self, event):
        width = self.width()
        height = self.height()

        frame_thickness = min(width, height) * 0.03
        drawable_width = width - 2 * frame_thickness
        drawable_height = height - 2 * frame_thickness
        rod_area_width = drawable_width / self.num_rods
        beam_height = drawable_height * 0.05

        total_bead_space_v = drawable_height - beam_height
        upper_bead_area_height = total_bead_space_v * 0.3
        lower_bead_area_height = total_bead_space_v * 0.7

        beam_y_start = frame_thickness + upper_bead_area_height
        beam_y_end = beam_y_start + beam_height

        click_x = event.position().x()
        click_y = event.position().y()

        if not (frame_thickness < click_x < width - frame_thickness and
                frame_thickness < click_y < height - frame_thickness):
            return

        # 确定点击的是哪一档
        rod_idx = int((click_x - frame_thickness) / rod_area_width)
        if rod_idx >= self.num_rods:
            return

        # 计算珠子的大小和间距
        bead_diameter = rod_area_width * 0.7
        bead_v_spacing_upper = upper_bead_area_height / (self.num_upper_beads + 1)
        bead_v_spacing_lower = lower_bead_area_height / (self.num_lower_beads + 1)

        # 获取当前档的状态
        rod_state = self.abacus_state[rod_idx]
        rod_x_center = frame_thickness + (rod_idx + 0.5) * rod_area_width

        # 检查是否点击了上珠
        if click_y < beam_y_start:
            # 计算点击的是哪一颗上珠
            for j in range(self.num_upper_beads):
                bead_center_y = beam_y_start - (j + 0.5) * bead_v_spacing_upper
                # 检查点击是否在珠子中心附近（更精确的点击检测）
                if (abs(click_x - rod_x_center) < bead_diameter/4 and 
                    abs(click_y - bead_center_y) < bead_diameter/4):
                    # 检查是否是第一颗上珠（最上面的）
                    if j == 0:
                        # 只有当第二颗上珠（j=1）已经激活时，才能移动第一颗
                        if rod_state['upper_active'] >= 1:  # 修改这里，只要第二颗激活就可以移动第一颗
                            if rod_state['upper_active'] == 1:
                                rod_state['upper_active'] = 2  # 激活第一颗
                            else:
                                rod_state['upper_active'] = 1  # 取消激活第一颗
                    else:
                        # 第二颗上珠可以自由移动
                        if rod_state['upper_active'] >= 1:
                            rod_state['upper_active'] = 0  # 取消激活第二颗
                        else:
                            rod_state['upper_active'] = 1  # 激活第二颗
                    self.update_display_value()
                    return

        # 检查是否点击了下珠
        elif click_y > beam_y_end:
            # 计算点击的是哪一颗下珠
            for j in range(self.num_lower_beads):
                bead_center_y = beam_y_end + (j + 0.5) * bead_v_spacing_lower
                # 检查点击是否在珠子中心附近（更精确的点击检测）
                if (abs(click_x - rod_x_center) < bead_diameter/4 and 
                    abs(click_y - bead_center_y) < bead_diameter/4):
                    # 下珠可以自由移动
                    if j < rod_state['lower_active']:
                        rod_state['lower_active'] = max(0, rod_state['lower_active'] - 1)
                    else:
                        rod_state['lower_active'] = min(self.num_lower_beads, rod_state['lower_active'] + 1)
                    self.update_display_value()
                    return


class AbacusApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("中国算盘模拟器")
        self.setGeometry(100, 100, 800, 600)
        
        # 设置应用样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F5F5F5;
            }
            QLabel {
                color: #333333;
                font-size: 12pt;
            }
            QPushButton {
                background-color: #4682B4;
                color: white;
                border-radius: 4px;
                padding: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5792C4;
            }
            QPushButton:pressed {
                background-color: #3672A4;
            }
            QLineEdit {
                border: 1px solid #AAAAAA;
                border-radius: 4px;
                padding: 4px;
                background-color: white;
            }
            QComboBox {
                border: 1px solid #AAAAAA;
                border-radius: 4px;
                padding: 4px;
                background-color: white;
            }
        """)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 算盘部件
        self.abacus_widget = AbacusWidget()
        main_layout.addWidget(self.abacus_widget, 1)  # 算盘占据更多空间
        
        # 显示数值的标签
        self.display_label = QLabel("0")
        self.display_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        font = QFont()
        font.setPointSize(24)
        font.setBold(True)
        self.display_label.setFont(font)
        self.display_label.setFixedHeight(50)
        main_layout.addWidget(self.display_label)
        
        # 连接值变化信号
        self.abacus_widget.valueChanged.connect(lambda val: self.display_label.setText(f"{val:,}"))
        
        # 控制区域布局
        controls_layout = QVBoxLayout()
        
        # --- 设置数字行 ---
        set_num_layout = QHBoxLayout()
        self.num_input = QLineEdit()
        self.num_input.setPlaceholderText("输入数字设置到算盘")
        set_num_layout.addWidget(self.num_input)
        
        btn_set_num = QPushButton("设置数字")
        btn_set_num.clicked.connect(self.set_abacus_value_from_input)
        set_num_layout.addWidget(btn_set_num)
        
        btn_clear = QPushButton("清空算盘")
        btn_clear.clicked.connect(self.abacus_widget.clear_abacus)
        set_num_layout.addWidget(btn_clear)
        controls_layout.addLayout(set_num_layout)
        
        # --- 计算行 ---
        calc_layout = QHBoxLayout()
        
        self.op_combo = QComboBox()
        self.op_combo.addItems(["+", "-", "×", "÷"])
        calc_layout.addWidget(self.op_combo)
        
        self.operand_b_input = QLineEdit()
        self.operand_b_input.setPlaceholderText("输入操作数 B")
        calc_layout.addWidget(QLabel("B:"))
        calc_layout.addWidget(self.operand_b_input)
        
        btn_calculate = QPushButton("=")
        btn_calculate.clicked.connect(self.perform_calculation)
        calc_layout.addWidget(btn_calculate)
        controls_layout.addLayout(calc_layout)
        
        # 结果标签
        self.result_label = QLabel("结果: ")
        font_result = QFont()
        font_result.setPointSize(14)
        self.result_label.setFont(font_result)
        controls_layout.addWidget(self.result_label)
        
        main_layout.addLayout(controls_layout)
        
    def set_abacus_value_from_input(self):
        try:
            val = int(self.num_input.text())
            self.abacus_widget.set_value(val)
        except ValueError:
            self.result_label.setText("错误: 输入的不是有效数字!")
    
    def perform_calculation(self):
        try:
            val_a = self.abacus_widget.get_total_value()
            operator = self.op_combo.currentText()
            
            if not self.operand_b_input.text():
                self.result_label.setText("错误: 操作数 B 不能为空!")
                return
            val_b = int(self.operand_b_input.text())
            
            result = 0
            expr_str = f"{val_a} {operator} {val_b} = "
            
            if operator == '+':
                result = val_a + val_b
            elif operator == '-':
                result = val_a - val_b
            elif operator == '×':
                result = val_a * val_b
            elif operator == '÷':
                if val_b == 0:
                    self.result_label.setText(expr_str + "错误: 除数不能为零!")
                    return
                result = int(val_a / val_b)  # 整数除法
            
            self.result_label.setText(expr_str + str(result))
            self.abacus_widget.set_value(result)
            self.num_input.setText(str(result))  # 同时更新输入框
            
        except ValueError:
            self.result_label.setText("错误: 操作数 B 不是有效数字!")
        except Exception as e:
            self.result_label.setText(f"计算错误: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = AbacusApp()
    main_window.show()
    sys.exit(app.exec()) 