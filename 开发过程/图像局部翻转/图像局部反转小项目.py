import cv2
import os
import random
import numpy as np

def alpha_blend(src, dst, alpha):
    """Alpha blending 两张图"""
    return cv2.addWeighted(src, 1 - alpha, dst, alpha, 0)

def run_sliding_animation(
        original_path, final_path, pool_folder,
        output_video="animation_output.mp4",
        interval=0.5, frame_rate=20,
        grid_size=(4, 4),  # 网格大小，将图像分成 4x4 的网格
        total_steps=30,
        blend_frames=10,
        progress_callback=None  # 添加进度回调函数
    ):
    # 图像读取 + 错误处理
    if not os.path.exists(original_path):
        raise FileNotFoundError(f"原始图像不存在: {original_path}")
    if not os.path.exists(final_path):
        raise FileNotFoundError(f"最终图像不存在: {final_path}")

    original = cv2.imread(original_path)
    final_image = cv2.imread(final_path)

    if original is None or final_image is None:
        raise ValueError("图像读取失败，可能是文件路径错误或图像损坏")

    if original.shape != final_image.shape:
        raise ValueError("原始图像和最终图像尺寸不一致，请确保尺寸完全一致")

    # 调整图像大小到指定分辨率
    h, w = original.shape[:2]
    if h > w:  # 长大于宽
        target_h, target_w = 1080, 720
    else:  # 宽大于长
        target_h, target_w = 720, 1080
    
    # 使用 INTER_AREA 算法调整图像大小
    original = cv2.resize(original, (target_w, target_h), interpolation=cv2.INTER_AREA)
    final_image = cv2.resize(final_image, (target_w, target_h), interpolation=cv2.INTER_AREA)
    
    h, w = original.shape[:2]
    canvas = original.copy()
    
    # 计算每个网格的大小
    grid_h = h // grid_size[0]
    grid_w = w // grid_size[1]
    
    # 加载图池
    if not os.path.isdir(pool_folder):
        raise FileNotFoundError(f"图像池文件夹不存在: {pool_folder}")

    pool_images = []
    for f in os.listdir(pool_folder):
        if f.lower().endswith(('.jpg', '.jpeg', '.png')):
            img_path = os.path.join(pool_folder, f)
            img = cv2.imread(img_path)
            if img is not None:
                pool_images.append(img)

    if not pool_images:
        raise ValueError("图像池为空或所有图像无法读取")

    # 初始化视频输出
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_out = cv2.VideoWriter(output_video, fourcc, frame_rate, (w, h))

    # 创建网格位置列表
    grid_positions = []
    for i in range(grid_size[0]):
        for j in range(grid_size[1]):
            y = i * grid_h
            x = j * grid_w
            grid_positions.append((x, y, grid_w, grid_h))
    
    # 随机打乱网格位置
    random.shuffle(grid_positions)
    
    # 限制步数不超过网格数
    total_steps = min(total_steps, len(grid_positions))
    
    for step in range(total_steps):
        # 更新进度
        if progress_callback:
            progress_callback(step, total_steps)
        
        # 获取当前网格位置
        x, y, width, height = grid_positions[step]
        
        # 随机图像 + resize (使用 INTER_AREA 算法)
        replacement = random.choice(pool_images)
        resized = cv2.resize(replacement, (width, height), interpolation=cv2.INTER_AREA)

        # 获取窗口区域
        old_region = canvas[y:y+height, x:x+width].copy()

        # alpha blending 渐变过程
        for i in range(1, blend_frames + 1):
            alpha = i / blend_frames
            blended = alpha_blend(old_region, resized, alpha)
            canvas[y:y+height, x:x+width] = blended
            video_out.write(canvas.copy())
            cv2.imshow("Animation", canvas)
            if cv2.waitKey(int(1000 / frame_rate)) & 0xFF == 27:
                break

    # 显示最终图像（延迟 1s）
    for _ in range(frame_rate):
        video_out.write(final_image)
        cv2.imshow("Animation", final_image)
        if cv2.waitKey(int(1000 / frame_rate)) & 0xFF == 27:
            break

    video_out.release()
    cv2.destroyAllWindows()
    print(f"✅ 动画完成，已保存为 {output_video}")
    
    # 最终进度更新
    if progress_callback:
        progress_callback(total_steps, total_steps)


# ✅ 示例调用（注意替换成你真实存在的路径）
if __name__ == "__main__":
    run_sliding_animation(
        original_path="face_replace.png",            # 原始图像
        final_path="face_replace.png",               # 最终图像
        pool_folder="face_images",                   # 替换图文件夹（必须存在且有图）
        output_video="output.mp4",                   # 输出视频文件名
        frame_rate=20,
        grid_size=(5, 5),                            # 将图像分成 5x5 的网格
        total_steps=25,
        blend_frames=12
    ) 