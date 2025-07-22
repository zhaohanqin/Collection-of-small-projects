import numpy as np
import math
import subprocess

# 尝试导入wmi，如果失败则使用备用方案
try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False
    print("警告: wmi模块未安装，将使用备用亮度控制方案")


class BrightnessController:
    """亮度控制器类"""
    
    def __init__(self):
        """初始化亮度控制器"""
        self.wmi_available = False
        self.api_available = False

        # 尝试使用WMI方式控制亮度
        if WMI_AVAILABLE:
            try:
                self.c = wmi.WMI(namespace='wmi')
                self.brightness_methods = self.c.WmiMonitorBrightnessMethods()[0]
                self.brightness_monitor = self.c.WmiMonitorBrightness()[0]
                self.wmi_available = True
                print("✅ 使用WMI方式控制亮度")
            except Exception as e:
                print(f"❌ WMI初始化失败: {e}")
                self.wmi_available = False

        # 备用方案：使用PowerShell命令
        if not self.wmi_available:
            try:
                # 测试PowerShell命令是否可用
                test_cmd = 'powershell.exe -Command "Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness"'
                result = subprocess.run(test_cmd, shell=True, capture_output=True, timeout=5)
                if result.returncode == 0:
                    self.api_available = True
                    print("✅ 使用PowerShell方式控制亮度")
                else:
                    print("❌ PowerShell亮度控制不可用")
            except Exception as e:
                print(f"❌ PowerShell测试失败: {e}")
                self.api_available = False

        if not self.wmi_available and not self.api_available:
            print("⚠️  警告: 所有亮度控制方案都不可用，程序将模拟亮度控制")
        
        # 初始化亮度相关变量
        self.currentBrightness = 50    # 当前亮度 (1-100)
        self.smoothBrightness = 50     # 平滑后的亮度
        self.smoothingFactor = 0.3     # 平滑因子
        self.brightnessHistory = []    # 亮度历史记录
        self.historySize = 5           # 历史记录大小
        
        # UI相关变量
        self.brightnessBar = 400       # 亮度条位置
        self.brightnessPer = 50        # 亮度百分比
        
        # 获取当前系统亮度作为初始值
        try:
            self.currentBrightness = self.get_brightness()
            self.smoothBrightness = self.currentBrightness
        except:
            self.currentBrightness = 50
            self.smoothBrightness = 50

        # 更新UI显示值
        import numpy as np
        self.brightnessBar = np.interp(self.smoothBrightness, [0, 100], [400, 150])
        self.brightnessPer = self.smoothBrightness
    
    def get_brightness(self):
        """获取当前屏幕亮度 (1-100)"""
        try:
            if self.wmi_available:
                return self.brightness_monitor.CurrentBrightness
            else:
                # 返回默认值
                return 50
        except Exception as e:
            print(f"获取亮度失败: {e}")
            return 50

    def set_brightness(self, brightness):
        """设置屏幕亮度 (1-100)"""
        try:
            brightness = max(1, min(100, int(brightness)))  # 确保在1-100范围内

            if self.wmi_available:
                self.brightness_methods.WmiSetBrightness(brightness, 0)
                return True
            elif self.api_available:
                # 使用PowerShell命令作为备用方案
                cmd = f'powershell.exe -Command "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{brightness})"'
                result = subprocess.run(cmd, shell=True, capture_output=True, timeout=3)
                return result.returncode == 0
            else:
                # 模拟模式 - 仅打印亮度值
                print(f"🔆 模拟设置亮度: {brightness}%")
                return True

        except Exception as e:
            print(f"设置亮度失败: {e}")
            return False
    
    def calculate_brightness_from_distance(self, finger_distance, reference_length):
        """
        根据手指距离计算亮度 - 使用与音量控制相同的逻辑

        Args:
            finger_distance: 拇指和食指之间的距离
            reference_length: 人脸宽度，用于归一化

        Returns:
            计算出的亮度值 (1-100)
        """
        if reference_length == 0:
            reference_length = 1  # 避免除零错误

        # 计算手指距离与人脸宽度的比例
        distance_ratio = finger_distance / reference_length

        # 将距离比例映射到亮度范围 (1-100)
        # 当手指距离等于人脸宽度时，亮度为100%
        # 距离比例范围 [0.0, 1.0] 映射到亮度范围 [1, 100]
        target_brightness = np.interp(distance_ratio, [0.0, 1.0], [1, 100])
        target_brightness = max(1, min(100, target_brightness))  # 确保在有效范围内

        return target_brightness
    
    def update_brightness(self, target_brightness):
        """
        更新亮度，包含平滑处理
        
        Args:
            target_brightness: 目标亮度 (1-100)
        """
        try:
            # 添加到历史记录
            self.brightnessHistory.append(target_brightness)
            if len(self.brightnessHistory) > self.historySize:
                self.brightnessHistory.pop(0)
            
            # 使用中值滤波减少抖动
            median_brightness = np.median(self.brightnessHistory)
            
            # 平滑过渡
            self.smoothBrightness = self.smoothBrightness * (1 - self.smoothingFactor) + median_brightness * self.smoothingFactor
            
            # 设置系统亮度
            self.set_brightness(self.smoothBrightness)
            
            # 更新UI显示值
            self.brightnessBar = np.interp(self.smoothBrightness, [0, 100], [400, 150])
            self.brightnessPer = self.smoothBrightness
            
            return True
            
        except Exception as e:
            print(f"更新亮度失败: {e}")
            return False
    
    def get_current_brightness(self):
        """
        获取当前亮度
        
        Returns:
            当前亮度 (1-100)
        """
        return self.get_brightness()
    
    def get_brightness_bar_position(self):
        """获取亮度条位置"""
        return self.brightnessBar
    
    def get_brightness_percentage(self):
        """获取亮度百分比"""
        return self.brightnessPer
    
    def get_smooth_brightness(self):
        """获取平滑后的亮度"""
        return self.smoothBrightness


def test_brightness_controller():
    """测试亮度控制器"""
    print("测试亮度控制器...")
    
    controller = BrightnessController()
    
    # 测试获取当前亮度
    current_brightness = controller.get_current_brightness()
    print(f"当前亮度: {current_brightness}%")
    
    # 测试设置亮度
    test_brightness_values = [20, 50, 80, 50]  # 测试不同亮度值
    
    for brightness in test_brightness_values:
        print(f"设置亮度为: {brightness}%")
        controller.update_brightness(brightness)
        print(f"亮度条位置: {controller.get_brightness_bar_position():.1f}")
        print(f"亮度百分比: {controller.get_brightness_percentage():.1f}%")
        print("-" * 30)


if __name__ == "__main__":
    test_brightness_controller()
