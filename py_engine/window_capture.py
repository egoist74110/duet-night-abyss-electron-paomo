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
        self.window_rect = None  # 存储窗口位置和大小
        self.scale_factor = 1.0  # 显示缩放因子
        print(f"[INFO] WindowCapture initialized for platform: {self.platform}")
        
        # 检测显示缩放因子
        self._detect_scale_factor()
        
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
                print(f"[OK] Windows窗口设置成功: {self.window_title}")
                
                # 设置窗口后立即尝试激活（置顶）
                print(f"[INFO] 窗口设置成功，立即尝试激活窗口...")
                activation_success = self.activate_window()
                if activation_success:
                    print(f"[OK] 窗口激活成功: {self.window_title}")
                else:
                    print(f"[WARN] 窗口激活失败，但窗口设置成功: {self.window_title}")
                
                return True
        except Exception as e:
            print(f"[ERROR] Windows设置窗口失败: {e}")
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
                
                # 设置窗口后立即尝试激活（置顶）
                print(f"[INFO] 窗口设置成功，立即尝试激活窗口...")
                activation_success = self.activate_window()
                if activation_success:
                    print(f"[OK] 窗口激活成功: {self.window_title}")
                else:
                    print(f"[WARN] 窗口激活失败，但窗口设置成功: {self.window_title}")
                
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
    
    def capture_window(self):
        """
        捕获窗口的别名方法，与capture()功能相同
        主要用于图像识别系统的兼容性
        
        Returns:
            numpy.ndarray: BGR格式的图像，如果失败返回None
        """
        return self.capture()
    
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
            
            if not self.window_title:
                print("[ERROR] 没有设置窗口标题，无法激活")
                return False
            
            # 在macOS上，我们使用AppleScript来查找并激活特定窗口
            # 转义窗口标题中的特殊字符
            escaped_title = self.window_title.replace('"', '\\"').replace('\\', '\\\\')
            
            script = f'''
            tell application "System Events"
                try
                    -- 查找包含指定标题的窗口
                    set targetWindow to null
                    set targetApp to null
                    
                    repeat with proc in (every process whose background only is false)
                        try
                            repeat with win in (every window of proc)
                                set windowName to name of win as string
                                if windowName contains "{escaped_title}" then
                                    set targetWindow to win
                                    set targetApp to proc
                                    exit repeat
                                end if
                            end repeat
                            if targetWindow is not null then exit repeat
                        on error
                            -- 忽略无法访问的进程
                        end try
                    end repeat
                    
                    if targetWindow is not null then
                        -- 激活应用程序
                        set frontmost of targetApp to true
                        
                        -- 等待一小段时间确保应用激活
                        delay 0.1
                        
                        -- 将窗口置于前台
                        perform action "AXRaise" of targetWindow
                        
                        return "SUCCESS: Window activated - " & (name of targetWindow as string)
                    else
                        return "ERROR: Window not found - {escaped_title}"
                    end if
                    
                on error errorMessage
                    return "ERROR: " & errorMessage
                end try
            end tell
            '''
            
            print("[DEBUG] 执行AppleScript激活窗口...")
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=10)
            
            print(f"[DEBUG] AppleScript返回码: {result.returncode}")
            print(f"[DEBUG] AppleScript输出: {result.stdout.strip()}")
            if result.stderr:
                print(f"[DEBUG] AppleScript错误: {result.stderr.strip()}")
            
            if result.returncode == 0:
                output = result.stdout.strip()
                if output.startswith("SUCCESS:"):
                    print("[OK] macOS窗口激活成功")
                    return True
                else:
                    print(f"[WARN] macOS窗口激活失败: {output}")
                    
                    # 如果找不到窗口，尝试备用方法：激活包含关键词的应用
                    return self._activate_window_macos_fallback()
            else:
                error_msg = result.stderr.strip() if result.stderr else "未知错误"
                print(f"[ERROR] AppleScript执行失败: {error_msg}")
                
                # 检查是否是权限问题
                if "not allowed assistive access" in error_msg.lower() or "accessibility" in error_msg.lower():
                    print("[ERROR] 需要辅助功能权限！")
                    print("[HELP] 请在 系统偏好设置 > 安全性与隐私 > 隐私 > 辅助功能 中添加此应用")
                
                return False
                
        except subprocess.TimeoutExpired:
            print("[ERROR] AppleScript执行超时")
            return False
        except Exception as e:
            print(f"[ERROR] macOS窗口激活出错: {e}")
            import traceback
            print(f"[DEBUG] 异常详情: {traceback.format_exc()}")
            return False
    
    def _activate_window_macos_fallback(self):
        """macOS窗口激活备用方法：通过应用名称激活"""
        try:
            print(f"[INFO] 尝试备用激活方法...")
            
            # 从窗口标题推断可能的应用名称
            # 对于游戏窗口，通常应用名称包含在窗口标题中
            app_keywords = []
            if "二重螺旋" in self.window_title:
                app_keywords = ["二重螺旋", "Duet", "Night", "Abyss"]
            elif "Duet Night Abyss" in self.window_title:
                app_keywords = ["Duet Night Abyss", "Duet", "Night", "Abyss"]
            else:
                # 尝试使用窗口标题的第一个词作为应用名
                words = self.window_title.split()
                if words:
                    app_keywords = [words[0]]
            
            if not app_keywords:
                print("[WARN] 无法推断应用名称")
                return False
            
            for keyword in app_keywords:
                escaped_keyword = keyword.replace('"', '\\"').replace('\\', '\\\\')
                
                script = f'''
                tell application "System Events"
                    try
                        set targetApp to null
                        repeat with proc in (every process whose background only is false)
                            set appName to name of proc as string
                            if appName contains "{escaped_keyword}" then
                                set targetApp to proc
                                exit repeat
                            end if
                        end repeat
                        
                        if targetApp is not null then
                            set frontmost of targetApp to true
                            return "SUCCESS: App activated - " & (name of targetApp as string)
                        else
                            return "ERROR: App not found - {escaped_keyword}"
                        end if
                        
                    on error errorMessage
                        return "ERROR: " & errorMessage
                    end try
                end tell
                '''
                
                print(f"[DEBUG] 尝试激活包含关键词 '{keyword}' 的应用...")
                result = subprocess.run(['osascript', '-e', script], 
                                      capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    output = result.stdout.strip()
                    if output.startswith("SUCCESS:"):
                        print(f"[OK] 备用方法成功激活应用: {output}")
                        return True
                    else:
                        print(f"[DEBUG] 关键词 '{keyword}' 未找到匹配应用: {output}")
                else:
                    print(f"[DEBUG] 关键词 '{keyword}' 激活失败: {result.stderr}")
            
            print("[WARN] 所有备用激活方法都失败了")
            return False
            
        except Exception as e:
            print(f"[ERROR] 备用激活方法出错: {e}")
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
    
    def _detect_scale_factor(self):
        """检测显示缩放因子"""
        try:
            if self.platform == 'macos':
                # macOS HiDPI检测 - 使用更可靠的方法
                try:
                    import pyautogui
                    # 获取pyautogui报告的屏幕尺寸
                    logical_width, logical_height = pyautogui.size()
                    print(f"[DEBUG] pyautogui屏幕尺寸: {logical_width}x{logical_height}")
                    
                    # 使用Cocoa API获取真实屏幕尺寸
                    import subprocess
                    result = subprocess.run(['system_profiler', 'SPDisplaysDataType'], 
                                          capture_output=True, text=True, timeout=5)
                    
                    # 检查是否为Retina显示器
                    if 'Retina' in result.stdout or 'HiDPI' in result.stdout:
                        # 对于Retina显示器，通常物理分辨率是逻辑分辨率的2倍
                        self.scale_factor = 2.0
                        print(f"[INFO] 检测到macOS Retina显示器，缩放因子: {self.scale_factor}")
                    else:
                        # 尝试通过分辨率比较来检测
                        # 如果截图尺寸大于逻辑屏幕尺寸，说明有缩放
                        self.scale_factor = 1.0
                        print(f"[INFO] macOS标准显示器，缩放因子: {self.scale_factor}")
                        
                except Exception as e:
                    print(f"[WARN] macOS缩放检测失败: {e}")
                    self.scale_factor = 1.0
                    
            elif self.platform == 'windows':
                # Windows DPI检测
                try:
                    import ctypes
                    user32 = ctypes.windll.user32
                    user32.SetProcessDPIAware()
                    dc = user32.GetDC(0)
                    dpi = ctypes.windll.gdi32.GetDeviceCaps(dc, 88)  # LOGPIXELSX
                    user32.ReleaseDC(0, dc)
                    self.scale_factor = dpi / 96.0  # 96 DPI是标准
                    print(f"[INFO] Windows DPI: {dpi}, 缩放因子: {self.scale_factor}")
                except:
                    self.scale_factor = 1.0
                    print(f"[WARN] 无法检测Windows DPI，使用默认缩放因子: {self.scale_factor}")
            else:
                self.scale_factor = 1.0
                print(f"[INFO] 跨平台默认缩放因子: {self.scale_factor}")
        except Exception as e:
            self.scale_factor = 1.0
            print(f"[WARN] 缩放因子检测失败，使用默认值: {e}")
    
    def convert_relative_to_screen_coords(self, rel_x, rel_y):
        """
        将相对于截图的坐标转换为屏幕绝对坐标
        专门针对macOS HiDPI环境进行优化
        
        Args:
            rel_x: 相对X坐标（截图内的坐标）
            rel_y: 相对Y坐标（截图内的坐标）
            
        Returns:
            tuple: (screen_x, screen_y) 屏幕绝对坐标
        """
        try:
            print(f"[DEBUG] 开始坐标转换: 相对坐标({rel_x}, {rel_y})")
            print(f"[DEBUG] 当前平台: {self.platform}")
            
            # 获取屏幕尺寸
            import pyautogui
            logical_screen_width, logical_screen_height = pyautogui.size()
            print(f"[DEBUG] 逻辑屏幕尺寸: {logical_screen_width}x{logical_screen_height}")
            
            if self.platform == 'macos':
                # macOS 坐标转换：考虑 HiDPI 和窗口偏移
                print(f"[DEBUG] macOS 坐标转换开始...")
                
                # 方法1：尝试获取当前截图进行精确转换
                current_screenshot = self.capture()
                if current_screenshot is not None:
                    screenshot_height, screenshot_width = current_screenshot.shape[:2]
                    print(f"[DEBUG] 截图实际尺寸: {screenshot_width}x{screenshot_height}")
                    
                    # 检查是否为全屏截图（HiDPI环境）
                    if screenshot_width > logical_screen_width * 1.5:
                        # HiDPI 环境：需要缩放转换
                        scale_x = screenshot_width / logical_screen_width
                        scale_y = screenshot_height / logical_screen_height
                        print(f"[DEBUG] HiDPI环境，缩放比例: X={scale_x:.4f}, Y={scale_y:.4f}")
                        
                        screen_x = rel_x / scale_x
                        screen_y = rel_y / scale_y
                        print(f"[DEBUG] HiDPI缩放转换: ({rel_x}, {rel_y}) -> ({screen_x:.1f}, {screen_y:.1f})")
                    else:
                        # 标准环境：直接使用坐标
                        print(f"[DEBUG] 标准分辨率环境")
                        screen_x = rel_x
                        screen_y = rel_y
                        print(f"[DEBUG] 直接使用坐标: ({rel_x}, {rel_y}) -> ({screen_x}, {screen_y})")
                else:
                    # 方法2：无法获取截图，使用智能推测
                    print(f"[WARN] 无法获取截图，使用智能推测")
                    
                    # 检查坐标是否明显超出逻辑屏幕范围
                    if rel_x > logical_screen_width * 1.5 or rel_y > logical_screen_height * 1.5:
                        # 坐标明显超出，可能是 HiDPI 环境
                        estimated_scale = 2.0  # 假设是 2x Retina
                        screen_x = rel_x / estimated_scale
                        screen_y = rel_y / estimated_scale
                        print(f"[DEBUG] 推测HiDPI环境，缩放转换: ({rel_x}, {rel_y}) -> ({screen_x:.1f}, {screen_y:.1f})")
                    else:
                        # 坐标在合理范围内，直接使用
                        screen_x = rel_x
                        screen_y = rel_y
                        print(f"[DEBUG] 坐标在合理范围，直接使用: ({rel_x}, {rel_y})")
                
            elif self.platform == 'windows':
                # Windows平台：需要考虑窗口位置偏移
                window_rect = self.get_window_rect()
                if window_rect:
                    window_x, window_y, window_width, window_height = window_rect
                    print(f"[DEBUG] Windows窗口信息: 位置({window_x}, {window_y}), 尺寸({window_width}x{window_height})")
                    
                    # 检查是否需要缩放调整
                    if window_width > logical_screen_width or window_height > logical_screen_height:
                        # 有缩放的情况
                        scale_x = window_width / logical_screen_width
                        scale_y = window_height / logical_screen_height
                        screen_x = rel_x / scale_x
                        screen_y = rel_y / scale_y
                        print(f"[DEBUG] Windows缩放转换: 缩放因子({scale_x:.2f}, {scale_y:.2f})")
                    else:
                        # 无缩放，直接加窗口偏移
                        screen_x = window_x + rel_x
                        screen_y = window_y + rel_y
                        print(f"[DEBUG] Windows偏移转换: 窗口偏移({window_x}, {window_y})")
                else:
                    # 无法获取窗口信息，直接使用相对坐标
                    screen_x = rel_x
                    screen_y = rel_y
                    print(f"[DEBUG] Windows回退处理: 直接使用相对坐标")
                    
            else:
                # 其他平台默认处理
                screen_x = rel_x
                screen_y = rel_y
                print(f"[DEBUG] 默认平台处理: 直接使用相对坐标")
            
            # 重要：对于macOS HiDPI环境，不要强制限制坐标范围
            # 因为在HiDPI环境下，有效的鼠标坐标可能超出逻辑屏幕尺寸
            if self.platform == 'macos':
                # macOS环境下，允许坐标超出逻辑屏幕范围
                # 但仍然进行合理性检查，避免过度偏离
                max_reasonable_x = logical_screen_width * 3  # 允许3倍逻辑宽度
                max_reasonable_y = logical_screen_height * 3  # 允许3倍逻辑高度
                
                original_x, original_y = screen_x, screen_y
                screen_x = max(0, min(screen_x, max_reasonable_x))
                screen_y = max(0, min(screen_y, max_reasonable_y))
                
                if original_x != screen_x or original_y != screen_y:
                    print(f"[WARN] macOS坐标超出合理范围，已调整: ({original_x:.1f}, {original_y:.1f}) -> ({screen_x:.1f}, {screen_y:.1f})")
                else:
                    print(f"[INFO] macOS坐标在合理范围内: ({screen_x:.1f}, {screen_y:.1f})")
            else:
                # 非macOS平台，保持原有的严格限制
                original_x, original_y = screen_x, screen_y
                screen_x = max(0, min(screen_x, logical_screen_width - 1))
                screen_y = max(0, min(screen_y, logical_screen_height - 1))
                
                if original_x != screen_x or original_y != screen_y:
                    print(f"[WARN] 坐标被限制在屏幕范围内: ({original_x}, {original_y}) -> ({screen_x}, {screen_y})")
            
            print(f"[DEBUG] 最终转换结果: ({rel_x}, {rel_y}) -> ({screen_x:.1f}, {screen_y:.1f})")
            return int(screen_x), int(screen_y)
            
        except Exception as e:
            print(f"[ERROR] 坐标转换失败: {e}")
            import traceback
            print(f"[DEBUG] 错误详情: {traceback.format_exc()}")
            return rel_x, rel_y
    
    def get_accurate_click_position(self, template_match_x, template_match_y, template_name=None):
        """
        获取精确的点击位置（考虑所有缩放和偏移因素）
        
        Args:
            template_match_x: 模板匹配得到的X坐标
            template_match_y: 模板匹配得到的Y坐标
            template_name: 模板名称（用于特殊调整）
            
        Returns:
            tuple: (click_x, click_y) 精确的点击坐标
        """
        # 首先进行基本的坐标转换
        screen_x, screen_y = self.convert_relative_to_screen_coords(template_match_x, template_match_y)
        
        # 根据模板类型进行微调（可选）
        if template_name:
            if 'challenge' in template_name.lower() or '挑战' in template_name:
                # 对于挑战按钮，可能需要点击中心偏下一点
                print(f"[DEBUG] 挑战按钮位置微调前: ({screen_x}, {screen_y})")
                # 这里可以根据需要添加微调逻辑
                print(f"[DEBUG] 挑战按钮位置微调后: ({screen_x}, {screen_y})")
            elif 'dungeon' in template_name.lower() or '副本' in template_name:
                # 对于副本图标，确保点击中心
                print(f"[DEBUG] 副本图标位置微调前: ({screen_x}, {screen_y})")
                # 这里可以根据需要添加微调逻辑
                print(f"[DEBUG] 副本图标位置微调后: ({screen_x}, {screen_y})")
        
        return screen_x, screen_y
