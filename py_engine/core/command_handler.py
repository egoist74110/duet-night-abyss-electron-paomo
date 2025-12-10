"""
命令处理器 - 负责处理来自Electron的所有命令
实现了命令路由、参数验证、响应处理等功能
"""
from typing import Dict, Any, Callable, Optional
from abc import ABC, abstractmethod
import json
import time


class CommandValidator:
    """
    命令验证器 - 验证命令格式和参数
    """
    
    @staticmethod
    def validate_command(cmd: Dict[str, Any]) -> tuple[bool, str]:
        """
        验证命令格式
        
        Args:
            cmd: 命令字典
            
        Returns:
            tuple[bool, str]: (是否有效, 错误信息)
        """
        if not isinstance(cmd, dict):
            return False, "命令必须是字典格式"
        
        if 'action' not in cmd:
            return False, "命令缺少action字段"
        
        action = cmd.get('action')
        if not isinstance(action, str) or not action.strip():
            return False, "action字段必须是非空字符串"
        
        return True, ""
    
    @staticmethod
    def validate_parameters(cmd: Dict[str, Any], required_params: list, optional_params: Optional[list] = None) -> tuple[bool, str]:
        """
        验证命令参数
        
        Args:
            cmd: 命令字典
            required_params: 必需参数列表
            optional_params: 可选参数列表
            
        Returns:
            tuple[bool, str]: (是否有效, 错误信息)
        """
        # 检查必需参数
        for param in required_params:
            if param not in cmd:
                return False, f"缺少必需参数: {param}"
        
        # 检查未知参数（可选）
        all_params = set(required_params + (optional_params or []))
        unknown_params = set(cmd.keys()) - all_params - {'action'}
        
        if unknown_params:
            return False, f"未知参数: {', '.join(unknown_params)}"
        
        return True, ""


class BaseCommandHandler(ABC):
    """
    命令处理器基类 - 定义命令处理的通用接口
    """
    
    def __init__(self, handler_name: str):
        """
        初始化命令处理器
        
        Args:
            handler_name: 处理器名称
        """
        self.handler_name = handler_name
        self._supported_actions = set()  # 支持的命令列表
    
    @abstractmethod
    def get_supported_actions(self) -> list:
        """
        获取支持的命令列表 - 抽象方法
        
        Returns:
            list: 支持的命令名称列表
        """
        pass
    
    @abstractmethod
    def handle_command(self, action: str, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理命令 - 抽象方法
        
        Args:
            action: 命令名称
            cmd: 命令参数
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        pass
    
    def can_handle(self, action: str) -> bool:
        """
        检查是否可以处理指定命令
        
        Args:
            action: 命令名称
            
        Returns:
            bool: 是否可以处理
        """
        if not self._supported_actions:
            self._supported_actions = set(self.get_supported_actions())
        
        return action in self._supported_actions
    
    def log(self, message: str, level: str = "INFO") -> None:
        """
        记录日志
        
        Args:
            message: 日志消息
            level: 日志级别
        """
        log_data = {
            "type": "log",
            "data": {
                "handler": self.handler_name,
                "level": level,
                "message": f"[{self.handler_name}] {message}",
                "timestamp": time.time()
            }
        }
        print(json.dumps(log_data), flush=True)
    
    def send_response(self, response_type: str, data: Dict[str, Any]) -> None:
        """
        发送响应
        
        Args:
            response_type: 响应类型
            data: 响应数据
        """
        response = {
            "type": response_type,
            "data": data,
            "handler": self.handler_name,
            "timestamp": time.time()
        }
        print(json.dumps(response), flush=True)


class CommandRouter:
    """
    命令路由器 - 负责将命令分发给对应的处理器
    """
    
    def __init__(self):
        """初始化命令路由器"""
        self._handlers: Dict[str, BaseCommandHandler] = {}  # 注册的处理器
        self._action_to_handler: Dict[str, str] = {}        # 命令到处理器的映射
        self._validator = CommandValidator()                 # 命令验证器
    
    def register_handler(self, handler: BaseCommandHandler) -> None:
        """
        注册命令处理器
        
        Args:
            handler: 命令处理器实例
        """
        handler_name = handler.handler_name
        self._handlers[handler_name] = handler
        
        # 建立命令到处理器的映射
        supported_actions = handler.get_supported_actions()
        for action in supported_actions:
            if action in self._action_to_handler:
                existing_handler = self._action_to_handler[action]
                print(f"[CommandRouter] 警告: 命令 '{action}' 已被处理器 '{existing_handler}' 注册，现在被 '{handler_name}' 覆盖", flush=True)
            
            self._action_to_handler[action] = handler_name
        
        print(f"[CommandRouter] 处理器已注册: {handler_name}, 支持 {len(supported_actions)} 个命令", flush=True)
    
    def route_command(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """
        路由命令到对应的处理器
        
        Args:
            cmd: 命令字典
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        # 1. 验证命令格式
        is_valid, error_msg = self._validator.validate_command(cmd)
        if not is_valid:
            return {
                "success": False,
                "error": f"命令格式错误: {error_msg}",
                "error_type": "validation_error"
            }
        
        action = cmd.get('action')
        
        # 2. 查找对应的处理器
        handler_name = self._action_to_handler.get(action)
        if not handler_name:
            return {
                "success": False,
                "error": f"未知命令: {action}",
                "error_type": "unknown_command",
                "supported_commands": list(self._action_to_handler.keys())
            }
        
        handler = self._handlers.get(handler_name)
        if not handler:
            return {
                "success": False,
                "error": f"处理器不存在: {handler_name}",
                "error_type": "handler_not_found"
            }
        
        # 3. 执行命令处理
        try:
            result = handler.handle_command(action, cmd)
            
            # 确保返回结果包含success字段
            if 'success' not in result:
                result['success'] = True
            
            return result
            
        except Exception as e:
            import traceback
            
            error_result = {
                "success": False,
                "error": str(e),
                "error_type": "execution_error",
                "handler": handler_name,
                "action": action,
                "traceback": traceback.format_exc()
            }
            
            # 记录错误日志
            print(f"[CommandRouter] 命令执行失败: {action}, 处理器: {handler_name}, 错误: {str(e)}", flush=True)
            print(f"[CommandRouter] 错误详情: {traceback.format_exc()}", flush=True)
            
            return error_result
    
    def get_supported_commands(self) -> Dict[str, str]:
        """
        获取所有支持的命令及其处理器
        
        Returns:
            Dict[str, str]: 命令名称到处理器名称的映射
        """
        return self._action_to_handler.copy()
    
    def get_handler_info(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有处理器的信息
        
        Returns:
            Dict[str, Dict[str, Any]]: 处理器信息
        """
        info = {}
        for handler_name, handler in self._handlers.items():
            info[handler_name] = {
                "name": handler_name,
                "supported_actions": handler.get_supported_actions(),
                "class": handler.__class__.__name__
            }
        
        return info


class SystemCommandHandler(BaseCommandHandler):
    """
    系统命令处理器 - 处理系统级别的命令
    如ping、获取状态、获取支持的命令列表等
    """
    
    def __init__(self, service_manager):
        """
        初始化系统命令处理器
        
        Args:
            service_manager: 服务管理器实例
        """
        super().__init__("SystemCommandHandler")
        self.service_manager = service_manager
    
    def get_supported_actions(self) -> list:
        """获取支持的命令列表"""
        return [
            'ping',
            'get_system_status',
            'get_supported_commands',
            'get_service_status'
        ]
    
    def handle_command(self, action: str, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理系统命令
        
        Args:
            action: 命令名称
            cmd: 命令参数
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        if action == 'ping':
            return self._handle_ping(cmd)
        elif action == 'get_system_status':
            return self._handle_get_system_status(cmd)
        elif action == 'get_supported_commands':
            return self._handle_get_supported_commands(cmd)
        elif action == 'get_service_status':
            return self._handle_get_service_status(cmd)
        else:
            return {
                "success": False,
                "error": f"系统命令处理器不支持命令: {action}"
            }
    
    def _handle_ping(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理ping命令
        
        Args:
            cmd: 命令参数
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        self.log("收到ping命令", "INFO")
        
        return {
            "success": True,
            "message": "pong",
            "timestamp": time.time(),
            "system_info": {
                "python_version": __import__('sys').version,
                "platform": __import__('platform').system()
            }
        }
    
    def _handle_get_system_status(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取系统状态
        
        Args:
            cmd: 命令参数
            
        Returns:
            Dict[str, Any]: 系统状态
        """
        import sys
        import platform
        
        status = {
            "success": True,
            "system": {
                "platform": platform.system(),
                "python_version": sys.version,
                "architecture": platform.architecture(),
                "processor": platform.processor()
            },
            "services": self.service_manager.get_all_status() if self.service_manager else {}
        }
        
        return status
    
    def _handle_get_supported_commands(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取支持的命令列表
        
        Args:
            cmd: 命令参数
            
        Returns:
            Dict[str, Any]: 支持的命令列表
        """
        # 这个方法需要访问CommandRouter，暂时返回基本信息
        return {
            "success": True,
            "message": "请使用CommandRouter.get_supported_commands()获取完整列表"
        }
    
    def _handle_get_service_status(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取服务状态
        
        Args:
            cmd: 命令参数
            
        Returns:
            Dict[str, Any]: 服务状态
        """
        if not self.service_manager:
            return {
                "success": False,
                "error": "服务管理器未初始化"
            }
        
        return {
            "success": True,
            "services": self.service_manager.get_all_status()
        }