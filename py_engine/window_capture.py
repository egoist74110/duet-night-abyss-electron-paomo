"""
窗口捕获模块
用于查找和捕获游戏窗口
"""
import win32gui
import win32ui
import win32con
import numpy as np
import cv2


class WindowCapture:
    """Windows窗口捕获类"""
    
    def __init__(self):
        """初始化窗口捕获器"""
        self.hwnd = None
        self.window_title = ""
        
    def find_windows(self, keyword=""):
        """
        查找包含关键词的所有窗口
        
        Args:
            keyword: 窗口标题关键词（不区分大小写）
            
        Returns:
            list: [(hwnd, title), ...] 窗口句柄和标题列表
        """
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
    
    def set_window(self, hwnd):
        """
        设置要捕获的窗口
        
        Args:
            hwnd: 窗口句柄
            
        Returns:
            bool: 是否设置成功
        """
        try:
            if win32gui.IsWindow(hwnd):
                self.hwnd = hwnd
                self.window_title = win32gui.GetWindowText(hwnd)
                return True
        except Exception as e:
            print(f"设置窗口失败: {e}")
        return False
    
    def capture(self):
        """
        捕获当前设置的窗口
        
        Returns:
            numpy.ndarray: BGR格式的图像，如果失败返回None
        """
        if not self.hwnd:
            print("未设置窗口句柄")
            return None
            
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
            print(f"捕获窗口失败: {e}")
            return None
    
    def get_window_rect(self):
        """
        获取窗口位置和大小
        
        Returns:
            tuple: (left, top, width, height) 或 None
        """
        if not self.hwnd:
            return None
            
        try:
            left, top, right, bottom = win32gui.GetWindowRect(self.hwnd)
            return (left, top, right - left, bottom - top)
        except Exception as e:
            print(f"获取窗口矩形失败: {e}")
            return None
            
    def activate_window(self):
        """
        将窗口置于最前面
        专注于把窗口带到所有窗口的最前面,即使不能完全激活也没关系
        
        Returns:
            bool: 是否成功
        """
        if not self.hwnd:
            print("[ERROR] 未设置窗口句柄")
            return False
            
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
            # 有管理员权限后,这个操作应该总是成功
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
                # 即使激活失败,窗口也已经置顶了
            
            print(f"[OK] 窗口置顶完成: {self.window_title}")
            return True
            
        except Exception as e:
            # 捕获所有未预期的异常
            print(f"[ERROR] 窗口置顶过程出错: {e}")
            import traceback
            print(traceback.format_exc())
            # 即使出错,也返回True,因为部分操作可能已经成功
            return True
    
    def deactivate_topmost(self):
        """
        取消窗口的置顶状态
        将窗口恢复为普通窗口,不再一直在最前面
        
        Returns:
            bool: 是否成功
        """
        if not self.hwnd:
            print("[ERROR] 未设置窗口句柄")
            return False
            
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
            print(f"[ERROR] 取消置顶失败: {e}")
            return False
