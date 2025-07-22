import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QLineEdit, QComboBox, QSizePolicy, QSpacerItem)
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QFont, QPolygonF
from PyQt5.QtCore import Qt, QPointF, QRectF, pyqtSignal

# --- Abacus Configuration ---
NUM_RODS = 9  # 算盘的档数，改为9档
NUM_UPPER_BEADS_PER_ROD = 1  # 每档上珠数量 (每颗代表5)
NUM_LOWER_BEADS_PER_ROD = 4  # 每档下珠数量 (每颗代表1)

BEAD_HEIGHT_RATIO = 0.18  # 珠子高度相对于档高度的比例
BEAD_WIDTH_RATIO = 0.8  # 珠子宽度相对于档宽度的比例
ROD_WIDTH_RATIO = 0.1  # 档（杆）的宽度相对于档宽度的比例
BEAM_HEIGHT_RATIO = 0.05  # 梁的高度相对于总高度的比例
FRAME_THICKNESS_RATIO = 0.03  # 外框厚度

# --- Colors (Light Theme) ---
COLOR_BACKGROUND = QColor("#F0F0F0")  # 背景色 (浅灰)
COLOR_FRAME = QColor("#A0A0A0")  # 外框色 (中灰)
COLOR_ROD = QColor("#707070")  # 杆颜色 (深灰)
COLOR_BEAM = QColor("#505050")  # 梁颜色 (更深灰)
COLOR_BEAD = QColor("#6495ED")  # 珠子颜色 (矢车菊蓝)
COLOR_BEAD_BORDER = QColor("#4070C0")  # 珠子边框
COLOR_TEXT = QColor("#333333")  # 文本颜色


class AbacusWidget(QWidget):
    valueChanged = pyqtSignal(int)
    valueOverflow = pyqtSignal(str)  # 新增信号用于通知数字溢出

    def __init__(self, parent=None):
        super().__init__(parent)
        self.num_rods = NUM_RODS
        self.num_upper_beads = NUM_UPPER_BEADS_PER_ROD
        self.num_lower_beads = NUM_LOWER_BEADS_PER_ROD

        # abacus_state[rod_index] = {'upper_active': count, 'lower_active': count}
        # 'upper_active': 靠梁的上珠数量 (0 or 1 for NUM_UPPER_BEADS_PER_ROD=1)
        # 'lower_active': 靠梁的下珠数量 (0 to NUM_LOWER_BEADS_PER_ROD)
        self.abacus_state = []
        self.init_abacus_state()

        self.setMinimumSize(400, 200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def init_abacus_state(self):
        self.abacus_state = [{'upper_active': 0, 'lower_active': 0} for _ in range(self.num_rods)]
        self.update_display_value()

    def get_rod_value(self, rod_idx):
        state = self.abacus_state[rod_idx]
        return state['upper_active'] * 5 + state['lower_active'] * 1

    def get_total_value(self):
        total = 0
        for i in range(self.num_rods):
            total = total * 10 + self.get_rod_value(i)
        return total

    def update_display_value(self):
        self.valueChanged.emit(self.get_total_value())
        self.update()  # Trigger repaint

    def clear_abacus(self):
        self.init_abacus_state()

    def set_value(self, number_to_set):
        self.clear_abacus()
        if not isinstance(number_to_set, int):
            try:
                number_to_set = int(number_to_set)
            except ValueError:
                print("Invalid number to set on abacus")
                return

        if number_to_set < 0:  # For simplicity, handle positive numbers
            number_to_set = 0

        s_num = str(number_to_set)

        # 检查数字是否超过算盘的最大容量
        max_value = 10 ** self.num_rods - 1
        if number_to_set > max_value:
            self.valueOverflow.emit(f"数字 {number_to_set} 超过算盘最大容量 ({max_value})，将显示为 {number_to_set % (10 ** self.num_rods)}")
            number_to_set = number_to_set % (10 ** self.num_rods)
            s_num = str(number_to_set)

        # 从右到左分配数字，保证个位在最右边
        for i, digit_char in enumerate(reversed(s_num)):
            digit = int(digit_char)
            rod_idx = self.num_rods - 1 - i

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

            if upper_active > self.num_upper_beads:  # Should not happen with 1 upper bead
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

        # --- Calculate dimensions ---
        frame_thickness = min(width, height) * FRAME_THICKNESS_RATIO

        drawable_width = width - 2 * frame_thickness
        drawable_height = height - 2 * frame_thickness

        rod_area_width = drawable_width / self.num_rods
        rod_width = rod_area_width * ROD_WIDTH_RATIO
        bead_width = rod_area_width * BEAD_WIDTH_RATIO

        beam_height = drawable_height * BEAM_HEIGHT_RATIO

        # Vertical sections for beads
        # Upper beads area, beam area, lower beads area
        # Let's say upper beads take 25%, beam 10%, lower 65% of vertical space for beads
        total_bead_space_v = drawable_height - beam_height
        upper_bead_area_height = total_bead_space_v * (
            0.3 if self.num_upper_beads > 0 else 0)  # More space for upper beads
        lower_bead_area_height = total_bead_space_v * (0.7 if self.num_lower_beads > 0 else 0)

        bead_v_spacing_upper = upper_bead_area_height / (self.num_upper_beads + 1) if self.num_upper_beads > 0 else 0
        bead_height_upper = bead_v_spacing_upper * 0.8  # BEAD_HEIGHT_RATIO applied locally

        bead_v_spacing_lower = lower_bead_area_height / (self.num_lower_beads + 1) if self.num_lower_beads > 0 else 0
        bead_height_lower = bead_v_spacing_lower * 0.8  # BEAD_HEIGHT_RATIO applied locally

        # --- Draw Frame ---
        painter.setPen(QPen(COLOR_FRAME, frame_thickness * 0.8))  # Slightly thinner pen for frame border
        painter.setBrush(COLOR_FRAME)
        painter.drawRect(0, 0, width, height)  # Outer border
        # Inner clear area:
        painter.fillRect(QRectF(frame_thickness, frame_thickness, drawable_width, drawable_height), COLOR_BACKGROUND)

        # --- Draw Beam ---
        beam_y = frame_thickness + upper_bead_area_height
        painter.setBrush(COLOR_BEAM)
        painter.setPen(Qt.NoPen)
        painter.drawRect(QRectF(frame_thickness, beam_y, drawable_width, beam_height))

        # --- Draw Rods and Beads ---
        for i in range(self.num_rods):
            rod_x_center = frame_thickness + (i + 0.5) * rod_area_width
            rod_x_start = rod_x_center - rod_width / 2

            # Draw Rod
            painter.setBrush(COLOR_ROD)
            painter.drawRect(QRectF(rod_x_start, frame_thickness, rod_width, drawable_height))

            rod_state = self.abacus_state[i]

            # Draw Upper Beads
            for j in range(self.num_upper_beads):
                bead_center_x = rod_x_center
                bead_rect = QRectF(0, 0, bead_width, bead_height_upper)

                if j < rod_state['upper_active']:  # Active bead (towards beam)
                    bead_center_y = beam_y - (
                                j + 0.5) * bead_v_spacing_upper - bead_v_spacing_upper * 0.1  # Move closer to beam
                else:  # Inactive bead (away from beam)
                    # inactive_idx = j - rod_state['upper_active']
                    bead_center_y = frame_thickness + (j - rod_state['upper_active'] + 0.5) * bead_v_spacing_upper

                bead_rect.moveCenter(QPointF(bead_center_x, bead_center_y))
                self._draw_bead(painter, bead_rect)

            # Draw Lower Beads
            for j in range(self.num_lower_beads):
                bead_center_x = rod_x_center
                bead_rect = QRectF(0, 0, bead_width, bead_height_lower)

                if j < rod_state['lower_active']:  # Active bead (towards beam)
                    # active_idx = rod_state['lower_active'] - 1 - j # 0 is furthest active from beam
                    # active_idx_from_beam = j
                    bead_center_y = beam_y + beam_height + (j + 0.5) * bead_v_spacing_lower + bead_v_spacing_lower * 0.1
                else:  # Inactive bead (away from beam)
                    inactive_idx = j - rod_state['lower_active']
                    bead_center_y = beam_y + beam_height + lower_bead_area_height - (
                                (self.num_lower_beads - 1 - j) + 0.5) * bead_v_spacing_lower
                    # inactive_idx_from_bottom = self.num_lower_beads - 1 - (j - rod_state['lower_active'])
                    # bead_center_y = frame_thickness + drawable_height - (inactive_idx_from_bottom + 0.5) * bead_v_spacing_lower

                bead_rect.moveCenter(QPointF(bead_center_x, bead_center_y))
                self._draw_bead(painter, bead_rect)

        # Draw decimal points markers (optional, small dots on beam)
        painter.setBrush(COLOR_BACKGROUND)
        painter.setPen(Qt.NoPen)
        dot_radius = beam_height / 4
        for i in range(self.num_rods):
            if (self.num_rods - 1 - i) % 3 == 0 and (self.num_rods - 1 - i) != 0:  # e.g., before thousands, millions
                dot_x = frame_thickness + (i + 0.5) * rod_area_width
                dot_y = beam_y + beam_height / 2
                painter.drawEllipse(QPointF(dot_x, dot_y), dot_radius, dot_radius)

    def _draw_bead(self, painter, rect):
        # Bicone shape for beads
        painter.setPen(QPen(COLOR_BEAD_BORDER, 1))
        painter.setBrush(COLOR_BEAD)

        # A simple ellipse for now
        # painter.drawEllipse(rect)

        # Bicone shape
        poly = QPolygonF()
        poly.append(QPointF(rect.center().x(), rect.top()))  # Top point
        poly.append(QPointF(rect.right(), rect.center().y()))  # Right mid point
        poly.append(QPointF(rect.center().x(), rect.bottom()))  # Bottom point
        poly.append(QPointF(rect.left(), rect.center().y()))  # Left mid point
        painter.drawPolygon(poly)

    def mousePressEvent(self, event):
        width = self.width()
        height = self.height()

        frame_thickness = min(width, height) * FRAME_THICKNESS_RATIO
        drawable_width = width - 2 * frame_thickness
        drawable_height = height - 2 * frame_thickness
        rod_area_width = drawable_width / self.num_rods
        beam_height = drawable_height * BEAM_HEIGHT_RATIO

        total_bead_space_v = drawable_height - beam_height
        upper_bead_area_height = total_bead_space_v * (0.3 if self.num_upper_beads > 0 else 0)
        # lower_bead_area_height = total_bead_space_v * (0.7 if self.num_lower_beads > 0 else 0)

        beam_y_start = frame_thickness + upper_bead_area_height
        # beam_y_end = beam_y_start + beam_height

        click_x = event.pos().x()
        click_y = event.pos().y()

        if not (frame_thickness < click_x < width - frame_thickness and \
                frame_thickness < click_y < height - frame_thickness):
            return  # Click outside drawable area

        rod_idx = int((click_x - frame_thickness) / rod_area_width)
        if not (0 <= rod_idx < self.num_rods):
            return

        rod_state = self.abacus_state[rod_idx]

        # Check if upper bead area is clicked
        if click_y < beam_y_start:
            # Upper beads are numbered 0 (closest to beam when active) to num_upper_beads-1
            # Here, with 1 upper bead, it's simple:
            if self.num_upper_beads == 1:
                rod_state['upper_active'] = 1 - rod_state['upper_active']  # Toggle

        # Check if lower bead area is clicked
        elif click_y > beam_y_start + beam_height:
            # Lower beads are numbered 0 (closest to beam when active) to num_lower_beads-1
            # Determine which bead was clicked based on relative y position in lower_bead_area

            # Simplified click logic for lower beads:
            # Click above midpoint of lower active beads: move all lower beads up
            # Click below midpoint of lower active beads: move all lower beads down
            # This isn't perfect abacus interaction, but simpler to implement initially.
            # A more accurate way:
            #   y_in_lower_area = click_y - (beam_y_start + beam_height)
            #   total_lower_area_h = drawable_height - upper_bead_area_height - beam_height
            #   clicked_bead_index_approx = int((y_in_lower_area / total_lower_area_h) * self.num_lower_beads)

            # Corrected logic based on bead positions:
            # bead_v_spacing_lower = lower_bead_area_height / (self.num_lower_beads + 1) if self.num_lower_beads > 0 else 0
            # (Calculations from paintEvent would be needed here to find bead rects)

            # Simpler interaction: if you click a lower bead:
            # - if it's inactive, it and all inactive beads between it and beam become active.
            # - if it's active, it and all active beads between it and the beam edge (further from beam) become inactive.

            # Let's find which bead was "intended"
            # Relative y in the lower bead section (0.0 to 1.0)
            y_lower_start = beam_y_start + beam_height
            y_lower_end = frame_thickness + drawable_height
            relative_y = (click_y - y_lower_start) / (y_lower_end - y_lower_start)

            # Estimate clicked bead index (0 to NUM_LOWER_BEADS-1)
            # 0 is top-most lower bead, NUM_LOWER_BEADS-1 is bottom-most
            clicked_idx_visual = int(relative_y * self.num_lower_beads)
            if clicked_idx_visual < 0: clicked_idx_visual = 0
            if clicked_idx_visual >= self.num_lower_beads: clicked_idx_visual = self.num_lower_beads - 1

            # Logic: if clicked_idx_visual < current_active_count, means clicked an active bead.
            #   Then, all beads from this one downwards (visually) become inactive.
            #   So, new active_count = clicked_idx_visual.
            # if clicked_idx_visual >= current_active_count, means clicked an inactive bead.
            #   Then, this bead and all above it up to current_active_count become active.
            #   So, new active_count = clicked_idx_visual + 1.

            current_lower_active = rod_state['lower_active']

            # If the clicked visual position 'clicked_idx_visual' corresponds to an already active bead
            if clicked_idx_visual < current_lower_active:
                rod_state['lower_active'] = clicked_idx_visual
            else:  # Corresponds to an inactive bead (or the one right below active ones)
                rod_state['lower_active'] = clicked_idx_visual + 1

        else:  # Clicked on beam or dead space
            return

        self.update_display_value()


class AbacusApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("中国算盘 (Chinese Abacus)")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet(f"QWidget {{ background-color: {COLOR_BACKGROUND.name()}; color: {COLOR_TEXT.name()}; }} \
                           QPushButton {{ background-color: #B0C4DE; border: 1px solid #778899; padding: 5px; border-radius: 3px; }} \
                           QPushButton:hover {{ background-color: #A0B4CE; }} \
                           QLineEdit {{ border: 1px solid #AAAAAA; padding: 3px; background-color: white; }} \
                           QLabel {{ padding: 5px; }}")

        layout = QVBoxLayout(self)

        self.abacus_widget = AbacusWidget()
        layout.addWidget(self.abacus_widget, 1)  # Give abacus widget more space

        self.display_label = QLabel("0")
        self.display_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        font = QFont()
        font.setPointSize(24)
        font.setBold(True)
        self.display_label.setFont(font)
        self.display_label.setFixedHeight(50)
        layout.addWidget(self.display_label)

        self.abacus_widget.valueChanged.connect(lambda val: self.display_label.setText(f"{val:,}"))
        self.abacus_widget.valueOverflow.connect(self.handle_value_overflow)  # 连接溢出信号

        # Controls Layout
        controls_layout = QVBoxLayout()

        # --- Set Number Row ---
        set_num_layout = QHBoxLayout()
        self.num_input = QLineEdit()
        self.num_input.setPlaceholderText("输入数字设置到算盘")
        set_num_layout.addWidget(self.num_input)

        btn_set_num = QPushButton("设置数字")
        btn_set_num.clicked.connect(self.set_abacus_value_from_input)
        set_num_layout.addWidget(btn_set_num)

        btn_clear = QPushButton("清盘 (Clear)")
        btn_clear.clicked.connect(self.abacus_widget.clear_abacus)
        set_num_layout.addWidget(btn_clear)
        controls_layout.addLayout(set_num_layout)

        # --- Calculation Row ---
        calc_layout = QHBoxLayout()
        self.operand_a_label = QLabel("算盘值 (A):")  # Operand A is from abacus
        # self.operand_a_input = QLineEdit() # Operand A is from abacus
        # self.operand_a_input.setReadOnly(True)
        # calc_layout.addWidget(QLabel("A:"))
        # calc_layout.addWidget(self.operand_a_input)

        self.op_combo = QComboBox()
        self.op_combo.addItems(["+", "-", "*", "/"])
        calc_layout.addWidget(self.op_combo)

        self.operand_b_input = QLineEdit()
        self.operand_b_input.setPlaceholderText("输入操作数 B")
        calc_layout.addWidget(QLabel("B:"))
        calc_layout.addWidget(self.operand_b_input)

        btn_calculate = QPushButton("=")
        btn_calculate.clicked.connect(self.perform_calculation)
        calc_layout.addWidget(btn_calculate)
        controls_layout.addLayout(calc_layout)

        self.result_label = QLabel("结果: ")
        font_result = QFont()
        font_result.setPointSize(14)
        self.result_label.setFont(font_result)
        controls_layout.addWidget(self.result_label)

        # Spacer to push controls up a bit if window is tall
        # controls_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        layout.addLayout(controls_layout)
        # self.abacus_widget.set_value(1234567890123) # Test initial value

    def set_abacus_value_from_input(self):
        try:
            val = int(self.num_input.text())
            self.abacus_widget.set_value(val)
        except ValueError:
            self.result_label.setText("错误: 输入的不是有效数字!")
            # self.num_input.clear()

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
            elif operator == '*':
                result = val_a * val_b
            elif operator == '/':
                if val_b == 0:
                    self.result_label.setText(expr_str + "错误: 除数不能为零!")
                    return
                result = int(val_a / val_b)  # Integer division for abacus

            self.result_label.setText(expr_str + str(result))
            self.abacus_widget.set_value(result)
            self.num_input.setText(str(result))  # Update input field as well

        except ValueError:
            self.result_label.setText("错误: 操作数 B 不是有效数字!")
        except Exception as e:
            self.result_label.setText(f"计算错误: {e}")

    def handle_value_overflow(self, message):
        """处理算盘数值溢出"""
        self.result_label.setText(message)
        self.result_label.setStyleSheet("color: #FF0000;")  # 红色显示警告信息


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = AbacusApp()
    main_window.show()
    sys.exit(app.exec_())