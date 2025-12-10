#!/usr/bin/env python3
"""
实时坐标调试工具
帮助诊断 macOS HiDPI 环境下的坐标转换问题
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pyautogui
import cv2
import numpy as np
import time
from window_capture import WindowCapture
from image_recognition import ImageRecognition
from human_mouse import HumanMouse

def analyze_coordinate_problem():
    """分析坐标问题的根本原因"""
    print("🔍 实时坐标问题诊断工具")
    print("=" * 60)
    
    # 获取基础信息
    logical_width, logical_height = pyautogui.size()
    print(f"📱 逻辑屏幕尺寸: {logical_width}x{logical_height}")
    
    # 获取实际截图
    screenshot = pyautogui.screenshot()
    actual_width = screenshot.width
    actual_height = screenshot.height
    print(f"📸 实际截图尺寸: {actual_width}x{actual_height}")
    
    # 计算缩放比例
    scale_x = actual_width / logical_width
    scale_y = actual_height / logical_height
    print(f"📏 缩放比例: X={scale_x:.4f}, Y={scale_y:.4f}")
    
    # 检查是否为 HiDPI 环境
    is_hidpi = scale_x > 1.5 or scale_y > 1.5
    print(f"🖥️ HiDPI 环境: {'是' if is_hidpi else '否'}")
    
    print("\n" + "="*60)
    print("🎯 开始实时坐标测试")
    print("请在游戏中找到火副本图标，然后按回车键开始测试...")
    input()
    
    # 创建图像识别实例
    image_recognition = ImageRecognition()
    window_capture = WindowCapture()
    
    # 加载火副本模板
    template_path = "static/dungeon/火.png"
    if not os.path.exists(template_path):
        template_path = "../static/dungeon/火.png"
    
    if not os.path.exists(template_path):
        print(f"❌ 找不到模板文件: {template_path}")
        return
    
    success = image_recognition.load_template('fire', template_path)
    if not success:
        print(f"❌ 加载模板失败: {template_path}")
        return
    
    print(f"✅ 模板加载成功: {template_path}")
    
    # 执行识别测试
    print("\n🔍 执行图像识别...")
    screenshot_cv = pyautogui.screenshot()
    screenshot_array = np.array(screenshot_cv)
    screenshot_bgr = cv2.cvtColor(screenshot_array, cv2.COLOR_RGB2BGR)
    
    found, position, confidence = image_recognition.match_template(screenshot_bgr, 'fire', 0.6)
    
    if not found:
        print(f"❌ 未找到火副本图标，置信度: {confidence:.3f}")
        print("💡 建议：")
        print("  1. 确保游戏窗口中有火副本图标")
        print("  2. 尝试降低匹配阈值")
        print("  3. 检查模板图片是否与游戏中的图标一致")
        return
    
    print(f"✅ 找到火副本图标！")
    print(f"   📍 识别位置: ({position[0]}, {position[1]})")
    print(f"   🎯 置信度: {confidence:.3f}")
    
    # 分析坐标转换
    print(f"\n📐 坐标转换分析:")
    
    # 方法1：直接使用识别坐标
    direct_x, direct_y = position[0], position[1]
    print(f"   方法1 (直接使用): ({direct_x}, {direct_y})")
    
    # 方法2：按缩放比例转换
    if is_hidpi:
        scaled_x = position[0] / scale_x
        scaled_y = position[1] / scale_y
        print(f"   方法2 (缩放转换): ({scaled_x:.1f}, {scaled_y:.1f})")
    else:
        scaled_x, scaled_y = direct_x, direct_y
        print(f"   方法2 (无需缩放): ({scaled_x}, {scaled_y})")
    
    # 方法3：使用窗口捕获的转换方法
    converted_x, converted_y = window_capture.convert_relative_to_screen_coords(position[0], position[1])
    print(f"   方法3 (窗口转换): ({converted_x}, {converted_y})")
    
    # 检查哪些坐标在屏幕范围内
    print(f"\n✅ 坐标有效性检查:")
    
    coords_to_test = [
        ("直接使用", direct_x, direct_y),
        ("缩放转换", scaled_x, scaled_y),
        ("窗口转换", converted_x, converted_y)
    ]
    
    valid_coords = []
    for name, x, y in coords_to_test:
        is_valid = 0 <= x <= logical_width and 0 <= y <= logical_height
        status = "✅ 有效" if is_valid else "❌ 超出范围"
        print(f"   {name}: ({x:.0f}, {y:.0f}) - {status}")
        if is_valid:
            valid_coords.append((name, x, y))
    
    if not valid_coords:
        print("\n❌ 所有转换方法都产生了无效坐标！")
        print("💡 可能的原因：")
        print("  1. 游戏窗口不在主屏幕上")
        print("  2. 游戏窗口被缩放或移动")
        print("  3. 坐标转换算法需要调整")
        return
    
    # 测试有效坐标的点击效果
    print(f"\n🖱️ 测试鼠标移动效果:")
    mouse = HumanMouse()
    
    for name, x, y in valid_coords:
        print(f"\n测试 {name} 坐标: ({x:.0f}, {y:.0f})")
        
        # 获取当前鼠标位置
        before_x, before_y = pyautogui.position()
        print(f"   移动前位置: ({before_x}, {before_y})")
        
        # 移动鼠标
        try:
            pyautogui.moveTo(x, y, duration=0.5)
            time.sleep(0.2)
            
            # 获取移动后位置
            after_x, after_y = pyautogui.position()
            print(f"   移动后位置: ({after_x}, {after_y})")
            
            # 计算误差
            error_x = abs(after_x - x)
            error_y = abs(after_y - y)
            total_error = (error_x ** 2 + error_y ** 2) ** 0.5
            
            print(f"   移动误差: X={error_x:.0f}, Y={error_y:.0f}, 总误差={total_error:.1f}像素")
            
            # 询问用户是否位置正确
            response = input(f"   鼠标是否移动到了火副本图标上？(y/n): ")
            if response.lower() == 'y':
                print(f"🎉 找到正确的坐标转换方法: {name}")
                print(f"   正确坐标: ({x:.0f}, {y:.0f})")
                
                # 保存结果
                result = {
                    'method': name,
                    'original_position': position,
                    'converted_position': [int(x), int(y)],
                    'scale_factor': [scale_x, scale_y],
                    'is_hidpi': is_hidpi,
                    'confidence': confidence
                }
                
                import json
                with open('coordinate_fix_result.json', 'w') as f:
                    json.dump(result, f, indent=2)
                
                print(f"✅ 结果已保存到 coordinate_fix_result.json")
                return result
            
        except Exception as e:
            print(f"   ❌ 移动失败: {e}")
    
    print("\n❌ 所有方法都无法正确定位到火副本图标")
    print("💡 建议进一步调试：")
    print("  1. 检查游戏窗口是否完全可见")
    print("  2. 尝试调整游戏窗口大小和位置")
    print("  3. 确认模板图片与游戏中的图标完全一致")

if __name__ == "__main__":
    try:
        analyze_coordinate_problem()
    except KeyboardInterrupt:
        print("\n\n👋 测试已取消")
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()