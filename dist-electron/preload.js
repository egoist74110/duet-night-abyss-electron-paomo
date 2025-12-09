"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
console.log('[Preload] Script loaded');
electron_1.contextBridge.exposeInMainWorld('electronAPI', {
    ping: () => electron_1.ipcRenderer.invoke('ping'),
    sendToPython: (data) => electron_1.ipcRenderer.send('to-python', data),
    onPythonData: (callback) => {
        electron_1.ipcRenderer.on('python-data', (_event, value) => callback(value));
    },
    // 配置相关方法
    saveConfig: (config) => electron_1.ipcRenderer.invoke('save-config', config),
    loadConfig: () => electron_1.ipcRenderer.invoke('load-config'),
    // 监听快捷键触发
    onHotkeyTriggered: (callback) => {
        electron_1.ipcRenderer.on('hotkey-triggered', (_event, action) => callback(action));
    },
    // 监听快捷键注册结果
    onHotkeyRegistrationResult: (callback) => {
        electron_1.ipcRenderer.on('hotkey-registration-result', (_event, results) => callback(results));
    },
    // 脚本运行模式相关方法
    enterScriptMode: (stopKey) => electron_1.ipcRenderer.invoke('enter-script-mode', stopKey),
    exitScriptMode: () => electron_1.ipcRenderer.invoke('exit-script-mode')
});
console.log('[Preload] electronAPI exposed');
