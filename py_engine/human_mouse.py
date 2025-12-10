"""
人性化鼠标控制模块
模拟真人鼠标移动和点击
"""
import pyautogui
import random
import time
import math
import numpy as np
import platform

class HumanMouse:
    """人性化鼠标控制类"""
    
    def __init__(self):
        """初始化鼠标控制器"""
        # 设置pyautogui参数
        pyautogui.FAILSAFE = True  # 移动到屏幕角落时中止
        pyautogui.PAUSE = 0.01  # 每次调用后的暂停时间
        
        # 获取屏幕尺寸
        self.screen_width, self.screen_height = pyautogui.size()
        print(f"[INFO] Screen size: {self.screen_width}x{self.screen_height}")
        
        # 检测操作系统
        self.platform = platform.system()
        print(f"[INFO] Platform: {self.platform}")
    
    def click(self, x, y, button='left', duration=0.1):
        """
        在指定位置点击鼠标（精确版本）
        针对macOS HiDPI环境进行优化
        
        Args:
            x: X坐标
            y: Y坐标
            button: 鼠标按钮 ('left', 'right', 'middle')
            duration: 点击持续时间（秒）
            
        Returns:
            bool: 是否点击成功
        """
        try:
            print(f"[INFO] 准备精确点击位置: ({x}, {y})")
            print(f"[INFO] 屏幕尺寸: {self.screen_width}x{self.screen_height}")
            print(f"[INFO] 操作系统: {self.platform}")
            
            # 根据平台进行不同的坐标验证
            if self.platform == 'Darwin':  # macOS
                # macOS HiDPI环境下，允许坐标超出逻辑屏幕范围
                # 但仍然进行合理性检查
                max_reasonable_x = self.screen_width * 3
                max_reasonable_y = self.screen_height * 3
                
                if not (0 <= x <= max_reasonable_x and 0 <= y <= max_reasonable_y):
                    print(f"[WARN] macOS坐标超出合理范围: ({x}, {y})")
                    print(f"[WARN] 合理范围: 0-{max_reasonable_x} x 0-{max_reasonable_y}")
                    # 对于macOS，我们仍然尝试点击，因为可能是HiDPI环境
                    print(f"[INFO] macOS HiDPI环境，尝试直接点击坐标: ({x}, {y})")
                else:
                    print(f"[INFO] macOS坐标在合理范围内: ({x}, {y})")
            else:
                # 非macOS平台，使用严格的屏幕范围检查
                if not (0 <= x <= self.screen_width and 0 <= y <= self.screen_height):
                    print(f"[WARN] 坐标超出屏幕范围: ({x}, {y}), 屏幕: {self.screen_width}x{self.screen_height}")
                    # 自动调整坐标到屏幕范围内
                    x = max(0, min(x, self.screen_width - 1))
                    y = max(0, min(y, self.screen_height - 1))
                    print(f"[INFO] 坐标已调整到屏幕范围内: ({x}, {y})")
            
            # 获取当前鼠标位置
            current_x, current_y = pyautogui.position()
            print(f"[INFO] 当前鼠标位置: ({current_x}, {current_y})")
            
            # 计算移动距离
            distance = math.sqrt((x - current_x) ** 2 + (y - current_y) ** 2)
            print(f"[INFO] 需要移动距离: {distance:.1f} 像素")
            
            # 根据平台选择不同的点击策略
            if self.platform == 'Darwin':  # macOS
                print(f"[INFO] macOS平台：使用HiDPI优化的点击策略")
                
                # macOS HiDPI环境下的特殊处理
                try:
                    # 第一步：尝试直接移动到目标位置
                    print(f"[DEBUG] 第一步：直接移动到目标位置")
                    pyautogui.moveTo(x, y, duration=0.3)
                    time.sleep(0.1)
                    
                    # 验证移动结果
                    actual_x, actual_y = pyautogui.position()
                    error_x = abs(actual_x - x)
                    error_y = abs(actual_y - y)
                    print(f"[DEBUG] 移动后位置: ({actual_x}, {actual_y}), 误差: ({error_x}, {error_y})")
                    
                    # 如果误差较大，尝试分步移动
                    if error_x > 5 or error_y > 5:
                        print(f"[DEBUG] 误差较大，尝试分步移动")
                        # 分两步移动：先移动到中间位置，再移动到目标位置
                        mid_x = (current_x + x) / 2
                        mid_y = (current_y + y) / 2
                        
                        pyautogui.moveTo(mid_x, mid_y, duration=0.2)
                        time.sleep(0.05)
                        pyautogui.moveTo(x, y, duration=0.2)
                        time.sleep(0.1)
                        
                        # 再次验证
                        actual_x, actual_y = pyautogui.position()
                        error_x = abs(actual_x - x)
                        error_y = abs(actual_y - y)
                        print(f"[DEBUG] 分步移动后位置: ({actual_x}, {actual_y}), 误差: ({error_x}, {error_y})")
                    
                    # 执行点击
                    print(f"[DEBUG] 执行点击...")
                    pyautogui.click(x, y, button=button, duration=duration)
                    print(f"[OK] macOS HiDPI点击完成: ({x}, {y})")
                    
                except Exception as mac_error:
                    print(f"[WARN] macOS HiDPI点击策略失败: {mac_error}")
                    # 回退到基础点击方法
                    print(f"[INFO] 回退到基础点击方法")
                    pyautogui.click(x, y, button=button, duration=duration)
                
            else:  # Windows和其他平台
                print(f"[INFO] {self.platform}平台：使用标准点击策略")
                # 使用更直接的移动方式确保精确性
                pyautogui.moveTo(x, y, duration=0.3)
                
                # 验证移动结果
                actual_x, actual_y = pyautogui.position()
                print(f"[INFO] 移动后实际位置: ({actual_x}, {actual_y})")
                
                # 计算位置误差
                error_x = abs(actual_x - x)
                error_y = abs(actual_y - y)
                print(f"[INFO] 位置误差: X={error_x}, Y={error_y}")
                
                # 如果误差较大，尝试多次精确移动
                max_attempts = 3
                attempt = 0
                while (error_x > 2 or error_y > 2) and attempt < max_attempts:
                    attempt += 1
                    print(f"[WARN] 位置误差过大，尝试第{attempt}次精确移动...")
                    pyautogui.moveTo(x, y, duration=0.1)
                    actual_x, actual_y = pyautogui.position()
                    error_x = abs(actual_x - x)
                    error_y = abs(actual_y - y)
                    print(f"[INFO] 第{attempt}次移动后位置: ({actual_x}, {actual_y}), 误差: X={error_x}, Y={error_y}")
                
                # 执行点击
                print(f"[INFO] 执行{button}键点击...")
                pyautogui.click(button=button, duration=duration)
            
            # 点击后验证
            time.sleep(0.1)
            after_click_x, after_click_y = pyautogui.position()
            print(f"[INFO] 点击后鼠标位置: ({after_click_x}, {after_click_y})")
            
            print(f"[OK] 精确点击完成: 目标({x}, {y})")
            return True
            
        except Exception as e:
            print(f"[ERROR] 精确点击失败: {e}")
            import traceback
            print(f"[DEBUG] 错误详情: {traceback.format_exc()}")
            return False
    
    def move_to(self, x, y, duration=0.5):
        """
        人性化移动鼠标到指定位置
        
        Args:
            x: 目标X坐标
            y: 目标Y坐标
            duration: 移动持续时间（秒）
        """
        try:
            # 获取当前位置
            start_x, start_y = pyautogui.position()
            
            # 计算移动距离
            distance = math.sqrt((x - start_x) ** 2 + (y - start_y) ** 2)
            
            if distance < 5:
                # 距离很近，直接移动
                pyautogui.moveTo(x, y, duration=0.1)
                return
            
            # 生成贝塞尔曲线路径
            control_points = self.generate_bezier_points(start_x, start_y, x, y)
            curve_points = self.bezier_curve(control_points, num_points=max(10, int(distance / 20)))
            
            # 沿着曲线移动
            total_time = duration
            time_per_point = total_time / len(curve_points)
            
            for point_x, point_y in curve_points:
                pyautogui.moveTo(point_x, point_y, duration=time_per_point)
                
        except Exception as e:
            print(f"[WARN] 人性化移动失败，使用直接移动: {e}")
            # 如果人性化移动失败，使用直接移动
            pyautogui.moveTo(x, y, duration=duration)
    
    def generate_bezier_points(self, start_x, start_y, end_x, end_y):
        """
        生成贝塞尔曲线的控制点
        
        Args:
            start_x, start_y: 起始点
            end_x, end_y: 结束点
            
        Returns:
            list: 控制点列表
        """
        # 计算中间控制点，添加一些随机性
        mid_x = (start_x + end_x) / 2
        mid_y = (start_y + end_y) / 2
        
        # 添加随机偏移，使路径更自然
        offset_x = random.randint(-50, 50)
        offset_y = random.randint(-50, 50)
        
        control1_x = start_x + (mid_x - start_x) * 0.5 + offset_x
        control1_y = start_y + (mid_y - start_y) * 0.5 + offset_y
        
        control2_x = end_x - (end_x - mid_x) * 0.5 + offset_x
        control2_y = end_y - (end_y - mid_y) * 0.5 + offset_y
        
        return [
            (start_x, start_y),
            (control1_x, control1_y),
            (control2_x, control2_y),
            (end_x, end_y)
        ]
    
    def bezier_curve(self, points, num_points=50):
        """
        生成贝塞尔曲线上的点
        
        Args:
            points: 控制点列表
            num_points: 生成的点数量
            
        Returns:
            list: 曲线上的点列表
        """
        if len(points) < 2:
            return points
            
        curve = []
        n = len(points) - 1
        
        for t in np.linspace(0, 1, num_points):
            x = 0
            y = 0
            for i, (px, py) in enumerate(points):
                # 贝塞尔曲线公式
                try:
                    bernstein = (
                        math.comb(n, i) * 
                        (1 - t) ** (n - i) * 
                        t ** i
                    )
                    x += px * bernstein
                    y += py * bernstein
                except:
                    # 如果math.comb不可用，使用简化版本
                    if i == 0:
                        bernstein = (1 - t) ** n
                    elif i == n:
                        bernstein = t ** n
                    else:
                        bernstein = t * (1 - t)  # 简化版本
                    x += px * bernstein
                    y += py * bernstein
            
            curve.append((int(x), int(y)))
        
        return curve
    
    def press_key(self, key):
        """
        按下指定按键
        
        Args:
            key: 按键名称（如 'enter', 'space', 'esc' 等）
            
        Returns:
            bool: 是否按键成功
        """
        try:
            print(f"[INFO] 按下按键: {key}")
            pyautogui.press(key)
            time.sleep(0.1)
            print(f"[OK] 按键完成: {key}")
            return True
            
        except Exception as e:
            print(f"[ERROR] 按键失败: {e}")
            return False
    
    def get_mouse_position(self):
        """
        获取当前鼠标位置
        
        Returns:
            tuple: (x, y) 坐标
        """
        return pyautogui.position()
    
    def is_position_valid(self, x, y):
        """
        检查坐标是否有效
        
        Args:
            x: X坐标
            y: Y坐标
            
        Returns:
            bool: 坐标是否在屏幕范围内
        """
        return 0 <= x <= self.screen_width and 0 <= y <= self.screen_height