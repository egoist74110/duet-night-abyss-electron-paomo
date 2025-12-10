#!/usr/bin/env python3
"""
坐标调试工具
用于测试和调试图像识别和鼠标点击的坐标转换问题
"""

import sys
import os
import json
import time

# 添加当前脚本目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from window_capture import WindowCapture
from image_recognition import ImageRecognition
from human_mouse import HumanMouse

def test_coordinate_conversion():
    """测试坐标转换功能"""
    print("=== 坐标转换测试 ===")
    
    # 初始化模块
    window_capture = WindowCapture()
    human_mouse = HumanMouse()
    
    print(f"平台: {window_capture.platform}")
    print(f"屏幕尺寸: {human_mouse.screen_width}x{human_mouse.screen_height}")
    
    # 测试几个关键坐标点
    test_points = [
        (100, 100),    # 左上角
        (500, 300),    # 中间偏左
        (1000, 600),   # 中间偏右
        (1800, 1000),  # 右下角
    ]
    
    for rel_x, rel_y in test_points:
        print(f"\n--- 测试点 ({rel_x}, {rel_y}) ---")
        
        # 执行坐标转换
        screen_x, screen_y = window_capture.convert_relative_to_screen_coords(rel_x, rel_y)
        print(f"转换结果: ({rel_x}, {rel_y}) -> ({screen_x}, {screen_y})")
        
        # 验证坐标是否有效
        is_valid = human_mouse.is_position_valid(screen_x, screen_y)
        print(f"坐标有效性: {is_valid}")
        
        if is_valid:
            print(f"移动鼠标到转换后的位置...")
            human_mouse.move_to(screen_x, screen_y, duration=1.0)
            time.sleep(2)  # 等待2秒观察
            
            # 获取实际鼠标位置
            actual_x, actual_y = human_mouse.get_mouse_position()
            print(f"实际鼠标位置: ({actual_x}, {actual_y})")
            
            # 计算误差
            error_x = abs(actual_x - screen_x)
            error_y = abs(actual_y - screen_y)
            print(f"位置误差: X={error_x}, Y={error_y}")

def test_image_recognition_with_debug():
    """测试图像识别并调试坐标"""
    print("\n=== 图像识别坐标调试 ===")
    
    # 初始化模块
    window_capture = WindowCapture()
    image_recognition = ImageRecognition(backend='cpu')
    human_mouse = HumanMouse()
    
    # 测试图像路径
    test_images = [
        ("static/dungeon/开始挑战.png", "开始挑战按钮"),
        ("static/dungeon/火.png", "火副本"),
        ("static/dungeon/水.png", "水副本"),
    ]
    
    for image_path, image_name in test_images:
        print(f"\n--- 测试 {image_name} ---")
        
        # 检查图像文件是否存在
        full_path = os.path.join(os.path.dirname(script_dir), image_path)
        if not os.path.exists(full_path):
            print(f"图像文件不存在: {full_path}")
            continue
        
        # 加载模板
        template_name = f"debug_{image_name}"
        success = image_recognition.load_template(template_name, full_path)
        if not success:
            print(f"无法加载模板: {image_name}")
            continue
        
        # 获取截图
        screenshot = window_capture.capture()
        if screenshot is None:
            print("无法获取截图")
            continue
        
        print(f"截图尺寸: {screenshot.shape}")
        
        # 执行识别
        found, position, confidence = image_recognition.match_template(
            screenshot, template_name, 0.4  # 降低阈值以便测试
        )
        
        print(f"识别结果: found={found}, confidence={confidence:.3f}")
        
        if found:
            print(f"原始匹配位置: {position}")
            
            # 执行坐标转换
            screen_x, screen_y = window_capture.convert_relative_to_screen_coords(
                position[0], position[1]
            )
            print(f"转换后屏幕坐标: ({screen_x}, {screen_y})")
            
            # 移动鼠标到该位置（不点击）
            print(f"移动鼠标到 {image_name} 位置...")
            human_mouse.move_to(screen_x, screen_y, duration=1.5)
            
            # 等待用户观察
            print(f"鼠标已移动到 {image_name} 位置，请观察是否准确")
            time.sleep(3)
            
            # 询问用户是否准确
            user_input = input(f"鼠标位置是否准确指向 {image_name}? (y/n): ").strip().lower()
            if user_input == 'y':
                print(f"✅ {image_name} 坐标转换准确")
            else:
                print(f"❌ {image_name} 坐标转换不准确")
                
                # 获取当前鼠标位置作为参考
                actual_x, actual_y = human_mouse.get_mouse_position()
                print(f"当前鼠标位置: ({actual_x}, {actual_y})")
                print(f"预期位置: ({screen_x}, {screen_y})")
                print(f"位置差异: X={actual_x - screen_x}, Y={actual_y - screen_y}")
        else:
            print(f"未找到 {image_name}")

def interactive_coordinate_test():
    """交互式坐标测试"""
    print("\n=== 交互式坐标测试 ===")
    print("输入相对坐标，程序会移动鼠标到对应的屏幕位置")
    print("输入格式: x,y (例如: 500,300)")
    print("输入 'quit' 退出")
    
    window_capture = WindowCapture()
    human_mouse = HumanMouse()
    
    while True:
        try:
            user_input = input("\n请输入坐标 (x,y): ").strip()
            
            if user_input.lower() == 'quit':
                break
            
            # 解析坐标
            x_str, y_str = user_input.split(',')
            rel_x = int(x_str.strip())
            rel_y = int(y_str.strip())
            
            print(f"输入的相对坐标: ({rel_x}, {rel_y})")
            
            # 转换坐标
            screen_x, screen_y = window_capture.convert_relative_to_screen_coords(rel_x, rel_y)
            print(f"转换后屏幕坐标: ({screen_x}, {screen_y})")
            
            # 移动鼠标
            print("移动鼠标...")
            human_mouse.move_to(screen_x, screen_y, duration=1.0)
            
            # 验证位置
            actual_x, actual_y = human_mouse.get_mouse_position()
            print(f"实际鼠标位置: ({actual_x}, {actual_y})")
            
            error_x = abs(actual_x - screen_x)
            error_y = abs(actual_y - screen_y)
            print(f"位置误差: X={error_x}, Y={error_y}")
            
        except ValueError:
            print("输入格式错误，请使用 x,y 格式")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"错误: {e}")

def main():
    """主函数"""
    print("坐标调试工具")
    print("请选择测试模式:")
    print("1. 坐标转换测试")
    print("2. 图像识别坐标调试")
    print("3. 交互式坐标测试")
    print("4. 全部测试")
    
    try:
        choice = input("请选择 (1-4): ").strip()
        
        if choice == '1':
            test_coordinate_conversion()
        elif choice == '2':
            test_image_recognition_with_debug()
        elif choice == '3':
            interactive_coordinate_test()
        elif choice == '4':
            test_coordinate_conversion()
            test_image_recognition_with_debug()
            interactive_coordinate_test()
        else:
            print("无效选择")
            
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()