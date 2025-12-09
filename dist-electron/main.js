"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
const path_1 = require("path");
// 屏蔽安全警告
process.env['ELECTRON_DISABLE_SECURITY_WARNINGS'] = 'true';
let win = null;
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
// 应用启动
electron_1.app.whenReady().then(() => {
    console.log('App is ready, creating window...');
    createWindow();
    startPythonEngine();
    electron_1.app.on('activate', () => {
        // 在 macOS 上,当点击 dock 图标且没有其他窗口打开时,重新创建窗口
        if (electron_1.BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});
