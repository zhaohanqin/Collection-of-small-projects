#!/usr/bin/env python3
"""
测试改进的算盘模拟器功能
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# 导入我们的算盘模块
from 算盘模拟器 import AbacusWidget, AbacusApp

def test_abacus_basic_functions(app):
    """测试算盘基本功能"""
    print("=== 测试算盘基本功能 ===")

    # 创建算盘部件
    abacus = AbacusWidget()
    
    # 测试1: 初始状态
    print(f"初始状态数值: {abacus.get_total_value()}")
    assert abacus.get_total_value() == 0, "初始状态应该为0"
    
    # 测试2: 设置简单数值
    test_values = [0, 1, 5, 9, 12, 56, 123, 1234, 9999]
    
    for value in test_values:
        success = abacus.set_value(value)
        result = abacus.get_total_value()
        print(f"设置 {value}, 结果: {result}, 成功: {success}")
        assert result == value, f"设置 {value} 失败，实际得到 {result}"
    
    # 测试3: 清空功能
    abacus.clear_abacus()
    print(f"清空后数值: {abacus.get_total_value()}")
    assert abacus.get_total_value() == 0, "清空后应该为0"
    
    # 测试4: 大数值
    large_value = 1234567890123
    abacus.set_value(large_value)
    result = abacus.get_total_value()
    print(f"大数值测试 - 设置: {large_value}, 结果: {result}")
    
    # 测试5: 各档位数值
    print("\n=== 测试各档位数值 ===")
    for i in range(10):
        abacus.set_value(i)
        print(f"数字 {i}:")
        for rod_idx in range(min(3, abacus.num_rods)):  # 只显示前3档
            rod_value = abacus.get_rod_value(rod_idx)
            state = abacus.abacus_state[rod_idx]
            print(f"  档{rod_idx}: 值={rod_value}, 上珠={state['upper_active']}, 下珠={state['lower_active']}")
    
    print("✓ 所有基本功能测试通过！")

def test_abacus_edge_cases(app):
    """测试边界情况"""
    print("\n=== 测试边界情况 ===")

    abacus = AbacusWidget()
    
    # 测试负数
    abacus.set_value(-100)
    print(f"负数测试: {abacus.get_total_value()}")
    assert abacus.get_total_value() == 0, "负数应该被设置为0"
    
    # 测试超大数值
    max_value = 10 ** abacus.num_rods - 1
    over_max = max_value + 1000
    abacus.set_value(over_max)
    result = abacus.get_total_value()
    print(f"超大数值测试 - 设置: {over_max}, 结果: {result}, 最大值: {max_value}")
    assert result <= max_value, "超大数值应该被限制在最大值内"
    
    # 测试字符串输入
    try:
        abacus.set_value("123")
        print(f"字符串输入测试: {abacus.get_total_value()}")
    except:
        print("字符串输入处理正常")
    
    print("✓ 边界情况测试通过！")

def test_rod_values(app):
    """测试单档数值计算"""
    print("\n=== 测试单档数值计算 ===")

    abacus = AbacusWidget()
    
    # 测试每个可能的单档数值 (0-9)
    for target_value in range(10):
        abacus.clear_abacus()
        
        # 手动设置最右边档位的珠子状态
        rod_idx = abacus.num_rods - 1  # 最右边的档（个位）
        
        if target_value >= 5:
            abacus.abacus_state[rod_idx]['upper_active'] = 1
            abacus.abacus_state[rod_idx]['lower_active'] = target_value - 5
        else:
            abacus.abacus_state[rod_idx]['upper_active'] = 0
            abacus.abacus_state[rod_idx]['lower_active'] = target_value
        
        calculated_value = abacus.get_rod_value(rod_idx)
        total_value = abacus.get_total_value()
        
        print(f"目标值: {target_value}, 档位值: {calculated_value}, 总值: {total_value}")
        assert calculated_value == target_value, f"档位值计算错误: 期望{target_value}, 得到{calculated_value}"
        assert total_value == target_value, f"总值计算错误: 期望{target_value}, 得到{total_value}"
    
    print("✓ 单档数值计算测试通过！")

def run_interactive_test():
    """运行交互式测试"""
    print("\n=== 启动交互式测试 ===")
    print("正在启动算盘应用程序...")
    print("请手动测试以下功能:")
    print("1. 点击珠子移动")
    print("2. 输入数字设置")
    print("3. 执行计算")
    print("4. 清空算盘")
    print("5. 悬停效果")
    
    app = QApplication(sys.argv)
    main_window = AbacusApp()
    main_window.show()
    
    # 设置一个定时器来自动关闭（可选）
    # timer = QTimer()
    # timer.timeout.connect(app.quit)
    # timer.start(30000)  # 30秒后自动关闭
    
    return app.exec()

if __name__ == '__main__':
    print("开始测试改进的算盘模拟器...")

    # 创建QApplication实例
    app = QApplication(sys.argv)

    # 运行自动化测试
    try:
        test_abacus_basic_functions(app)
        test_abacus_edge_cases(app)
        test_rod_values(app)
        print("\n🎉 所有自动化测试通过！")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 询问是否运行交互式测试
    print("\n是否要运行交互式测试？(y/n): ", end="")
    try:
        choice = input().lower().strip()
        if choice in ['y', 'yes', '是', '']:
            run_interactive_test()
    except KeyboardInterrupt:
        print("\n测试结束。")
    except:
        print("\n跳过交互式测试。")
