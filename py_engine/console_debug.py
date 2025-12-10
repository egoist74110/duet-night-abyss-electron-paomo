#!/usr/bin/env python3
"""
控制台调试模块
不依赖任何GUI库，通过控制台输出调试信息
"""

import threading
import time
import json
from datetime import datetime
import os

class ConsoleDebugger:
    """控制台调试器类"""
    
    def __init__(self, window_capture, image_recognition, human_mouse):
        """
        初始化控制台调试器
        
        Args:
            window_capture: 窗口捕获实例
            image_recognition: 图像识别实例
            human_mouse: 鼠标控制实例
        """
        self.window_capture = window_capture
        self.image_recognition = image_recognition
        self.human_mouse = human_mouse
        
        # 调试状态
        self.is_running = False
        self.scan_thread = None
        self.scan_interval = 2.0
        
        # 模板配置
        self.templates = {
            '开始挑战': 'static/dungeon/开始挑战.png',
            '火副本': 'static/dungeon/火.png',
            '水副本': 'static/dungeon/水.png',
            '风副本': 'static/dungeon/风.png',
            '电副本': 'static/dungeon/电.png',
            '暗副本': 'static/dungeon/暗.png',
            '光副本': 'static/dungeon/光.png'
        }
        
    def log(self, message, level="INFO"):
        """输出日志到控制台"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def start_debugging(self):
        """开始控制台调试"""
        if self.is_running:
            self.log("调试已在运行中", "WARN")
            return False
            
        if not self.window_capture.hwnd:
            self.log("未连接游戏窗口，无法开始调试", "ERROR")
            return False
            
        self.is_running = True
        self.scan_thread = threading.Thread(target=self.debug_loop, daemon=True)
        self.scan_thread.start()
        
        self.log("开始控制台调试...")
        self.log("按 Ctrl+C 停止调试")
        return True
        
    def stop_debugging(self):
        """停止控制台调试"""
        if not self.is_running:
            self.log("调试未在运行", "WARN")
            return
            
        self.is_running = False
        self.log("停止控制台调试")
        
    def debug_loop(self):
        """调试循环"""
        while self.is_running:
            try:
                self.perform_debug_scan()
                time.sleep(self.scan_interval)
            except Exception as e:
                self.log(f"调试过程中出错: {e}", "ERROR")
                time.sleep(1)
                
    def perform_debug_scan(self):
        """执行一次调试扫描"""
        try:
            # 显示系统信息
            self.show_system_info()
            
            # 获取截图
            screenshot = self.window_capture.capture()
            if screenshot is None:
                self.log("无法获取截图", "ERROR")
                return
                
            height, width = screenshot.shape[:2]
            self.log(f"截图获取成功: {width}x{height}")
            
            # 执行图像识别
            self.perform_recognition(screenshot)
            
            self.log("=" * 60)
            
        except Exception as e:
            self.log(f"调试扫描失败: {e}", "ERROR")
            
    def show_system_info(self):
        """显示系统信息"""
        try:
            # 屏幕尺寸
            screen_size = f"{self.human_mouse.screen_width}x{self.human_mouse.screen_height}"
            self.log(f"屏幕尺寸: {screen_size}")
            
            # 当前鼠标位置
            mouse_pos = self.human_mouse.get_mouse_position()
            self.log(f"鼠标位置: ({mouse_pos[0]}, {mouse_pos[1]})")
            
            # 窗口信息
            window_rect = self.window_capture.get_window_rect()
            if window_rect:
                window_x, window_y, window_w, window_h = window_rect
                self.log(f"窗口位置: ({window_x}, {window_y})")
                self.log(f"窗口尺寸: {window_w}x{window_h}")
            else:
                self.log("窗口信息: 无法获取")
                
            # 缩放因子
            scale_factor = getattr(self.window_capture, 'scale_factor', 1.0)
            self.log(f"缩放因子: {scale_factor:.2f}")
            
        except Exception as e:
            self.log(f"获取系统信息失败: {e}", "ERROR")
            
    def perform_recognition(self, screenshot):
        """执行图像识别"""
        self.log("开始图像识别...")
        found_count = 0
        
        # 加载并识别所有模板
        for template_name, template_path in self.templates.items():
            try:
                # 构建完整路径
                script_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(script_dir)
                full_path = os.path.join(project_root, template_path)
                
                if not os.path.exists(full_path):
                    self.log(f"模板文件不存在: {template_path}", "WARN")
                    continue
                    
                # 加载模板
                template_key = f"console_debug_{template_name}"
                if not self.image_recognition.load_template(template_key, full_path):
                    self.log(f"模板加载失败: {template_name}", "WARN")
                    continue
                    
                # 执行识别
                found, position, confidence = self.image_recognition.match_template(
                    screenshot, template_key, 0.6
                )
                
                if found:
                    found_count += 1
                    # 计算屏幕坐标
                    screen_x, screen_y = self.window_capture.convert_relative_to_screen_coords(
                        position[0], position[1]
                    )
                    self.log(f"✅ {template_name}: 相对({position[0]}, {position[1]}) -> 屏幕({screen_x}, {screen_y}), 置信度: {confidence:.3f}", "SUCCESS")
                else:
                    self.log(f"❌ {template_name}: 未找到 (最高置信度: {confidence:.3f})")
                    
            except Exception as e:
                self.log(f"识别 {template_name} 时出错: {e}", "ERROR")
                
        self.log(f"识别完成，找到 {found_count}/{len(self.templates)} 个目标")
        
    def single_scan(self):
        """执行单次扫描"""
        if not self.window_capture.hwnd:
            self.log("未连接游戏窗口，无法扫描", "ERROR")
            return False
            
        self.log("执行单次调试扫描...")
        self.perform_debug_scan()
        return True


def create_console_debugger(window_capture, image_recognition, human_mouse):
    """
    创建控制台调试器
    
    Args:
        window_capture: 窗口捕获实例
        image_recognition: 图像识别实例
        human_mouse: 鼠标控制实例
        
    Returns:
        ConsoleDebugger: 控制台调试器实例
    """
    return ConsoleDebugger(window_capture, image_recognition, human_mouse)


def run_interactive_debug(window_capture, image_recognition, human_mouse):
    """
    运行交互式控制台调试
    """
    debugger = create_console_debugger(window_capture, image_recognition, human_mouse)
    
    print("=" * 60)
    print("DNA Automator - 控制台调试模式")
    print("=" * 60)
    print("可用命令:")
    print("  1 - 单次扫描")
    print("  2 - 开始连续扫描")
    print("  3 - 停止扫描")
    print("  4 - 显示系统信息")
    print("  q - 退出")
    print("=" * 60)
    
    try:
        while True:
            command = input("\n请输入命令 (1/2/3/4/q): ").strip().lower()
            
            if command == '1':
                debugger.single_scan()
            elif command == '2':
                if debugger.start_debugging():
                    print("连续扫描已启动，按 3 停止")
            elif command == '3':
                debugger.stop_debugging()
            elif command == '4':
                debugger.show_system_info()
            elif command == 'q':
                debugger.stop_debugging()
                print("退出调试模式")
                break
            else:
                print("无效命令，请输入 1/2/3/4/q")
                
    except KeyboardInterrupt:
        debugger.stop_debugging()
        print("\n调试已停止")
    except Exception as e:
        print(f"调试过程中出错: {e}")
        debugger.stop_debugging()


if __name__ == "__main__":
    # 如果直接运行此文件，启动交互式调试
    print("请先启动主程序并连接游戏窗口，然后使用此调试工具")