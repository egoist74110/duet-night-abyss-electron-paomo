"""
图像识别模块
支持CPU、CUDA、OpenCL多后端
包含全局静默图像识别系统
"""
import cv2
import numpy as np
import os
import threading
import time
import json
from typing import Dict, List, Tuple, Optional, Any


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
        在截图中查找模板（支持多尺度匹配和图像预处理优化）
        
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
        
        # 动态调整阈值 - 游戏界面识别建议使用更低的阈值
        adjusted_threshold = max(0.6, threshold - 0.1)  # 降低10%，但不低于60%
        print(f"[INFO] Adjusted threshold from {threshold:.2f} to {adjusted_threshold:.2f} for better game UI recognition")
        
        # 首先尝试原始尺寸匹配
        found, position, confidence = self._match_single_scale_enhanced(screenshot, template, adjusted_threshold)
        if found:
            print(f"[OK] Match found at original scale: {template_name} at {position}, confidence: {confidence:.3f}")
            return True, position, confidence
        
        print(f"[INFO] Original scale failed (confidence: {confidence:.3f}), trying enhanced multi-scale matching...")
        
        # 优化的多尺度匹配 - 针对游戏界面优化
        scales = [0.8, 0.9, 1.1, 1.2, 0.7, 1.3, 0.6, 1.4, 0.5, 1.5]  # 重新排序，优先尝试接近原始尺寸的缩放
        best_confidence = confidence
        best_position = position
        best_scale = 1.0
        
        for scale in scales:
            try:
                # 缩放模板
                new_width = int(template.shape[1] * scale)
                new_height = int(template.shape[0] * scale)
                
                # 跳过过大或过小的尺寸
                if new_width < 15 or new_height < 15 or new_width > screenshot.shape[1] or new_height > screenshot.shape[0]:
                    continue
                
                scaled_template = cv2.resize(template, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
                found, position, confidence = self._match_single_scale_enhanced(screenshot, scaled_template, adjusted_threshold)
                
                print(f"[DEBUG] Scale {scale:.2f}: confidence={confidence:.3f}")
                
                if found:
                    print(f"[OK] Match found at scale {scale:.2f}: {template_name} at {position}, confidence: {confidence:.3f}")
                    return True, position, confidence
                
                # 记录最佳结果
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_position = position
                    best_scale = scale
                    
            except Exception as e:
                print(f"[WARN] Scale {scale:.2f} failed: {e}")
                continue
        
        # 如果多尺度匹配也失败，尝试更宽松的阈值
        if best_confidence > 0.5:  # 如果最佳置信度超过50%，可能是阈值问题
            relaxed_threshold = 0.5
            print(f"[INFO] Trying relaxed threshold {relaxed_threshold:.2f} with best scale {best_scale:.2f}")
            
            try:
                if best_scale != 1.0:
                    new_width = int(template.shape[1] * best_scale)
                    new_height = int(template.shape[0] * best_scale)
                    scaled_template = cv2.resize(template, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
                    found, position, confidence = self._match_single_scale_enhanced(screenshot, scaled_template, relaxed_threshold)
                else:
                    found, position, confidence = self._match_single_scale_enhanced(screenshot, template, relaxed_threshold)
                
                if found:
                    print(f"[OK] Match found with relaxed threshold: {template_name} at {position}, confidence: {confidence:.3f}")
                    return True, position, confidence
            except Exception as e:
                print(f"[WARN] Relaxed threshold matching failed: {e}")
        
        print(f"[WARN] All matching attempts failed: {template_name}, best confidence: {best_confidence:.3f} at scale {best_scale:.2f}")
        print(f"[SUGGESTION] Consider lowering threshold below 0.5 or checking template image quality")
        return False, best_position, best_confidence
    
    def _match_single_scale(self, screenshot, template, threshold):
        """
        单一尺度的模板匹配
        
        Args:
            screenshot: 截图
            template: 模板图像
            threshold: 匹配阈值
            
        Returns:
            tuple: (found, position, confidence)
        """
        try:
            if self.backend == 'cuda' and self.use_cuda:
                # CUDA加速版本
                result = self._match_cuda(screenshot, template)
            else:
                # CPU或OpenCL版本（OpenCV会自动选择）
                result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                # 计算精确的中心点
                h, w = template.shape[:2]
                
                # 匹配区域的左上角坐标
                match_top_left_x = max_loc[0]
                match_top_left_y = max_loc[1]
                
                # 计算几何中心点（使用浮点数确保精度）
                center_x = match_top_left_x + w / 2.0
                center_y = match_top_left_y + h / 2.0
                
                print(f"[DEBUG] 模板尺寸: {w}x{h}")
                print(f"[DEBUG] 匹配区域左上角: ({match_top_left_x}, {match_top_left_y})")
                print(f"[DEBUG] 计算的中心点: ({center_x}, {center_y})")
                
                return True, (int(center_x), int(center_y)), max_val
            else:
                return False, None, max_val
                
        except Exception as e:
            print(f"[ERROR] Template matching failed: {e}")
            return False, None, 0.0

    def _match_single_scale_enhanced(self, screenshot, template, threshold):
        """
        增强的单一尺度模板匹配 - 包含图像预处理优化
        
        Args:
            screenshot: 截图
            template: 模板图像
            threshold: 匹配阈值
            
        Returns:
            tuple: (found, position, confidence)
        """
        try:
            # 图像预处理 - 提高匹配精度
            processed_screenshot = self._preprocess_image(screenshot)
            processed_template = self._preprocess_image(template)
            
            # 尝试多种匹配方法
            methods = [
                cv2.TM_CCOEFF_NORMED,    # 标准化相关系数匹配（推荐）
                cv2.TM_CCORR_NORMED,     # 标准化相关匹配
                cv2.TM_SQDIFF_NORMED     # 标准化平方差匹配（需要反转结果）
            ]
            
            best_confidence = 0.0
            best_position = None
            best_method = None
            
            for i, method in enumerate(methods):
                try:
                    if self.backend == 'cuda' and self.use_cuda:
                        # CUDA加速版本
                        result = self._match_cuda_enhanced(processed_screenshot, processed_template, method)
                    else:
                        # CPU或OpenCL版本
                        result = cv2.matchTemplate(processed_screenshot, processed_template, method)
                    
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    
                    # 对于TM_SQDIFF_NORMED，值越小越好，需要转换
                    if method == cv2.TM_SQDIFF_NORMED:
                        confidence = 1.0 - min_val
                        loc = min_loc
                    else:
                        confidence = max_val
                        loc = max_loc
                    
                    print(f"[DEBUG] Method {i+1}: confidence={confidence:.3f}")
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_position = loc
                        best_method = method
                        
                except Exception as e:
                    print(f"[WARN] Matching method {i+1} failed: {e}")
                    continue
            
            # 检查最佳结果是否满足阈值
            if best_confidence >= threshold and best_position is not None:
                # 计算精确的中心点
                h, w = template.shape[:2]
                
                # 匹配区域的左上角坐标
                match_top_left_x = best_position[0]
                match_top_left_y = best_position[1]
                
                # 计算几何中心点（使用浮点数确保精度）
                center_x = match_top_left_x + w / 2.0
                center_y = match_top_left_y + h / 2.0
                
                print(f"[DEBUG] 最佳匹配方法: {best_method}")
                print(f"[DEBUG] 模板尺寸: {w}x{h}")
                print(f"[DEBUG] 匹配区域左上角: ({match_top_left_x}, {match_top_left_y})")
                print(f"[DEBUG] 计算的中心点: ({center_x}, {center_y})")
                
                return True, (int(center_x), int(center_y)), best_confidence
            else:
                return False, best_position, best_confidence
                
        except Exception as e:
            print(f"[ERROR] Enhanced template matching failed: {e}")
            return False, None, 0.0

    def _preprocess_image(self, image):
        """
        图像预处理 - 提高匹配精度
        
        Args:
            image: 输入图像
            
        Returns:
            numpy.ndarray: 预处理后的图像
        """
        try:
            # 如果是彩色图像，转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 应用高斯模糊减少噪声
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # 直方图均衡化 - 改善对比度
            equalized = cv2.equalizeHist(blurred)
            
            return equalized
            
        except Exception as e:
            print(f"[WARN] Image preprocessing failed: {e}, using original image")
            return image

    def _match_cuda_enhanced(self, screenshot, template, method):
        """增强的CUDA模板匹配"""
        try:
            # 上传到GPU
            gpu_screenshot = cv2.cuda_GpuMat()
            gpu_template = cv2.cuda_GpuMat()
            gpu_screenshot.upload(screenshot)
            gpu_template.upload(template)
            
            # 创建模板匹配器
            matcher = cv2.cuda.createTemplateMatching(
                cv2.CV_8UC1,  # 灰度图像
                method
            )
            
            # 执行匹配
            gpu_result = matcher.match(gpu_screenshot, gpu_template)
            
            # 下载结果
            return gpu_result.download()
            
        except Exception as e:
            print(f"[WARN] CUDA enhanced matching failed: {e}, fallback to CPU")
            return cv2.matchTemplate(screenshot, template, method)
    
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


class GlobalImageRecognitionSystem:
    """
    全局静默图像识别系统
    负责持续监控游戏窗口，识别副本图片和开始挑战按钮，并执行自动点击
    """
    
    def __init__(self, window_capture, human_mouse, image_recognition):
        """
        初始化全局图像识别系统
        
        Args:
            window_capture: 窗口捕获实例
            human_mouse: 鼠标控制实例  
            image_recognition: 图像识别实例
        """
        self.window_capture = window_capture
        self.human_mouse = human_mouse
        self.image_recognition = image_recognition
        
        # 系统状态
        self.is_running = False
        self.recognition_thread = None
        self.stop_event = threading.Event()
        
        # 配置参数
        self.config = {
            'dungeons': [],  # 启用的副本配置
            'start_challenge': {'imagePath': 'static/dungeon/开始挑战.png'},
            'interval': 2000,  # 识别间隔（毫秒）
            'accuracy': 'normal',  # 识别精度
            'click_delay': 500,  # 点击延迟
            'match_threshold': 0.65,  # 匹配阈值 (游戏界面推荐0.6-0.7)
            'max_retries': 3,  # 最大重试次数
            'debug_mode': False  # 调试模式
        }
        
        # 统计信息
        self.statistics = {
            'recognition_count': 0,
            'click_count': 0,
            'start_time': 0,
            'last_recognition_time': 0,
            'current_dungeon': None
        }
        
        # 回调函数
        self.result_callback = None
        self.error_callback = None
        
    def set_config(self, config: Dict[str, Any]):
        """
        设置识别配置
        
        Args:
            config: 配置字典
        """
        self.config.update(config)
        print(f"[INFO] Recognition config updated: {len(self.config.get('dungeons', []))} dungeons enabled")
        
        # 加载模板图片
        self._load_templates()
        
    def _load_templates(self):
        """加载所有需要的模板图片"""
        try:
            # 加载副本模板
            for dungeon in self.config.get('dungeons', []):
                template_name = f"dungeon_{dungeon['key']}"
                image_path = dungeon['imagePath']
                
                # 转换相对路径为绝对路径
                if not os.path.isabs(image_path):
                    # 从py_engine目录向上查找static目录
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    project_root = os.path.dirname(script_dir)
                    image_path = os.path.join(project_root, image_path)
                
                success = self.image_recognition.load_template(template_name, image_path)
                if success:
                    print(f"[OK] Loaded dungeon template: {dungeon['name']} -> {template_name}")
                else:
                    print(f"[ERROR] Failed to load dungeon template: {dungeon['name']}")
            
            # 加载开始挑战按钮模板
            start_challenge = self.config.get('start_challenge', {})
            if start_challenge.get('imagePath'):
                image_path = start_challenge['imagePath']
                
                # 转换相对路径为绝对路径
                if not os.path.isabs(image_path):
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    project_root = os.path.dirname(script_dir)
                    image_path = os.path.join(project_root, image_path)
                
                success = self.image_recognition.load_template('start_challenge', image_path)
                if success:
                    print(f"[OK] Loaded start challenge template")
                else:
                    print(f"[ERROR] Failed to load start challenge template")
                    
        except Exception as e:
            print(f"[ERROR] Failed to load templates: {e}")
            
    def start_recognition(self) -> bool:
        """
        启动图像识别系统
        
        Returns:
            bool: 是否启动成功
        """
        if self.is_running:
            print("[WARN] Recognition system is already running")
            return False
            
        if not self.window_capture.window_hwnd:
            print("[ERROR] No game window connected")
            return False
            
        if not self.config.get('dungeons'):
            print("[ERROR] No dungeons enabled")
            return False
            
        try:
            # 重置统计信息
            self.statistics = {
                'recognition_count': 0,
                'click_count': 0,
                'start_time': time.time(),
                'last_recognition_time': 0,
                'current_dungeon': None
            }
            
            # 重置停止事件
            self.stop_event.clear()
            
            # 启动识别线程
            self.recognition_thread = threading.Thread(
                target=self._recognition_loop,
                daemon=True,
                name="ImageRecognitionThread"
            )
            
            self.is_running = True
            self.recognition_thread.start()
            
            print("[INFO] Global image recognition system started")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to start recognition system: {e}")
            self.is_running = False
            return False
            
    def stop_recognition(self) -> bool:
        """
        停止图像识别系统
        
        Returns:
            bool: 是否停止成功
        """
        if not self.is_running:
            print("[WARN] Recognition system is not running")
            return False
            
        try:
            print("[INFO] Stopping recognition system...")
            
            # 设置停止事件
            self.stop_event.set()
            
            # 等待线程结束
            if self.recognition_thread and self.recognition_thread.is_alive():
                self.recognition_thread.join(timeout=5.0)
                
                if self.recognition_thread.is_alive():
                    print("[WARN] Recognition thread did not stop gracefully")
                else:
                    print("[INFO] Recognition thread stopped successfully")
            
            self.is_running = False
            self.recognition_thread = None
            
            print("[INFO] Global image recognition system stopped")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to stop recognition system: {e}")
            return False
            
    def _recognition_loop(self):
        """
        图像识别主循环
        在独立线程中运行，持续监控游戏窗口
        """
        print("[INFO] Recognition loop started")
        
        try:
            while not self.stop_event.is_set():
                try:
                    # 执行一次识别
                    self._perform_recognition()
                    
                    # 更新统计信息
                    self.statistics['recognition_count'] += 1
                    self.statistics['last_recognition_time'] = time.time()
                    
                    # 等待下次识别（可中断等待）
                    interval_seconds = self.config.get('interval', 2000) / 1000.0
                    if self.stop_event.wait(timeout=interval_seconds):
                        break  # 收到停止信号
                        
                except Exception as e:
                    print(f"[ERROR] Recognition loop error: {e}")
                    if self.error_callback:
                        self.error_callback({
                            'message': str(e),
                            'critical': False
                        })
                    
                    # 出错后等待一段时间再继续
                    if self.stop_event.wait(timeout=1.0):
                        break
                        
        except Exception as e:
            print(f"[ERROR] Fatal error in recognition loop: {e}")
            if self.error_callback:
                self.error_callback({
                    'message': f"Fatal error: {str(e)}",
                    'critical': True
                })
        finally:
            print("[INFO] Recognition loop ended")
            
    def _perform_recognition(self):
        """
        执行一次图像识别
        """
        try:
            # 获取游戏窗口截图
            screenshot = self.window_capture.capture_window()
            if screenshot is None:
                print("[WARN] Failed to capture window screenshot")
                return
                
            print(f"[DEBUG] Screenshot captured: {screenshot.shape}")
            
            # 获取匹配阈值
            threshold = self.config.get('match_threshold', 0.8)
            
            # 识别副本图片
            dungeon_found = None
            dungeon_position = None
            
            for dungeon in self.config.get('dungeons', []):
                template_name = f"dungeon_{dungeon['key']}"
                found, position, confidence = self.image_recognition.match_template(
                    screenshot, template_name, threshold
                )
                
                if found:
                    print(f"[INFO] Found dungeon: {dungeon['name']} at {position} (confidence: {confidence:.3f})")
                    dungeon_found = dungeon
                    dungeon_position = position
                    self.statistics['current_dungeon'] = dungeon['name']
                    break
            
            # 识别开始挑战按钮
            challenge_found = False
            challenge_position = None
            
            found, position, confidence = self.image_recognition.match_template(
                screenshot, 'start_challenge', threshold
            )
            
            if found:
                print(f"[INFO] Found start challenge button at {position} (confidence: {confidence:.3f})")
                challenge_found = True
                challenge_position = position
            
            # 执行点击逻辑
            if dungeon_found and challenge_found:
                print(f"[INFO] Both dungeon and challenge button found, executing click sequence...")
                self._execute_click_sequence(dungeon_position, challenge_position, dungeon_found)
            elif dungeon_found:
                print(f"[INFO] Only dungeon found: {dungeon_found['name']}")
            elif challenge_found:
                print(f"[INFO] Only challenge button found")
            else:
                print(f"[DEBUG] No targets found in current screenshot")
                self.statistics['current_dungeon'] = None
            
            # 发送识别结果
            if self.result_callback:
                self.result_callback({
                    'found': dungeon_found is not None or challenge_found,
                    'dungeon': dungeon_found,
                    'startChallenge': challenge_found,
                    'clickPosition': dungeon_position if dungeon_found else challenge_position if challenge_found else None
                })
                
        except Exception as e:
            print(f"[ERROR] Recognition failed: {e}")
            if self.error_callback:
                self.error_callback({
                    'message': str(e),
                    'critical': False
                })
                
    def _execute_click_sequence(self, dungeon_position: Tuple[int, int], 
                               challenge_position: Tuple[int, int], dungeon_info: Dict):
        """
        执行点击序列：先点击副本，再点击开始挑战
        
        Args:
            dungeon_position: 副本图片位置
            challenge_position: 开始挑战按钮位置
            dungeon_info: 副本信息
        """
        try:
            click_delay = self.config.get('click_delay', 500) / 1000.0  # 转换为秒
            
            print(f"[INFO] Executing click sequence for {dungeon_info['name']} dungeon")
            
            # 第一步：点击副本图片
            print(f"[INFO] Step 1: Clicking dungeon at {dungeon_position}")
            success = self.human_mouse.click(dungeon_position[0], dungeon_position[1])
            
            if success:
                print(f"[OK] Dungeon clicked successfully")
                self.statistics['click_count'] += 1
                
                # 等待点击延迟
                time.sleep(click_delay)
                
                # 第二步：点击开始挑战按钮
                print(f"[INFO] Step 2: Clicking start challenge at {challenge_position}")
                success = self.human_mouse.click(challenge_position[0], challenge_position[1])
                
                if success:
                    print(f"[OK] Start challenge clicked successfully")
                    self.statistics['click_count'] += 1
                    print(f"[SUCCESS] Click sequence completed for {dungeon_info['name']} dungeon")
                else:
                    print(f"[ERROR] Failed to click start challenge button")
            else:
                print(f"[ERROR] Failed to click dungeon")
                
        except Exception as e:
            print(f"[ERROR] Click sequence failed: {e}")
            
    def get_status(self) -> Dict[str, Any]:
        """
        获取系统状态
        
        Returns:
            Dict: 状态信息
        """
        running_time = 0
        if self.is_running and self.statistics['start_time'] > 0:
            running_time = int(time.time() - self.statistics['start_time'])
            
        return {
            'is_running': self.is_running,
            'current_dungeon': self.statistics.get('current_dungeon'),
            'recognition_count': self.statistics.get('recognition_count', 0),
            'click_count': self.statistics.get('click_count', 0),
            'running_time': running_time,
            'enabled_dungeons': len(self.config.get('dungeons', [])),
            'last_recognition_time': self.statistics.get('last_recognition_time', 0)
        }
        
    def set_callbacks(self, result_callback=None, error_callback=None):
        """
        设置回调函数
        
        Args:
            result_callback: 识别结果回调
            error_callback: 错误回调
        """
        self.result_callback = result_callback
        self.error_callback = error_callback
