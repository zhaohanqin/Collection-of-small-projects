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
        total_steps=None,  # 如果为None，则使用所有网格
        blend_frames=10,
        progress_callback=None,  # 添加进度回调函数
        target_resolution=None   # 目标分辨率，如果为None则自动根据图像比例确定
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

    # 获取原始图像尺寸
    original_h, original_w = original.shape[:2]
    final_h, final_w = final_image.shape[:2]
    
    print(f"原始图像尺寸: {original_w}x{original_h}")
    print(f"最终图像尺寸: {final_w}x{final_h}")

    # 确定目标分辨率
    if target_resolution:
        target_w, target_h = target_resolution
    else:
        # 根据图像比例确定目标分辨率
        if original_h > original_w:  # 长大于宽（竖向图像）
            target_h, target_w = 1080, 720
            print("检测到竖向图像，设置分辨率为 720x1080")
        else:  # 宽大于长（横向图像）
            target_h, target_w = 720, 1080
            print("检测到横向图像，设置分辨率为 1080x720")
    
    # 使用 INTER_AREA 算法调整两个图像到相同尺寸
    print(f"调整两个图像到相同尺寸: {target_w}x{target_h}")
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
    
    # 如果未指定步数，则使用所有网格
    if total_steps is None:
        total_steps = len(grid_positions)
    else:
        # 限制步数不超过网格数
        total_steps = min(total_steps, len(grid_positions))
    
    # 记录已经处理过的网格
    processed_grids = set()
    
    for step in range(total_steps):
        # 更新进度
        if progress_callback:
            progress_callback(step, total_steps)
        
        # 获取当前网格位置
        x, y, width, height = grid_positions[step]
        
        # 记录当前网格已处理
        processed_grids.add((x, y))
        
        # 第一阶段：随机图像替换
        # 随机图像 + resize (使用 INTER_AREA 算法)
        replacement = random.choice(pool_images)
        resized = cv2.resize(replacement, (width, height), interpolation=cv2.INTER_AREA)

        # 获取窗口区域
        old_region = canvas[y:y+height, x:x+width].copy()

        # alpha blending 渐变过程 (随机图像)
        for i in range(1, blend_frames + 1):
            alpha = i / blend_frames
            blended = alpha_blend(old_region, resized, alpha)
            canvas[y:y+height, x:x+width] = blended
            video_out.write(canvas.copy())
            cv2.imshow("Animation", canvas)
            if cv2.waitKey(int(1000 / frame_rate)) & 0xFF == 27:
                break
        
        # 第二阶段：最终图像替换
        # 获取最终图像对应的区域
        final_region = final_image[y:y+height, x:x+width].copy()
        
        # 获取当前画布上的区域（已经是随机图像了）
        current_region = canvas[y:y+height, x:x+width].copy()
        
        # alpha blending 渐变过程 (最终图像)
        for i in range(1, blend_frames + 1):
            alpha = i / blend_frames
            blended = alpha_blend(current_region, final_region, alpha)
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


# ✅ 示例调用
if __name__ == "__main__":
    run_sliding_animation(
        original_path="face_replace.png",            # 原始图像
        final_path="1.png",                          # 最终图像
        pool_folder="face_images",                   # 替换图文件夹（必须存在且有图）
        output_video="transition_output.mp4",        # 输出视频文件名
        frame_rate=20,
        grid_size=(5, 5),                            # 将图像分成 5x5 的网格
        total_steps=25,                              # 如果为None则使用所有网格
        blend_frames=12,                             # 每次过渡的帧数
        target_resolution=None                       # 如果为None则自动根据图像比例确定
    ) 