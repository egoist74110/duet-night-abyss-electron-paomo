"""
窗口服务 - 负责游戏窗口的检测、连接、激活等功能
封装了所有与窗口操作相关的逻辑
"""
from typing import Dict, Any, Optional, List, Tuple
import time

from core.base_service import BaseService
from core.command_handler import BaseCommandHandler
from window_capture import WindowCapture


class WindowService(BaseService):
    """
    窗口服务 - 管理游戏窗口的所有操作
    
    职责：
    1. 窗口检测和枚举
    2. 窗口连接和设置
    3. 窗口激活和置顶
    4. 窗口状态管理
    """
    
    def __init__(self):
        """初始化窗口服务"""
        super().__init__("WindowService")
        self.window_capture: Optional[WindowCapture] = None
        self.current_window_hwnd: Optional[int] = None
        self.current_window_title: Optional[str] = None
        self.is_window_connected = False
    
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        初始化窗口服务
        
        Args:
            config: 服务配置
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            self.log("正在初始化窗口服务...", "INFO")
            
            # 创建窗口捕获实例
            self.window_capture = WindowCapture()
            
            # 设置配置
            if config:
                self.set_config(config)
            
            self.is_initialized = True
            self.log("窗口服务初始化成功", "INFO")
            return True
            
        except Exception as e:
            self.handle_error(e, "窗口服务初始化失败")
            return False
    
    def start(self) -> bool:
        """
        启动窗口服务
        
        Returns:
            bool: 启动是否成功
        """
        if not self.is_initialized:
            self.log("窗口服务未初始化，无法启动", "ERROR")
            return False
        
        try:
            self.is_running = True
            self.log("窗口服务已启动", "INFO")
            return True
            
        except Exception as e:
            self.handle_error(e, "窗口服务启动失败")
            return False
    
    def stop(self) -> bool:
        """
        停止窗口服务
        
        Returns:
            bool: 停止是否成功
        """
        try:
            # 如果有连接的窗口，先断开连接
            if self.is_window_connected:
                self.disconnect_window()
            
            self.is_running = False
            self.log("窗口服务已停止", "INFO")
            return True
            
        except Exception as e:
            self.handle_error(e, "窗口服务停止失败")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取窗口服务状态
        
        Returns:
            Dict[str, Any]: 服务状态
        """
        return {
            "service_name": self.service_name,
            "is_initialized": self.is_initialized,
            "is_running": self.is_running,
            "is_window_connected": self.is_window_connected,
            "current_window": {
                "hwnd": self.current_window_hwnd,
                "title": self.current_window_title
            } if self.is_window_connected else None,
            "platform": self.window_capture.platform if self.window_capture else None
        }
    
    def find_windows(self, keyword: str = "") -> List[Tuple[int, str]]:
        """
        查找窗口
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            List[Tuple[int, str]]: 窗口列表 (hwnd, title)
        """
        if not self.window_capture:
            self.log("窗口捕获未初始化", "ERROR")
            return []
        
        try:
            self.log(f"开始查找窗口，关键词: '{keyword}'", "INFO")
            start_time = time.time()
            
            windows = self.window_capture.find_windows(keyword)
            
            end_time = time.time()
            duration = end_time - start_time
            
            self.log(f"窗口查找完成，找到 {len(windows)} 个窗口，耗时: {duration:.2f}秒", "INFO")
            
            # 记录找到的窗口
            for i, (hwnd, title) in enumerate(windows):
                self.log(f"  窗口 {i+1}: {title} (hwnd: {hwnd})", "INFO")
            
            return windows
            
        except Exception as e:
            self.handle_error(e, "窗口查找失败")
            return []
    
    def connect_window(self, hwnd: int) -> bool:
        """
        连接到指定窗口
        
        Args:
            hwnd: 窗口句柄
            
        Returns:
            bool: 连接是否成功
        """
        if not self.window_capture:
            self.log("窗口捕获未初始化", "ERROR")
            return False
        
        try:
            self.log(f"正在连接窗口，句柄: {hwnd}", "INFO")
            
            # 设置窗口
            if self.window_capture.set_window(hwnd):
                self.current_window_hwnd = hwnd
                self.current_window_title = self.window_capture.window_title
                self.is_window_connected = True
                
                self.log(f"窗口连接成功: {self.current_window_title}", "INFO")
                return True
            else:
                self.log(f"窗口连接失败，句柄: {hwnd}", "ERROR")
                return False
                
        except Exception as e:
            self.handle_error(e, f"连接窗口失败，句柄: {hwnd}")
            return False
    
    def disconnect_window(self) -> bool:
        """
        断开当前窗口连接
        
        Returns:
            bool: 断开是否成功
        """
        try:
            if self.is_window_connected:
                # 取消窗口置顶
                if self.window_capture:
                    self.window_capture.deactivate_topmost()
                
                self.log(f"断开窗口连接: {self.current_window_title}", "INFO")
                
                self.current_window_hwnd = None
                self.current_window_title = None
                self.is_window_connected = False
            
            return True
            
        except Exception as e:
            self.handle_error(e, "断开窗口连接失败")
            return False
    
    def activate_window(self) -> bool:
        """
        激活当前窗口（置顶）
        
        Returns:
            bool: 激活是否成功
        """
        if not self.is_window_connected or not self.window_capture:
            self.log("没有连接的窗口，无法激活", "ERROR")
            return False
        
        try:
            self.log("正在激活窗口...", "INFO")
            
            success = self.window_capture.activate_window()
            
            if success:
                self.log("窗口激活成功", "INFO")
            else:
                self.log("窗口激活失败", "WARN")
            
            return success
            
        except Exception as e:
            self.handle_error(e, "窗口激活失败")
            return False
    
    def deactivate_topmost(self) -> bool:
        """
        取消窗口置顶
        
        Returns:
            bool: 取消是否成功
        """
        if not self.is_window_connected or not self.window_capture:
            self.log("没有连接的窗口，无法取消置顶", "ERROR")
            return False
        
        try:
            self.log("正在取消窗口置顶...", "INFO")
            
            success = self.window_capture.deactivate_topmost()
            
            if success:
                self.log("窗口置顶已取消", "INFO")
            else:
                self.log("取消窗口置顶失败", "WARN")
            
            return success
            
        except Exception as e:
            self.handle_error(e, "取消窗口置顶失败")
            return False
    
    def capture_window(self):
        """
        捕获当前窗口截图
        
        Returns:
            numpy.ndarray: 截图数据，失败返回None
        """
        if not self.is_window_connected or not self.window_capture:
            self.log("没有连接的窗口，无法截图", "ERROR")
            return None
        
        try:
            screenshot = self.window_capture.capture()
            
            if screenshot is not None:
                height, width = screenshot.shape[:2]
                self.log(f"窗口截图成功，尺寸: {width}x{height}", "INFO")
            else:
                self.log("窗口截图失败", "ERROR")
            
            return screenshot
            
        except Exception as e:
            self.handle_error(e, "窗口截图失败")
            return None
    
    def get_window_info(self) -> Optional[Dict[str, Any]]:
        """
        获取当前窗口信息
        
        Returns:
            Dict[str, Any]: 窗口信息，未连接返回None
        """
        if not self.is_window_connected or not self.window_capture:
            return None
        
        try:
            window_rect = self.window_capture.get_window_rect()
            
            return {
                "hwnd": self.current_window_hwnd,
                "title": self.current_window_title,
                "rect": window_rect,
                "scale_factor": getattr(self.window_capture, 'scale_factor', 1.0),
                "platform": self.window_capture.platform
            }
            
        except Exception as e:
            self.handle_error(e, "获取窗口信息失败")
            return None


class WindowCommandHandler(BaseCommandHandler):
    """
    窗口命令处理器 - 处理所有与窗口相关的命令
    """
    
    def __init__(self, window_service: WindowService):
        """
        初始化窗口命令处理器
        
        Args:
            window_service: 窗口服务实例
        """
        super().__init__("WindowCommandHandler")
        self.window_service = window_service
    
    def get_supported_actions(self) -> list:
        """获取支持的命令列表"""
        return [
            'detect_window',
            'set_window',
            'activate_window',
            'deactivate_topmost',
            'get_window_status',
            'capture_window',
            'disconnect_window'
        ]
    
    def handle_command(self, action: str, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理窗口相关命令
        
        Args:
            action: 命令名称
            cmd: 命令参数
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        if action == 'detect_window':
            return self._handle_detect_window(cmd)
        elif action == 'set_window':
            return self._handle_set_window(cmd)
        elif action == 'activate_window':
            return self._handle_activate_window(cmd)
        elif action == 'deactivate_topmost':
            return self._handle_deactivate_topmost(cmd)
        elif action == 'get_window_status':
            return self._handle_get_window_status(cmd)
        elif action == 'capture_window':
            return self._handle_capture_window(cmd)
        elif action == 'disconnect_window':
            return self._handle_disconnect_window(cmd)
        else:
            return {
                "success": False,
                "error": f"窗口命令处理器不支持命令: {action}"
            }
    
    def _handle_detect_window(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """处理窗口检测命令"""
        keyword = cmd.get('keyword', '')
        
        try:
            windows = self.window_service.find_windows(keyword)
            
            # 转换为前端需要的格式
            window_list = [{'hwnd': hwnd, 'title': title} for hwnd, title in windows]
            
            # 发送响应到前端
            self.send_response('windows_found', {
                'windows': window_list,
                'count': len(window_list),
                'search_keyword': keyword
            })
            
            return {
                "success": True,
                "windows": window_list,
                "count": len(window_list)
            }
            
        except Exception as e:
            # 发送错误响应到前端
            self.send_response('windows_found', {
                'windows': [],
                'count': 0,
                'error': str(e)
            })
            
            return {
                "success": False,
                "error": str(e)
            }
    
    def _handle_set_window(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """处理窗口设置命令"""
        hwnd = cmd.get('hwnd')
        
        if not hwnd:
            return {
                "success": False,
                "error": "缺少hwnd参数"
            }
        
        try:
            success = self.window_service.connect_window(hwnd)
            
            if success:
                window_info = self.window_service.get_window_info()
                
                # 发送成功响应到前端
                self.send_response('window_set', {
                    'hwnd': hwnd,
                    'title': window_info['title'] if window_info else 'Unknown'
                })
                
                return {
                    "success": True,
                    "window_info": window_info
                }
            else:
                # 发送失败响应到前端
                self.send_response('window_set_error', {
                    'hwnd': hwnd,
                    'error': '无效的窗口句柄或窗口未找到'
                })
                
                return {
                    "success": False,
                    "error": "窗口连接失败"
                }
                
        except Exception as e:
            # 发送错误响应到前端
            self.send_response('window_set_error', {
                'hwnd': hwnd,
                'error': str(e)
            })
            
            return {
                "success": False,
                "error": str(e)
            }
    
    def _handle_activate_window(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """处理窗口激活命令"""
        try:
            success = self.window_service.activate_window()
            
            # 发送响应到前端
            self.send_response('window_activated', {
                'success': success,
                'error': '窗口激活失败' if not success else None
            })
            
            return {
                "success": success,
                "message": "窗口激活成功" if success else "窗口激活失败"
            }
            
        except Exception as e:
            # 发送错误响应到前端
            self.send_response('window_activated', {
                'success': False,
                'error': str(e)
            })
            
            return {
                "success": False,
                "error": str(e)
            }
    
    def _handle_deactivate_topmost(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """处理取消窗口置顶命令"""
        try:
            success = self.window_service.deactivate_topmost()
            
            # 发送响应到前端
            self.send_response('topmost_deactivated', {
                'success': success,
                'error': '取消置顶失败' if not success else None
            })
            
            return {
                "success": success,
                "message": "窗口置顶已取消" if success else "取消置顶失败"
            }
            
        except Exception as e:
            # 发送错误响应到前端
            self.send_response('topmost_deactivated', {
                'success': False,
                'error': str(e)
            })
            
            return {
                "success": False,
                "error": str(e)
            }
    
    def _handle_get_window_status(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取窗口状态命令"""
        try:
            status = self.window_service.get_status()
            window_info = self.window_service.get_window_info()
            
            return {
                "success": True,
                "status": status,
                "window_info": window_info
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _handle_capture_window(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """处理窗口截图命令"""
        try:
            screenshot = self.window_service.capture_window()
            
            if screenshot is not None:
                height, width = screenshot.shape[:2]
                return {
                    "success": True,
                    "screenshot_info": {
                        "width": width,
                        "height": height,
                        "channels": screenshot.shape[2] if len(screenshot.shape) > 2 else 1
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "截图失败"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _handle_disconnect_window(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """处理断开窗口连接命令"""
        try:
            success = self.window_service.disconnect_window()
            
            return {
                "success": success,
                "message": "窗口连接已断开" if success else "断开连接失败"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }