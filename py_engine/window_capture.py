"""
窗口捕获模块
用于查找和捕获游戏窗口
跨平台支持: Windows, macOS, Linux
"""
import sys
import platform
import numpy as np
import cv2

# 根据操作系统导入不同的模块
if platform.system() == 'Windows':
    try:
        import win32gui
        import win32ui
        import win32con
        PLATFORM = 'windows'
    except ImportError:
        print("[WARN] Windows API modules not available, falling back to cross-platform mode")
        PLATFORM = 'cross_platform'
elif platform.system() == 'Darwin':  # macOS
    try:
        import pyautogui
        import subprocess
        PLATFORM = 'macos'
    except ImportError:
        print("[WARN] macOS modules not available, falling back to cross-platform mode")
        PLATFORM = 'cross_platform'
else:  # Linux and others
    try:
        import pyautogui
        PLATFORM = 'linux'
    except ImportError:
        print("[WARN] Linux modules not available, falling back to cross-platform mode")
        PLATFORM = 'cross_platform'

print(f"[INFO] Window capture platform: {PLATFORM}")


class WindowCapture:
    """跨平台窗口捕获类"""
    
    def __init__(self):
        """初始化窗口捕获器"""
        self.hwnd = None
        self.window_title = ""
        self.platform = PLATFORM
        print(f"[INFO] WindowCapture initialized for platform: {self.platform}")
        
    def find_windows(self, keyword=""):
        """
        查找包含关键词的所有窗口
        
        Args:
            keyword: 窗口标题关键词（不区分大小写）
            
        Returns:
            list: [(hwnd, title), ...] 窗口句柄和标题列表
        """
        if self.platform == 'windows':
            return self._find_windows_windows(keyword)
        elif self.platform == 'macos':
            return self._find_windows_macos(keyword)
        else:
            return self._find_windows_cross_platform(keyword)
    
    def _find_windows_windows(self, keyword=""):
        """Windows平台窗口查找"""
        windows = []
        
        def callback(hwnd, windows_list):
            """枚举窗口回调函数"""
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                if window_text and (not keyword or keyword.lower() in window_text.lower()):
                    windows_list.append((hwnd, window_text))
            return True
        
        win32gui.EnumWindows(callback, windows)
        return windows
    
    def _find_windows_macos(self, keyword=""):
        """macOS平台窗口查找"""
        try:
            print(f"[INFO] macOS窗口检测开始，搜索关键词: '{keyword}'")
            
            # 改进的AppleScript，返回更易解析的格式
            script = '''
            tell application "System Events"
                set windowList to {}
                set processCount to 0
                set windowCount to 0
                
                repeat with proc in (every process whose background only is false)
                    set processCount to processCount + 1
                    try
                        repeat with win in (every window of proc)
                            set windowCount to windowCount + 1
                            set windowName to name of win as string
                            if windowName is not "" then
                                set windowList to windowList & {windowName}
                            end if
                        end repeat
                    on error
                        -- 忽略无法访问的进程
                    end try
                end repeat
                
                -- 返回统计信息和窗口列表
                set AppleScript's text item delimiters to "|||"
                set windowListString to windowList as string
                set AppleScript's text item delimiters to ""
                
                return "STATS:" & processCount & ":" & windowCount & "|||" & windowListString
            end tell
            '''
            
            print("[INFO] 执行AppleScript获取窗口列表...")
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=10)
            
            print(f"[DEBUG] AppleScript返回码: {result.returncode}")
            print(f"[DEBUG] AppleScript输出: {result.stdout[:200]}...")  # 只显示前200字符
            if result.stderr:
                print(f"[DEBUG] AppleScript错误: {result.stderr}")
            
            if result.returncode == 0:
                output = result.stdout.strip()
                
                # 解析统计信息和窗口列表
                if output.startswith("STATS:"):
                    parts = output.split("|||", 1)
                    stats_part = parts[0]
                    window_part = parts[1] if len(parts) > 1 else ""
                    
                    # 解析统计信息
                    stats = stats_part.replace("STATS:", "").split(":")
                    process_count = int(stats[0]) if len(stats) > 0 else 0
                    window_count = int(stats[1]) if len(stats) > 1 else 0
                    
                    print(f"[INFO] 扫描了 {process_count} 个进程，找到 {window_count} 个窗口")
                    
                    # 解析窗口列表
                    if window_part:
                        window_titles = window_part.split("|||")
                        print(f"[DEBUG] 解析到 {len(window_titles)} 个窗口标题")
                    else:
                        window_titles = []
                        print("[DEBUG] 没有窗口标题数据")
                else:
                    # 兼容旧格式
                    window_titles = output.split(", ") if output else []
                    print(f"[DEBUG] 使用兼容模式解析，得到 {len(window_titles)} 个窗口")
                
                # 过滤和匹配窗口
                windows = []
                matched_count = 0
                
                for i, title in enumerate(window_titles):
                    title = title.strip()
                    if title and title != "":
                        if not keyword or keyword.lower() in title.lower():
                            windows.append((i, title))
                            matched_count += 1
                            print(f"[MATCH] 窗口 {i}: {title}")
                        else:
                            print(f"[SKIP] 窗口 {i}: {title}")
                
                print(f"[INFO] 匹配到 {matched_count} 个符合条件的窗口")
                return windows
            else:
                error_msg = result.stderr.strip() if result.stderr else "未知错误"
                print(f"[ERROR] AppleScript执行失败 (返回码 {result.returncode}): {error_msg}")
                
                # 检查是否是权限问题
                if "not allowed assistive access" in error_msg.lower() or "accessibility" in error_msg.lower():
                    print("[ERROR] 需要辅助功能权限！")
                    print("[HELP] 请在 系统偏好设置 > 安全性与隐私 > 隐私 > 辅助功能 中添加此应用")
                
                return []
                
        except subprocess.TimeoutExpired:
            print("[ERROR] AppleScript执行超时")
            return []
        except Exception as e:
            print(f"[ERROR] macOS窗口枚举异常: {e}")
            import traceback
            print(f"[DEBUG] 异常详情: {traceback.format_exc()}")
            return []
    
    def _find_windows_cross_platform(self, keyword=""):
        """跨平台窗口查找（基础实现）"""
        print("[WARN] Cross-platform window enumeration not fully implemented")
        # 返回一个模拟的窗口列表用于测试
        return [(1, "Test Window"), (2, "Another Window")]
    
    def set_window(self, hwnd):
        """
        设置要捕获的窗口
        
        Args:
            hwnd: 窗口句柄（在不同平台上含义不同）
            
        Returns:
            bool: 是否设置成功
        """
        if self.platform == 'windows':
            return self._set_window_windows(hwnd)
        elif self.platform == 'macos':
            return self._set_window_macos(hwnd)
        else:
            return self._set_window_cross_platform(hwnd)
    
    def _set_window_windows(self, hwnd):
        """Windows平台设置窗口"""
        try:
            if win32gui.IsWindow(hwnd):
                self.hwnd = hwnd
                self.window_title = win32gui.GetWindowText(hwnd)
                return True
        except Exception as e:
            print(f"设置窗口失败: {e}")
        return False
    
    def _set_window_macos(self, hwnd):
        """macOS平台设置窗口"""
        try:
            print(f"[INFO] macOS设置窗口，索引: {hwnd}")
            
            # 在macOS上，hwnd实际上是窗口索引
            # 我们需要重新获取窗口列表来找到对应的窗口
            windows = self._find_windows_macos("")
            print(f"[DEBUG] 重新获取窗口列表，共 {len(windows)} 个窗口")
            
            if 0 <= hwnd < len(windows):
                self.hwnd = hwnd
                self.window_title = windows[hwnd][1]
                print(f"[OK] macOS窗口设置成功: {self.window_title}")
                return True
            else:
                print(f"[ERROR] 窗口索引 {hwnd} 超出范围 (0-{len(windows)-1})")
                return False
        except Exception as e:
            print(f"[ERROR] macOS设置窗口失败: {e}")
            import traceback
            print(f"[DEBUG] 异常详情: {traceback.format_exc()}")
        return False
    
    def _set_window_cross_platform(self, hwnd):
        """跨平台设置窗口"""
        self.hwnd = hwnd
        self.window_title = f"Cross-platform Window {hwnd}"
        return True
    
    def capture(self):
        """
        捕获当前设置的窗口
        
        Returns:
            numpy.ndarray: BGR格式的图像，如果失败返回None
        """
        if self.hwnd is None:
            print("未设置窗口句柄")
            return None
            
        if self.platform == 'windows':
            return self._capture_windows()
        elif self.platform == 'macos':
            return self._capture_macos()
        else:
            return self._capture_cross_platform()
    
    def _capture_windows(self):
        """Windows平台窗口捕获"""
        try:
            # 获取窗口矩形
            left, top, right, bottom = win32gui.GetWindowRect(self.hwnd)
            width = right - left
            height = bottom - top
            
            # 获取窗口设备上下文
            hwndDC = win32gui.GetWindowDC(self.hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            
            # 创建位图对象
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)
            
            # 截图到位图
            saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)
            
            # 转换为numpy数组
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)
            img = np.frombuffer(bmpstr, dtype='uint8')
            img.shape = (height, width, 4)  # BGRA格式
            
            # 清理资源
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(self.hwnd, hwndDC)
            
            # 转换为BGR格式（OpenCV标准）
            return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
        except Exception as e:
            print(f"Windows捕获窗口失败: {e}")
            return None
    
    def _capture_macos(self):
        """macOS平台窗口捕获"""
        try:
            # 在macOS上，我们使用pyautogui进行屏幕截图
            # 注意：这会截取整个屏幕，不是特定窗口
            # 更精确的窗口捕获需要使用Quartz框架，但比较复杂
            screenshot = pyautogui.screenshot()
            # 转换为numpy数组
            img = np.array(screenshot)
            # 转换为BGR格式（OpenCV标准）
            return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        except Exception as e:
            print(f"macOS捕获窗口失败: {e}")
            return None
    
    def _capture_cross_platform(self):
        """跨平台窗口捕获"""
        try:
            # 使用pyautogui进行屏幕截图
            screenshot = pyautogui.screenshot()
            img = np.array(screenshot)
            return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        except Exception as e:
            print(f"跨平台捕获失败: {e}")
            return None
    
    def get_window_rect(self):
        """
        获取窗口位置和大小
        
        Returns:
            tuple: (left, top, width, height) 或 None
        """
        if self.hwnd is None:
            return None
            
        if self.platform == 'windows':
            return self._get_window_rect_windows()
        elif self.platform == 'macos':
            return self._get_window_rect_macos()
        else:
            return self._get_window_rect_cross_platform()
    
    def _get_window_rect_windows(self):
        """Windows平台获取窗口矩形"""
        try:
            left, top, right, bottom = win32gui.GetWindowRect(self.hwnd)
            return (left, top, right - left, bottom - top)
        except Exception as e:
            print(f"Windows获取窗口矩形失败: {e}")
            return None
    
    def _get_window_rect_macos(self):
        """macOS平台获取窗口矩形"""
        # macOS上获取特定窗口的位置比较复杂，暂时返回屏幕尺寸
        try:
            size = pyautogui.size()
            return (0, 0, size.width, size.height)
        except Exception as e:
            print(f"macOS获取窗口矩形失败: {e}")
            return None
    
    def _get_window_rect_cross_platform(self):
        """跨平台获取窗口矩形"""
        try:
            size = pyautogui.size()
            return (0, 0, size.width, size.height)
        except Exception as e:
            print(f"跨平台获取窗口矩形失败: {e}")
            return None
            
    def activate_window(self):
        """
        将窗口置于最前面
        专注于把窗口带到所有窗口的最前面,即使不能完全激活也没关系
        
        Returns:
            bool: 是否成功
        """
        if self.hwnd is None:
            print("[ERROR] 未设置窗口句柄")
            return False
            
        if self.platform == 'windows':
            return self._activate_window_windows()
        elif self.platform == 'macos':
            return self._activate_window_macos()
        else:
            return self._activate_window_cross_platform()
    
    def _activate_window_windows(self):
        """Windows平台窗口激活"""
        try:
            # 检查窗口是否存在
            if not win32gui.IsWindow(self.hwnd):
                print("[ERROR] 窗口句柄无效")
                return False
            
            print(f"[INFO] 开始置顶窗口: {self.window_title} (hwnd={self.hwnd})")
            
            # 步骤1: 如果窗口最小化，则还原
            try:
                if win32gui.IsIconic(self.hwnd):
                    print("  [1/4] 窗口已最小化,正在还原...")
                    win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
                    import time
                    time.sleep(0.15)
                else:
                    print("  [1/4] 窗口未最小化,跳过还原步骤")
            except Exception as e:
                print(f"  [1/4] 检查最小化状态失败: {e}")
            
            # 步骤2: 显示窗口
            try:
                print("  [2/4] 显示窗口...")
                win32gui.ShowWindow(self.hwnd, win32con.SW_SHOW)
            except Exception as e:
                print(f"  [2/4] 显示窗口失败: {e}")
            
            # 步骤3: 设置窗口为TOPMOST(保持置顶)
            try:
                print("  [3/4] 设置窗口为TOPMOST(保持置顶)...")
                win32gui.SetWindowPos(
                    self.hwnd,
                    win32con.HWND_TOPMOST,
                    0, 0, 0, 0,
                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
                )
                print("  [3/4] 窗口已设置为置顶状态")
            except Exception as e:
                print(f"  [3/4] SetWindowPos失败: {e}")
                print("  [提示] 请确保应用以管理员权限运行")
            
            # 步骤4: 激活窗口(获得焦点)
            try:
                print("  [4/4] 激活窗口...")
                win32gui.SetForegroundWindow(self.hwnd)
                print("  [4/4] 窗口已激活")
            except Exception as e:
                print(f"  [4/4] SetForegroundWindow失败: {e}")
            
            print(f"[OK] 窗口置顶完成: {self.window_title}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Windows窗口置顶过程出错: {e}")
            return True
    
    def _activate_window_macos(self):
        """macOS平台窗口激活"""
        try:
            print(f"[INFO] macOS窗口激活: {self.window_title}")
            
            # 在macOS上，我们使用AppleScript来激活窗口
            # 这是一个简化的实现，实际上需要更复杂的逻辑来找到特定窗口
            script = f'''
            tell application "System Events"
                try
                    set frontApp to first application process whose frontmost is true
                    set frontApp to frontmost
                    return "Window activated"
                on error
                    return "Failed to activate window"
                end try
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("[OK] macOS窗口激活完成")
                return True
            else:
                print(f"[WARN] macOS窗口激活失败: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"[ERROR] macOS窗口激活出错: {e}")
            return False
    
    def _activate_window_cross_platform(self):
        """跨平台窗口激活"""
        print("[INFO] 跨平台窗口激活（基础实现）")
        # 基础实现，总是返回成功
        return True
    
    def deactivate_topmost(self):
        """
        取消窗口的置顶状态
        将窗口恢复为普通窗口,不再一直在最前面
        
        Returns:
            bool: 是否成功
        """
        if self.hwnd is None:
            print("[ERROR] 未设置窗口句柄")
            return False
            
        if self.platform == 'windows':
            return self._deactivate_topmost_windows()
        elif self.platform == 'macos':
            return self._deactivate_topmost_macos()
        else:
            return self._deactivate_topmost_cross_platform()
    
    def _deactivate_topmost_windows(self):
        """Windows平台取消置顶"""
        try:
            if not win32gui.IsWindow(self.hwnd):
                print("[ERROR] 窗口句柄无效")
                return False
            
            print(f"[INFO] 取消窗口置顶: {self.window_title}")
            win32gui.SetWindowPos(
                self.hwnd,
                win32con.HWND_NOTOPMOST,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
            )
            print("[OK] 窗口置顶已取消")
            return True
            
        except Exception as e:
            print(f"[ERROR] Windows取消置顶失败: {e}")
            return False
    
    def _deactivate_topmost_macos(self):
        """macOS平台取消置顶"""
        print("[INFO] macOS取消窗口置顶")
        # macOS上的置顶取消逻辑
        # 由于我们的激活实现比较简单，这里也简单处理
        print("[OK] macOS窗口置顶已取消")
        return True
    
    def _deactivate_topmost_cross_platform(self):
        """跨平台取消置顶"""
        print("[INFO] 跨平台取消窗口置顶")
        return True
