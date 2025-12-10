"""
脚本服务 - 负责游戏自动化脚本的执行和管理
封装了脚本的生命周期管理、状态监控等功能
"""
from typing import Dict, Any, Optional, Callable
import threading
import time

from core.base_service import BaseService
from core.command_handler import BaseCommandHandler


class ScriptService(BaseService):
    """
    脚本服务 - 管理游戏自动化脚本的执行
    
    职责：
    1. 脚本生命周期管理（启动、停止、暂停）
    2. 脚本状态监控和报告
    3. 脚本配置管理
    4. 脚本执行统计
    """
    
    def __init__(self):
        """初始化脚本服务"""
        super().__init__("ScriptService")
        
        # 脚本执行相关
        self.script_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        
        # 脚本状态
        self.script_running = False
        self.script_paused = False
        self.current_script_name = ""
        
        # 脚本统计
        self.start_time: Optional[float] = None
        self.total_iterations = 0
        self.successful_iterations = 0
        self.failed_iterations = 0
        
        # 脚本逻辑回调
        self.script_logic: Optional[Callable] = None
        
        # 依赖的服务
        self.window_service = None
        self.recognition_service = None
    
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        初始化脚本服务
        
        Args:
            config: 服务配置
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            self.log("正在初始化脚本服务...", "INFO")
            
            # 设置配置
            if config:
                self.set_config(config)
            
            # 重置状态
            self._reset_script_state()
            
            self.is_initialized = True
            self.log("脚本服务初始化成功", "INFO")
            return True
            
        except Exception as e:
            self.handle_error(e, "脚本服务初始化失败")
            return False
    
    def start(self) -> bool:
        """
        启动脚本服务（不是启动脚本执行）
        
        Returns:
            bool: 启动是否成功
        """
        if not self.is_initialized:
            self.log("脚本服务未初始化，无法启动", "ERROR")
            return False
        
        try:
            self.is_running = True
            self.log("脚本服务已启动", "INFO")
            return True
            
        except Exception as e:
            self.handle_error(e, "脚本服务启动失败")
            return False
    
    def stop(self) -> bool:
        """
        停止脚本服务
        
        Returns:
            bool: 停止是否成功
        """
        try:
            # 如果有脚本在运行，先停止脚本
            if self.script_running:
                self.stop_script()
            
            self.is_running = False
            self.log("脚本服务已停止", "INFO")
            return True
            
        except Exception as e:
            self.handle_error(e, "脚本服务停止失败")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取脚本服务状态
        
        Returns:
            Dict[str, Any]: 服务状态
        """
        runtime = time.time() - self.start_time if self.start_time else 0
        
        return {
            "service_name": self.service_name,
            "is_initialized": self.is_initialized,
            "is_running": self.is_running,
            "script_status": {
                "running": self.script_running,
                "paused": self.script_paused,
                "current_script": self.current_script_name,
                "runtime_seconds": runtime,
                "statistics": {
                    "total_iterations": self.total_iterations,
                    "successful_iterations": self.successful_iterations,
                    "failed_iterations": self.failed_iterations,
                    "success_rate": (self.successful_iterations / max(self.total_iterations, 1)) * 100
                }
            }
        }
    
    def set_dependencies(self, window_service=None, recognition_service=None):
        """
        设置依赖的服务
        
        Args:
            window_service: 窗口服务实例
            recognition_service: 图像识别服务实例
        """
        self.window_service = window_service
        self.recognition_service = recognition_service
        self.log("服务依赖已设置", "INFO")
    
    def set_script_logic(self, script_logic: Callable):
        """
        设置脚本逻辑回调函数
        
        Args:
            script_logic: 脚本逻辑函数
        """
        self.script_logic = script_logic
        self.log("脚本逻辑已设置", "INFO")
    
    def start_script(self, script_name: str = "default") -> bool:
        """
        启动脚本执行
        
        Args:
            script_name: 脚本名称
            
        Returns:
            bool: 启动是否成功
        """
        if self.script_running:
            self.log("脚本已在运行中", "WARN")
            return False
        
        if not self.script_logic:
            self.log("脚本逻辑未设置，无法启动", "ERROR")
            return False
        
        try:
            self.log(f"正在启动脚本: {script_name}", "INFO")
            
            # 重置状态和统计
            self._reset_script_state()
            self.current_script_name = script_name
            self.start_time = time.time()
            
            # 创建并启动脚本线程
            self.script_thread = threading.Thread(
                target=self._script_main_loop,
                name=f"ScriptThread-{script_name}",
                daemon=True
            )
            self.script_thread.start()
            
            self.script_running = True
            self.log(f"脚本启动成功: {script_name}", "INFO")
            return True
            
        except Exception as e:
            self.handle_error(e, f"脚本启动失败: {script_name}")
            return False
    
    def stop_script(self) -> bool:
        """
        停止脚本执行
        
        Returns:
            bool: 停止是否成功
        """
        if not self.script_running:
            self.log("脚本未在运行", "WARN")
            return True
        
        try:
            self.log("正在停止脚本...", "INFO")
            
            # 设置停止事件
            self.stop_event.set()
            
            # 等待脚本线程结束（最多等待5秒）
            if self.script_thread and self.script_thread.is_alive():
                self.script_thread.join(timeout=5.0)
                
                if self.script_thread.is_alive():
                    self.log("脚本线程未能正常停止", "WARN")
                else:
                    self.log("脚本线程已正常停止", "INFO")
            
            # 重置状态
            self.script_running = False
            self.script_paused = False
            self.script_thread = None
            
            self.log("脚本已停止", "INFO")
            return True
            
        except Exception as e:
            self.handle_error(e, "脚本停止失败")
            return False
    
    def pause_script(self) -> bool:
        """
        暂停脚本执行
        
        Returns:
            bool: 暂停是否成功
        """
        if not self.script_running:
            self.log("脚本未在运行，无法暂停", "WARN")
            return False
        
        if self.script_paused:
            self.log("脚本已处于暂停状态", "WARN")
            return True
        
        try:
            self.pause_event.set()
            self.script_paused = True
            self.log("脚本已暂停", "INFO")
            return True
            
        except Exception as e:
            self.handle_error(e, "脚本暂停失败")
            return False
    
    def resume_script(self) -> bool:
        """
        恢复脚本执行
        
        Returns:
            bool: 恢复是否成功
        """
        if not self.script_running:
            self.log("脚本未在运行，无法恢复", "WARN")
            return False
        
        if not self.script_paused:
            self.log("脚本未处于暂停状态", "WARN")
            return True
        
        try:
            self.pause_event.clear()
            self.script_paused = False
            self.log("脚本已恢复", "INFO")
            return True
            
        except Exception as e:
            self.handle_error(e, "脚本恢复失败")
            return False
    
    def _reset_script_state(self):
        """重置脚本状态和统计"""
        self.stop_event.clear()
        self.pause_event.clear()
        self.script_running = False
        self.script_paused = False
        self.current_script_name = ""
        self.start_time = None
        self.total_iterations = 0
        self.successful_iterations = 0
        self.failed_iterations = 0
    
    def _script_main_loop(self):
        """
        脚本主循环 - 在独立线程中运行
        """
        self.log("脚本主循环开始", "INFO")
        
        try:
            while not self.stop_event.is_set():
                # 检查暂停状态
                if self.pause_event.is_set():
                    self.log("脚本已暂停，等待恢复...", "INFO")
                    while self.pause_event.is_set() and not self.stop_event.is_set():
                        time.sleep(0.1)
                    
                    if self.stop_event.is_set():
                        break
                    
                    self.log("脚本已恢复执行", "INFO")
                
                # 执行一次脚本迭代
                try:
                    self.total_iterations += 1
                    
                    # 调用脚本逻辑
                    if self.script_logic:
                        success = self.script_logic(self)
                        
                        if success:
                            self.successful_iterations += 1
                        else:
                            self.failed_iterations += 1
                    
                    # 记录进度
                    if self.total_iterations % 10 == 0:  # 每10次迭代记录一次
                        success_rate = (self.successful_iterations / self.total_iterations) * 100
                        self.log(f"脚本执行进度: 第{self.total_iterations}次迭代，成功率: {success_rate:.1f}%", "INFO")
                
                except Exception as e:
                    self.failed_iterations += 1
                    self.handle_error(e, f"脚本迭代失败 (第{self.total_iterations}次)")
                
                # 检查是否需要停止
                if self.stop_event.wait(timeout=2.0):  # 每2秒检查一次
                    break
        
        except Exception as e:
            self.handle_error(e, "脚本主循环异常")
        
        finally:
            self.log("脚本主循环结束", "INFO")


class ScriptCommandHandler(BaseCommandHandler):
    """
    脚本命令处理器 - 处理所有与脚本执行相关的命令
    """
    
    def __init__(self, script_service: ScriptService):
        """
        初始化脚本命令处理器
        
        Args:
            script_service: 脚本服务实例
        """
        super().__init__("ScriptCommandHandler")
        self.script_service = script_service
    
    def get_supported_actions(self) -> list:
        """获取支持的命令列表"""
        return [
            'start_script',
            'stop_script',
            'pause_script',
            'resume_script',
            'get_script_status',
            'set_script_config'
        ]
    
    def handle_command(self, action: str, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理脚本相关命令
        
        Args:
            action: 命令名称
            cmd: 命令参数
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        if action == 'start_script':
            return self._handle_start_script(cmd)
        elif action == 'stop_script':
            return self._handle_stop_script(cmd)
        elif action == 'pause_script':
            return self._handle_pause_script(cmd)
        elif action == 'resume_script':
            return self._handle_resume_script(cmd)
        elif action == 'get_script_status':
            return self._handle_get_script_status(cmd)
        elif action == 'set_script_config':
            return self._handle_set_script_config(cmd)
        else:
            return {
                "success": False,
                "error": f"脚本命令处理器不支持命令: {action}"
            }
    
    def _handle_start_script(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """处理启动脚本命令"""
        script_name = cmd.get('script_name', 'default')
        
        try:
            success = self.script_service.start_script(script_name)
            
            return {
                "success": success,
                "message": f"脚本启动{'成功' if success else '失败'}: {script_name}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _handle_stop_script(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """处理停止脚本命令"""
        try:
            success = self.script_service.stop_script()
            
            return {
                "success": success,
                "message": f"脚本停止{'成功' if success else '失败'}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _handle_pause_script(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """处理暂停脚本命令"""
        try:
            success = self.script_service.pause_script()
            
            return {
                "success": success,
                "message": f"脚本暂停{'成功' if success else '失败'}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _handle_resume_script(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """处理恢复脚本命令"""
        try:
            success = self.script_service.resume_script()
            
            return {
                "success": success,
                "message": f"脚本恢复{'成功' if success else '失败'}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _handle_get_script_status(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取脚本状态命令"""
        try:
            status = self.script_service.get_status()
            
            return {
                "success": True,
                "status": status
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _handle_set_script_config(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """处理设置脚本配置命令"""
        config = cmd.get('config', {})
        
        try:
            self.script_service.set_config(config)
            
            return {
                "success": True,
                "message": "脚本配置已更新"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }