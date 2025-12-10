import sys
import os
import json
import time
import threading

# 添加当前脚本目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# 导入自定义模块
from window_capture import WindowCapture
from image_recognition import ImageRecognition
from human_mouse import HumanMouse

# 初始化模块
window_capture = WindowCapture()
image_recognition = ImageRecognition(backend='cpu')  # 默认使用CPU，可通过命令切换
human_mouse = HumanMouse()

# 脚本运行状态
script_thread = None
stop_event = threading.Event()

# 简单的日志辅助函数
def log(message, level="INFO"):
    output = {
        "type": "log",
        "data": {
            "level": level,
            "message": message,
            "timestamp": time.time()
        }
    }
    print(json.dumps(output), flush=True)

# 脚本主循环
def script_loop():
    """
    这是脚本的主要执行逻辑
    在这里实现你的自动化脚本功能
    """
    log("Script started", "INFO")
    iteration = 0
    
    try:
        while not stop_event.is_set():
            iteration += 1
            log(f"Script running... iteration {iteration}", "INFO")
            
            # 这里添加你的脚本逻辑
            # 例如:游戏自动化、数据处理等
            
            # 每次循环检查是否需要停止
            # 使用 wait 而不是 sleep,这样可以立即响应停止信号
            if stop_event.wait(timeout=2.0):  # 每2秒执行一次循环
                break
                
    except Exception as e:
        log(f"Error in script loop: {str(e)}", "ERROR")
    finally:
        log("Script stopped", "INFO")

def start_script():
    """启动脚本"""
    global script_thread, stop_event
    
    if script_thread and script_thread.is_alive():
        log("Script is already running", "WARN")
        return
    
    # 重置停止事件
    stop_event.clear()
    
    # 创建并启动新线程
    script_thread = threading.Thread(target=script_loop, daemon=True)
    script_thread.start()
    log("Script thread started", "INFO")

def stop_script():
    """停止脚本"""
    global script_thread, stop_event
    
    if not script_thread or not script_thread.is_alive():
        log("Script is not running", "WARN")
        return
    
    # 设置停止事件
    log("Stopping script...", "INFO")
    stop_event.set()
    
    # 等待线程结束(最多等待5秒)
    script_thread.join(timeout=5.0)
    
    if script_thread.is_alive():
        log("Script thread did not stop gracefully", "WARN")
    else:
        log("Script stopped successfully", "INFO")
    
    script_thread = None

def main():
    """主函数:处理来自Electron的命令"""
    log("Python Engine Started", "INFO")
    log(f"Python version: {sys.version}", "INFO")
    log(f"Script directory: {script_dir}", "INFO")
    log("Waiting for commands from Electron...", "INFO")
    
    while True:
        try:
            # 读取来自Electron的命令
            line = sys.stdin.readline()
            if not line:
                log("stdin closed, exiting...", "INFO")
                break
            
            line = line.strip()
            if not line:
                continue
            
            log(f"Received command: {line}", "DEBUG")
                
            try:
                command = json.loads(line)
                handle_command(command)
            except json.JSONDecodeError as e:
                log(f"Invalid JSON received: {line}, error: {str(e)}", "ERROR")
                
        except KeyboardInterrupt:
            log("Received keyboard interrupt, exiting...", "INFO")
            break
        except Exception as e:
            log(f"Error in main loop: {str(e)}", "ERROR")
            import traceback
            log(f"Traceback: {traceback.format_exc()}", "ERROR")
    
    # 程序退出时确保停止脚本
    log("Shutting down Python engine...", "INFO")
    if script_thread and script_thread.is_alive():
        stop_script()
    log("Python engine stopped", "INFO")

def handle_command(cmd):
    """处理来自Electron的命令"""
    action = cmd.get('action')
    log(f"Handling command: {action}", "DEBUG")
    
    try:
        if action == 'ping':
            log("Pong from Python!", "INFO")
            
        elif action == 'start_script':
            start_script()
            
        elif action == 'stop_script':
            stop_script()
            
        elif action == 'detect_window':
            # 检测游戏窗口
            keyword = cmd.get('keyword', '')
            log(f"开始检测窗口，关键词: '{keyword}'", "INFO")
            
            try:
                # 记录开始时间
                import time
                start_time = time.time()
                
                windows = window_capture.find_windows(keyword)
                
                # 记录结束时间
                end_time = time.time()
                duration = end_time - start_time
                log(f"窗口检测完成，耗时: {duration:.2f}秒", "INFO")
                
                if windows:
                    # 返回找到的窗口列表
                    window_list = [{'hwnd': hwnd, 'title': title} for hwnd, title in windows]
                    
                    log(f"准备发送窗口列表: {len(window_list)} 个窗口", "INFO")
                    send_response({
                        'type': 'windows_found',
                        'data': {
                            'windows': window_list,
                            'count': len(window_list)
                        }
                    })
                    log(f"已发送窗口列表到前端", "INFO")
                else:
                    log("未找到任何窗口", "WARN")
                    send_response({
                        'type': 'windows_found',
                        'data': {
                            'windows': [],
                            'count': 0
                        }
                    })
                    log("已发送空窗口列表到前端", "INFO")
            except Exception as e:
                log(f"窗口检测异常: {str(e)}", "ERROR")
                import traceback
                log(f"异常详情: {traceback.format_exc()}", "ERROR")
                send_response({
                    'type': 'windows_found',
                    'data': {
                        'windows': [],
                        'count': 0,
                        'error': str(e)
                    }
                })
                log("已发送错误响应到前端", "ERROR")
        
        elif action == 'set_window':
            # 设置要捕获的窗口
            hwnd = cmd.get('hwnd')
            log(f"Setting window with hwnd: {hwnd}", "INFO")
            
            try:
                if hwnd and window_capture.set_window(hwnd):
                    send_response({
                        'type': 'window_set',
                        'data': {
                            'hwnd': hwnd,
                            'title': window_capture.window_title
                        }
                    })
                    log(f"Window set successfully: {window_capture.window_title}", "INFO")
                else:
                    log(f"Failed to set window with hwnd: {hwnd}", "ERROR")
                    send_response({
                        'type': 'window_set_error',
                        'data': {
                            'hwnd': hwnd,
                            'error': 'Invalid window handle or window not found'
                        }
                    })
            except Exception as e:
                log(f"Error setting window: {str(e)}", "ERROR")
                send_response({
                    'type': 'window_set_error',
                    'data': {
                        'hwnd': hwnd,
                        'error': str(e)
                    }
                })
        
        elif action == 'set_backend':
            # 切换图像识别后端
            backend = cmd.get('backend', 'cpu')
            global image_recognition
            image_recognition = ImageRecognition(backend=backend)
            log(f"Backend switched to: {backend}", "INFO")
        
        elif action == 'get_backend_info':
            # 获取后端信息
            info = image_recognition.get_backend_info()
            send_response({
                'type': 'backend_info',
                'data': info
            })
            log(f"Backend info: {info['backend']}", "INFO")
            
        elif action == 'activate_window':
            # 激活窗口(置顶)
            log("Activating window...", "INFO")
            if window_capture.activate_window():
                send_response({
                    'type': 'window_activated',
                    'data': {'success': True}
                })
                log("Window activated successfully", "INFO")
            else:
                send_response({
                    'type': 'window_activated',
                    'data': {'success': False, 'error': 'Failed to activate window'}
                })
                log("Failed to activate window", "WARN")
        
        elif action == 'deactivate_topmost':
            # 取消窗口置顶
            log("Deactivating window topmost...", "INFO")
            if window_capture.deactivate_topmost():
                send_response({
                    'type': 'topmost_deactivated',
                    'data': {'success': True}
                })
                log("Window topmost deactivated", "INFO")
            else:
                send_response({
                    'type': 'topmost_deactivated',
                    'data': {'success': False, 'error': 'Failed to deactivate topmost'}
                })
                log("Failed to deactivate topmost", "WARN")
            
        else:
            log(f"Unknown command: {action}", "WARN")
            
    except Exception as e:
        log(f"Error handling command '{action}': {str(e)}", "ERROR")
        import traceback
        log(f"Traceback: {traceback.format_exc()}", "ERROR")

def send_response(response):
    """发送响应到前端"""
    print(json.dumps(response), flush=True)


if __name__ == "__main__":
    main()
