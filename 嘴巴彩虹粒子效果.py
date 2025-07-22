import pygame
import pygame.camera
import mediapipe as mp
import numpy as np
import math
import platform
import asyncio
import cv2
import time

# Mediapipe drawing utils
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Pygame setup
WIDTH, HEIGHT = 800, 600
COLS, ROWS = 80, 60  # 网格大小，使粒子更大更明显
CELL_SIZE = WIDTH // COLS
FPS = 60

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mouth Rainbow Particles")
clock = pygame.time.Clock()

# Mediapipe Face Mesh setup
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Camera setup
pygame.camera.init()
cameras = pygame.camera.list_cameras()
if not cameras:
    raise Exception("No cameras found")
cam = pygame.camera.Camera(cameras[0], (320, 240))
cam.start()

# 嘴部关键点索引 (MediaPipe Face Mesh 468个关键点中的嘴部点)
# 上嘴唇外轮廓
UPPER_LIP_OUTER = [61, 84, 17, 314, 405, 320, 307, 375, 321, 308, 324, 318]
# 下嘴唇外轮廓  
LOWER_LIP_OUTER = [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308, 415]
# 嘴角
MOUTH_CORNERS = [61, 291]
# 上下嘴唇中心点
UPPER_LIP_CENTER = 13
LOWER_LIP_CENTER = 14

# Grid for particle simulation
class Grid:
    def __init__(self, cols, rows):
        self.cols = cols
        self.rows = rows
        # 初始化网格，None表示空，颜色值表示有粒子
        self.grid = [[None for _ in range(rows)] for _ in range(cols)]
    
    def add_particle(self, x, y, color):
        # 确保坐标在有效范围内
        if 0 <= x < self.cols and 0 <= y < self.rows:
            # 只在空位置添加粒子
            if self.grid[x][y] is None:
                self.grid[x][y] = color
                return True
        return False
    
    def update(self):
        # 从底部向上更新，防止连锁效应
        for y in range(self.rows - 1, -1, -1):
            for x in range(self.cols):
                # 如果当前位置有粒子
                if self.grid[x][y] is not None:
                    # 如果在底部，不移动（边界保持）
                    if y == self.rows - 1:
                        continue

                    # 检查下方是否为空
                    if self.grid[x][y + 1] is None:
                        # 向下移动
                        self.grid[x][y + 1] = self.grid[x][y]
                        self.grid[x][y] = None
                    # 如果下方有障碍，检查左下（确保不越界）
                    elif x > 0 and self.grid[x - 1][y + 1] is None:
                        # 向左下移动
                        self.grid[x - 1][y + 1] = self.grid[x][y]
                        self.grid[x][y] = None
                    # 如果左下有障碍，检查右下（确保不越界）
                    elif x < self.cols - 1 and self.grid[x + 1][y + 1] is None:
                        # 向右下移动
                        self.grid[x + 1][y + 1] = self.grid[x][y]
                        self.grid[x][y] = None
                    # 如果三个方向都有障碍，粒子保持不动

        # 处理左右边界的粒子堆积
        self._handle_side_boundaries()

    def _handle_side_boundaries(self):
        """处理左右边界的粒子，确保它们不会消失"""
        # 左边界处理
        for y in range(self.rows - 1):
            if self.grid[0][y] is not None and y < self.rows - 1:
                # 如果左边界有粒子且下方为空，让它向下移动
                if self.grid[0][y + 1] is None:
                    self.grid[0][y + 1] = self.grid[0][y]
                    self.grid[0][y] = None
                # 如果下方被占用，尝试向右下移动
                elif self.cols > 1 and self.grid[1][y + 1] is None:
                    self.grid[1][y + 1] = self.grid[0][y]
                    self.grid[0][y] = None

        # 右边界处理
        for y in range(self.rows - 1):
            if self.grid[self.cols - 1][y] is not None and y < self.rows - 1:
                # 如果右边界有粒子且下方为空，让它向下移动
                if self.grid[self.cols - 1][y + 1] is None:
                    self.grid[self.cols - 1][y + 1] = self.grid[self.cols - 1][y]
                    self.grid[self.cols - 1][y] = None
                # 如果下方被占用，尝试向左下移动
                elif self.cols > 1 and self.grid[self.cols - 2][y + 1] is None:
                    self.grid[self.cols - 2][y + 1] = self.grid[self.cols - 1][y]
                    self.grid[self.cols - 1][y] = None

    def render(self, surface):
        # 绘制所有粒子
        for x in range(self.cols):
            for y in range(self.rows):
                if self.grid[x][y] is not None:
                    pygame.draw.rect(surface, self.grid[x][y], 
                                   (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

# Global variables
grid = Grid(COLS, ROWS)
hue_value = 0
last_particle_time = 0
show_clean_view = True  # 控制是否显示纯净画面（无人脸标记）

def hsv_to_rgb(h, s, v):
    # Convert HSV (0-360, 0-1, 0-1) to RGB (0-255, 0-255, 0-255)
    h = h % 360
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c
    if 0 <= h < 60:
        r, g, b = c, x, 0
    elif 60 <= h < 120:
        r, g, b = x, c, 0
    elif 120 <= h < 180:
        r, g, b = 0, c, x
    elif 180 <= h < 240:
        r, g, b = 0, x, c
    elif 240 <= h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x
    return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))

def detect_mouth_opening(face_landmarks):
    """检测嘴巴张开程度并生成覆盖整个嘴巴宽度的粒子点"""
    if len(face_landmarks) < 468:
        return 0, None, None, [], 0

    # 获取上下嘴唇中心点
    upper_lip = face_landmarks[UPPER_LIP_CENTER]
    lower_lip = face_landmarks[LOWER_LIP_CENTER]

    # 计算嘴巴张开距离
    mouth_opening = math.sqrt((upper_lip[0] - lower_lip[0])**2 + (upper_lip[1] - lower_lip[1])**2)

    # 获取嘴角点计算嘴巴宽度作为参考
    left_corner = face_landmarks[MOUTH_CORNERS[0]]
    right_corner = face_landmarks[MOUTH_CORNERS[1]]
    mouth_width = math.sqrt((left_corner[0] - right_corner[0])**2 + (left_corner[1] - right_corner[1])**2)

    # 归一化张开程度（相对于嘴巴宽度）
    if mouth_width > 0:
        normalized_opening = mouth_opening / mouth_width
    else:
        normalized_opening = 0

    # 计算嘴巴中心位置
    mouth_center = ((upper_lip[0] + lower_lip[0]) // 2, (upper_lip[1] + lower_lip[1]) // 2)

    # 生成覆盖整个嘴巴宽度的粒子点
    mouth_points = []
    if normalized_opening > 0.1:  # 只有当嘴巴足够张开时才生成粒子
        # 计算粒子生成的数量，基于嘴巴宽度
        num_particles = max(5, int(mouth_width / 8))  # 至少5个粒子，根据嘴巴宽度调整

        # 在嘴巴宽度范围内均匀分布粒子点
        for i in range(num_particles):
            # 计算从左嘴角到右嘴角的插值位置
            t = i / (num_particles - 1) if num_particles > 1 else 0.5

            # 在左右嘴角之间插值
            point_x = int(left_corner[0] + t * (right_corner[0] - left_corner[0]))
            point_y = int(left_corner[1] + t * (right_corner[1] - left_corner[1]))

            # 稍微向嘴巴内部偏移，让粒子从嘴巴内部生成
            offset_y = int(mouth_opening * 0.2)  # 向嘴巴内部偏移
            point_y += offset_y

            mouth_points.append((point_x, point_y))

    return normalized_opening, mouth_center, (upper_lip, lower_lip), mouth_points, mouth_width

async def main():
    global hue_value, last_particle_time, grid, show_clean_view
    running = True
    
    def setup():
        pass  # Pygame and Mediapipe already initialized
    
    def update_loop():
        nonlocal running
        global hue_value, last_particle_time, grid, show_clean_view
        
        # Get camera image
        try:
            img = cam.get_image()
        except:
            return
        
        # Flip for mirror view so it's more intuitive
        img = pygame.transform.flip(img, True, False)
        
        # Convert Pygame surface to array for processing
        img_array = pygame.surfarray.array3d(img)
        img_array = np.swapaxes(img_array, 0, 1)  # Transpose for Mediapipe
        
        # Convert to OpenCV format (RGB)
        img_cv = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
        
        # Process face landmarks
        results = face_mesh.process(img_cv)
        
        # Create a copy for drawing
        img_display = img_cv.copy()
        
        # 清空屏幕
        screen.fill((0, 0, 0))
        
        # 创建纯净画面（无标记）
        clean_img = img_cv.copy()
        clean_img_pygame = cv2.cvtColor(clean_img, cv2.COLOR_RGB2BGR)
        clean_img_pygame = np.swapaxes(clean_img_pygame, 0, 1)
        clean_surface = pygame.surfarray.make_surface(clean_img_pygame)

        # 处理人脸检测和粒子生成
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # 收集所有脸部关键点坐标
                face_points = []
                for lm in face_landmarks.landmark:
                    x, y = int(lm.x * WIDTH), int(lm.y * HEIGHT)
                    face_points.append([x, y])

                # 检测嘴巴张开程度
                mouth_opening, mouth_center, lip_points, mouth_points, mouth_width = detect_mouth_opening(face_points)

                # 如果需要显示调试信息，绘制人脸网格
                if not show_clean_view:
                    mp_drawing.draw_landmarks(
                        img_display,
                        face_landmarks,
                        mp_face_mesh.FACEMESH_TESSELATION,
                        mp_drawing.DrawingSpec(thickness=1, circle_radius=1),
                        mp_drawing.DrawingSpec(thickness=1, circle_radius=1)
                    )

                # 如果嘴巴张开程度超过阈值，生成粒子
                if mouth_opening > 0.12 and mouth_points:  # 降低阈值，更容易触发
                    current_time = time.time()

                    # 限制粒子生成速率
                    if current_time - last_particle_time > 0.015:  # 更快的生成速率
                        # 在嘴巴宽度范围内生成粒子
                        for point in mouth_points:
                            grid_x = max(0, min(COLS - 1, point[0] // CELL_SIZE))
                            grid_y = max(0, min(ROWS - 1, point[1] // CELL_SIZE))

                            # 生成彩虹色粒子，每个点使用稍微不同的颜色
                            color = hsv_to_rgb(hue_value, 1.0, 1.0)
                            if grid.add_particle(grid_x, grid_y, color):
                                hue_value = (hue_value + 3) % 360  # 颜色变化

                        last_particle_time = current_time

                        # 如果不是纯净视图，绘制嘴巴生成点的标记
                        if not show_clean_view:
                            # 绘制嘴巴宽度线
                            if lip_points:
                                left_corner = face_points[MOUTH_CORNERS[0]]
                                right_corner = face_points[MOUTH_CORNERS[1]]
                                pygame.draw.line(screen, (255, 255, 0),
                                               (left_corner[0], left_corner[1]),
                                               (right_corner[0], right_corner[1]), 2)

                            # 绘制粒子生成点
                            for point in mouth_points:
                                pygame.draw.circle(screen, (0, 255, 0), point, 3)

        # 绘制背景（根据视图模式选择）
        if show_clean_view:
            # 使用纯净画面
            screen.blit(pygame.transform.scale(clean_surface, (WIDTH, HEIGHT)), (0, 0))
        else:
            # 使用带标记的画面
            img_with_marks = cv2.cvtColor(img_display, cv2.COLOR_RGB2BGR)
            img_with_marks = np.swapaxes(img_with_marks, 0, 1)
            marked_surface = pygame.surfarray.make_surface(img_with_marks)
            screen.blit(pygame.transform.scale(marked_surface, (WIDTH, HEIGHT)), (0, 0))

        # 更新和绘制粒子（在背景之上）
        grid.update()
        grid.render(screen)

        # 只在非纯净视图下显示调试信息
        if not show_clean_view and results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                face_points = []
                for lm in face_landmarks.landmark:
                    x, y = int(lm.x * WIDTH), int(lm.y * HEIGHT)
                    face_points.append([x, y])

                mouth_opening, mouth_center, lip_points, mouth_points, mouth_width = detect_mouth_opening(face_points)

                # 绘制嘴巴张开程度信息
                if lip_points:
                    upper_lip, lower_lip = lip_points
                    pygame.draw.circle(screen, (255, 0, 0), upper_lip, 3)
                    pygame.draw.circle(screen, (255, 0, 0), lower_lip, 3)
                    pygame.draw.line(screen, (255, 255, 0), upper_lip, lower_lip, 2)

                # 显示张开程度和使用说明
                font = pygame.font.Font(None, 36)
                small_font = pygame.font.Font(None, 24)

                # 主要信息
                text = font.render(f"Mouth Opening: {mouth_opening:.2f}", True, (255, 255, 255))
                screen.blit(text, (10, 10))

                # 状态指示
                if mouth_opening > 0.12:
                    status_text = small_font.render("Generating particles!", True, (0, 255, 0))
                    screen.blit(status_text, (10, 50))
                else:
                    status_text = small_font.render("Open your mouth to generate particles", True, (255, 255, 0))
                    screen.blit(status_text, (10, 50))

                # 使用说明
                instruction1 = small_font.render("Instructions:", True, (200, 200, 200))
                instruction2 = small_font.render("- Open your mouth to create rainbow particles", True, (200, 200, 200))
                instruction3 = small_font.render("- Particles will fall like sand and stay in the screen", True, (200, 200, 200))
                instruction4 = small_font.render("- Press ESC to exit, C to clear, V to toggle view", True, (200, 200, 200))

                screen.blit(instruction1, (10, HEIGHT - 100))
                screen.blit(instruction2, (10, HEIGHT - 80))
                screen.blit(instruction3, (10, HEIGHT - 60))
                screen.blit(instruction4, (10, HEIGHT - 40))

        # 在纯净视图下显示简单的状态信息
        if show_clean_view:
            small_font = pygame.font.Font(None, 24)
            view_text = small_font.render("Clean View - Press V to toggle debug view", True, (255, 255, 255))
            screen.blit(view_text, (10, 10))
        
        # 更新显示
        pygame.display.flip()
    
    setup()
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_c:
                    # 清空所有粒子
                    grid = Grid(COLS, ROWS)
                elif event.key == pygame.K_v:
                    # 切换视图模式
                    show_clean_view = not show_clean_view
                elif event.key == pygame.K_SPACE:
                    # 暂停/继续粒子更新
                    pass  # 可以在这里添加暂停功能
        update_loop()
        await asyncio.sleep(1.0 / FPS)
    
    # Cleanup
    cam.stop()
    face_mesh.close()
    pygame.quit()

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())
