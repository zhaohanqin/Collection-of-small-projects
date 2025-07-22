import numpy as np
import math
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume


class VolumeController:
    """音量控制器类"""
    
    def __init__(self):
        """初始化音量控制器"""
        try:
            # 获取音频设备
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self.volume = cast(interface, POINTER(IAudioEndpointVolume))
            
            # 获取音量范围
            volRange = self.volume.GetVolumeRange()
            self.minVol, self.maxVol = volRange[0], volRange[1]
            
            # 初始化音量相关变量
            self.currentVolume = 0.5  # 当前音量 (0.0-1.0)
            self.smoothVolume = 0.5   # 平滑后的音量
            self.smoothingFactor = 0.3  # 平滑因子
            self.volHistory = []      # 音量历史记录
            self.historySize = 5      # 历史记录大小
            
            # UI相关变量
            self.volBar = 400         # 音量条位置
            self.volPer = 50          # 音量百分比
            
            # 获取当前系统音量作为初始值
            try:
                self.currentVolume = self.volume.GetMasterVolumeLevelScalar()
                self.smoothVolume = self.currentVolume
            except:
                self.currentVolume = 0.5
                self.smoothVolume = 0.5
                
            print("✅ 音量控制器初始化成功")
            
        except Exception as e:
            print(f"❌ 音量控制器初始化失败: {e}")
            self.volume = None
    
    def calculate_volume_from_distance(self, finger_distance, reference_length):
        """
        根据手指距离计算音量
        
        Args:
            finger_distance: 拇指和食指之间的距离
            reference_length: 手掌参考长度，用于归一化
            
        Returns:
            计算出的音量值 (0.0-1.0)
        """
        if reference_length == 0:
            reference_length = 1  # 避免除零错误
        
        # 使用手掌宽度进行归一化
        scaling_factor = 80 / reference_length  # 归一化因子，80 为理想手掌宽度
        normalized_length = finger_distance * scaling_factor
        
        # 将归一化距离映射到音量范围 (0.0-1.0)
        # 距离范围 [30, 200] 映射到音量范围 [0.0, 1.0]
        target_volume = np.interp(normalized_length, [30, 200], [0.0, 1.0])
        target_volume = max(0.0, min(1.0, target_volume))  # 确保在有效范围内
        
        return target_volume
    
    def update_volume(self, target_volume):
        """
        更新音量，包含平滑处理
        
        Args:
            target_volume: 目标音量 (0.0-1.0)
        """
        if self.volume is None:
            return False
            
        try:
            # 添加到历史记录
            self.volHistory.append(target_volume)
            if len(self.volHistory) > self.historySize:
                self.volHistory.pop(0)
            
            # 使用中值滤波减少抖动
            median_vol = np.median(self.volHistory)
            
            # 平滑过渡
            self.smoothVolume = self.smoothVolume * (1 - self.smoothingFactor) + median_vol * self.smoothingFactor
            
            # 设置系统音量（使用标量值而不是分贝值）
            self.volume.SetMasterVolumeLevelScalar(self.smoothVolume, None)
            
            # 更新UI显示值
            self.volBar = np.interp(self.smoothVolume, [0.0, 1.0], [400, 150])
            self.volPer = np.interp(self.smoothVolume, [0.0, 1.0], [0, 100])
            
            return True
            
        except Exception as e:
            print(f"设置音量失败: {e}")
            return False
    
    def get_current_volume(self):
        """
        获取当前音量
        
        Returns:
            当前音量 (0.0-1.0)
        """
        if self.volume is None:
            return 0.5
            
        try:
            return self.volume.GetMasterVolumeLevelScalar()
        except Exception as e:
            print(f"获取音量失败: {e}")
            return 0.5
    
    def get_volume_bar_position(self):
        """获取音量条位置"""
        return self.volBar
    
    def get_volume_percentage(self):
        """获取音量百分比"""
        return self.volPer
    
    def get_smooth_volume(self):
        """获取平滑后的音量"""
        return self.smoothVolume


def test_volume_controller():
    """测试音量控制器"""
    print("测试音量控制器...")
    
    controller = VolumeController()
    
    if controller.volume is None:
        print("音量控制器初始化失败，无法进行测试")
        return
    
    # 测试获取当前音量
    current_vol = controller.get_current_volume()
    print(f"当前音量: {current_vol:.2f}")
    
    # 测试设置音量
    test_volumes = [0.2, 0.5, 0.8, 0.5]  # 测试不同音量值
    
    for vol in test_volumes:
        print(f"设置音量为: {vol:.2f}")
        controller.update_volume(vol)
        print(f"音量条位置: {controller.get_volume_bar_position():.1f}")
        print(f"音量百分比: {controller.get_volume_percentage():.1f}%")
        print("-" * 30)


if __name__ == "__main__":
    test_volume_controller()
