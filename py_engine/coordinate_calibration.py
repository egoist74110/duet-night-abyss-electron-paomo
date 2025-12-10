#!/usr/bin/env python3
"""
坐标校准工具
通过用户交互来确定正确的坐标转换参数
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pyautogui
import cv2
import numpy as np
import json
from datetime import datetime
from image_recognition import ImageRecognition

class CoordinateCalibrator:
    """坐标校准器"""
    
    def __init__(self):
        self.image_recognition = ImageRecognition()
        self.calibration_data = {}
        
    def calibrate_fire_dungeon(self):
        """校准火副本的坐标转换"""
        print("🎯 火副本坐标校准工具")
        print("=" * 50)
        
        # 加载火副本模板
        template_path = "static/dungeon/火.png"
        if not os.path.exists(template_path):
            template_path = "../static/dungeon/火.png"
        
        if not os.path.exists(template_path):
            print(f"❌ 找不到模板文件: {template_path}")
            return None
        
        success = self.image_recognition.load_template('fire', template_path)
        if not success:
            print(f"❌ 加载模板失败")
            return None
        
        print("✅ 模板加载成功")
        print("\n📋 校准步骤:")
        print("1. 确保游戏窗口中有火副本图标")
        print("2. 我会识别图标位置并移动鼠标")
        print("3. 你告诉我鼠标位置是否正确")
        print("4. 如果不正确，我会尝试不同的转换方法")
        
        input("\n按回车键开始校准...")
        
        # 执行图像识别
        screenshot = pyautogui.screenshot()
        screenshot_array = np.array(screenshot)
        screenshot_bgr = cv2.cvtColor(screenshot_array, cv2.COLOR_RGB2BGR)
        
        found, position, confidence = self.image_recognition.match_template(screenshot_bgr, 'fire', 0.6)
        
        if not found:
            print(f"❌ 未找到火副本图标，置信度: {confidence:.3f}")
            return None
        
        print(f"✅ 找到火副本图标！")
        print(f"   📍 识别位置: ({position[0]}, {position[1]})")
        print(f"   🎯 置信度: {confidence:.3f}")
        
        # 获取屏幕信息
        logical_width, logical_height = pyautogui.size()
        actual_width = screenshot.width
        actual_height = screenshot.height
        
        print(f"\n📱 屏幕信息:")
        print(f"   逻辑尺寸: {logical_width}x{logical_height}")
        print(f"   实际尺寸: {actual_width}x{actual_height}")
        
        # 尝试不同的转换方法
        methods = []
        
        # 方法1：直接使用识别坐标
        methods.append(("直接使用", position[0], position[1]))
        
        # 方法2：HiDPI 缩放转换
        if actual_width > logical_width * 1.5:
            scale_x = actual_width / logical_width
            scale_y = actual_height / logical_height
            scaled_x = position[0] / scale_x
            scaled_y = position[1] / scale_y
            methods.append(("HiDPI缩放", scaled_x, scaled_y))
        
        # 方法3：常见偏移修正
        # 假设窗口有标题栏和边框
        offset_methods = [
            ("偏移修正1", position[0] - 100, position[1] - 100),
            ("偏移修正2", position[0] - 200, position[1] - 150),
            ("偏移修正3", position[0] / 2, position[1] / 2),
            ("偏移修正4", position[0] * 0.6, position[1] * 0.6),
        ]
        
        for name, x, y in offset_methods:
            if 0 <= x <= logical_width and 0 <= y <= logical_height:
                methods.append((name, x, y))
        
        print(f"\n🧪 开始测试 {len(methods)} 种转换方法:")
        
        for i, (name, x, y) in enumerate(methods, 1):
            print(f"\n--- 方法 {i}: {name} ---")
            print(f"目标坐标: ({x:.0f}, {y:.0f})")
            
            # 检查坐标是否在屏幕范围内
            if not (0 <= x <= logical_width and 0 <= y <= logical_height):
                print("❌ 坐标超出屏幕范围，跳过")
                continue
            
            # 移动鼠标到目标位置
            try:
                before_x, before_y = pyautogui.position()
                print(f"移动前位置: ({before_x}, {before_y})")
                
                pyautogui.moveTo(x, y, duration=0.5)
                import time
                time.sleep(0.3)
                
                after_x, after_y = pyautogui.position()
                print(f"移动后位置: ({after_x}, {after_y})")
                
                # 计算移动精度
                error_x = abs(after_x - x)
                error_y = abs(after_y - y)
                total_error = (error_x ** 2 + error_y ** 2) ** 0.5
                print(f"移动精度: 误差 {total_error:.1f} 像素")
                
                # 询问用户
                response = input("鼠标是否准确指向火副本图标？(y/n/s=跳过): ")
                
                if response.lower() == 'y':
                    print(f"🎉 找到正确的转换方法: {name}")
                    
                    # 保存校准结果
                    calibration_result = {
                        'method': name,
                        'original_position': position,
                        'correct_position': [int(x), int(y)],
                        'screen_info': {
                            'logical_size': [logical_width, logical_height],
                            'actual_size': [actual_width, actual_height]
                        },
                        'confidence': confidence,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # 计算转换参数
                    if name == "HiDPI缩放":
                        calibration_result['scale_factor'] = [actual_width / logical_width, actual_height / logical_height]
                        calibration_result['conversion_type'] = 'scale'
                    elif "偏移修正" in name:
                        calibration_result['offset'] = [int(x - position[0]), int(y - position[1])]
                        calibration_result['conversion_type'] = 'offset'
                    else:
                        calibration_result['conversion_type'] = 'direct'
                    
                    # 保存到文件
                    filename = f"coordinate_calibration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(calibration_result, f, indent=2, ensure_ascii=False)
                    
                    print(f"✅ 校准结果已保存到: {filename}")
                    
                    # 生成修复代码
                    self.generate_fix_code(calibration_result)
                    
                    return calibration_result
                
                elif response.lower() == 's':
                    print("⏭️ 跳过此方法")
                    continue
                else:
                    print("❌ 此方法不正确，继续测试下一个")
                    
            except Exception as e:
                print(f"❌ 测试失败: {e}")
                continue
        
        print("\n😞 所有方法都无法正确定位火副本图标")
        print("💡 建议:")
        print("  1. 检查游戏窗口是否完全可见")
        print("  2. 确认火副本图标在屏幕上")
        print("  3. 尝试调整游戏窗口大小和位置")
        print("  4. 检查模板图片是否与游戏中的图标一致")
        
        return None
    
    def generate_fix_code(self, calibration_result):
        """根据校准结果生成修复代码"""
        print(f"\n🔧 生成修复代码:")
        
        conversion_type = calibration_result['conversion_type']
        
        if conversion_type == 'scale':
            scale_factor = calibration_result['scale_factor']
            print(f"# HiDPI 缩放修复")
            print(f"scale_x = {scale_factor[0]:.4f}")
            print(f"scale_y = {scale_factor[1]:.4f}")
            print(f"screen_x = rel_x / scale_x")
            print(f"screen_y = rel_y / scale_y")
            
        elif conversion_type == 'offset':
            offset = calibration_result['offset']
            print(f"# 偏移修正")
            print(f"offset_x = {offset[0]}")
            print(f"offset_y = {offset[1]}")
            print(f"screen_x = rel_x + offset_x")
            print(f"screen_y = rel_y + offset_y")
            
        else:
            print(f"# 直接使用坐标")
            print(f"screen_x = rel_x")
            print(f"screen_y = rel_y")

def main():
    """主函数"""
    calibrator = CoordinateCalibrator()
    result = calibrator.calibrate_fire_dungeon()
    
    if result:
        print(f"\n🎉 校准成功！")
        print(f"转换方法: {result['method']}")
        print(f"原始位置: {result['original_position']}")
        print(f"正确位置: {result['correct_position']}")
    else:
        print(f"\n😞 校准失败，请检查游戏状态后重试")

if __name__ == "__main__":
    main()