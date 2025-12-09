"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
const path_1 = require("path");
const fs_1 = require("fs");
// 屏蔽安全警告
process.env['ELECTRON_DISABLE_SECURITY_WARNINGS'] = 'true';
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
    // 注册开始脚本快捷键
    if (config.hotkeys.start) {
        const registered = electron_1.globalShortcut.register(config.hotkeys.start, () => {
            console.log('Start hotkey pressed:', config.hotkeys.start);
            if (win) {
                win.webContents.send('hotkey-triggered', 'start');
            }
        });
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
        if (registered) {
            console.log('Stop hotkey registered:', config.hotkeys.stop);
        }
        else {
            console.error('Failed to register stop hotkey:', config.hotkeys.stop);
        }
    }
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
const child_process_1 = require("child_process");
let pyProc = null;
function startPythonEngine() {
    const pythonPath = 'python3'; // 假设环境变量中有 python3，生产环境可能需要指向打包后的 python
    // Fix: __dirname is dist-electron. We need to go up one level to root, then into py_engine.
    const scriptPath = (0, path_1.join)(__dirname, '../py_engine/main.py');
    console.log(`Starting Python engine at: ${scriptPath}`);
    pyProc = (0, child_process_1.spawn)(pythonPath, [scriptPath]);
    pyProc.stdout?.on('data', (data) => {
        const str = data.toString();
        console.log('[Python Raw]', str);
        try {
            // Python 可能会一次输出多行，或者分块输出。这里做简单的按行分割处理。
            // 实际生产中可能需要更健壮的缓冲区处理。
            const lines = str.split('\n');
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
        }
        catch (e) {
            console.error('Error parsing python output:', e);
        }
    });
    pyProc.stderr?.on('data', (data) => {
        console.error(`[Python Err]: ${data}`);
    });
    pyProc.on('close', (code) => {
        console.log(`Python process exited with code ${code}`);
        pyProc = null;
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
    console.log('App is ready, creating window...');
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
