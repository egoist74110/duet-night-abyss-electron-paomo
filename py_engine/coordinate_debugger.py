"""
坐标调试和修复工具
专门用于解决鼠标点击位置不准确的问题
"""
import pyautogui
import cv2
import numpy as np
import time
import platform
import json
from typing import Tuple, Dict, Any


class CoordinateDebugger:
    """坐标调试器 - 专门解决点击位置不准确问题"""
    
    def __init__(self, window_capture, human_mouse, image_recognition):
        """
        初始化坐标调试器
        
        Args:
            window_capture: 窗口捕获实例
            human_mouse: 鼠标控制实例
            image_recognition: 图像识别实例
        """
        self.window_capture = window_capture
        self.human_mouse = human_mouse
        self.image_recognition = image_recognition
        self.platform = platform.system()
        
        # 获取屏幕信息
        self.screen_width, self.screen_height = pyautogui.size()
        print(f"[INFO] 坐标调试器初始化完成")
        print(f"[INFO] 平台: {self.platform}")
        print(f"[INFO] 屏幕尺寸: {self.screen_width}x{self.screen_height}")
        
    def comprehensive_coordinate_test(self, template_path: str, template_name: str) -> Dict[str, Any]:
        """
        全面的坐标测试 - 这是解决点击位置问题的核心功能
        
        Args:
            template_path: 模板图片路径
            template_name: 模板名称
            
        Returns:
            Dict: 详细的测试结果和修复建议
        """
        print("=" * 60)
        print(f"🎯 开始全面坐标测试: {template_name}")
        print("=" * 60)
        
        result = {
            'template_name': template_name,
            'template_path': template_path,
            'platform': self.platform,
            'screen_info': {
                'width': self.screen_width,
                'height': self.screen_height
            },
            'tests': {},
            'recommendations': [],
            'success': False
        }
        
        try:
            # 第一步：加载模板并识别
            print("📸 第一步：图像识别测试")
            recognition_result = self._test_image_recognition(template_path, template_name)
            result['tests']['recognition'] = recognition_result
            
            if not recognition_result['found']:
                result['recommendations'].append({
                    'type': 'error',
                    'message': f'图像识别失败，无法进行坐标测试。置信度: {recognition_result["confidence"]:.3f}'
                })
                return result
            
            # 第二步：坐标转换测试
            print("\n🔄 第二步：坐标转换测试")
            conversion_result = self._test_coordinate_conversion(recognition_result)
            result['tests']['conversion'] = conversion_result
            
            # 第三步：鼠标移动测试（不点击）
            print("\n🖱️ 第三步：鼠标移动精度测试")
            movement_result = self._test_mouse_movement(conversion_result['screen_coords'])
            result['tests']['movement'] = movement_result
            
            # 第四步：点击精度测试
            print("\n🎯 第四步：点击精度测试")
            click_result = self._test_click_accuracy(conversion_result['screen_coords'])
            result['tests']['click'] = click_result
            
            # 第五步：生成修复建议
            print("\n💡 第五步：生成修复建议")
            self._generate_coordinate_recommendations(result)
            
            # 判断整体成功率
            result['success'] = (
                recognition_result['found'] and
                movement_result['accuracy'] < 5 and  # 移动误差小于5像素
                click_result['success']
            )
            
            print(f"\n🎉 坐标测试完成，成功率: {'✅ 优秀' if result['success'] else '⚠️ 需要优化'}")
            
        except Exception as e:
            print(f"❌ 坐标测试过程出错: {e}")
            result['error'] = str(e)
            result['recommendations'].append({
                'type': 'error',
                'message': f'测试过程出错: {str(e)}'
            })
        
        return result
    
    def _test_image_recognition(self, template_path: str, template_name: str) -> Dict[str, Any]:
        """测试图像识别"""
        try:
            # 加载模板
            success = self.image_recognition.load_template('coord_test', template_path)
            if not success:
                return {'found': False, 'error': '无法加载模板图片'}
            
            # 获取截图
            screenshot = self.window_capture.capture()
            if screenshot is None:
                return {'found': False, 'error': '无法获取游戏窗口截图'}
            
            print(f"   📸 截图尺寸: {screenshot.shape[1]}x{screenshot.shape[0]}")
            
            # 执行识别
            found, position, confidence = self.image_recognition.match_template(
                screenshot, 'coord_test', 0.6  # 使用较低阈值确保能找到
            )
            
            result = {
                'found': found,
                'position': position,
                'confidence': confidence,
                'screenshot_size': (screenshot.shape[1], screenshot.shape[0])
            }
            
            if found:
                print(f"   ✅ 识别成功: 位置({position[0]}, {position[1]}), 置信度: {confidence:.3f}")
            else:
                print(f"   ❌ 识别失败: 最高置信度: {confidence:.3f}")
            
            return result
            
        except Exception as e:
            print(f"   ❌ 识别测试出错: {e}")
            return {'found': False, 'error': str(e)}
    
    def _test_coordinate_conversion(self, recognition_result: Dict[str, Any]) -> Dict[str, Any]:
        """测试坐标转换"""
        try:
            if not recognition_result['found']:
                return {'error': '图像识别失败，无法测试坐标转换'}
            
            rel_x, rel_y = recognition_result['position']
            print(f"   🔍 识别到的相对坐标: ({rel_x}, {rel_y})")
            
            # 使用窗口捕获的坐标转换方法
            screen_x, screen_y = self.window_capture.convert_relative_to_screen_coords(rel_x, rel_y)
            print(f"   🔄 转换后的屏幕坐标: ({screen_x}, {screen_y})")
            
            # 验证坐标是否在屏幕范围内
            in_bounds = (0 <= screen_x <= self.screen_width and 0 <= screen_y <= self.screen_height)
            print(f"   📏 坐标范围检查: {'✅ 在范围内' if in_bounds else '❌ 超出范围'}")
            
            # 计算坐标转换的合理性
            screenshot_size = recognition_result['screenshot_size']
            conversion_ratio_x = screen_x / screenshot_size[0] if screenshot_size[0] > 0 else 0
            conversion_ratio_y = screen_y / screenshot_size[1] if screenshot_size[1] > 0 else 0
            
            print(f"   📊 转换比例: X={conversion_ratio_x:.3f}, Y={conversion_ratio_y:.3f}")
            
            result = {
                'relative_coords': (rel_x, rel_y),
                'screen_coords': (screen_x, screen_y),
                'in_bounds': in_bounds,
                'conversion_ratio': (conversion_ratio_x, conversion_ratio_y),
                'screenshot_size': screenshot_size
            }
            
            return result
            
        except Exception as e:
            print(f"   ❌ 坐标转换测试出错: {e}")
            return {'error': str(e)}
    
    def _test_mouse_movement(self, target_coords: Tuple[int, int]) -> Dict[str, Any]:
        """测试鼠标移动精度"""
        try:
            target_x, target_y = target_coords
            print(f"   🎯 目标位置: ({target_x}, {target_y})")
            
            # 记录移动前位置
            before_x, before_y = pyautogui.position()
            print(f"   📍 移动前位置: ({before_x}, {before_y})")
            
            # 执行移动
            print(f"   🖱️ 开始移动鼠标...")
            pyautogui.moveTo(target_x, target_y, duration=0.5)
            time.sleep(0.2)  # 等待移动完成
            
            # 记录移动后位置
            after_x, after_y = pyautogui.position()
            print(f"   📍 移动后位置: ({after_x}, {after_y})")
            
            # 计算精度
            error_x = abs(after_x - target_x)
            error_y = abs(after_y - target_y)
            total_error = (error_x ** 2 + error_y ** 2) ** 0.5
            
            print(f"   📏 移动误差: X={error_x}, Y={error_y}, 总误差={total_error:.1f}像素")
            
            # 评估精度等级
            if total_error <= 2:
                accuracy_level = "优秀"
            elif total_error <= 5:
                accuracy_level = "良好"
            elif total_error <= 10:
                accuracy_level = "一般"
            else:
                accuracy_level = "较差"
            
            print(f"   🎯 移动精度: {accuracy_level}")
            
            result = {
                'target_coords': (target_x, target_y),
                'before_coords': (before_x, before_y),
                'after_coords': (after_x, after_y),
                'error': (error_x, error_y),
                'accuracy': total_error,
                'accuracy_level': accuracy_level
            }
            
            return result
            
        except Exception as e:
            print(f"   ❌ 鼠标移动测试出错: {e}")
            return {'error': str(e)}
    
    def _test_click_accuracy(self, target_coords: Tuple[int, int]) -> Dict[str, Any]:
        """测试点击精度"""
        try:
            target_x, target_y = target_coords
            print(f"   🎯 准备点击位置: ({target_x}, {target_y})")
            
            # 记录点击前位置
            before_x, before_y = pyautogui.position()
            
            # 执行点击（使用human_mouse的精确点击方法）
            print(f"   🖱️ 执行精确点击...")
            click_success = self.human_mouse.click(target_x, target_y)
            
            # 记录点击后位置
            after_x, after_y = pyautogui.position()
            
            # 计算点击精度
            error_x = abs(after_x - target_x)
            error_y = abs(after_y - target_y)
            total_error = (error_x ** 2 + error_y ** 2) ** 0.5
            
            print(f"   📏 点击误差: X={error_x}, Y={error_y}, 总误差={total_error:.1f}像素")
            print(f"   🎯 点击结果: {'✅ 成功' if click_success else '❌ 失败'}")
            
            result = {
                'target_coords': (target_x, target_y),
                'before_coords': (before_x, before_y),
                'after_coords': (after_x, after_y),
                'error': (error_x, error_y),
                'accuracy': total_error,
                'success': click_success
            }
            
            return result
            
        except Exception as e:
            print(f"   ❌ 点击测试出错: {e}")
            return {'error': str(e), 'success': False}
    
    def _generate_coordinate_recommendations(self, result: Dict[str, Any]):
        """生成坐标修复建议"""
        recommendations = result['recommendations']
        tests = result['tests']
        
        # 分析识别结果
        if 'recognition' in tests and tests['recognition']['found']:
            recommendations.append({
                'type': 'success',
                'message': f'✅ 图像识别正常，置信度: {tests["recognition"]["confidence"]:.3f}'
            })
        
        # 分析坐标转换
        if 'conversion' in tests and 'screen_coords' in tests['conversion']:
            conversion = tests['conversion']
            if conversion['in_bounds']:
                recommendations.append({
                    'type': 'success',
                    'message': '✅ 坐标转换正常，目标位置在屏幕范围内'
                })
            else:
                recommendations.append({
                    'type': 'error',
                    'message': '❌ 坐标转换异常，目标位置超出屏幕范围'
                })
                recommendations.append({
                    'type': 'fix',
                    'message': '🔧 建议检查窗口捕获的坐标转换逻辑'
                })
        
        # 分析鼠标移动精度
        if 'movement' in tests and 'accuracy' in tests['movement']:
            movement = tests['movement']
            accuracy = movement['accuracy']
            
            if accuracy <= 2:
                recommendations.append({
                    'type': 'success',
                    'message': f'✅ 鼠标移动精度优秀，误差仅{accuracy:.1f}像素'
                })
            elif accuracy <= 5:
                recommendations.append({
                    'type': 'good',
                    'message': f'🟢 鼠标移动精度良好，误差{accuracy:.1f}像素'
                })
            elif accuracy <= 10:
                recommendations.append({
                    'type': 'warning',
                    'message': f'⚠️ 鼠标移动精度一般，误差{accuracy:.1f}像素'
                })
                recommendations.append({
                    'type': 'fix',
                    'message': '🔧 建议检查系统DPI设置或显示缩放'
                })
            else:
                recommendations.append({
                    'type': 'error',
                    'message': f'❌ 鼠标移动精度较差，误差{accuracy:.1f}像素'
                })
                recommendations.append({
                    'type': 'fix',
                    'message': '🔧 建议重新校准坐标转换算法'
                })
        
        # 分析点击结果
        if 'click' in tests:
            click = tests['click']
            if click.get('success', False):
                recommendations.append({
                    'type': 'success',
                    'message': '✅ 点击功能正常'
                })
            else:
                recommendations.append({
                    'type': 'error',
                    'message': '❌ 点击功能异常'
                })
                recommendations.append({
                    'type': 'fix',
                    'message': '🔧 建议检查鼠标控制权限或pyautogui配置'
                })
        
        # 平台特定建议
        if self.platform == 'Darwin':  # macOS
            recommendations.append({
                'type': 'tip',
                'message': '💡 macOS用户：确保应用有辅助功能和屏幕录制权限'
            })
            recommendations.append({
                'type': 'tip',
                'message': '💡 macOS用户：如果使用Retina显示器，可能需要调整坐标缩放'
            })
        elif self.platform == 'Windows':
            recommendations.append({
                'type': 'tip',
                'message': '💡 Windows用户：确保以管理员权限运行应用'
            })
            recommendations.append({
                'type': 'tip',
                'message': '💡 Windows用户：检查显示缩放设置，建议使用100%缩放'
            })
    
    def quick_position_test(self, x: int, y: int) -> Dict[str, Any]:
        """
        快速位置测试 - 测试指定坐标的点击精度
        
        Args:
            x: X坐标
            y: Y坐标
            
        Returns:
            Dict: 测试结果
        """
        print(f"🚀 快速位置测试: ({x}, {y})")
        
        try:
            # 移动到指定位置
            print(f"   🖱️ 移动到目标位置...")
            pyautogui.moveTo(x, y, duration=0.3)
            time.sleep(0.1)
            
            # 检查实际位置
            actual_x, actual_y = pyautogui.position()
            error_x = abs(actual_x - x)
            error_y = abs(actual_y - y)
            total_error = (error_x ** 2 + error_y ** 2) ** 0.5
            
            print(f"   📍 目标位置: ({x}, {y})")
            print(f"   📍 实际位置: ({actual_x}, {actual_y})")
            print(f"   📏 位置误差: X={error_x}, Y={error_y}, 总误差={total_error:.1f}像素")
            
            # 执行点击
            print(f"   🖱️ 执行点击...")
            click_success = self.human_mouse.click(x, y)
            
            result = {
                'target': (x, y),
                'actual': (actual_x, actual_y),
                'error': (error_x, error_y),
                'total_error': total_error,
                'click_success': click_success,
                'accuracy_level': 'excellent' if total_error <= 2 else 'good' if total_error <= 5 else 'poor'
            }
            
            print(f"   🎯 测试结果: {'✅ 优秀' if result['accuracy_level'] == 'excellent' else '🟢 良好' if result['accuracy_level'] == 'good' else '❌ 需要优化'}")
            
            return result
            
        except Exception as e:
            print(f"   ❌ 快速测试出错: {e}")
            return {'error': str(e)}
    
    def save_debug_results(self, results: Dict[str, Any], filename: str = None):
        """保存调试结果到文件"""
        try:
            if filename is None:
                filename = f"coordinate_debug_{int(time.time())}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"💾 调试结果已保存到: {filename}")
            
        except Exception as e:
            print(f"⚠️ 保存调试结果失败: {e}")


def create_coordinate_debugger(window_capture, human_mouse, image_recognition):
    """创建坐标调试器实例"""
    return CoordinateDebugger(window_capture, human_mouse, image_recognition)