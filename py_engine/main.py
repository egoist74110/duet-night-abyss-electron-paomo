import sys
import os
import json
import time
import threading

# 添加当前脚本目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# 项目配置
project_config = None

def load_project_config():
    """加载项目配置文件"""
    global project_config
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
                    project_config = json.load(f)
                    print(f"[INFO] Project config loaded from: {config_path}", flush=True)
                    print(f"[INFO] Project: {project_config.get('name', 'Unknown')} v{project_config.get('version', '0.0.0')}", flush=True)
                    return project_config
        
        print("[WARN] Project config file not found, using defaults", flush=True)
        # 默认配置
        project_config = {
            "name": "DNA Automator",
            "displayName": "Duet Night Abyss Automator",
            "version": "0.1.0"
        }
        return project_config
        
    except Exception as e:
        print(f"[ERROR] Failed to load project config: {str(e)}", flush=True)
        # 使用默认配置
        project_config = {
            "name": "DNA Automator",
            "displayName": "Duet Night Abyss Automator",
            "version": "0.1.0"
        }
        return project_config

# 导入自定义模块
from window_capture import WindowCapture
from image_recognition import ImageRecognition, GlobalImageRecognitionSystem
from human_mouse import HumanMouse

# 初始化模块
window_capture = WindowCapture()
image_recognition = ImageRecognition(backend='cpu')  # 默认使用CPU，可通过命令切换
human_mouse = HumanMouse()

# 初始化全局图像识别系统
global_recognition_system = GlobalImageRecognitionSystem(
    window_capture=window_capture,
    human_mouse=human_mouse,
    image_recognition=image_recognition
)

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
    # 加载项目配置
    config = load_project_config()
    
    log("Python Engine Started", "INFO")
    log(f"Project: {config.get('name', 'Unknown')} v{config.get('version', '0.0.0')}", "INFO")
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
            # 检测游戏窗口 - 修复：获取所有窗口让用户选择，不进行过滤
            keyword = cmd.get('keyword', '')
            log(f"开始检测窗口，关键词: '{keyword}'", "INFO")
            
            try:
                # 记录开始时间
                start_time = time.time()
                
                # 对于手动检测，总是获取所有窗口（传入空字符串）
                # 这样用户可以看到所有可用窗口并进行选择
                search_keyword = '' if not keyword else keyword
                log(f"实际搜索关键词: '{search_keyword}'", "INFO")
                
                windows = window_capture.find_windows(search_keyword)
                
                # 记录结束时间
                end_time = time.time()
                duration = end_time - start_time
                log(f"窗口检测完成，耗时: {duration:.2f}秒", "INFO")
                
                # 总是返回窗口列表，即使为空也要让用户知道
                window_list = [{'hwnd': hwnd, 'title': title} for hwnd, title in windows]
                
                log(f"找到 {len(window_list)} 个窗口", "INFO")
                
                # 显示找到的窗口详情
                for i, window in enumerate(window_list):
                    log(f"  窗口 {i+1}: {window['title']} (hwnd: {window['hwnd']})", "INFO")
                
                send_response({
                    'type': 'windows_found',
                    'data': {
                        'windows': window_list,
                        'count': len(window_list),
                        'search_keyword': search_keyword
                    }
                })
                
                if len(window_list) > 0:
                    log(f"成功发送 {len(window_list)} 个窗口到前端", "INFO")
                else:
                    log("未找到任何窗口，但已发送空列表到前端", "WARN")
                    
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
        
        elif action == 'start_image_recognition':
            # 启动图像识别系统
            log("Starting image recognition system...", "INFO")
            
            # 设置配置
            config = {
                'dungeons': cmd.get('dungeons', []),
                'start_challenge': cmd.get('startChallenge', {}),
                'interval': cmd.get('interval', 2000),
                'accuracy': cmd.get('accuracy', 'normal'),
                'click_delay': cmd.get('clickDelay', 500),
                'match_threshold': cmd.get('matchThreshold', 0.65),
                'max_retries': cmd.get('maxRetries', 3),
                'debug_mode': cmd.get('debugMode', False)
            }
            
            global_recognition_system.set_config(config)
            
            # 设置回调函数
            def result_callback(result):
                send_response({
                    'type': 'recognition_result',
                    'data': result
                })
                
            def error_callback(error):
                send_response({
                    'type': 'recognition_error', 
                    'data': error
                })
                
            global_recognition_system.set_callbacks(result_callback, error_callback)
            
            # 启动系统
            success = global_recognition_system.start_recognition()
            
            if success:
                send_response({
                    'type': 'recognition_started',
                    'data': {'success': True}
                })
                log("Image recognition system started successfully", "INFO")
            else:
                send_response({
                    'type': 'recognition_started',
                    'data': {'success': False, 'error': 'Failed to start recognition system'}
                })
                log("Failed to start image recognition system", "ERROR")
        
        elif action == 'stop_image_recognition':
            # 停止图像识别系统
            log("Stopping image recognition system...", "INFO")
            
            success = global_recognition_system.stop_recognition()
            
            if success:
                send_response({
                    'type': 'recognition_stopped',
                    'data': {'success': True}
                })
                log("Image recognition system stopped successfully", "INFO")
            else:
                send_response({
                    'type': 'recognition_stopped',
                    'data': {'success': False, 'error': 'Failed to stop recognition system'}
                })
                log("Failed to stop image recognition system", "ERROR")
        
        elif action == 'get_recognition_status':
            # 获取图像识别系统状态
            status = global_recognition_system.get_status()
            send_response({
                'type': 'recognition_status',
                'data': status
            })
            log(f"Recognition status: {status['is_running']}", "INFO")
        
        elif action == 'test_image_recognition_click':
            # 测试单个图像识别点击功能 - 增强版本
            target_image = cmd.get('target_image', '')
            target_name = cmd.get('target_name', '目标图像')
            use_debug_threshold = cmd.get('use_debug_threshold', False)
            custom_threshold = cmd.get('custom_threshold', 0.65)
            
            log(f"Testing image recognition click for: {target_name} ({target_image})", "INFO")
            
            try:
                # 加载测试模板
                if target_image:
                    # 转换相对路径为绝对路径
                    if not os.path.isabs(target_image):
                        script_dir = os.path.dirname(os.path.abspath(__file__))
                        project_root = os.path.dirname(script_dir)
                        target_image = os.path.join(project_root, target_image)
                    
                    success = image_recognition.load_template('test_target', target_image)
                    if success:
                        # 获取截图
                        screenshot = window_capture.capture()
                        if screenshot is not None:
                            log(f"Screenshot captured for {target_name}, starting enhanced recognition...", "INFO")
                            
                            # 使用优化的阈值
                            test_threshold = custom_threshold if use_debug_threshold else 0.65
                            log(f"Using threshold: {test_threshold:.2f}", "INFO")
                            
                            # 执行识别 - 使用增强的识别方法
                            found, position, confidence = image_recognition.match_template(
                                screenshot, 'test_target', test_threshold
                            )
                            
                            # 如果第一次识别失败，尝试更宽松的阈值
                            if not found and confidence > 0.4:
                                log(f"First attempt failed (confidence: {confidence:.3f}), trying relaxed threshold...", "INFO")
                                relaxed_threshold = max(0.4, confidence - 0.05)
                                found, position, confidence = image_recognition.match_template(
                                    screenshot, 'test_target', relaxed_threshold
                                )
                                if found:
                                    log(f"✅ Found with relaxed threshold {relaxed_threshold:.2f}", "INFO")
                            
                            if found:
                                log(f"✅ {target_name} found at {position} (confidence: {confidence:.3f})", "INFO")
                                
                                # 执行点击
                                log(f"Clicking {target_name} at position {position}...", "INFO")
                                log(f"{target_name} 原始坐标: x={position[0]}, y={position[1]}", "INFO")
                                
                                # 转换为精确的屏幕坐标
                                accurate_click_x, accurate_click_y = window_capture.get_accurate_click_position(
                                    position[0], position[1], 'test_target'
                                )
                                log(f"{target_name} 转换后坐标: x={accurate_click_x}, y={accurate_click_y}", "INFO")
                                
                                click_success = human_mouse.click(accurate_click_x, accurate_click_y)
                                
                                if click_success:
                                    log(f"✅ Successfully clicked {target_name}!", "INFO")
                                else:
                                    log(f"❌ Failed to click {target_name}", "ERROR")
                                
                                send_response({
                                    'type': 'test_recognition_result',
                                    'data': {
                                        'found': True,
                                        'position': position,
                                        'confidence': confidence,
                                        'clicked': click_success,
                                        'target_name': target_name,
                                        'threshold_used': test_threshold
                                    }
                                })
                            else:
                                log(f"❌ {target_name} not found (max confidence: {confidence:.3f})", "WARN")
                                
                                # 提供优化建议
                                if confidence > 0.4:
                                    suggested_threshold = max(0.4, confidence - 0.05)
                                    log(f"💡 建议: 尝试降低阈值到 {suggested_threshold:.2f}", "INFO")
                                elif confidence > 0.2:
                                    log(f"💡 建议: 检查模板图像是否与当前游戏界面匹配", "INFO")
                                else:
                                    log(f"💡 建议: 重新制作模板图像，当前置信度过低", "INFO")
                                
                                send_response({
                                    'type': 'test_recognition_result',
                                    'data': {
                                        'found': False,
                                        'confidence': confidence,
                                        'target_name': target_name,
                                        'threshold_used': test_threshold,
                                        'suggestion': f"建议阈值: {max(0.4, confidence - 0.05):.2f}" if confidence > 0.4 else "需要重新制作模板"
                                    }
                                })
                        else:
                            log("❌ Test recognition failed: cannot capture window", "ERROR")
                            send_response({
                                'type': 'test_recognition_result',
                                'data': {
                                    'error': 'Cannot capture window',
                                    'target_name': target_name
                                }
                            })
                    else:
                        log(f"❌ Test recognition failed: cannot load template {target_image}", "ERROR")
                        send_response({
                            'type': 'test_recognition_result',
                            'data': {
                                'error': f'Cannot load template: {target_image}',
                                'target_name': target_name
                            }
                        })
                        
            except Exception as e:
                log(f"❌ Test recognition error: {e}", "ERROR")
                send_response({
                    'type': 'test_recognition_result',
                    'data': {
                        'error': str(e),
                        'target_name': target_name
                    }
                })
        
        elif action == 'test_full_click_sequence':
            # 测试完整点击序列（副本 + 开始挑战）
            dungeon_image = cmd.get('dungeon_image', '')
            challenge_image = cmd.get('challenge_image', '')
            dungeon_name = cmd.get('dungeon_name', '副本')
            
            log(f"Testing full click sequence: {dungeon_name} + 开始挑战", "INFO")
            
            try:
                # 加载副本模板
                if dungeon_image:
                    if not os.path.isabs(dungeon_image):
                        script_dir = os.path.dirname(os.path.abspath(__file__))
                        project_root = os.path.dirname(script_dir)
                        dungeon_image = os.path.join(project_root, dungeon_image)
                    
                    log(f"尝试加载副本模板: {dungeon_image}", "INFO")
                    log(f"文件是否存在: {os.path.exists(dungeon_image)}", "INFO")
                    dungeon_loaded = image_recognition.load_template('test_dungeon', dungeon_image)
                    log(f"副本模板加载结果: {dungeon_loaded}", "INFO")
                else:
                    dungeon_loaded = False
                
                # 加载开始挑战模板
                if challenge_image:
                    if not os.path.isabs(challenge_image):
                        script_dir = os.path.dirname(os.path.abspath(__file__))
                        project_root = os.path.dirname(script_dir)
                        challenge_image = os.path.join(project_root, challenge_image)
                    
                    log(f"尝试加载挑战模板: {challenge_image}", "INFO")
                    log(f"文件是否存在: {os.path.exists(challenge_image)}", "INFO")
                    challenge_loaded = image_recognition.load_template('test_challenge', challenge_image)
                    log(f"挑战模板加载结果: {challenge_loaded}", "INFO")
                else:
                    challenge_loaded = False
                
                if dungeon_loaded and challenge_loaded:
                    # 获取截图
                    log("开始获取屏幕截图...", "INFO")
                    screenshot = window_capture.capture()
                    if screenshot is not None:
                        log(f"截图成功! 尺寸: {screenshot.shape[1]}x{screenshot.shape[0]}", "INFO")
                        log("Screenshot captured, starting full sequence recognition...", "INFO")
                        
                        # 识别副本
                        log(f"开始识别副本: {dungeon_name}", "INFO")
                        dungeon_found, dungeon_pos, dungeon_conf = image_recognition.match_template(
                            screenshot, 'test_dungeon', 0.4
                        )
                        log(f"副本识别结果: found={dungeon_found}, confidence={dungeon_conf:.3f}", "INFO")
                        
                        # 识别开始挑战
                        log("开始识别挑战按钮", "INFO")
                        challenge_found, challenge_pos, challenge_conf = image_recognition.match_template(
                            screenshot, 'test_challenge', 0.4
                        )
                        log(f"挑战按钮识别结果: found={challenge_found}, confidence={challenge_conf:.3f}", "INFO")
                        
                        log(f"Recognition results: {dungeon_name}={dungeon_found}, 开始挑战={challenge_found}", "INFO")
                        
                        if dungeon_found and challenge_found:
                            log(f"✅ Both targets found! Starting click sequence...", "INFO")
                            
                            # 初始化点击结果变量
                            dungeon_click = False
                            challenge_click = False
                            
                            # 第一步：点击副本
                            log(f"Step 1: Clicking {dungeon_name} at {dungeon_pos}...", "INFO")
                            log(f"副本原始坐标: x={dungeon_pos[0]}, y={dungeon_pos[1]}", "INFO")
                            
                            # 转换为精确的屏幕坐标
                            accurate_x, accurate_y = window_capture.get_accurate_click_position(
                                dungeon_pos[0], dungeon_pos[1], 'test_dungeon'
                            )
                            log(f"副本转换后坐标: x={accurate_x}, y={accurate_y}", "INFO")
                            
                            dungeon_click = human_mouse.click(accurate_x, accurate_y)
                            log(f"副本点击结果: {dungeon_click}", "INFO")
                            
                            if dungeon_click:
                                log(f"✅ {dungeon_name} clicked successfully", "INFO")
                                
                                # 等待500毫秒
                                log("Waiting 500ms before next click...", "INFO")
                                time.sleep(0.5)
                                
                                # 第二步：点击开始挑战
                                log(f"Step 2: Clicking 开始挑战 at {challenge_pos}...", "INFO")
                                log(f"挑战按钮原始坐标: x={challenge_pos[0]}, y={challenge_pos[1]}", "INFO")
                                
                                # 转换为精确的屏幕坐标
                                accurate_challenge_x, accurate_challenge_y = window_capture.get_accurate_click_position(
                                    challenge_pos[0], challenge_pos[1], 'test_challenge'
                                )
                                log(f"挑战按钮转换后坐标: x={accurate_challenge_x}, y={accurate_challenge_y}", "INFO")
                                
                                challenge_click = human_mouse.click(accurate_challenge_x, accurate_challenge_y)
                                log(f"挑战按钮点击结果: {challenge_click}", "INFO")
                                
                                if challenge_click:
                                    log("✅ 开始挑战 clicked successfully", "INFO")
                                    log("🎉 Full click sequence completed successfully!", "INFO")
                                else:
                                    log("❌ Failed to click 开始挑战", "ERROR")
                            else:
                                log(f"❌ Failed to click {dungeon_name}", "ERROR")
                            
                            send_response({
                                'type': 'test_full_sequence_result',
                                'data': {
                                    'dungeon_found': dungeon_found,
                                    'challenge_found': challenge_found,
                                    'dungeon_clicked': dungeon_click,
                                    'challenge_clicked': challenge_click,
                                    'sequence_completed': dungeon_click and challenge_click
                                }
                            })
                        else:
                            missing = []
                            if not dungeon_found:
                                missing.append(dungeon_name)
                            if not challenge_found:
                                missing.append('开始挑战')
                            
                            log(f"❌ Missing targets: {', '.join(missing)}", "WARN")
                            send_response({
                                'type': 'test_full_sequence_result',
                                'data': {
                                    'dungeon_found': dungeon_found,
                                    'challenge_found': challenge_found,
                                    'error': f'Missing targets: {", ".join(missing)}'
                                }
                            })
                    else:
                        log("❌ Cannot capture window screenshot", "ERROR")
                        send_response({
                            'type': 'test_full_sequence_result',
                            'data': {
                                'error': 'Cannot capture window screenshot'
                            }
                        })
                else:
                    errors = []
                    if not dungeon_loaded:
                        errors.append(f'Cannot load {dungeon_name} template')
                    if not challenge_loaded:
                        errors.append('Cannot load 开始挑战 template')
                    
                    error_msg = '; '.join(errors)
                    log(f"❌ Template loading failed: {error_msg}", "ERROR")
                    send_response({
                        'type': 'test_full_sequence_result',
                        'data': {
                            'error': error_msg
                        }
                    })
                    
            except Exception as e:
                log(f"❌ Full sequence test error: {e}", "ERROR")
                send_response({
                    'type': 'test_full_sequence_result',
                    'data': {
                        'error': str(e)
                    }
                })
        
        elif action == 'simulate_mouse_click':
            # 模拟鼠标点击
            x = cmd.get('x', 0)
            y = cmd.get('y', 0)
            log(f"Simulating mouse click at ({x}, {y})", "INFO")
            
            # 记录点击前的鼠标位置
            before_click_pos = human_mouse.get_mouse_position()
            log(f"点击前鼠标位置: {before_click_pos}", "INFO")
            log(f"屏幕尺寸: {human_mouse.screen_width}x{human_mouse.screen_height}", "INFO")
            log(f"目标坐标是否有效: {human_mouse.is_position_valid(x, y)}", "INFO")
            
            success = human_mouse.click(x, y)
            
            # 记录点击后的鼠标位置
            after_click_pos = human_mouse.get_mouse_position()
            log(f"点击后鼠标位置: {after_click_pos}", "INFO")
            
            # 计算位置偏差
            offset_x = after_click_pos[0] - x
            offset_y = after_click_pos[1] - y
            log(f"位置偏差: X={offset_x}, Y={offset_y}", "INFO")
            
            send_response({
                'type': 'simulate_click_result',
                'data': {
                    'success': success,
                    'target_position': (x, y),
                    'actual_position': after_click_pos,
                    'offset': (offset_x, offset_y),
                    'before_position': before_click_pos
                }
            })
            
            if success:
                log(f"Mouse click simulated successfully at ({x}, {y}), actual: {after_click_pos}", "INFO")
            else:
                log(f"Failed to simulate mouse click at ({x}, {y})", "ERROR")
        
        elif action == 'simulate_key_press':
            # 模拟按键
            key = cmd.get('key', '')
            log(f"Simulating key press: {key}", "INFO")
            
            success = human_mouse.press_key(key)
            
            send_response({
                'type': 'simulate_key_result',
                'data': {
                    'success': success,
                    'key': key
                }
            })
            
            if success:
                log(f"Key press simulated successfully: {key}", "INFO")
            else:
                log(f"Failed to simulate key press: {key}", "ERROR")
        
        elif action == 'save_recognition_config':
            # 保存图像识别配置
            config = cmd.get('config', {})
            log("Saving recognition config...", "INFO")
            
            try:
                # 这里可以将配置保存到文件
                # 暂时只是设置到全局识别系统
                global_recognition_system.set_config(config)
                
                send_response({
                    'type': 'config_saved',
                    'data': {'success': True}
                })
                log("Recognition config saved successfully", "INFO")
                
            except Exception as e:
                log(f"Failed to save config: {e}", "ERROR")
                send_response({
                    'type': 'config_saved',
                    'data': {'success': False, 'error': str(e)}
                })
        
        elif action == 'load_recognition_config':
            # 加载图像识别配置
            log("Loading recognition config...", "INFO")
            
            try:
                # 这里可以从文件加载配置
                # 暂时返回当前配置
                config = global_recognition_system.config
                
                send_response({
                    'type': 'config_loaded',
                    'data': {
                        'success': True,
                        'config': config
                    }
                })
                log("Recognition config loaded successfully", "INFO")
                
            except Exception as e:
                log(f"Failed to load config: {e}", "ERROR")
                send_response({
                    'type': 'config_loaded',
                    'data': {'success': False, 'error': str(e)}
                })
        
        elif action == 'debug_click_position':
            # 调试点击位置 - 只移动鼠标不点击，用于验证位置
            target_image = cmd.get('target_image', '')
            target_name = cmd.get('target_name', '目标图像')
            log(f"Debug click position for: {target_name} ({target_image})", "INFO")
            
            try:
                # 加载模板
                if target_image:
                    if not os.path.isabs(target_image):
                        script_dir = os.path.dirname(os.path.abspath(__file__))
                        project_root = os.path.dirname(script_dir)
                        target_image = os.path.join(project_root, target_image)
                    
                    success = image_recognition.load_template('debug_target', target_image)
                    if success:
                        # 获取截图
                        screenshot = window_capture.capture()
                        if screenshot is not None:
                            # 执行识别
                            found, position, confidence = image_recognition.match_template(
                                screenshot, 'debug_target', 0.4
                            )
                            
                            if found:
                                log(f"✅ {target_name} found at {position} (confidence: {confidence:.3f})", "INFO")
                                
                                # 转换坐标
                                accurate_x, accurate_y = window_capture.get_accurate_click_position(
                                    position[0], position[1], 'debug_target'
                                )
                                
                                # 只移动鼠标，不点击
                                log(f"移动鼠标到位置: ({accurate_x}, {accurate_y})", "INFO")
                                human_mouse.move_to(accurate_x, accurate_y, duration=1.0)
                                
                                # 等待3秒让用户观察位置
                                log("鼠标已移动到目标位置，请观察位置是否正确", "INFO")
                                time.sleep(3)
                                
                                send_response({
                                    'type': 'debug_position_result',
                                    'data': {
                                        'found': True,
                                        'original_position': position,
                                        'converted_position': (accurate_x, accurate_y),
                                        'confidence': confidence,
                                        'target_name': target_name
                                    }
                                })
                            else:
                                log(f"❌ {target_name} not found", "WARN")
                                send_response({
                                    'type': 'debug_position_result',
                                    'data': {
                                        'found': False,
                                        'confidence': confidence,
                                        'target_name': target_name
                                    }
                                })
                        else:
                            log("❌ Cannot capture screenshot", "ERROR")
                    else:
                        log(f"❌ Cannot load template: {target_image}", "ERROR")
                        
            except Exception as e:
                log(f"❌ Debug position error: {e}", "ERROR")
                send_response({
                    'type': 'debug_position_result',
                    'data': {
                        'error': str(e),
                        'target_name': target_name
                    }
                })
        
        elif action == 'click_screen_center':
            # 点击屏幕中心进行测试
            log("Testing click at screen center", "INFO")
            
            try:
                # 获取屏幕中心坐标
                center_x = human_mouse.screen_width // 2
                center_y = human_mouse.screen_height // 2
                
                log(f"屏幕尺寸: {human_mouse.screen_width}x{human_mouse.screen_height}", "INFO")
                log(f"屏幕中心坐标: ({center_x}, {center_y})", "INFO")
                
                # 记录点击前位置
                before_pos = human_mouse.get_mouse_position()
                log(f"点击前鼠标位置: {before_pos}", "INFO")
                
                # 执行点击
                success = human_mouse.click(center_x, center_y)
                
                # 记录点击后位置
                after_pos = human_mouse.get_mouse_position()
                log(f"点击后鼠标位置: {after_pos}", "INFO")
                
                # 计算偏差
                offset_x = after_pos[0] - center_x
                offset_y = after_pos[1] - center_y
                log(f"中心点击偏差: X={offset_x}, Y={offset_y}", "INFO")
                
                send_response({
                    'type': 'center_click_result',
                    'data': {
                        'success': success,
                        'screen_size': (human_mouse.screen_width, human_mouse.screen_height),
                        'target_center': (center_x, center_y),
                        'actual_position': after_pos,
                        'offset': (offset_x, offset_y),
                        'before_position': before_pos
                    }
                })
                
            except Exception as e:
                log(f"Center click test failed: {e}", "ERROR")
                send_response({
                    'type': 'center_click_result',
                    'data': {
                        'success': False,
                        'error': str(e)
                    }
                })
        
        elif action == 'test_coordinate_conversion':
            # 测试坐标转换功能
            test_x = cmd.get('x', 100)
            test_y = cmd.get('y', 100)
            log(f"Testing coordinate conversion for ({test_x}, {test_y})", "INFO")
            
            try:
                # 显示窗口信息
                window_rect = window_capture.get_window_rect()
                log(f"窗口位置信息: {window_rect}", "INFO")
                log(f"缩放因子: {window_capture.scale_factor}", "INFO")
                
                # 执行坐标转换
                screen_x, screen_y = window_capture.convert_relative_to_screen_coords(test_x, test_y)
                log(f"坐标转换结果: ({test_x}, {test_y}) -> ({screen_x}, {screen_y})", "INFO")
                
                # 获取当前鼠标位置
                current_pos = human_mouse.get_mouse_position()
                log(f"当前鼠标位置: {current_pos}", "INFO")
                
                send_response({
                    'type': 'coordinate_test_result',
                    'data': {
                        'original': (test_x, test_y),
                        'converted': (screen_x, screen_y),
                        'window_rect': window_rect,
                        'scale_factor': window_capture.scale_factor,
                        'current_mouse': current_pos
                    }
                })
                
            except Exception as e:
                log(f"坐标转换测试失败: {e}", "ERROR")
                send_response({
                    'type': 'coordinate_test_result',
                    'data': {
                        'error': str(e)
                    }
                })
        
        elif action == 'test_click_with_offset':
            # 使用偏移量测试点击
            base_x = cmd.get('x', 0)
            base_y = cmd.get('y', 0)
            offset_x = cmd.get('offset_x', 0)
            offset_y = cmd.get('offset_y', 0)
            
            # 计算最终坐标
            final_x = base_x + offset_x
            final_y = base_y + offset_y
            
            log(f"Testing click with offset: base({base_x}, {base_y}) + offset({offset_x}, {offset_y}) = final({final_x}, {final_y})", "INFO")
            
            try:
                # 记录点击前位置
                before_pos = human_mouse.get_mouse_position()
                
                # 执行点击
                success = human_mouse.click(final_x, final_y)
                
                # 记录点击后位置
                after_pos = human_mouse.get_mouse_position()
                
                # 计算实际偏差
                actual_offset_x = after_pos[0] - final_x
                actual_offset_y = after_pos[1] - final_y
                
                log(f"点击结果: 目标({final_x}, {final_y}), 实际{after_pos}, 偏差({actual_offset_x}, {actual_offset_y})", "INFO")
                
                send_response({
                    'type': 'offset_click_result',
                    'data': {
                        'success': success,
                        'base_position': (base_x, base_y),
                        'applied_offset': (offset_x, offset_y),
                        'target_position': (final_x, final_y),
                        'actual_position': after_pos,
                        'actual_offset': (actual_offset_x, actual_offset_y),
                        'before_position': before_pos
                    }
                })
                
            except Exception as e:
                log(f"Offset click test failed: {e}", "ERROR")
                send_response({
                    'type': 'offset_click_result',
                    'data': {
                        'success': False,
                        'error': str(e)
                    }
                })
        
        elif action == 'coordinate_debug_test':
            # 坐标调试测试 - 专门解决点击位置不准确问题
            target_image = cmd.get('target_image', '')
            target_name = cmd.get('target_name', '测试目标')
            
            log(f"Starting coordinate debug test for: {target_name}", "INFO")
            
            try:
                from coordinate_debugger import create_coordinate_debugger
                
                debugger = create_coordinate_debugger(window_capture, human_mouse, image_recognition)
                
                # 转换相对路径为绝对路径
                if target_image and not os.path.isabs(target_image):
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    project_root = os.path.dirname(script_dir)
                    target_image = os.path.join(project_root, target_image)
                
                # 执行全面坐标测试
                results = debugger.comprehensive_coordinate_test(target_image, target_name)
                
                # 保存调试结果
                debugger.save_debug_results(results)
                
                send_response({
                    'type': 'coordinate_debug_result',
                    'data': results
                })
                
            except Exception as e:
                log(f"Coordinate debug test failed: {e}", "ERROR")
                send_response({
                    'type': 'coordinate_debug_result',
                    'data': {'error': str(e)}
                })
        
        elif action == 'debug_window_detection':
            # 调试窗口检测功能 - 增强版
            log("🔍 开始调试窗口检测功能", "INFO")
            
            try:
                # 显示平台信息
                log(f"📱 当前平台: {window_capture.platform}", "INFO")
                
                # 直接调用窗口检测方法，获取所有窗口
                log("📋 调用 window_capture.find_windows('') 获取所有窗口", "INFO")
                windows = window_capture.find_windows('')
                
                log(f"📊 窗口检测返回 {len(windows)} 个窗口", "INFO")
                
                if windows:
                    log("✅ 找到的窗口列表:", "INFO")
                    for i, (hwnd, title) in enumerate(windows):
                        log(f"  窗口 {i+1}: hwnd={hwnd}, 标题='{title}'", "INFO")
                else:
                    log("⚠️ 未找到任何窗口", "WARN")
                
                # 如果是macOS，进行详细的AppleScript调试
                if window_capture.platform == 'macos':
                    log("🍎 macOS平台 - 进行AppleScript调试", "INFO")
                    import subprocess
                    
                    # 测试1：获取所有进程名称
                    try:
                        log("测试1: 获取所有进程名称", "INFO")
                        result = subprocess.run(['osascript', '-e', 'tell application "System Events" to get name of every process'], 
                                              capture_output=True, text=True, timeout=10)
                        if result.returncode == 0:
                            processes = result.stdout.strip().split(', ')
                            log(f"✅ 成功获取 {len(processes)} 个进程", "INFO")
                            # 显示前10个进程作为示例
                            for i, process in enumerate(processes[:10]):
                                log(f"  进程 {i+1}: {process}", "INFO")
                            if len(processes) > 10:
                                log(f"  ... 还有 {len(processes) - 10} 个进程", "INFO")
                        else:
                            log(f"❌ 获取进程失败: {result.stderr}", "ERROR")
                    except Exception as e:
                        log(f"❌ 进程获取异常: {e}", "ERROR")
                    
                    # 测试2：获取窗口信息
                    try:
                        log("测试2: 获取窗口信息", "INFO")
                        script = '''
                        tell application "System Events"
                            set windowCount to 0
                            set processCount to 0
                            set windowList to {}
                            
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
                            
                            return "进程数:" & processCount & ",窗口数:" & windowCount & ",窗口:" & (windowList as string)
                        end tell
                        '''
                        
                        result = subprocess.run(['osascript', '-e', script], 
                                              capture_output=True, text=True, timeout=15)
                        if result.returncode == 0:
                            log(f"✅ AppleScript窗口检测成功: {result.stdout.strip()}", "INFO")
                        else:
                            log(f"❌ AppleScript窗口检测失败: {result.stderr}", "ERROR")
                    except Exception as e:
                        log(f"❌ AppleScript窗口检测异常: {e}", "ERROR")
                    
                    # 测试3：检查权限
                    try:
                        log("测试3: 检查辅助功能权限", "INFO")
                        result = subprocess.run(['osascript', '-e', 'tell application "System Events" to get name of first process'], 
                                              capture_output=True, text=True, timeout=5)
                        if result.returncode == 0:
                            log("✅ 辅助功能权限正常", "INFO")
                        else:
                            if "not allowed assistive access" in result.stderr.lower():
                                log("❌ 缺少辅助功能权限！", "ERROR")
                                log("💡 解决方案: 系统偏好设置 > 安全性与隐私 > 隐私 > 辅助功能 > 添加此应用", "INFO")
                            else:
                                log(f"⚠️ 权限检查异常: {result.stderr}", "WARN")
                    except Exception as e:
                        log(f"❌ 权限检查失败: {e}", "ERROR")
                
                # 返回调试结果
                send_response({
                    'type': 'window_detection_debug',
                    'data': {
                        'windows': [{'hwnd': hwnd, 'title': title} for hwnd, title in windows],
                        'count': len(windows),
                        'platform': window_capture.platform,
                        'debug_completed': True
                    }
                })
                
                if len(windows) > 0:
                    log("🎉 窗口检测调试完成 - 功能正常", "INFO")
                else:
                    log("⚠️ 窗口检测调试完成 - 未找到窗口，可能是权限问题", "WARN")
                
            except Exception as e:
                log(f"❌ 窗口检测调试失败: {e}", "ERROR")
                import traceback
                log(f"错误详情: {traceback.format_exc()}", "ERROR")
                send_response({
                    'type': 'window_detection_debug',
                    'data': {'error': str(e)}
                })
        
        elif action == 'test_original_coordinates':
            # 测试使用原始坐标（不进行缩放转换）- 验证用户建议
            log("🎯 测试原始坐标方案（按用户建议）", "INFO")
            
            try:
                # 首先进行实际的图像识别，获取真实的识别坐标
                target_image = cmd.get('target_image', 'static/dungeon/火.png')
                
                # 转换相对路径为绝对路径
                if not os.path.isabs(target_image):
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    project_root = os.path.dirname(script_dir)
                    target_image = os.path.join(project_root, target_image)
                
                log(f"使用测试图像: {target_image}", "INFO")
                
                # 加载模板并进行识别
                success = image_recognition.load_template('original_test', target_image)
                if not success:
                    raise Exception(f"无法加载测试模板: {target_image}")
                
                # 获取截图并识别
                screenshot = window_capture.capture()
                if screenshot is None:
                    raise Exception("无法获取屏幕截图")
                
                found, position, confidence = image_recognition.match_template(
                    screenshot, 'original_test', 0.6
                )
                
                if not found:
                    raise Exception(f"未能识别到目标图像，置信度: {confidence:.3f}")
                
                # 获取识别到的原始坐标
                original_x, original_y = position
                log(f"✅ 图像识别成功: 位置({original_x}, {original_y}), 置信度: {confidence:.3f}", "INFO")
                
                import pyautogui
                
                # 获取屏幕尺寸
                screen_width, screen_height = pyautogui.size()
                log(f"📺 逻辑屏幕尺寸: {screen_width}x{screen_height}", "INFO")
                log(f"📸 截图尺寸: {screenshot.shape[1]}x{screenshot.shape[0]}", "INFO")
                
                # 按照你的建议：直接使用原始坐标，不进行缩放
                test_x, test_y = original_x, original_y
                
                # 检查坐标是否在逻辑屏幕范围内
                within_bounds = 0 <= test_x <= screen_width and 0 <= test_y <= screen_height
                log(f"📏 原始坐标范围检查: {'✅ 在范围内' if within_bounds else '❌ 超出范围'}", "INFO")
                
                if not within_bounds:
                    log(f"⚠️ 原始坐标({test_x}, {test_y})超出逻辑屏幕范围({screen_width}x{screen_height})", "WARN")
                    # 如果超出范围，按比例缩放到屏幕范围内
                    scale_x = screen_width / screenshot.shape[1]
                    scale_y = screen_height / screenshot.shape[0]
                    test_x = int(original_x * scale_x)
                    test_y = int(original_y * scale_y)
                    log(f"🔧 自动缩放到: ({test_x}, {test_y})", "INFO")
                
                # 记录移动前位置
                before_x, before_y = pyautogui.position()
                log(f"📍 移动前鼠标位置: ({before_x}, {before_y})", "INFO")
                
                # 移动到测试位置（慢速移动，便于观察）
                log(f"🖱️ 移动到测试位置: ({test_x}, {test_y})", "INFO")
                pyautogui.moveTo(test_x, test_y, duration=1.0)
                time.sleep(0.5)
                
                # 记录移动后位置
                after_x, after_y = pyautogui.position()
                log(f"📍 移动后鼠标位置: ({after_x}, {after_y})", "INFO")
                
                # 计算误差
                error_x = abs(after_x - test_x)
                error_y = abs(after_y - test_y)
                total_error = (error_x ** 2 + error_y ** 2) ** 0.5
                
                log(f"📏 位置误差: X={error_x}, Y={error_y}, 总误差={total_error:.1f}像素", "INFO")
                
                # 让鼠标在目标位置闪烁，便于用户观察是否在正确位置
                log("✨ 鼠标闪烁提示（观察是否在正确的图标位置）", "INFO")
                for i in range(4):
                    pyautogui.moveTo(test_x + 8, test_y + 8, duration=0.1)
                    time.sleep(0.1)
                    pyautogui.moveTo(test_x - 8, test_y - 8, duration=0.1)
                    time.sleep(0.1)
                    pyautogui.moveTo(test_x, test_y, duration=0.1)
                    time.sleep(0.3)
                
                # 判断测试结果
                success = error_x <= 5 and error_y <= 5
                
                send_response({
                    'type': 'original_coordinates_test',
                    'data': {
                        'original': (original_x, original_y),
                        'test_coords': (test_x, test_y),
                        'before': (before_x, before_y),
                        'after': (after_x, after_y),
                        'error': (error_x, error_y),
                        'total_error': total_error,
                        'screen_size': (screen_width, screen_height),
                        'screenshot_size': (screenshot.shape[1], screenshot.shape[0]),
                        'within_bounds': within_bounds,
                        'confidence': confidence,
                        'success': success
                    }
                })
                
                if success:
                    log("🎉 原始坐标测试成功！你的建议是正确的", "INFO")
                else:
                    log("❌ 原始坐标测试失败，可能需要进一步调试", "ERROR")
                
            except Exception as e:
                log(f"❌ 原始坐标测试失败: {e}", "ERROR")
                import traceback
                log(f"错误详情: {traceback.format_exc()}", "ERROR")
                send_response({
                    'type': 'original_coordinates_test',
                    'data': {'error': str(e)}
                })
        
        elif action == 'visual_mouse_test':
            # 可视化鼠标移动测试 - 让用户能看到鼠标是否真的移动了
            target_x = cmd.get('x', 960)  # 默认屏幕中心
            target_y = cmd.get('y', 540)
            
            log(f"Visual mouse test: moving to ({target_x}, {target_y})", "INFO")
            
            try:
                import pyautogui
                
                # 记录移动前位置
                before_x, before_y = pyautogui.position()
                log(f"Mouse position before: ({before_x}, {before_y})", "INFO")
                
                # 先移动到一个明显不同的位置
                log("Moving to corner first...", "INFO")
                pyautogui.moveTo(100, 100, duration=0.5)
                time.sleep(0.5)
                corner_x, corner_y = pyautogui.position()
                log(f"Corner position: ({corner_x}, {corner_y})", "INFO")
                
                # 再移动到目标位置
                log(f"Moving to target ({target_x}, {target_y})...", "INFO")
                pyautogui.moveTo(target_x, target_y, duration=1.0)  # 慢速移动，用户能看到
                time.sleep(0.5)
                
                # 记录移动后位置
                after_x, after_y = pyautogui.position()
                log(f"Mouse position after: ({after_x}, {after_y})", "INFO")
                
                # 计算误差
                error_x = abs(after_x - target_x)
                error_y = abs(after_y - target_y)
                total_error = (error_x ** 2 + error_y ** 2) ** 0.5
                
                # 让鼠标在目标位置闪烁几次，用户能明显看到
                log("Making mouse blink at target position...", "INFO")
                for i in range(3):
                    pyautogui.moveTo(target_x + 10, target_y + 10, duration=0.1)
                    time.sleep(0.1)
                    pyautogui.moveTo(target_x - 10, target_y - 10, duration=0.1)
                    time.sleep(0.1)
                    pyautogui.moveTo(target_x, target_y, duration=0.1)
                    time.sleep(0.2)
                
                success = error_x <= 5 and error_y <= 5
                
                send_response({
                    'type': 'visual_mouse_test_result',
                    'data': {
                        'target': (target_x, target_y),
                        'before': (before_x, before_y),
                        'corner': (corner_x, corner_y),
                        'after': (after_x, after_y),
                        'error': (error_x, error_y),
                        'total_error': total_error,
                        'success': success
                    }
                })
                
            except Exception as e:
                log(f"Visual mouse test failed: {e}", "ERROR")
                send_response({
                    'type': 'visual_mouse_test_result',
                    'data': {'error': str(e)}
                })
        
        elif action == 'test_coordinate_conversion':
            # 测试坐标转换修复效果
            log("Testing coordinate conversion fix...", "INFO")
            
            try:
                # 获取当前截图信息
                screenshot = window_capture.capture()
                if screenshot is not None:
                    actual_width = screenshot.shape[1]
                    actual_height = screenshot.shape[0]
                    
                    # 获取逻辑屏幕尺寸
                    import pyautogui
                    logical_width, logical_height = pyautogui.size()
                    
                    # 计算缩放比例
                    scale_x = actual_width / logical_width
                    scale_y = actual_height / logical_height
                    
                    log(f"Screenshot size: {actual_width}x{actual_height}", "INFO")
                    log(f"Logical screen size: {logical_width}x{logical_height}", "INFO")
                    log(f"Scale factors: X={scale_x:.2f}, Y={scale_y:.2f}", "INFO")
                    
                    # 测试几个坐标点的转换
                    test_points = [
                        (1498, 367),  # 你的测试点
                        (1920, 540),  # 屏幕中心在4K中的位置
                        (3840, 1080)  # 4K右下角
                    ]
                    
                    results = []
                    for rel_x, rel_y in test_points:
                        screen_x, screen_y = window_capture.convert_relative_to_screen_coords(rel_x, rel_y)
                        results.append({
                            'relative': (rel_x, rel_y),
                            'screen': (screen_x, screen_y),
                            'in_bounds': 0 <= screen_x <= logical_width and 0 <= screen_y <= logical_height
                        })
                        log(f"Convert ({rel_x}, {rel_y}) -> ({screen_x}, {screen_y}), in_bounds: {results[-1]['in_bounds']}", "INFO")
                    
                    send_response({
                        'type': 'coordinate_conversion_test',
                        'data': {
                            'screenshot_size': (actual_width, actual_height),
                            'logical_size': (logical_width, logical_height),
                            'scale_factors': (scale_x, scale_y),
                            'test_results': results
                        }
                    })
                else:
                    send_response({
                        'type': 'coordinate_conversion_test',
                        'data': {'error': 'Cannot capture screenshot'}
                    })
                    
            except Exception as e:
                log(f"Coordinate conversion test failed: {e}", "ERROR")
                send_response({
                    'type': 'coordinate_conversion_test',
                    'data': {'error': str(e)}
                })
        
        elif action == 'quick_position_test':
            # 快速位置测试
            test_x = cmd.get('x', 0)
            test_y = cmd.get('y', 0)
            
            log(f"Quick position test at ({test_x}, {test_y})", "INFO")
            
            try:
                from coordinate_debugger import create_coordinate_debugger
                
                debugger = create_coordinate_debugger(window_capture, human_mouse, image_recognition)
                results = debugger.quick_position_test(test_x, test_y)
                
                send_response({
                    'type': 'quick_position_result',
                    'data': results
                })
                
            except Exception as e:
                log(f"Quick position test failed: {e}", "ERROR")
                send_response({
                    'type': 'quick_position_result',
                    'data': {'error': str(e)}
                })
        
        elif action == 'comprehensive_recognition_test':
            # 全面的图像识别测试
            log("Starting comprehensive recognition test...", "INFO")
            
            try:
                from image_recognition_debugger import create_debugger
                
                debugger = create_debugger(image_recognition, window_capture)
                
                # 准备测试的模板路径
                script_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(script_dir)
                
                template_paths = {
                    '火副本': os.path.join(project_root, 'static/dungeon/火.png'),
                    '水副本': os.path.join(project_root, 'static/dungeon/水.png'),
                    '风副本': os.path.join(project_root, 'static/dungeon/风.png'),
                    '电副本': os.path.join(project_root, 'static/dungeon/电.png'),
                    '暗副本': os.path.join(project_root, 'static/dungeon/暗.png'),
                    '光副本': os.path.join(project_root, 'static/dungeon/光.png'),
                    '开始挑战': os.path.join(project_root, 'static/dungeon/开始挑战.png')
                }
                
                # 执行全面测试
                results = debugger.comprehensive_test(template_paths)
                
                send_response({
                    'type': 'comprehensive_test_result',
                    'data': results
                })
                
            except Exception as e:
                log(f"Comprehensive test failed: {e}", "ERROR")
                send_response({
                    'type': 'comprehensive_test_result',
                    'data': {'error': str(e)}
                })
        
        elif action == 'open_debug_window':
            # 打开实时调试窗口
            log("Opening debug window...", "INFO")
            
            try:
                # 由于macOS Sequoia与Python 3.9的tkinter兼容性问题，
                # 直接使用控制台调试器作为主要解决方案
                log("检测到macOS Sequoia系统，使用控制台调试器", "INFO")
                
                from console_debug import create_console_debugger
                
                # 创建控制台调试器
                console_debugger = create_console_debugger(
                    window_capture=window_capture,
                    image_recognition=image_recognition,
                    human_mouse=human_mouse
                )
                
                if console_debugger:
                    # 执行一次调试扫描作为演示
                    log("执行调试扫描演示...", "INFO")
                    if console_debugger.single_scan():
                        send_response({
                            'type': 'debug_window_opened',
                            'data': {
                                'success': True, 
                                'type': 'console',
                                'message': '控制台调试器已启动，请查看Python控制台输出'
                            }
                        })
                        log("控制台调试器启动成功", "INFO")
                        log("调试信息已输出到控制台", "INFO")
                        log("如需持续调试，请使用: python console_debug.py", "INFO")
                    else:
                        send_response({
                            'type': 'debug_window_opened',
                            'data': {
                                'success': False, 
                                'error': '控制台调试器无法执行扫描，请检查游戏窗口连接'
                            }
                        })
                else:
                    send_response({
                        'type': 'debug_window_opened',
                        'data': {
                            'success': False, 
                            'error': '控制台调试器创建失败'
                        }
                    })
                
            except Exception as e:
                log(f"Failed to open debug window: {e}", "ERROR")
                import traceback
                log(f"Debug window error details: {traceback.format_exc()}", "ERROR")
                send_response({
                    'type': 'debug_window_opened',
                    'data': {'success': False, 'error': str(e)}
                })
        
        elif action == 'test_recognition_config':
            # 测试图像识别配置
            config = cmd.get('config', {})
            log("Testing recognition config...", "INFO")
            
            try:
                # 临时设置配置进行测试
                global_recognition_system.set_config(config)
                
                # 执行一次识别测试
                screenshot = window_capture.capture()
                if screenshot is not None:
                    results = []
                    
                    # 测试每个启用的副本
                    for dungeon in config.get('dungeons', []):
                        template_name = f"dungeon_{dungeon['key']}"
                        found, position, confidence = image_recognition.match_template(
                            screenshot, template_name, config.get('matchThreshold', 0.8)
                        )
                        
                        results.append({
                            'dungeon': dungeon['name'],
                            'found': found,
                            'position': position,
                            'confidence': confidence
                        })
                    
                    # 测试开始挑战按钮
                    found, position, confidence = image_recognition.match_template(
                        screenshot, 'start_challenge', config.get('matchThreshold', 0.8)
                    )
                    
                    results.append({
                        'dungeon': '开始挑战',
                        'found': found,
                        'position': position,
                        'confidence': confidence
                    })
                    
                    send_response({
                        'type': 'config_test_result',
                        'data': {
                            'success': True,
                            'results': results
                        }
                    })
                    log(f"Config test completed: {len(results)} templates tested", "INFO")
                else:
                    log("Config test failed: cannot capture window", "ERROR")
                    
            except Exception as e:
                log(f"Config test error: {e}", "ERROR")
                send_response({
                    'type': 'config_test_result',
                    'data': {'success': False, 'error': str(e)}
                })
            
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
