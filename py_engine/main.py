import sys
import json
import time
import threading

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

def main():
    log("Python Engine Started", "INFO")
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            line = line.strip()
            if not line:
                continue
                
            try:
                command = json.loads(line)
                handle_command(command)
            except json.JSONDecodeError:
                log(f"Invalid JSON received: {line}", "ERROR")
                
        except Exception as e:
            log(f"Error in main loop: {str(e)}", "ERROR")

def handle_command(cmd):
    action = cmd.get('action')
    
    if action == 'ping':
        log("Pong from Python!", "INFO")
    elif action == 'start_script':
        log("Script functionality not implemented yet", "WARN")
    else:
        log(f"Unknown command: {action}", "WARN")

if __name__ == "__main__":
    main()
