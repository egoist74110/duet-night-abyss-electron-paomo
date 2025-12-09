import { contextBridge, ipcRenderer } from 'electron'

console.log('[Preload] Script loaded')

contextBridge.exposeInMainWorld('electronAPI', {
  ping: () => ipcRenderer.invoke('ping'),
  sendToPython: (data: any) => ipcRenderer.send('to-python', data),
  onPythonData: (callback: (data: any) => void) => {
    ipcRenderer.on('python-data', (_event, value) => callback(value))
  },
  // 配置相关方法
  saveConfig: (config: any) => ipcRenderer.invoke('save-config', config),
  loadConfig: () => ipcRenderer.invoke('load-config'),
  // 监听快捷键触发
  onHotkeyTriggered: (callback: (action: 'start' | 'stop') => void) => {
    ipcRenderer.on('hotkey-triggered', (_event, action) => callback(action))
  }
})

console.log('[Preload] electronAPI exposed')
