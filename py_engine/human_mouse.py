"""
人性化鼠标控制模块
模拟真人鼠标移动和点击
"""
import pyautogui
import random
import time
import numpy as np
from scipy import interpolate


class HumanMouse:
    """人性化鼠标控制类"""
    
    def __init__(self):
        """初始化鼠标控制器"""
        # 设置pyautogui参数
        pyautogui.FAILSAFE = True  # 移动到屏幕角落时中止
        pyautogui.PAUSE = 0.01  # 每次调用后的暂停时间
        
    @staticmethod
    def bezier_curve(start, end, control_points=2, num_points=50):
        """
        生成贝塞尔曲线路径
        
        Args:
            start: 起点 (x, y)
            end: 终点 (x, y)
            control_points: 控制点数量
            num_points: 曲线点数
            
        Returns:
            list: [(x, y), ...] 路径点列表
        """
        # 生成控制点
        points = [start]
        
        for _ in range(control_points):
            # 在起点和终点之间随机生成控制点
            x = random.randint(
                min(start[0], end[0]) - 50,
                max(start[0], end[0]) + 50
            )
            y = random.randint(
                min(start[1], end[1]) - 50,
                max(start[1], end[1]) + 50
            )
            points.append((x, y))
        
        points.append(end)
        
        # 使用numpy计算贝塞尔曲线
        n = len(points) - 1
        curve = []
        
        for t in np.linspace(0, 1, num_points):
            x = 0
            y = 0
            for i, (px, py) in enumerate(points):
                # 贝塞尔曲线公式
                bernstein = (
                    np.math.comb(n, i) * 
                    (1 - t) ** (n - i) * 
                    t ** i
                )
                x += px * bernstein
                y += py * bernstein
            
            curve.append((int(x), int(y)))
        
        return curve
    
    @staticmethod
    def move_to(x, y, duration=None, window_offset=(0, 0)):
        """
        移动鼠标到指定位置（使用贝塞尔曲线）
        
        Args:
            x: 目标X坐标
            y: 目标Y坐标
            duration: 移动时间（秒），None则随机0.3-0.7秒
            window_offset: 窗口偏移 (offset_x, offset_y)
        """
        # 计算实际坐标（加上窗口偏移）
        target_x = x + window_offset[0]
        target_y = y + window_offset[1]
        
        # 随机移动时间
        if duration is None:
            duration = random.uniform(0.3, 0.7)
        
        # 获取当前位置
        start_x, start_y = pyautogui.position()
        
        # 生成贝塞尔曲线路径
        path = HumanMouse.bezier_curve(
            (start_x, start_y), 
            (target_x, target_y),
            control_points=random.randint(1, 3)
        )
        
        # 沿路径移动
        step_duration = duration / len(path)
        
        for point in path:
            pyautogui.moveTo(point[0], point[1])
            time.sleep(step_duration)
        
        # 确保到达目标位置
        pyautogui.moveTo(target_x, target_y)
        
        # 到达后短暂停顿
        time.sleep(random.uniform(0.05, 0.15))
    
    @staticmethod
    def click(x=None, y=None, button='left', clicks=1, window_offset=(0, 0)):
        """
        点击鼠标
        
        Args:
            x: X坐标（None则在当前位置点击）
            y: Y坐标
            button: 'left', 'right', 'middle'
            clicks: 点击次数
            window_offset: 窗口偏移
        """
        # 如果指定了坐标，先移动过去
        if x is not None and y is not None:
            HumanMouse.move_to(x, y, window_offset=window_offset)
        
        # 点击前短暂停顿
        time.sleep(random.uniform(0.05, 0.15))
        
        # 执行点击
        pyautogui.click(button=button, clicks=clicks)
        
        # 点击后短暂停顿
        time.sleep(random.uniform(0.1, 0.2))
    
    @staticmethod
    def double_click(x=None, y=None, window_offset=(0, 0)):
        """双击"""
        HumanMouse.click(x, y, clicks=2, window_offset=window_offset)
    
    @staticmethod
    def right_click(x=None, y=None, window_offset=(0, 0)):
        """右键点击"""
        HumanMouse.click(x, y, button='right', window_offset=window_offset)
    
    @staticmethod
    def drag(start_x, start_y, end_x, end_y, duration=None, window_offset=(0, 0)):
        """
        拖拽鼠标
        
        Args:
            start_x, start_y: 起点坐标
            end_x, end_y: 终点坐标
            duration: 拖拽时间
            window_offset: 窗口偏移
        """
        # 移动到起点
        HumanMouse.move_to(start_x, start_y, window_offset=window_offset)
        
        # 按下鼠标
        pyautogui.mouseDown()
        time.sleep(random.uniform(0.05, 0.1))
        
        # 移动到终点
        HumanMouse.move_to(end_x, end_y, duration=duration, window_offset=window_offset)
        
        # 释放鼠标
        time.sleep(random.uniform(0.05, 0.1))
        pyautogui.mouseUp()
    
    @staticmethod
    def get_position():
        """获取当前鼠标位置"""
        return pyautogui.position()
