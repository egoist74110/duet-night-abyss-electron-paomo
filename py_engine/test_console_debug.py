#!/usr/bin/env python3
"""
测试控制台调试器
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_console_debugger():
    """测试控制台调试器的基本功能"""
    print("=" * 60)
    print("测试控制台调试器")
    print("=" * 60)
    
    try:
        # 导入必要的模块
        from console_debug import create_console_debugger
        from window_capture import WindowCapture
        from image_recognition import ImageRecognition
        from human_mouse import HumanMouse
        
        print("✅ 所有模块导入成功")
        
        # 创建实例
        window_capture = WindowCapture()
        image_recognition = ImageRecognition(backend='cpu')
        human_mouse = HumanMouse()
        
        print("✅ 所有实例创建成功")
        
        # 创建控制台调试器
        debugger = create_console_debugger(
            window_capture=window_capture,
            image_recognition=image_recognition,
            human_mouse=human_mouse
        )
        
        print("✅ 控制台调试器创建成功")
        
        # 显示系统信息
        print("\n系统信息测试:")
        debugger.show_system_info()
        
        print("\n✅ 控制台调试器测试完成")
        print("注意: 要进行完整测试，需要先连接游戏窗口")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_console_debugger()