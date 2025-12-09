"""
图像识别模块
支持CPU、CUDA、OpenCL多后端
"""
import cv2
import numpy as np
import os


class ImageRecognition:
    """图像识别类，支持多后端"""
    
    def __init__(self, backend='cpu'):
        """
        初始化图像识别器
        
        Args:
            backend: 'cpu', 'cuda', 'opencl'
        """
        self.backend = backend
        self.use_cuda = False
        self.templates = {}  # 缓存加载的模板
        self._init_backend()
        
    def _init_backend(self):
        """初始化后端"""
        if self.backend == 'cuda':
            # 检查CUDA是否可用
            try:
                if cv2.cuda.getCudaEnabledDeviceCount() > 0:
                    print(f"[OK] CUDA backend enabled, device count: {cv2.cuda.getCudaEnabledDeviceCount()}")
                    self.use_cuda = True
                else:
                    print("[WARN] CUDA not available, fallback to CPU")
                    self.backend = 'cpu'
            except:
                print("[WARN] CUDA module not available, fallback to CPU")
                self.backend = 'cpu'
                
        elif self.backend == 'opencl':
            # 启用OpenCL
            cv2.ocl.setUseOpenCL(True)
            if cv2.ocl.useOpenCL():
                print("[OK] OpenCL backend enabled")
            else:
                print("[WARN] OpenCL not available, fallback to CPU")
                self.backend = 'cpu'
        else:
            print("[OK] Using CPU backend")
    
    def load_template(self, name, image_path):
        """
        加载模板图片
        
        Args:
            name: 模板名称
            image_path: 图片路径
            
        Returns:
            bool: 是否加载成功
        """
        try:
            if not os.path.exists(image_path):
                print(f"[ERROR] Template file not found: {image_path}")
                return False
                
            template = cv2.imread(image_path)
            if template is None:
                print(f"[ERROR] Cannot read template: {image_path}")
                return False
                
            self.templates[name] = template
            print(f"[OK] Template loaded: {name} ({template.shape[1]}x{template.shape[0]})")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to load template: {e}")
            return False
    
    def match_template(self, screenshot, template_name, threshold=0.8):
        """
        在截图中查找模板
        
        Args:
            screenshot: 截图（numpy数组）
            template_name: 模板名称
            threshold: 匹配阈值（0-1）
            
        Returns:
            tuple: (found, position, confidence)
                found: bool - 是否找到
                position: tuple - (x, y) 中心点坐标
                confidence: float - 匹配置信度
        """
        if template_name not in self.templates:
            print(f"[ERROR] Template not loaded: {template_name}")
            return False, None, 0.0
            
        template = self.templates[template_name]
        
        try:
            if self.backend == 'cuda' and self.use_cuda:
                # CUDA加速版本
                result = self._match_cuda(screenshot, template)
            else:
                # CPU或OpenCL版本（OpenCV会自动选择）
                result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                # 计算中心点
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                
                print(f"[OK] Match found: {template_name} at ({center_x}, {center_y}), confidence: {max_val:.3f}")
                return True, (center_x, center_y), max_val
            else:
                print(f"[WARN] No match found: {template_name}, max confidence: {max_val:.3f}")
                return False, None, max_val
                
        except Exception as e:
            print(f"[ERROR] Template matching failed: {e}")
            return False, None, 0.0
    
    def _match_cuda(self, screenshot, template):
        """CUDA加速的模板匹配"""
        # 上传到GPU
        gpu_screenshot = cv2.cuda_GpuMat()
        gpu_template = cv2.cuda_GpuMat()
        gpu_screenshot.upload(screenshot)
        gpu_template.upload(template)
        
        # 创建模板匹配器
        matcher = cv2.cuda.createTemplateMatching(
            cv2.CV_8UC3, 
            cv2.TM_CCOEFF_NORMED
        )
        
        # 执行匹配
        gpu_result = matcher.match(gpu_screenshot, gpu_template)
        
        # 下载结果
        return gpu_result.download()
    
    def match_all(self, screenshot, template_name, threshold=0.8, max_results=10):
        """
        查找所有匹配位置
        
        Args:
            screenshot: 截图
            template_name: 模板名称
            threshold: 匹配阈值
            max_results: 最大结果数量
            
        Returns:
            list: [(x, y, confidence), ...] 匹配位置列表
        """
        if template_name not in self.templates:
            return []
            
        template = self.templates[template_name]
        
        try:
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            
            # 找到所有超过阈值的位置
            locations = np.where(result >= threshold)
            matches = []
            
            h, w = template.shape[:2]
            for pt in zip(*locations[::-1]):
                center_x = pt[0] + w // 2
                center_y = pt[1] + h // 2
                confidence = result[pt[1], pt[0]]
                matches.append((center_x, center_y, confidence))
                
                if len(matches) >= max_results:
                    break
            
            return matches
            
        except Exception as e:
            print(f"[ERROR] Batch matching failed: {e}")
            return []
    
    def get_backend_info(self):
        """获取后端信息"""
        info = {
            'backend': self.backend,
            'cuda_available': cv2.cuda.getCudaEnabledDeviceCount() > 0 if hasattr(cv2, 'cuda') else False,
            'opencl_available': cv2.ocl.useOpenCL(),
            'loaded_templates': list(self.templates.keys())
        }
        return info
