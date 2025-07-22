#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手势亮度控制器依赖安装脚本
"""

import subprocess
import sys
import os

def install_package(package_name):
    """安装Python包"""
    try:
        print(f"正在安装 {package_name}...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", package_name], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {package_name} 安装成功")
            return True
        else:
            print(f"❌ {package_name} 安装失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 安装 {package_name} 时出错: {e}")
        return False

def check_package(package_name):
    """检查包是否已安装"""
    try:
        __import__(package_name)
        print(f"✅ {package_name} 已安装")
        return True
    except ImportError:
        print(f"❌ {package_name} 未安装")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🌟 手势亮度控制器 - 依赖安装脚本")
    print("=" * 60)
    
    # 必需的包列表
    required_packages = [
        ("cv2", "opencv-python"),
        ("mediapipe", "mediapipe"),
        ("numpy", "numpy"),
    ]
    
    # 可选的包列表
    optional_packages = [
        ("wmi", "wmi"),
    ]
    
    print("\n📦 检查必需依赖...")
    missing_required = []
    
    for import_name, package_name in required_packages:
        if not check_package(import_name):
            missing_required.append(package_name)
    
    print("\n📦 检查可选依赖...")
    missing_optional = []
    
    for import_name, package_name in optional_packages:
        if not check_package(import_name):
            missing_optional.append(package_name)
    
    # 安装缺失的必需包
    if missing_required:
        print(f"\n🔧 需要安装 {len(missing_required)} 个必需包...")
        for package in missing_required:
            if not install_package(package):
                print(f"\n❌ 必需包 {package} 安装失败，程序可能无法正常运行")
                return False
    else:
        print("\n✅ 所有必需依赖都已安装")
    
    # 安装缺失的可选包
    if missing_optional:
        print(f"\n🔧 发现 {len(missing_optional)} 个可选包未安装...")
        for package in missing_optional:
            print(f"\n是否安装可选包 {package}？")
            print("(wmi包用于更好的亮度控制，如果不安装将使用备用方案)")
            choice = input("输入 y/n [y]: ").lower().strip()
            if choice in ['', 'y', 'yes']:
                install_package(package)
            else:
                print(f"⏭️  跳过安装 {package}")
    else:
        print("\n✅ 所有可选依赖都已安装")
    
    print("\n" + "=" * 60)
    print("🎉 依赖检查和安装完成！")
    print("=" * 60)
    
    # 测试导入
    print("\n🧪 测试程序导入...")
    try:
        import 手势控制亮度大小
        print("✅ HandBrightnessControl.py 导入成功")
        
        # 显示使用说明
        print("\n📖 使用说明:")
        print("1. 运行程序: python HandBrightnessControl.py")
        print("2. 将手放在摄像头前")
        print("3. 使用拇指和食指间距离控制亮度")
        print("4. 按 'q' 键退出程序")
        
        # 询问是否立即运行
        print("\n🚀 是否立即运行手势亮度控制器？")
        choice = input("输入 y/n [n]: ").lower().strip()
        if choice in ['y', 'yes']:
            print("\n启动手势亮度控制器...")
            controller = 手势控制亮度大小.BrightnessHandController()
            controller.run()
        
    except Exception as e:
        print(f"❌ 程序导入失败: {e}")
        print("请检查是否有其他依赖问题")
        return False
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  安装被用户中断")
    except Exception as e:
        print(f"\n❌ 安装过程出错: {e}")
        sys.exit(1)
