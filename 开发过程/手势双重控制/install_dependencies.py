#!/usr/bin/env python3
"""
依赖库安装脚本
用于安装手势双重控制项目所需的所有依赖库
"""

import subprocess
import sys
import importlib


def check_module(module_name):
    """检查模块是否已安装"""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


def install_package(package_name):
    """安装Python包"""
    try:
        print(f"正在安装 {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ {package_name} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {package_name} 安装失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("🔧 手势双重控制项目 - 依赖库安装器")
    print("=" * 60)
    
    # 定义所需的依赖库
    dependencies = {
        'opencv-python': 'cv2',
        'mediapipe': 'mediapipe',
        'numpy': 'numpy',
        'pycaw': 'pycaw',
        'comtypes': 'comtypes',
        'Pillow': 'PIL',  # 用于中文字体显示
        'wmi': 'wmi'  # 可选依赖
    }
    
    optional_dependencies = ['wmi']
    
    print("📋 检查已安装的依赖库...")
    
    installed = []
    missing = []
    
    for package, module in dependencies.items():
        if check_module(module):
            print(f"✅ {package} 已安装")
            installed.append(package)
        else:
            print(f"❌ {package} 未安装")
            missing.append(package)
    
    if not missing:
        print("\n🎉 所有依赖库都已安装！")
        return
    
    print(f"\n📦 需要安装 {len(missing)} 个依赖库:")
    for package in missing:
        print(f"  - {package}")
    
    # 询问用户是否要安装
    response = input("\n是否要自动安装这些依赖库？(y/n): ").lower().strip()
    
    if response not in ['y', 'yes', '是']:
        print("取消安装。请手动安装以下依赖库：")
        for package in missing:
            print(f"pip install {package}")
        return
    
    print("\n🚀 开始安装依赖库...")
    
    success_count = 0
    failed_packages = []
    
    for package in missing:
        if install_package(package):
            success_count += 1
        else:
            failed_packages.append(package)
    
    print("\n" + "=" * 60)
    print("📊 安装结果:")
    print(f"✅ 成功安装: {success_count} 个")
    
    if failed_packages:
        print(f"❌ 安装失败: {len(failed_packages)} 个")
        print("失败的包:")
        for package in failed_packages:
            print(f"  - {package}")
        
        print("\n💡 手动安装建议:")
        for package in failed_packages:
            if package in optional_dependencies:
                print(f"pip install {package}  # 可选依赖")
            else:
                print(f"pip install {package}  # 必需依赖")
    else:
        print("🎉 所有依赖库安装完成！")
    
    print("\n📖 使用说明:")
    print("1. 运行主程序: python DualHandController.py")
    print("2. 左手控制音量，右手控制亮度")
    print("3. 按 'q' 键退出程序")
    print("=" * 60)


if __name__ == "__main__":
    main()
