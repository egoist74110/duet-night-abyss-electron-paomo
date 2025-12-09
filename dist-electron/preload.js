"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
console.log('[Preload] Script loaded');
electron_1.contextBridge.exposeInMainWorld('electronAPI', {
    ping: () => electron_1.ipcRenderer.invoke('ping'),
    sendToPython: (data) => electron_1.ipcRenderer.send('to-python', data),
    onPythonData: (callback) => {
        electron_1.ipcRenderer.on('python-data', (_event, value) => callback(value));
    }
});
console.log('[Preload] electronAPI exposed');
