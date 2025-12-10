"""
DNA Automator Python引擎主文件 - 重构版本
采用面向对象设计，遵循SOLID原则，实现了服务化架构

架构特点：
1. 服务化架构：每个功能模块都是独立的服务
2. 命令路由：统一的命令处理和路由机制
3. 依赖注入：服务之间通过依赖注入解耦
4. 生命周期管理：统一的服务生命周期管理
5. 错误处理：完善的错误处理和日志记录
"""
import sys
import os
import json
import time

# 添加当前脚本目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# 导入核心组件
from core.base_service import ServiceManager
from core.command_handler import CommandRouter, SystemCommandHandler

# 导入服务
from services.window_service import WindowService, WindowCommandHandler
from services.script_service import ScriptService, ScriptCommandHandler

# 导入现有模块（保持兼容性）
from image_recognition import ImageRecognition, GlobalImageRecognitionSystem
from human_mouse import HumanMouse


class ProjectConfigManager:
    """
    项目配置管理器 - 负责加载和管理项目配置
    """
    
    def __init__(self):
        """初始化配置管理器"""
        self.config = None
    
    def load_config(self) -> dict:
        """
        加载项目配置文件
        
        Returns:
            dict: 项目配置
        """
        try:
            # 尝试从多个可能的路径加载配置文件
            possible_paths = [
                os.path.join(script_dir, '..', 'project.config.json'),  # 开发模式
                os.path.join(os.path.dirname(script_dir), 'project.config.json'),  # 生产模式
                os.path.join(script_dir, 'project.config.json')  # 备用路径
            ]
            
            for config_path in possible_paths:
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        self.config = json.load(f)
                        print(f"[ConfigManager] 项目配置已加载: {config_path}", flush=True)
                        print(f"[ConfigManager] 项目: {self.config.get('name', 'Unknown')} v{self.config.get('version', '0.0.0')}", flush=True)
                        return self.config
            
            print("[ConfigManager] 项目配置文件未找到，使用默认配置", flush=True)
            
        except Exception as e:
            print(f"[ConfigManager] 加载项目配置失败: {str(e)}", flush=True)
        
        # 使用默认配置
        self.config = {
            "name": "DNA Automator",
            "displayName": "Duet Night Abyss Automator",
            "version": "0.1.0"
        }
        return self.config
    
    def get_config(self) -> dict:
        """
        获取项目配置
        
        Returns:
            dict: 项目配置
        """
        if self.config is None:
            self.load_config()
        return self.config


class DNAAutomatorEngine:
    """
    DNA Automator引擎主类 - 负责整个Python后端的初始化和管理
    
    职责：
    1. 服务初始化和管理
    2. 命令路由设置
    3. 应用生命周期管理
    4. 全局错误处理
    """
    
    def __init__(self):
        """初始化DNA Automator引擎"""
        self.config_manager = ProjectConfigManager()
        self.service_manager = ServiceManager()
        self.command_router = CommandRouter()
        
        # 服务实例
        self.window_service = None
        self.script_service = None
        
        # 兼容性支持（保留原有模块）
        self.image_recognition = None
        self.human_mouse = None
        self.global_recognition_system = None
        
        # 运行状态
        self.is_initialized = False
        self.is_running = False
    
    def initialize(self) -> bool:
        """
        初始化引擎
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            print("[DNAEngine] 正在初始化DNA Automator引擎...", flush=True)
            
            # 1. 加载项目配置
            config = self.config_manager.load_config()
            
            # 2. 初始化兼容性模块
            self._initialize_legacy_modules()
            
            # 3. 创建和注册服务
            self._create_services()
            
            # 4. 注册命令处理器
            self._register_command_handlers()
            
            # 5. 初始化所有服务
            if not self.service_manager.initialize_all_services(config):
                print("[DNAEngine] 服务初始化失败", flush=True)
                return False
            
            # 6. 设置服务依赖关系
            self._setup_service_dependencies()
            
            # 7. 设置脚本逻辑
            self._setup_script_logic()
            
            self.is_initialized = True
            print("[DNAEngine] DNA Automator引擎初始化完成", flush=True)
            return True
            
        except Exception as e:
            print(f"[DNAEngine] 引擎初始化失败: {str(e)}", flush=True)
            import traceback
            print(f"[DNAEngine] 错误详情: {traceback.format_exc()}", flush=True)
            return False
    
    def start(self) -> bool:
        """
        启动引擎
        
        Returns:
            bool: 启动是否成功
        """
        if not self.is_initialized:
            print("[DNAEngine] 引擎未初始化，无法启动", flush=True)
            return False
        
        try:
            print("[DNAEngine] 正在启动引擎...", flush=True)
            
            # 启动窗口服务
            if not self.service_manager.start_service("WindowService"):
                print("[DNAEngine] 窗口服务启动失败", flush=True)
                return False
            
            # 启动脚本服务
            if not self.service_manager.start_service("ScriptService"):
                print("[DNAEngine] 脚本服务启动失败", flush=True)
                return False
            
            self.is_running = True
            print("[DNAEngine] 引擎启动成功", flush=True)
            return True
            
        except Exception as e:
            print(f"[DNAEngine] 引擎启动失败: {str(e)}", flush=True)
            return False
    
    def stop(self) -> None:
        """停止引擎"""
        try:
            print("[DNAEngine] 正在停止引擎...", flush=True)
            
            # 停止所有服务
            self.service_manager.stop_all_services()
            
            self.is_running = False
            print("[DNAEngine] 引擎已停止", flush=True)
            
        except Exception as e:
            print(f"[DNAEngine] 引擎停止失败: {str(e)}", flush=True)
    
    def process_command(self, cmd: dict) -> dict:
        """
        处理命令
        
        Args:
            cmd: 命令字典
            
        Returns:
            dict: 处理结果
        """
        if not self.is_running:
            return {
                "success": False,
                "error": "引擎未运行",
                "error_type": "engine_not_running"
            }
        
        try:
            return self.command_router.route_command(cmd)
            
        except Exception as e:
            import traceback
            
            error_result = {
                "success": False,
                "error": str(e),
                "error_type": "command_processing_error",
                "traceback": traceback.format_exc()
            }
            
            print(f"[DNAEngine] 命令处理失败: {str(e)}", flush=True)
            print(f"[DNAEngine] 错误详情: {traceback.format_exc()}", flush=True)
            
            return error_result
    
    def get_engine_status(self) -> dict:
        """
        获取引擎状态
        
        Returns:
            dict: 引擎状态
        """
        return {
            "engine": {
                "initialized": self.is_initialized,
                "running": self.is_running,
                "version": self.config_manager.get_config().get("version", "0.1.0")
            },
            "services": self.service_manager.get_all_status(),
            "commands": {
                "supported_commands": len(self.command_router.get_supported_commands()),
                "handlers": list(self.command_router.get_handler_info().keys())
            }
        }
    
    def _initialize_legacy_modules(self):
        """初始化兼容性模块（保持与原有代码的兼容性）"""
        try:
            print("[DNAEngine] 初始化兼容性模块...", flush=True)
            
            # 初始化图像识别
            self.image_recognition = ImageRecognition(backend='cpu')
            
            # 初始化鼠标控制
            self.human_mouse = HumanMouse()
            
            # 初始化全局图像识别系统（暂时保留）
            # 注意：这里需要窗口服务，所以在服务创建后再初始化
            
            print("[DNAEngine] 兼容性模块初始化完成", flush=True)
            
        except Exception as e:
            print(f"[DNAEngine] 兼容性模块初始化失败: {str(e)}", flush=True)
            raise
    
    def _create_services(self):
        """创建和注册服务"""
        try:
            print("[DNAEngine] 创建服务...", flush=True)
            
            # 创建窗口服务
            self.window_service = WindowService()
            self.service_manager.register_service(self.window_service)
            
            # 创建脚本服务
            self.script_service = ScriptService()
            self.service_manager.register_service(self.script_service, dependencies=["WindowService"])
            
            print("[DNAEngine] 服务创建完成", flush=True)
            
        except Exception as e:
            print(f"[DNAEngine] 服务创建失败: {str(e)}", flush=True)
            raise
    
    def _register_command_handlers(self):
        """注册命令处理器"""
        try:
            print("[DNAEngine] 注册命令处理器...", flush=True)
            
            # 注册系统命令处理器
            system_handler = SystemCommandHandler(self.service_manager)
            self.command_router.register_handler(system_handler)
            
            # 注册窗口命令处理器
            window_handler = WindowCommandHandler(self.window_service)
            self.command_router.register_handler(window_handler)
            
            # 注册脚本命令处理器
            script_handler = ScriptCommandHandler(self.script_service)
            self.command_router.register_handler(script_handler)
            
            print("[DNAEngine] 命令处理器注册完成", flush=True)
            
        except Exception as e:
            print(f"[DNAEngine] 命令处理器注册失败: {str(e)}", flush=True)
            raise
    
    def _setup_service_dependencies(self):
        """设置服务依赖关系"""
        try:
            print("[DNAEngine] 设置服务依赖关系...", flush=True)
            
            # 脚本服务依赖窗口服务
            self.script_service.set_dependencies(
                window_service=self.window_service,
                recognition_service=None  # 图像识别服务暂时为None
            )
            
            print("[DNAEngine] 服务依赖关系设置完成", flush=True)
            
        except Exception as e:
            print(f"[DNAEngine] 服务依赖关系设置失败: {str(e)}", flush=True)
            raise
    
    def _setup_script_logic(self):
        """设置脚本逻辑"""
        try:
            print("[DNAEngine] 设置脚本逻辑...", flush=True)
            
            # 定义默认的脚本逻辑
            def default_script_logic(script_service):
                """
                默认脚本逻辑 - 这里可以实现具体的游戏自动化逻辑
                
                Args:
                    script_service: 脚本服务实例
                    
                Returns:
                    bool: 本次迭代是否成功
                """
                try:
                    # 检查窗口连接状态
                    if not self.window_service.is_window_connected:
                        script_service.log("窗口未连接，跳过本次迭代", "WARN")
                        return False
                    
                    # 这里添加具体的游戏自动化逻辑
                    # 例如：图像识别、自动点击等
                    
                    script_service.log(f"脚本迭代执行完成 (第{script_service.total_iterations}次)", "INFO")
                    return True
                    
                except Exception as e:
                    script_service.log(f"脚本逻辑执行失败: {str(e)}", "ERROR")
                    return False
            
            # 设置脚本逻辑
            self.script_service.set_script_logic(default_script_logic)
            
            print("[DNAEngine] 脚本逻辑设置完成", flush=True)
            
        except Exception as e:
            print(f"[DNAEngine] 脚本逻辑设置失败: {str(e)}", flush=True)
            raise


def main():
    """
    主函数 - 引擎入口点
    
    职责：
    1. 创建和初始化引擎
    2. 处理来自Electron的命令
    3. 管理引擎生命周期
    """
    engine = None
    
    try:
        # 创建引擎实例
        engine = DNAAutomatorEngine()
        
        # 初始化引擎
        if not engine.initialize():
            print("[Main] 引擎初始化失败，程序退出", flush=True)
            return
        
        # 启动引擎
        if not engine.start():
            print("[Main] 引擎启动失败，程序退出", flush=True)
            return
        
        # 输出启动信息
        config = engine.config_manager.get_config()
        print(f"[Main] {config.get('name', 'DNA Automator')} Python引擎已启动", flush=True)
        print(f"[Main] 版本: {config.get('version', '0.1.0')}", flush=True)
        print(f"[Main] Python版本: {sys.version}", flush=True)
        print(f"[Main] 脚本目录: {script_dir}", flush=True)
        print("[Main] 等待来自Electron的命令...", flush=True)
        
        # 主循环 - 处理来自Electron的命令
        while True:
            try:
                # 读取来自Electron的命令
                line = sys.stdin.readline()
                if not line:
                    print("[Main] stdin已关闭，正在退出...", flush=True)
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                # 解析JSON命令
                try:
                    command = json.loads(line)
                    
                    # 处理命令
                    result = engine.process_command(command)
                    
                    # 如果命令处理失败，记录日志
                    if not result.get('success', False):
                        print(f"[Main] 命令处理失败: {command.get('action', 'unknown')}, 错误: {result.get('error', 'unknown')}", flush=True)
                    
                except json.JSONDecodeError as e:
                    print(f"[Main] 收到无效JSON: {line}, 错误: {str(e)}", flush=True)
                    
                    # 发送错误响应
                    error_response = {
                        "type": "error",
                        "data": {
                            "error": f"无效的JSON格式: {str(e)}",
                            "received": line
                        }
                    }
                    print(json.dumps(error_response), flush=True)
                
            except KeyboardInterrupt:
                print("[Main] 收到键盘中断，正在退出...", flush=True)
                break
                
            except Exception as e:
                print(f"[Main] 主循环出错: {str(e)}", flush=True)
                import traceback
                print(f"[Main] 错误详情: {traceback.format_exc()}", flush=True)
    
    except Exception as e:
        print(f"[Main] 程序启动失败: {str(e)}", flush=True)
        import traceback
        print(f"[Main] 错误详情: {traceback.format_exc()}", flush=True)
    
    finally:
        # 清理资源
        if engine:
            print("[Main] 正在清理资源...", flush=True)
            engine.stop()
        
        print("[Main] DNA Automator Python引擎已停止", flush=True)


if __name__ == "__main__":
    main()