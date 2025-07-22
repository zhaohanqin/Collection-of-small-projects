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
COLS, ROWS = 80, 60  # 减少网格大小，使沙子颗粒更大更明显
CELL_SIZE = WIDTH // COLS
FPS = 60

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Interactive Rainbow Sand")
clock = pygame.time.Clock()

# Mediapipe Hands setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=4, min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Camera setup
pygame.camera.init()
cameras = pygame.camera.list_cameras()
if not cameras:
    raise Exception("No cameras found")
cam = pygame.camera.Camera(cameras[0], (320, 240))
cam.start()

# Grid for sand simulation
class Grid:
    def __init__(self, cols, rows):
        self.cols = cols
        self.rows = rows
        # 初始化网格，None表示空，颜色值表示有沙子
        self.grid = [[None for _ in range(rows)] for _ in range(cols)]
    
    def add_sand(self, x, y, color):
        # 确保坐标在有效范围内
        if 0 <= x < self.cols and 0 <= y < self.rows:
            # 只在空位置添加沙子
            if self.grid[x][y] is None:
                self.grid[x][y] = color
                return True
        return False
    
    def update(self):
        # 从底部向上更新，防止连锁效应
        for y in range(self.rows - 1, -1, -1):
            for x in range(self.cols):
                # 如果当前位置有沙子
                if self.grid[x][y] is not None:
                    # 如果在底部，不移动
                    if y == self.rows - 1:
                        continue
                    
                    # 检查下方是否为空
                    if self.grid[x][y + 1] is None:
                        # 向下移动
                        self.grid[x][y + 1] = self.grid[x][y]
                        self.grid[x][y] = None
                    # 如果下方有障碍，检查左下
                    elif x > 0 and self.grid[x - 1][y + 1] is None:
                        # 向左下移动
                        self.grid[x - 1][y + 1] = self.grid[x][y]
                        self.grid[x][y] = None
                    # 如果左下有障碍，检查右下
                    elif x < self.cols - 1 and self.grid[x + 1][y + 1] is None:
                        # 向右下移动
                        self.grid[x + 1][y + 1] = self.grid[x][y]
                        self.grid[x][y] = None
                    # 如果三个方向都有障碍，沙子保持不动
    
    def render(self, surface):
        # 绘制所有沙子
        for x in range(self.cols):
            for y in range(self.rows):
                if self.grid[x][y] is not None:
                    pygame.draw.rect(surface, self.grid[x][y], 
                                   (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

# Global variables
grid = Grid(COLS, ROWS)
hue_value = 0
last_sand_times = {}  # 用字典记录每只手的最后沙子生成时间

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

async def main():
    global hue_value, last_sand_times
    running = True
    
    def setup():
        pass  # Pygame and Mediapipe already initialized
    
    def update_loop():
        nonlocal running
        global hue_value, last_sand_times
        
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
        
        # Process hand landmarks
        results = hands.process(img_cv)
        
        # Create a copy for drawing
        img_display = img_cv.copy()
        
        # 清空屏幕
        screen.fill((0, 0, 0))
        
        # 绘制摄像头背景
        img_display_pygame = cv2.cvtColor(img_display, cv2.COLOR_RGB2BGR)
        img_display_pygame = np.swapaxes(img_display_pygame, 0, 1)
        drawn_surface = pygame.surfarray.make_surface(img_display_pygame)
        screen.blit(pygame.transform.scale(drawn_surface, (WIDTH, HEIGHT)), (0, 0))
        
        # 更新和绘制沙子
        grid.update()
        grid.render(screen)
        
        # 处理手部检测和沙子生成
        if results.multi_hand_landmarks:
            for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                # 绘制手部关节点
                mp_drawing.draw_landmarks(
                    img_display,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style())

                # 获取拇指和食指位置
                thumb = hand_landmarks.landmark[4]
                index = hand_landmarks.landmark[8]
                
                # 计算两指间距离
                dist = math.sqrt((thumb.x - index.x) ** 2 + (thumb.y - index.y) ** 2)
                
                # 捏合检测 - 当两指距离小于阈值时
                if dist < 0.05:
                    current_time = time.time()
                    # 为每只手设置独立的时间控制
                    if hand_idx not in last_sand_times:
                        last_sand_times[hand_idx] = 0
                        
                    # 限制沙子生成速率，避免一次生成太多
                    if current_time - last_sand_times[hand_idx] > 0.01:  # 每10毫秒生成一粒沙子
                        # 计算两指中点
                        mid_x = (thumb.x + index.x) / 2
                        mid_y = (thumb.y + index.y) / 2
                        
                        # 在屏幕上绘制捏合点的绿色标记
                        pinch_screen_x = int(mid_x * WIDTH)
                        pinch_screen_y = int(mid_y * HEIGHT)
                        pygame.draw.circle(screen, (0, 255, 0), (pinch_screen_x, pinch_screen_y), 10)
                        
                        # 将中点映射到网格坐标
                        grid_x = int(mid_x * COLS)
                        grid_y = int(mid_y * ROWS)
                        
                        # 生成彩虹色沙子
                        color = hsv_to_rgb(hue_value, 1.0, 1.0)
                        if grid.add_sand(grid_x, grid_y, color):
                            hue_value = (hue_value + 1) % 360
                            last_sand_times[hand_idx] = current_time
        
        # 将带有手部骨架的图像转换为Pygame可显示的格式
        img_with_hands = cv2.cvtColor(img_display, cv2.COLOR_RGB2BGR)
        img_with_hands = np.swapaxes(img_with_hands, 0, 1)
        hands_surface = pygame.surfarray.make_surface(img_with_hands)
        
        # 重新绘制背景，这次带有手部骨架
        screen.blit(pygame.transform.scale(hands_surface, (WIDTH, HEIGHT)), (0, 0))
        
        # 重新绘制沙子，确保它显示在手部骨架之上
        grid.render(screen)
        
        # 更新显示
        pygame.display.flip()
    
    setup()
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        update_loop()
        await asyncio.sleep(1.0 / FPS)
    
    # Cleanup
    cam.stop()
    hands.close()
    pygame.quit()

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())