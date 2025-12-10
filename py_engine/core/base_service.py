"""
基础服务类 - 所有服务的抽象基类
实现了服务的基本生命周期管理和日志功能
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import json
import time


class BaseService(ABC):
    """
    服务基类 - 定义所有服务的通用接口和行为
    
    所有具体服务都应该继承这个基类，并实现抽象方法
    这样确保了所有服务都有统一的接口和行为
    """
    
    def __init__(self, service_name: str):
        """
        初始化服务
        
        Args:
            service_name: 服务名称，用于日志标识
        """
        self.service_name = service_name  # 服务名称
        self.is_initialized = False       # 是否已初始化
        self.is_running = False          # 是否正在运行
        self._config = {}                # 服务配置
        
    @abstractmethod
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        初始化服务 - 抽象方法，子类必须实现
        
        Args:
            config: 服务配置参数
            
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    @abstractmethod
    def start(self) -> bool:
        """
        启动服务 - 抽象方法，子类必须实现
        
        Returns:
            bool: 启动是否成功
        """
        pass
    
    @abstractmethod
    def stop(self) -> bool:
        """
        停止服务 - 抽象方法，子类必须实现
        
        Returns:
            bool: 停止是否成功
        """
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        获取服务状态 - 抽象方法，子类必须实现
        
        Returns:
            Dict[str, Any]: 服务状态信息
        """
        pass
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """
        设置服务配置
        
        Args:
            config: 配置参数字典
        """
        self._config.update(config)
        self.log(f"配置已更新: {len(config)} 个参数", "INFO")
    
    def get_config(self) -> Dict[str, Any]:
        """
        获取服务配置
        
        Returns:
            Dict[str, Any]: 当前配置
        """
        return self._config.copy()
    
    def log(self, message: str, level: str = "INFO") -> None:
        """
        记录日志 - 统一的日志格式
        
        Args:
            message: 日志消息
            level: 日志级别 (INFO, WARN, ERROR, DEBUG)
        """
        log_data = {
            "type": "log",
            "data": {
                "service": self.service_name,
                "level": level,
                "message": f"[{self.service_name}] {message}",
                "timestamp": time.time()
            }
        }
        print(json.dumps(log_data), flush=True)
    
    def send_response(self, response_type: str, data: Dict[str, Any]) -> None:
        """
        发送响应到前端 - 统一的响应格式
        
        Args:
            response_type: 响应类型
            data: 响应数据
        """
        response = {
            "type": response_type,
            "data": data,
            "service": self.service_name,
            "timestamp": time.time()
        }
        print(json.dumps(response), flush=True)
    
    def handle_error(self, error: Exception, context: str = "") -> None:
        """
        统一的错误处理
        
        Args:
            error: 异常对象
            context: 错误上下文信息
        """
        import traceback
        
        error_msg = f"{context}: {str(error)}" if context else str(error)
        self.log(f"发生错误: {error_msg}", "ERROR")
        self.log(f"错误详情: {traceback.format_exc()}", "ERROR")
        
        # 发送错误响应到前端
        self.send_response("service_error", {
            "service": self.service_name,
            "error": error_msg,
            "context": context
        })


class ServiceManager:
    """
    服务管理器 - 管理所有服务的生命周期
    
    负责服务的注册、初始化、启动、停止等操作
    实现了服务之间的解耦和统一管理
    """
    
    def __init__(self):
        """初始化服务管理器"""
        self._services: Dict[str, BaseService] = {}  # 注册的服务
        self._service_dependencies: Dict[str, list] = {}  # 服务依赖关系
        
    def register_service(self, service: BaseService, dependencies: Optional[list] = None) -> None:
        """
        注册服务
        
        Args:
            service: 要注册的服务实例
            dependencies: 服务依赖列表（其他服务的名称）
        """
        service_name = service.service_name
        self._services[service_name] = service
        self._service_dependencies[service_name] = dependencies or []
        
        print(f"[ServiceManager] 服务已注册: {service_name}", flush=True)
    
    def get_service(self, service_name: str) -> Optional[BaseService]:
        """
        获取服务实例
        
        Args:
            service_name: 服务名称
            
        Returns:
            BaseService: 服务实例，如果不存在返回None
        """
        return self._services.get(service_name)
    
    def initialize_all_services(self, global_config: Optional[Dict[str, Any]] = None) -> bool:
        """
        初始化所有服务（按依赖顺序）
        
        Args:
            global_config: 全局配置
            
        Returns:
            bool: 是否全部初始化成功
        """
        global_config = global_config or {}
        
        # 按依赖顺序排序服务
        sorted_services = self._sort_services_by_dependencies()
        
        for service_name in sorted_services:
            service = self._services[service_name]
            service_config = global_config.get(service_name, {})
            
            try:
                if not service.initialize(service_config):
                    print(f"[ServiceManager] 服务初始化失败: {service_name}", flush=True)
                    return False
                    
                print(f"[ServiceManager] 服务初始化成功: {service_name}", flush=True)
                
            except Exception as e:
                print(f"[ServiceManager] 服务初始化异常: {service_name}, 错误: {str(e)}", flush=True)
                return False
        
        print("[ServiceManager] 所有服务初始化完成", flush=True)
        return True
    
    def start_service(self, service_name: str) -> bool:
        """
        启动指定服务
        
        Args:
            service_name: 服务名称
            
        Returns:
            bool: 启动是否成功
        """
        service = self._services.get(service_name)
        if not service:
            print(f"[ServiceManager] 服务不存在: {service_name}", flush=True)
            return False
        
        try:
            return service.start()
        except Exception as e:
            print(f"[ServiceManager] 启动服务失败: {service_name}, 错误: {str(e)}", flush=True)
            return False
    
    def stop_service(self, service_name: str) -> bool:
        """
        停止指定服务
        
        Args:
            service_name: 服务名称
            
        Returns:
            bool: 停止是否成功
        """
        service = self._services.get(service_name)
        if not service:
            print(f"[ServiceManager] 服务不存在: {service_name}", flush=True)
            return False
        
        try:
            return service.stop()
        except Exception as e:
            print(f"[ServiceManager] 停止服务失败: {service_name}, 错误: {str(e)}", flush=True)
            return False
    
    def stop_all_services(self) -> None:
        """停止所有服务"""
        # 按依赖关系的逆序停止服务
        sorted_services = self._sort_services_by_dependencies()
        
        for service_name in reversed(sorted_services):
            self.stop_service(service_name)
        
        print("[ServiceManager] 所有服务已停止", flush=True)
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有服务的状态
        
        Returns:
            Dict[str, Dict[str, Any]]: 所有服务的状态信息
        """
        status = {}
        for service_name, service in self._services.items():
            try:
                status[service_name] = service.get_status()
            except Exception as e:
                status[service_name] = {
                    "error": str(e),
                    "is_running": False
                }
        
        return status
    
    def _sort_services_by_dependencies(self) -> list:
        """
        按依赖关系对服务进行拓扑排序
        
        Returns:
            list: 排序后的服务名称列表
        """
        # 简单的拓扑排序实现
        visited = set()
        result = []
        
        def visit(service_name: str):
            if service_name in visited:
                return
            
            visited.add(service_name)
            
            # 先访问依赖的服务
            for dependency in self._service_dependencies.get(service_name, []):
                if dependency in self._services:
                    visit(dependency)
            
            result.append(service_name)
        
        # 访问所有服务
        for service_name in self._services:
            visit(service_name)
        
        return result