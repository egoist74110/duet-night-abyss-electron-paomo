"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
const path_1 = require("path");
const fs_1 = require("fs");
const child_process_1 = require("child_process");
// 屏蔽安全警告
process.env['ELECTRON_DISABLE_SECURITY_WARNINGS'] = 'true';
// 检查是否以管理员权限运行
function isAdmin() {
    if (process.platform === 'win32') {
        try {
            // 在Windows上,尝试访问需要管理员权限的注册表项
            const { execSync } = require('child_process');
            execSync('net session', { stdio: 'ignore' });
            return true;
        }
        catch {
            return false;
        }
    }
    // 其他平台暂不处理
    return true;
}
// 请求管理员权限并重启应用
function requestAdminAndRestart() {
    const options = {
        type: 'warning',
        buttons: ['以管理员身份重启', '退出应用'],
        defaultId: 0,
        title: '需要管理员权限',
        message: 'DNA Automator 需要管理员权限才能正常工作',
        detail: '应用需要管理员权限来:\n' +
            '• 置顶游戏窗口\n' +
            '• 模拟鼠标和键盘操作\n' +
            '• 注册全局快捷键\n\n' +
            '点击"以管理员身份重启"将关闭当前应用并以管理员权限重新启动。'
    };
    electron_1.dialog.showMessageBoxSync(options);
    if (options.buttons[0]) {
        // 用户选择重启
        const exePath = process.execPath;
        const args = process.argv.slice(1);
        if (process.platform === 'win32') {
            // Windows: 使用PowerShell以管理员身份启动
            const command = `Start-Process -FilePath "${exePath}" -ArgumentList "${args.join(' ')}" -Verb RunAs`;
            (0, child_process_1.exec)(`powershell -Command "${command}"`, (error) => {
                if (error) {
                    console.error('Failed to restart as admin:', error);
                }
                electron_1.app.quit();
            });
        }
        else {
            electron_1.app.quit();
        }
    }
    else {
        // 用户选择退出
        electron_1.app.quit();
    }
}
let win = null;
// 配置文件路径
const getConfigPath = () => {
    const userDataPath = electron_1.app.getPath('userData');
    // 确保目录存在
    if (!(0, fs_1.existsSync)(userDataPath)) {
        (0, fs_1.mkdirSync)(userDataPath, { recursive: true });
    }
    return (0, path_1.join)(userDataPath, 'config.json');
};
// 默认配置
const defaultConfig = {
    hotkeys: {
        start: '',
        stop: ''
    }
};
// 读取配置
function loadConfig() {
    try {
        const configPath = getConfigPath();
        if ((0, fs_1.existsSync)(configPath)) {
            const data = (0, fs_1.readFileSync)(configPath, 'utf-8');
            return JSON.parse(data);
        }
    }
    catch (error) {
        console.error('Failed to load config:', error);
    }
    return defaultConfig;
}
// 保存配置
function saveConfig(config) {
    try {
        const configPath = getConfigPath();
        (0, fs_1.writeFileSync)(configPath, JSON.stringify(config, null, 2), 'utf-8');
        console.log('Config saved to:', configPath);
        return true;
    }
    catch (error) {
        console.error('Failed to save config:', error);
        return false;
    }
}
// 注册全局快捷键
function registerHotkeys(config) {
    // 先注销所有快捷键
    electron_1.globalShortcut.unregisterAll();
    const results = {
        start: { success: false, key: config.hotkeys.start },
        stop: { success: false, key: config.hotkeys.stop }
    };
    // 注册开始脚本快捷键
    if (config.hotkeys.start) {
        const registered = electron_1.globalShortcut.register(config.hotkeys.start, () => {
            console.log('Start hotkey pressed:', config.hotkeys.start);
            if (win) {
                win.webContents.send('hotkey-triggered', 'start');
            }
        });
        results.start.success = registered;
        if (registered) {
            console.log('Start hotkey registered:', config.hotkeys.start);
        }
        else {
            console.error('Failed to register start hotkey:', config.hotkeys.start);
        }
    }
    // 注册停止脚本快捷键
    if (config.hotkeys.stop) {
        const registered = electron_1.globalShortcut.register(config.hotkeys.stop, () => {
            console.log('Stop hotkey pressed:', config.hotkeys.stop);
            if (win) {
                win.webContents.send('hotkey-triggered', 'stop');
            }
        });
        results.stop.success = registered;
        if (registered) {
            console.log('Stop hotkey registered:', config.hotkeys.stop);
        }
        else {
            console.error('Failed to register stop hotkey:', config.hotkeys.stop);
        }
    }
    // 通知前端注册结果
    if (win) {
        win.webContents.send('hotkey-registration-result', results);
    }
    return results;
}
function createWindow() {
    const preloadPath = (0, path_1.join)(__dirname, 'preload.js');
    win = new electron_1.BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            preload: preloadPath,
            nodeIntegration: false,
            contextIsolation: true,
            sandbox: false
        },
        titleBarStyle: 'hidden',
    });
    // 开发模式加载 Vite 开发服务器,生产模式加载打包后的文件
    if (!electron_1.app.isPackaged) {
        win.loadURL('http://localhost:5173');
        win.webContents.openDevTools();
    }
    else {
        win.loadURL(`file://${(0, path_1.join)(__dirname, '../dist/index.html')}`);
    }
}
electron_1.app.on('window-all-closed', () => {
    killPythonEngine();
    if (process.platform !== 'darwin')
        electron_1.app.quit();
});
// --- Python Engine Management ---
const child_process_2 = require("child_process");
let pyProc = null;
let pythonOutputBuffer = ''; // 缓冲区用于处理不完整的JSON
function startPythonEngine() {
    // 优先使用嵌入式Python，如果不存在则使用系统Python
    const embeddedPythonPath = (0, path_1.join)(__dirname, '../python/python.exe');
    const systemPythonPath = 'python';
    // 检查嵌入式Python是否存在
    const fs = require('fs');
    const pythonPath = fs.existsSync(embeddedPythonPath) ? embeddedPythonPath : systemPythonPath;
    // Fix: __dirname is dist-electron. We need to go up one level to root, then into py_engine.
    const scriptPath = (0, path_1.join)(__dirname, '../py_engine/main.py');
    console.log(`Using Python: ${pythonPath}`);
    console.log(`Starting Python engine at: ${scriptPath}`);
    // 重置缓冲区
    pythonOutputBuffer = '';
    pyProc = (0, child_process_2.spawn)(pythonPath, [scriptPath]);
    pyProc.stdout?.on('data', (data) => {
        const str = data.toString();
        console.log('[Python Raw]', str);
        // 将新数据添加到缓冲区
        pythonOutputBuffer += str;
        // 按行分割处理
        const lines = pythonOutputBuffer.split('\n');
        // 保留最后一个可能不完整的行
        pythonOutputBuffer = lines.pop() || '';
        // 处理完整的行
        lines.forEach((line) => {
            if (!line.trim())
                return;
            try {
                const json = JSON.parse(line);
                if (win) {
                    win.webContents.send('python-data', json);
                }
            }
            catch (e) {
                console.log('[Python Non-JSON]', line);
            }
        });
    });
    pyProc.stderr?.on('data', (data) => {
        console.error(`[Python Err]: ${data}`);
        // 也将错误信息发送到前端日志
        if (win) {
            win.webContents.send('python-data', {
                type: 'log',
                data: {
                    level: 'ERROR',
                    message: `Python stderr: ${data.toString()}`,
                    timestamp: Date.now() / 1000
                }
            });
        }
    });
    pyProc.on('close', (code) => {
        console.log(`Python process exited with code ${code}`);
        if (win) {
            win.webContents.send('python-data', {
                type: 'log',
                data: {
                    level: 'WARN',
                    message: `Python process exited with code ${code}`,
                    timestamp: Date.now() / 1000
                }
            });
        }
        pyProc = null;
        pythonOutputBuffer = '';
    });
    pyProc.on('error', (error) => {
        console.error('Failed to start Python process:', error);
        if (win) {
            win.webContents.send('python-data', {
                type: 'log',
                data: {
                    level: 'ERROR',
                    message: `Failed to start Python: ${error.message}`,
                    timestamp: Date.now() / 1000
                }
            });
        }
    });
}
function killPythonEngine() {
    if (pyProc) {
        pyProc.kill();
        pyProc = null;
    }
}
// 监听渲染进程发送的消息转发给 Python
const electron_2 = require("electron");
electron_2.ipcMain.on('to-python', (event, arg) => {
    if (pyProc && pyProc.stdin) {
        const data = JSON.stringify(arg) + '\n';
        pyProc.stdin.write(data);
    }
});
// 处理 ping 请求
electron_2.ipcMain.handle('ping', async () => {
    console.log('Received ping from renderer');
    return 'pong from main';
});
// 处理保存配置请求
electron_2.ipcMain.handle('save-config', async (event, config) => {
    const success = saveConfig(config);
    if (success) {
        // 重新注册快捷键
        registerHotkeys(config);
    }
    return success;
});
// 处理加载配置请求
electron_2.ipcMain.handle('load-config', async () => {
    return loadConfig();
});
// 应用启动
electron_1.app.whenReady().then(() => {
    console.log('App is ready, checking admin privileges...');
    // 检查管理员权限
    if (!isAdmin()) {
        console.warn('Application is not running with administrator privileges');
        requestAdminAndRestart();
        return;
    }
    console.log('Running with administrator privileges ✓');
    console.log('Creating window...');
    createWindow();
    startPythonEngine();
    // 加载配置并注册快捷键
    const config = loadConfig();
    registerHotkeys(config);
    electron_1.app.on('activate', () => {
        // 在 macOS 上,当点击 dock 图标且没有其他窗口打开时,重新创建窗口
        if (electron_1.BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});
// 应用退出时注销所有快捷键
electron_1.app.on('will-quit', () => {
    electron_1.globalShortcut.unregisterAll();
});
