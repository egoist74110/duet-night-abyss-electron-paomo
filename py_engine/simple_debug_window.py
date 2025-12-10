#!/usr/bin/env python3
"""
简化的调试窗口模块
不依赖PIL，只显示文本信息和识别结果
"""

import platform
import threading
import time
import json
from datetime import datetime
import os

def check_simple_gui_support():
    """检查简单GUI支持情况"""
    try:
        import tkinter as tk
        from tkinter import ttk, scrolledtext
        return True, "简单GUI支持正常"
    except ImportError as e:
        return False, f"缺少tkinter库: {str(e)}"
    except Exception as e:
        return False, f"tkinter初始化失败: {str(e)}"

# 检查GUI支持
SIMPLE_GUI_SUPPORTED, SIMPLE_GUI_ERROR = check_simple_gui_support()

if SIMPLE_GUI_SUPPORTED:
    import tkinter as tk
    from tkinter import ttk, scrolledtext

class SimpleDebugWindow:
    """简化的调试窗口类 - 不依赖PIL"""
    
    def __init__(self, window_capture, image_recognition, human_mouse):
        """
        初始化简化调试窗口
        
        Args:
            window_capture: 窗口捕获实例
            image_recognition: 图像识别实例
            human_mouse: 鼠标控制实例
        """
        self.window_capture = window_capture
        self.image_recognition = image_recognition
        self.human_mouse = human_mouse
        
        # 窗口状态
        self.root = None
        self.is_running = False
        self.scan_thread = None
        self.scan_interval = 2.0
        
        # UI组件
        self.log_text = None
        self.status_label = None
        self.coord_labels = {}
        
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
        
    def create_window(self):
        """创建简化调试窗口界面"""
        self.root = tk.Tk()
        self.root.title("DNA Automator - 简化调试窗口")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 顶部控制面板
        self.create_control_panel(main_frame)
        
        # 中间内容区域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # 左侧：坐标信息和识别结果
        left_frame = ttk.LabelFrame(content_frame, text="系统信息", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.create_info_panel(left_frame)
        
        # 右侧：日志
        right_frame = ttk.LabelFrame(content_frame, text="实时日志", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.create_log_panel(right_frame)
        
        # 底部状态栏
        self.create_status_bar(main_frame)
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_control_panel(self, parent):
        """创建控制面板"""
        control_frame = ttk.LabelFrame(parent, text="控制面板", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 扫描控制按钮
        ttk.Button(
            control_frame, 
            text="开始实时扫描", 
            command=self.start_scanning
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            control_frame, 
            text="停止扫描", 
            command=self.stop_scanning
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            control_frame, 
            text="单次扫描", 
            command=self.single_scan
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # 扫描间隔设置
        ttk.Label(control_frame, text="扫描间隔(秒):").pack(side=tk.LEFT, padx=(20, 5))
        
        self.interval_var = tk.StringVar(value=str(self.scan_interval))
        interval_spinbox = ttk.Spinbox(
            control_frame,
            from_=0.5,
            to=10.0,
            increment=0.5,
            width=8,
            textvariable=self.interval_var,
            command=self.update_interval
        )
        interval_spinbox.pack(side=tk.LEFT, padx=(0, 10))
        
        # 清空日志按钮
        ttk.Button(
            control_frame, 
            text="清空日志", 
            command=self.clear_log
        ).pack(side=tk.RIGHT)
        
    def create_info_panel(self, parent):
        """创建信息面板"""
        # 坐标信息
        coord_frame = ttk.LabelFrame(parent, text="坐标信息", padding=10)
        coord_frame.pack(fill=tk.X, pady=(0, 10))
        
        coord_info = [
            ('屏幕尺寸', 'screen_size'),
            ('当前鼠标位置', 'mouse_pos'),
            ('窗口位置', 'window_pos'),
            ('窗口尺寸', 'window_size'),
            ('缩放因子', 'scale_factor')
        ]
        
        for i, (label, key) in enumerate(coord_info):
            ttk.Label(coord_frame, text=f"{label}:").grid(row=i, column=0, sticky=tk.W, pady=2)
            self.coord_labels[key] = ttk.Label(coord_frame, text="--")
            self.coord_labels[key].grid(row=i, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # 识别结果表格
        results_frame = ttk.LabelFrame(parent, text="识别结果", padding=5)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('目标', '状态', '位置', '置信度')
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=80)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def create_log_panel(self, parent):
        """创建日志面板"""
        self.log_text = scrolledtext.ScrolledText(
            parent, 
            wrap=tk.WORD, 
            width=50, 
            height=25,
            font=('Consolas', 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
    def create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = ttk.Label(
            status_frame, 
            text="就绪 - 点击'开始实时扫描'开始调试",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X)
        
    def update_interval(self):
        """更新扫描间隔"""
        try:
            self.scan_interval = float(self.interval_var.get())
            self.log(f"扫描间隔已更新为 {self.scan_interval} 秒")
        except ValueError:
            self.log("无效的扫描间隔值", "ERROR")
            
    def start_scanning(self):
        """开始实时扫描"""
        if self.is_running:
            self.log("扫描已在运行中", "WARN")
            return
            
        if not self.window_capture.hwnd:
            self.log("未连接游戏窗口，无法开始扫描", "ERROR")
            self.update_status("错误：未连接游戏窗口")
            return
            
        self.is_running = True
        self.scan_thread = threading.Thread(target=self.scan_loop, daemon=True)
        self.scan_thread.start()
        
        self.log("开始实时扫描...")
        self.update_status("正在实时扫描...")
        
    def stop_scanning(self):
        """停止实时扫描"""
        if not self.is_running:
            self.log("扫描未在运行", "WARN")
            return
            
        self.is_running = False
        self.log("停止实时扫描")
        self.update_status("扫描已停止")
        
    def single_scan(self):
        """执行单次扫描"""
        if not self.window_capture.hwnd:
            self.log("未连接游戏窗口，无法扫描", "ERROR")
            return
            
        self.log("执行单次扫描...")
        self.update_status("正在执行单次扫描...")
        
        threading.Thread(target=self.perform_scan, daemon=True).start()
        
    def scan_loop(self):
        """扫描循环"""
        while self.is_running:
            try:
                self.perform_scan()
                time.sleep(self.scan_interval)
            except Exception as e:
                self.log(f"扫描过程中出错: {e}", "ERROR")
                time.sleep(1)
                
    def perform_scan(self):
        """执行一次完整扫描"""
        try:
            # 更新坐标信息
            self.update_coordinate_info()
            
            # 获取截图
            screenshot = self.window_capture.capture()
            if screenshot is None:
                self.log("无法获取截图", "ERROR")
                return
                
            # 执行图像识别
            self.perform_recognition(screenshot)
            
            # 更新状态
            current_time = datetime.now().strftime("%H:%M:%S")
            if self.is_running:
                self.update_status(f"实时扫描中... 最后更新: {current_time}")
            else:
                self.update_status(f"单次扫描完成 - {current_time}")
                
        except Exception as e:
            self.log(f"扫描执行失败: {e}", "ERROR")
            
    def update_coordinate_info(self):
        """更新坐标信息显示"""
        try:
            # 屏幕尺寸
            screen_size = f"{self.human_mouse.screen_width}x{self.human_mouse.screen_height}"
            self.coord_labels['screen_size'].config(text=screen_size)
            
            # 当前鼠标位置
            mouse_pos = self.human_mouse.get_mouse_position()
            self.coord_labels['mouse_pos'].config(text=f"({mouse_pos[0]}, {mouse_pos[1]})")
            
            # 窗口信息
            window_rect = self.window_capture.get_window_rect()
            if window_rect:
                window_x, window_y, window_w, window_h = window_rect
                self.coord_labels['window_pos'].config(text=f"({window_x}, {window_y})")
                self.coord_labels['window_size'].config(text=f"{window_w}x{window_h}")
            else:
                self.coord_labels['window_pos'].config(text="--")
                self.coord_labels['window_size'].config(text="--")
                
            # 缩放因子
            scale_factor = getattr(self.window_capture, 'scale_factor', 1.0)
            self.coord_labels['scale_factor'].config(text=f"{scale_factor:.2f}")
            
        except Exception as e:
            self.log(f"更新坐标信息失败: {e}", "ERROR")
            
    def perform_recognition(self, screenshot):
        """执行图像识别"""
        # 清空之前的结果
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
            
        # 加载并识别所有模板
        for template_name, template_path in self.templates.items():
            try:
                # 构建完整路径
                script_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(script_dir)
                full_path = os.path.join(project_root, template_path)
                
                if not os.path.exists(full_path):
                    continue
                    
                # 加载模板
                template_key = f"debug_{template_name}"
                if not self.image_recognition.load_template(template_key, full_path):
                    continue
                    
                # 执行识别
                found, position, confidence = self.image_recognition.match_template(
                    screenshot, template_key, 0.6
                )
                
                # 更新结果表格
                status = "✅ 找到" if found else "❌ 未找到"
                pos_text = f"({position[0]}, {position[1]})" if found else "--"
                conf_text = f"{confidence:.3f}" if confidence > 0 else "--"
                
                # 根据结果设置颜色标签
                tag = "found" if found else "not_found"
                
                self.results_tree.insert(
                    "", tk.END,
                    values=(template_name, status, pos_text, conf_text),
                    tags=(tag,)
                )
                
                # 如果找到目标，记录日志
                if found:
                    # 计算屏幕坐标
                    screen_x, screen_y = self.window_capture.convert_relative_to_screen_coords(
                        position[0], position[1]
                    )
                    self.log(f"✅ {template_name}: 相对({position[0]}, {position[1]}) -> 屏幕({screen_x}, {screen_y}), 置信度: {confidence:.3f}")
                    
            except Exception as e:
                self.log(f"识别 {template_name} 时出错: {e}", "ERROR")
                
        # 设置表格样式
        self.results_tree.tag_configure("found", background="#e8f5e8")
        self.results_tree.tag_configure("not_found", background="#ffebee")
        
    def log(self, message, level="INFO"):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        if self.log_text:
            self.root.after(0, self._update_log_text, log_entry, level)
            
    def _update_log_text(self, log_entry, level):
        """在UI线程中更新日志文本"""
        # 设置颜色标签
        if level == "ERROR":
            tag = "error"
        elif level == "WARN":
            tag = "warn"
        elif level == "SUCCESS":
            tag = "success"
        else:
            tag = "info"
            
        # 配置标签颜色
        self.log_text.tag_configure("error", foreground="red")
        self.log_text.tag_configure("warn", foreground="orange")
        self.log_text.tag_configure("success", foreground="green")
        self.log_text.tag_configure("info", foreground="black")
        
        # 插入日志
        self.log_text.insert(tk.END, log_entry, tag)
        self.log_text.see(tk.END)
        
        # 限制日志行数
        lines = int(self.log_text.index('end-1c').split('.')[0])
        if lines > 1000:
            self.log_text.delete('1.0', '100.0')
            
    def update_status(self, status):
        """更新状态栏"""
        if self.status_label:
            self.root.after(0, lambda: self.status_label.config(text=status))
            
    def clear_log(self):
        """清空日志"""
        if self.log_text:
            self.log_text.delete('1.0', tk.END)
            self.log("日志已清空")
            
    def on_closing(self):
        """窗口关闭事件"""
        self.stop_scanning()
        if self.root:
            self.root.destroy()
            
    def show(self):
        """显示调试窗口"""
        try:
            if not self.root:
                self.create_window()
                
            self.log("简化调试窗口已启动")
            self.log(f"当前平台: {self.window_capture.platform}")
            self.log(f"已连接窗口: {self.window_capture.window_title or '未连接'}")
            self.log("注意: 此版本不显示截图，仅显示识别结果和坐标信息")
            
            # 启动窗口主循环
            self.root.mainloop()
        except Exception as e:
            print(f"[ERROR] 简化调试窗口启动失败: {e}")


def create_simple_debug_window(window_capture, image_recognition, human_mouse):
    """
    创建并显示简化调试窗口
    
    Args:
        window_capture: 窗口捕获实例
        image_recognition: 图像识别实例
        human_mouse: 鼠标控制实例
        
    Returns:
        SimpleDebugWindow: 简化调试窗口实例，如果GUI不支持则返回None
    """
    if not SIMPLE_GUI_SUPPORTED:
        print(f"[ERROR] 无法创建简化调试窗口: {SIMPLE_GUI_ERROR}")
        return None
    
    try:
        debug_window = SimpleDebugWindow(window_capture, image_recognition, human_mouse)
        
        # 在新线程中显示窗口，避免阻塞主程序
        window_thread = threading.Thread(target=debug_window.show, daemon=True)
        window_thread.start()
        
        return debug_window
    except Exception as e:
        print(f"[ERROR] 创建简化调试窗口失败: {e}")
        return None