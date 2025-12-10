"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.requestAdminAndRestart = requestAdminAndRestart;
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
// 注意: 此函数暂时未使用,因为我们改为让用户手动设置管理员权限
// 保留此函数以备将来需要时使用
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
// 注册停止快捷键 - 只在脚本运行模式下使用
function registerStopHotkey(stopKey) {
    // 先注销所有快捷键
    electron_1.globalShortcut.unregisterAll();
    if (!stopKey) {
        console.warn('Stop hotkey is empty, cannot register');
        return false;
    }
    const registered = electron_1.globalShortcut.register(stopKey, () => {
        console.log('Stop hotkey pressed:', stopKey);
        if (win) {
            win.webContents.send('hotkey-triggered', 'stop');
        }
    });
    if (registered) {
        console.log('Stop hotkey registered:', stopKey);
    }
    else {
        console.error('Failed to register stop hotkey:', stopKey);
    }
    return registered;
}
// 注销所有快捷键
function unregisterAllHotkeys() {
    electron_1.globalShortcut.unregisterAll();
    console.log('All hotkeys unregistered');
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
        // 移除 titleBarStyle: 'hidden',让窗口显示标准的标题栏和控制按钮
        // 这样用户就可以看到最小化、最大化、关闭按钮
    });
    // 移除Electron默认菜单栏(File, Edit, View等)
    // 让程序看起来更专业,不显示开发工具相关的菜单
    win.setMenu(null);
    // 开发模式加载 Vite 开发服务器并打开控制台,生产模式加载打包后的文件且不打开控制台
    if (!electron_1.app.isPackaged) {
        win.loadURL('http://localhost:5173');
        win.webContents.openDevTools(); // 只在开发模式打开控制台
    }
    else {
        win.loadURL(`file://${(0, path_1.join)(__dirname, '../dist/index.html')}`);
        // 生产模式不打开控制台,让程序看起来像正经的exe程序
    }
}
electron_1.app.on('window-all-closed', () => {
    console.log('All windows closed, cleaning up...');
    // 1. 注销所有快捷键
    unregisterAllHotkeys();
    // 2. 发送取消置顶命令到Python(如果Python进程还在运行)
    if (pyProc && pyProc.stdin) {
        try {
            const command = JSON.stringify({ action: 'deactivate_topmost' }) + '\n';
            pyProc.stdin.write(command);
            console.log('Sent deactivate_topmost command to Python');
        }
        catch (error) {
            console.error('Failed to send deactivate_topmost command:', error);
        }
    }
    // 3. 等待一小段时间让Python处理命令
    setTimeout(() => {
        // 4. 终止Python进程
        killPythonEngine();
        // 5. 退出应用
        if (process.platform !== 'darwin')
            electron_1.app.quit();
    }, 200); // 等待200ms
});
// --- Python Engine Management ---
const child_process_2 = require("child_process");
let pyProc = null;
let pythonOutputBuffer = ''; // 缓冲区用于处理不完整的JSON
function startPythonEngine() {
    // 根据操作系统选择合适的Python路径
    let pythonPath;
    if (process.platform === 'win32') {
        // Windows: 优先使用嵌入式Python，如果不存在则使用系统Python
        const embeddedPythonPath = (0, path_1.join)(__dirname, '../python/python.exe');
        const fs = require('fs');
        pythonPath = fs.existsSync(embeddedPythonPath) ? embeddedPythonPath : 'python';
    }
    else {
        // macOS/Linux: 尝试多个可能的Python命令
        const possiblePythonPaths = ['python3', 'python', '/usr/bin/python3', '/usr/local/bin/python3'];
        pythonPath = 'python3'; // 默认使用python3
        // 检查哪个Python命令可用
        const { execSync } = require('child_process');
        for (const path of possiblePythonPaths) {
            try {
                execSync(`${path} --version`, { stdio: 'ignore' });
                pythonPath = path;
                console.log(`Found Python at: ${path}`);
                break;
            }
            catch (error) {
                // 继续尝试下一个路径
            }
        }
    }
    // Python脚本路径
    // 开发模式: __dirname 是 dist-electron,需要回到根目录再进入 py_engine
    // 生产模式(打包后): 需要从 resources 目录读取
    const scriptPath = electron_1.app.isPackaged
        ? (0, path_1.join)(process.resourcesPath, 'py_engine/main.py')
        : (0, path_1.join)(__dirname, '../py_engine/main.py');
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
electron_2.ipcMain.on('to-python', (_event, arg) => {
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
electron_2.ipcMain.handle('save-config', async (_event, config) => {
    const success = saveConfig(config);
    // 注意: 保存配置时不再自动注册快捷键
    // 快捷键只在用户点击"开始监听"时才注册
    return success;
});
// 处理加载配置请求
electron_2.ipcMain.handle('load-config', async () => {
    return loadConfig();
});
// 处理进入脚本运行模式 - 注册停止快捷键
electron_2.ipcMain.handle('enter-script-mode', async (_event, stopKey) => {
    console.log('Entering script mode, registering stop hotkey:', stopKey);
    const success = registerStopHotkey(stopKey);
    return success;
});
// 处理退出脚本运行模式 - 注销所有快捷键
electron_2.ipcMain.handle('exit-script-mode', async () => {
    console.log('Exiting script mode, unregistering all hotkeys');
    unregisterAllHotkeys();
    return true;
});
// 应用启动
electron_1.app.whenReady().then(() => {
    console.log('App is ready, checking admin privileges...');
    // 检查管理员权限 - 只记录日志,不弹窗提示
    // 用户应该通过右键exe文件 -> 属性 -> 兼容性 -> 以管理员身份运行此程序
    // 或者使用"以管理员身份运行.bat"来启动
    if (!isAdmin()) {
        console.warn('⚠ Application is not running with administrator privileges');
        console.warn('⚠ Some features may not work properly (window activation, hotkeys, etc.)');
        console.warn('⚠ Please run as administrator for full functionality');
        // 不再弹窗,让程序继续运行
    }
    else {
        console.log('✓ Running with administrator privileges');
    }
    console.log('Creating window...');
    createWindow();
    startPythonEngine();
    // 注意: 不再在启动时自动注册快捷键
    // 快捷键只在用户点击"开始监听"时才注册
    electron_1.app.on('activate', () => {
        // 在 macOS 上,当点击 dock 图标且没有其他窗口打开时,重新创建窗口
        if (electron_1.BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});
// 应用退出时清理所有资源
electron_1.app.on('will-quit', (event) => {
    console.log('Application will quit, performing cleanup...');
    // 1. 注销所有快捷键
    electron_1.globalShortcut.unregisterAll();
    console.log('All hotkeys unregistered');
    // 2. 如果Python进程还在运行,发送取消置顶命令
    if (pyProc && pyProc.stdin) {
        try {
            const command = JSON.stringify({ action: 'deactivate_topmost' }) + '\n';
            pyProc.stdin.write(command);
            console.log('Sent deactivate_topmost command to Python');
            // 阻止立即退出,等待Python处理命令
            event.preventDefault();
            // 等待一小段时间后再退出
            setTimeout(() => {
                killPythonEngine();
                console.log('Python engine killed');
                electron_1.app.exit(0);
            }, 200);
        }
        catch (error) {
            console.error('Failed to send cleanup command:', error);
            killPythonEngine();
        }
    }
    else {
        // Python进程已经停止,直接清理
        killPythonEngine();
    }
});
