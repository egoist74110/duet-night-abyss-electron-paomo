"""
图像识别调试工具
专门用于分析和优化图像识别成功率
"""
import cv2
import numpy as np
import os
import json
from typing import Dict, List, Tuple, Optional


class ImageRecognitionDebugger:
    """图像识别调试器 - 帮助分析识别问题和优化参数"""
    
    def __init__(self, image_recognition, window_capture):
        """
        初始化调试器
        
        Args:
            image_recognition: 图像识别实例
            window_capture: 窗口捕获实例
        """
        self.image_recognition = image_recognition
        self.window_capture = window_capture
        self.debug_results = []
        
    def comprehensive_test(self, template_paths: Dict[str, str], 
                          thresholds: List[float] = None) -> Dict:
        """
        全面测试不同阈值下的识别效果
        
        Args:
            template_paths: 模板路径字典 {'name': 'path'}
            thresholds: 要测试的阈值列表
            
        Returns:
            Dict: 详细的测试结果
        """
        if thresholds is None:
            thresholds = [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9]
        
        print("=" * 60)
        print("🔍 开始全面图像识别测试")
        print("=" * 60)
        
        # 获取当前截图
        screenshot = self.window_capture.capture()
        if screenshot is None:
            return {'error': '无法获取游戏窗口截图'}
        
        print(f"📸 截图尺寸: {screenshot.shape[1]}x{screenshot.shape[0]}")
        
        results = {
            'screenshot_info': {
                'width': screenshot.shape[1],
                'height': screenshot.shape[0],
                'channels': screenshot.shape[2] if len(screenshot.shape) > 2 else 1
            },
            'template_tests': {},
            'recommendations': []
        }
        
        # 测试每个模板
        for template_name, template_path in template_paths.items():
            print(f"\n🎯 测试模板: {template_name}")
            print(f"📁 路径: {template_path}")
            
            # 加载模板
            if not self.image_recognition.load_template(f"debug_{template_name}", template_path):
                print(f"❌ 无法加载模板: {template_path}")
                continue
            
            template_results = {
                'template_path': template_path,
                'threshold_tests': {},
                'best_result': None,
                'template_info': self._analyze_template(template_path)
            }
            
            best_confidence = 0.0
            best_threshold = 0.0
            
            # 测试不同阈值
            for threshold in thresholds:
                print(f"  🔍 测试阈值: {threshold:.2f}")
                
                found, position, confidence = self.image_recognition.match_template(
                    screenshot, f"debug_{template_name}", threshold
                )
                
                test_result = {
                    'found': found,
                    'position': position,
                    'confidence': confidence,
                    'threshold': threshold
                }
                
                template_results['threshold_tests'][threshold] = test_result
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_threshold = threshold
                    template_results['best_result'] = test_result
                
                status = "✅ 找到" if found else "❌ 未找到"
                print(f"    {status} - 置信度: {confidence:.3f}")
            
            results['template_tests'][template_name] = template_results
            
            # 生成建议
            self._generate_recommendations(template_name, template_results, results['recommendations'])
        
        # 保存调试结果
        self._save_debug_results(results)
        
        # 打印总结
        self._print_summary(results)
        
        return results
    
    def _analyze_template(self, template_path: str) -> Dict:
        """分析模板图像的特征"""
        try:
            template = cv2.imread(template_path)
            if template is None:
                return {'error': '无法读取模板图像'}
            
            # 基本信息
            height, width = template.shape[:2]
            channels = template.shape[2] if len(template.shape) > 2 else 1
            
            # 转换为灰度图进行分析
            if channels > 1:
                gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            else:
                gray = template
            
            # 计算图像特征
            mean_brightness = np.mean(gray)
            std_brightness = np.std(gray)
            
            # 边缘检测
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / (width * height)
            
            # 直方图分析
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            hist_peak = np.argmax(hist)
            
            return {
                'width': width,
                'height': height,
                'channels': channels,
                'mean_brightness': float(mean_brightness),
                'std_brightness': float(std_brightness),
                'edge_density': float(edge_density),
                'histogram_peak': int(hist_peak),
                'size_category': self._categorize_size(width, height)
            }
            
        except Exception as e:
            return {'error': f'模板分析失败: {str(e)}'}
    
    def _categorize_size(self, width: int, height: int) -> str:
        """根据尺寸分类模板"""
        area = width * height
        if area < 1000:
            return 'small'  # 小图标
        elif area < 5000:
            return 'medium'  # 中等按钮
        else:
            return 'large'   # 大型元素
    
    def _generate_recommendations(self, template_name: str, 
                                template_results: Dict, 
                                recommendations: List):
        """生成优化建议"""
        best_result = template_results.get('best_result')
        template_info = template_results.get('template_info', {})
        
        if not best_result:
            recommendations.append({
                'template': template_name,
                'type': 'error',
                'message': f'{template_name}: 所有阈值下都无法识别，建议检查模板图像质量'
            })
            return
        
        best_confidence = best_result['confidence']
        best_threshold = best_result['threshold']
        
        # 基于置信度生成建议
        if best_confidence >= 0.8:
            recommendations.append({
                'template': template_name,
                'type': 'excellent',
                'message': f'{template_name}: 识别效果优秀 (置信度: {best_confidence:.3f})，建议阈值: {best_threshold:.2f}'
            })
        elif best_confidence >= 0.65:
            recommendations.append({
                'template': template_name,
                'type': 'good',
                'message': f'{template_name}: 识别效果良好 (置信度: {best_confidence:.3f})，建议阈值: {best_threshold:.2f}'
            })
        elif best_confidence >= 0.5:
            recommendations.append({
                'template': template_name,
                'type': 'warning',
                'message': f'{template_name}: 识别效果一般 (置信度: {best_confidence:.3f})，建议阈值: {best_threshold:.2f}，考虑优化模板图像'
            })
        else:
            recommendations.append({
                'template': template_name,
                'type': 'error',
                'message': f'{template_name}: 识别效果差 (置信度: {best_confidence:.3f})，需要重新制作模板图像'
            })
        
        # 基于模板特征生成建议
        if 'edge_density' in template_info:
            edge_density = template_info['edge_density']
            if edge_density < 0.1:
                recommendations.append({
                    'template': template_name,
                    'type': 'tip',
                    'message': f'{template_name}: 边缘特征较少，建议选择边缘更清晰的区域作为模板'
                })
        
        if 'std_brightness' in template_info:
            std_brightness = template_info['std_brightness']
            if std_brightness < 20:
                recommendations.append({
                    'template': template_name,
                    'type': 'tip',
                    'message': f'{template_name}: 对比度较低，建议选择对比度更高的图像区域'
                })
    
    def _save_debug_results(self, results: Dict):
        """保存调试结果到文件"""
        try:
            debug_dir = 'debug_results'
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
            
            # 保存JSON结果
            json_path = os.path.join(debug_dir, 'recognition_debug_results.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"\n💾 调试结果已保存到: {json_path}")
            
        except Exception as e:
            print(f"⚠️ 保存调试结果失败: {e}")
    
    def _print_summary(self, results: Dict):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("📊 测试总结")
        print("=" * 60)
        
        template_tests = results.get('template_tests', {})
        recommendations = results.get('recommendations', [])
        
        # 统计各类结果
        excellent_count = sum(1 for r in recommendations if r['type'] == 'excellent')
        good_count = sum(1 for r in recommendations if r['type'] == 'good')
        warning_count = sum(1 for r in recommendations if r['type'] == 'warning')
        error_count = sum(1 for r in recommendations if r['type'] == 'error')
        
        print(f"📈 测试模板数量: {len(template_tests)}")
        print(f"✅ 优秀识别: {excellent_count}")
        print(f"🟢 良好识别: {good_count}")
        print(f"⚠️ 需要优化: {warning_count}")
        print(f"❌ 识别失败: {error_count}")
        
        print("\n🎯 推荐设置:")
        
        # 计算推荐的全局阈值
        all_confidences = []
        for template_name, template_result in template_tests.items():
            best_result = template_result.get('best_result')
            if best_result and best_result['confidence'] > 0.5:
                all_confidences.append(best_result['confidence'])
        
        if all_confidences:
            avg_confidence = np.mean(all_confidences)
            recommended_threshold = max(0.5, avg_confidence - 0.1)
            print(f"   推荐全局阈值: {recommended_threshold:.2f}")
            print(f"   平均最佳置信度: {avg_confidence:.3f}")
        
        print("\n📋 详细建议:")
        for rec in recommendations:
            icon = {
                'excellent': '🌟',
                'good': '✅',
                'warning': '⚠️',
                'error': '❌',
                'tip': '💡'
            }.get(rec['type'], '📌')
            print(f"   {icon} {rec['message']}")
    
    def quick_test(self, template_name: str, template_path: str, 
                   threshold: float = 0.65) -> Dict:
        """
        快速测试单个模板
        
        Args:
            template_name: 模板名称
            template_path: 模板路径
            threshold: 测试阈值
            
        Returns:
            Dict: 测试结果
        """
        print(f"🚀 快速测试: {template_name}")
        
        # 获取截图
        screenshot = self.window_capture.capture()
        if screenshot is None:
            return {'error': '无法获取游戏窗口截图'}
        
        # 加载模板
        if not self.image_recognition.load_template(f"quick_{template_name}", template_path):
            return {'error': f'无法加载模板: {template_path}'}
        
        # 执行识别
        found, position, confidence = self.image_recognition.match_template(
            screenshot, f"quick_{template_name}", threshold
        )
        
        result = {
            'template_name': template_name,
            'template_path': template_path,
            'threshold': threshold,
            'found': found,
            'position': position,
            'confidence': confidence,
            'screenshot_size': (screenshot.shape[1], screenshot.shape[0])
        }
        
        # 打印结果
        status = "✅ 找到" if found else "❌ 未找到"
        print(f"   {status} - 置信度: {confidence:.3f}")
        
        if found:
            print(f"   📍 位置: ({position[0]}, {position[1]})")
        
        # 生成建议
        if confidence >= 0.8:
            print(f"   🌟 识别效果优秀，当前阈值 {threshold:.2f} 合适")
        elif confidence >= 0.65:
            print(f"   ✅ 识别效果良好，当前阈值 {threshold:.2f} 合适")
        elif confidence >= 0.5:
            print(f"   ⚠️ 识别效果一般，建议降低阈值到 {max(0.5, confidence - 0.05):.2f}")
        else:
            print(f"   ❌ 识别效果差，建议检查模板图像质量或降低阈值到 0.5")
        
        return result


def create_debugger(image_recognition, window_capture):
    """创建图像识别调试器实例"""
    return ImageRecognitionDebugger(image_recognition, window_capture)