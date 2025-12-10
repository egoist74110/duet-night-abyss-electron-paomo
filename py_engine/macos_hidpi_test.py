#!/usr/bin/env python3
"""
macOS HiDPI 坐标测试工具
专门用于测试和调试 macOS HiDPI 环境下的鼠标坐标问题
"""
import pyautogui
import cv2
import numpy as np
import time
import subprocess
import json
from datetime import datetime


class MacOSHiDPITester:
    """macOS HiDPI 坐标测试器"""
    
    def __init__(self):
        """初始化测试器"""
        self.screen_width, self.screen_height = pyautogui.size()
        print(f"[INFO] macOS HiDPI 测试器初始化")
        print(f"[INFO] 逻辑屏幕尺寸: {self.screen_width}x{self.screen_height}")
        
        # 检测显示器信息
        self.display_info = self._get_display_info()
        self.test_results = []
    
    def _get_display_info(self):
        """获取显示器详细信息"""
        try:
            print("[INFO] 获取显示器信息...")
            result = subprocess.run(['system_profiler', 'SPDisplaysDataType'], 
                                  capture_output=True, text=True, timeout=10)
            
            display_info = {
                'is_retina': False,
                'resolution': 'unknown',
                'scaling': 'unknown'
            }
            
            if result.returncode == 0:
                output = result.stdout
                
                # 检查是否为 Retina 显示器
                if 'Retina' in output or 'HiDPI' in output:
                    display_info['is_retina'] = True
                    print("[INFO] 检测到 Retina 显示器")
                else:
                    print("[INFO] 检测到标准显示器")
                
                # 尝试提取分辨率信息
                lines = output.split('\n')
                for line in lines:
                    if 'Resolution:' in line:
                        display_info['resolution'] = line.strip()
                        print(f"[INFO] 显示器分辨率: {line.strip()}")
                        break
            
            return display_info
            
        except Exception as e:
            print(f"[WARN] 获取显示器信息失败: {e}")
            return {'is_retina': False, 'resolution': 'unknown', 'scaling': 'unknown'}
    
    def test_screenshot_resolution(self):
        """测试截图分辨率"""
        print("\n" + "="*60)
        print("📸 测试截图分辨率")
        print("="*60)
        
        try:
            # 使用 pyautogui 截图
            screenshot = pyautogui.screenshot()
            screenshot_array = np.array(screenshot)
            
            actual_width = screenshot_array.shape[1]
            actual_height = screenshot_array.shape[0]
            
            print(f"[INFO] pyautogui 逻辑屏幕尺寸: {self.screen_width}x{self.screen_height}")
            print(f"[INFO] 截图实际尺寸: {actual_width}x{actual_height}")
            
            # 计算缩放比例
            scale_x = actual_width / self.screen_width
            scale_y = actual_height / self.screen_height
            
            print(f"[INFO] 缩放比例: X={scale_x:.4f}, Y={scale_y:.4f}")
            
            # 判断是否为 HiDPI 环境
            is_hidpi = scale_x > 1.5 or scale_y > 1.5
            print(f"[INFO] HiDPI 环境: {'是' if is_hidpi else '否'}")
            
            test_result = {
                'test_name': 'screenshot_resolution',
                'timestamp': datetime.now().isoformat(),
                'logical_size': (self.screen_width, self.screen_height),
                'actual_size': (actual_width, actual_height),
                'scale_factor': (scale_x, scale_y),
                'is_hidpi': is_hidpi,
                'display_info': self.display_info
            }
            
            self.test_results.append(test_result)
            return test_result
            
        except Exception as e:
            print(f"[ERROR] 截图分辨率测试失败: {e}")
            return None
    
    def test_mouse_coordinate_accuracy(self, test_points=None):
        """测试鼠标坐标精度"""
        print("\n" + "="*60)
        print("🖱️ 测试鼠标坐标精度")
        print("="*60)
        
        if test_points is None:
            # 默认测试点：屏幕的几个关键位置
            test_points = [
                (100, 100),  # 左上角
                (self.screen_width // 2, self.screen_height // 2),  # 中心
                (self.screen_width - 100, self.screen_height - 100),  # 右下角
                (self.screen_width // 4, self.screen_height // 4),  # 左上象限
                (3 * self.screen_width // 4, 3 * self.screen_height // 4),  # 右下象限
            ]
        
        accuracy_results = []
        
        for i, (target_x, target_y) in enumerate(test_points):
            print(f"\n[TEST {i+1}] 测试点: ({target_x}, {target_y})")
            
            try:
                # 移动到目标位置
                print(f"  移动到目标位置...")
                pyautogui.moveTo(target_x, target_y, duration=0.3)
                time.sleep(0.1)
                
                # 获取实际位置
                actual_x, actual_y = pyautogui.position()
                print(f"  实际位置: ({actual_x}, {actual_y})")
                
                # 计算误差
                error_x = abs(actual_x - target_x)
                error_y = abs(actual_y - target_y)
                total_error = (error_x ** 2 + error_y ** 2) ** 0.5
                
                print(f"  误差: X={error_x}, Y={error_y}, 总误差={total_error:.2f}像素")
                
                # 评估精度
                if total_error <= 1:
                    accuracy = "完美"
                elif total_error <= 3:
                    accuracy = "优秀"
                elif total_error <= 5:
                    accuracy = "良好"
                elif total_error <= 10:
                    accuracy = "一般"
                else:
                    accuracy = "较差"
                
                print(f"  精度评估: {accuracy}")
                
                result = {
                    'target': (target_x, target_y),
                    'actual': (actual_x, actual_y),
                    'error': (error_x, error_y),
                    'total_error': total_error,
                    'accuracy': accuracy
                }
                
                accuracy_results.append(result)
                
            except Exception as e:
                print(f"  [ERROR] 测试点 {i+1} 失败: {e}")
                accuracy_results.append({
                    'target': (target_x, target_y),
                    'error': str(e)
                })
        
        # 计算总体精度
        valid_results = [r for r in accuracy_results if 'total_error' in r]
        if valid_results:
            avg_error = sum(r['total_error'] for r in valid_results) / len(valid_results)
            max_error = max(r['total_error'] for r in valid_results)
            print(f"\n[总结] 平均误差: {avg_error:.2f}像素, 最大误差: {max_error:.2f}像素")
        
        test_result = {
            'test_name': 'mouse_coordinate_accuracy',
            'timestamp': datetime.now().isoformat(),
            'test_points': accuracy_results,
            'summary': {
                'avg_error': avg_error if valid_results else None,
                'max_error': max_error if valid_results else None,
                'total_tests': len(test_points),
                'successful_tests': len(valid_results)
            }
        }
        
        self.test_results.append(test_result)
        return test_result
    
    def test_coordinate_conversion(self, screenshot_coords):
        """测试坐标转换算法"""
        print("\n" + "="*60)
        print("🔄 测试坐标转换算法")
        print("="*60)
        
        conversion_results = []
        
        # 获取截图信息
        screenshot_test = self.test_screenshot_resolution()
        if not screenshot_test:
            print("[ERROR] 无法获取截图信息，跳过坐标转换测试")
            return None
        
        scale_x, scale_y = screenshot_test['scale_factor']
        
        for i, (screenshot_x, screenshot_y) in enumerate(screenshot_coords):
            print(f"\n[转换 {i+1}] 截图坐标: ({screenshot_x}, {screenshot_y})")
            
            # 方法1：直接使用截图坐标
            method1_x = screenshot_x
            method1_y = screenshot_y
            print(f"  方法1 (直接使用): ({method1_x}, {method1_y})")
            
            # 方法2：按缩放比例转换
            method2_x = screenshot_x * (self.screen_width / screenshot_test['actual_size'][0])
            method2_y = screenshot_y * (self.screen_height / screenshot_test['actual_size'][1])
            print(f"  方法2 (缩放转换): ({method2_x:.1f}, {method2_y:.1f})")
            
            # 方法3：逆向缩放
            method3_x = screenshot_x / scale_x
            method3_y = screenshot_y / scale_y
            print(f"  方法3 (逆向缩放): ({method3_x:.1f}, {method3_y:.1f})")
            
            # 测试每种方法的精度
            methods = [
                ('直接使用', method1_x, method1_y),
                ('缩放转换', method2_x, method2_y),
                ('逆向缩放', method3_x, method3_y)
            ]
            
            method_results = []
            for method_name, conv_x, conv_y in methods:
                try:
                    # 移动到转换后的位置
                    pyautogui.moveTo(conv_x, conv_y, duration=0.2)
                    time.sleep(0.05)
                    
                    # 获取实际位置
                    actual_x, actual_y = pyautogui.position()
                    
                    # 计算与目标的误差
                    error_x = abs(actual_x - conv_x)
                    error_y = abs(actual_y - conv_y)
                    total_error = (error_x ** 2 + error_y ** 2) ** 0.5
                    
                    print(f"    {method_name}: 实际({actual_x}, {actual_y}), 误差={total_error:.2f}")
                    
                    method_results.append({
                        'method': method_name,
                        'converted': (conv_x, conv_y),
                        'actual': (actual_x, actual_y),
                        'error': total_error
                    })
                    
                except Exception as e:
                    print(f"    {method_name}: 测试失败 - {e}")
                    method_results.append({
                        'method': method_name,
                        'error': str(e)
                    })
            
            conversion_results.append({
                'screenshot_coord': (screenshot_x, screenshot_y),
                'methods': method_results
            })
        
        test_result = {
            'test_name': 'coordinate_conversion',
            'timestamp': datetime.now().isoformat(),
            'scale_factor': (scale_x, scale_y),
            'conversions': conversion_results
        }
        
        self.test_results.append(test_result)
        return test_result
    
    def run_comprehensive_test(self):
        """运行全面测试"""
        print("🚀 开始 macOS HiDPI 全面测试")
        print("="*80)
        
        # 测试1：截图分辨率
        self.test_screenshot_resolution()
        
        # 测试2：鼠标坐标精度
        self.test_mouse_coordinate_accuracy()
        
        # 测试3：坐标转换（使用一些示例坐标）
        sample_coords = [
            (1000, 500),   # 中等位置
            (2000, 1000),  # 可能超出逻辑屏幕的位置
            (3000, 1500),  # 明显超出逻辑屏幕的位置
        ]
        self.test_coordinate_conversion(sample_coords)
        
        # 生成测试报告
        self.generate_test_report()
    
    def generate_test_report(self):
        """生成测试报告"""
        print("\n" + "="*80)
        print("📊 测试报告")
        print("="*80)
        
        # 保存详细结果到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"macos_hidpi_test_report_{timestamp}.json"
        
        report = {
            'test_info': {
                'timestamp': datetime.now().isoformat(),
                'platform': 'macOS',
                'logical_screen_size': (self.screen_width, self.screen_height),
                'display_info': self.display_info
            },
            'test_results': self.test_results
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            print(f"[INFO] 详细测试报告已保存到: {filename}")
        except Exception as e:
            print(f"[WARN] 保存测试报告失败: {e}")
        
        # 打印简要总结
        print("\n📋 测试总结:")
        
        for result in self.test_results:
            test_name = result['test_name']
            
            if test_name == 'screenshot_resolution':
                scale_x, scale_y = result['scale_factor']
                is_hidpi = result['is_hidpi']
                print(f"  📸 截图分辨率: {'HiDPI环境' if is_hidpi else '标准环境'} (缩放: {scale_x:.2f}x{scale_y:.2f})")
                
            elif test_name == 'mouse_coordinate_accuracy':
                summary = result['summary']
                avg_error = summary.get('avg_error', 0)
                max_error = summary.get('max_error', 0)
                success_rate = summary.get('successful_tests', 0) / summary.get('total_tests', 1) * 100
                print(f"  🖱️ 鼠标精度: 平均误差{avg_error:.2f}px, 最大误差{max_error:.2f}px, 成功率{success_rate:.1f}%")
        
        # 给出建议
        print("\n💡 建议:")
        
        # 检查是否为HiDPI环境
        hidpi_test = next((r for r in self.test_results if r['test_name'] == 'screenshot_resolution'), None)
        if hidpi_test and hidpi_test['is_hidpi']:
            print("  ✅ 检测到HiDPI环境，建议使用优化后的坐标转换算法")
            print("  ✅ 在坐标转换时不要强制限制到逻辑屏幕范围")
            print("  ✅ 使用截图实际尺寸计算缩放比例")
        else:
            print("  ℹ️ 标准分辨率环境，可以使用常规坐标转换")
        
        # 检查鼠标精度
        accuracy_test = next((r for r in self.test_results if r['test_name'] == 'mouse_coordinate_accuracy'), None)
        if accuracy_test and accuracy_test['summary'].get('avg_error', 0) > 5:
            print("  ⚠️ 鼠标精度较低，建议检查系统设置或使用分步移动")
        
        print(f"\n📄 完整报告文件: {filename}")


def main():
    """主函数"""
    print("macOS HiDPI 坐标测试工具")
    print("="*50)
    
    # 创建测试器
    tester = MacOSHiDPITester()
    
    # 运行测试
    tester.run_comprehensive_test()
    
    print("\n🎉 测试完成！")


if __name__ == "__main__":
    main()