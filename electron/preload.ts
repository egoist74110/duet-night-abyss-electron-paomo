import { contextBridge, ipcRenderer } from 'electron'

console.log('[Preload] Script loaded')

contextBridge.exposeInMainWorld('electronAPI', {
  ping: () => ipcRenderer.invoke('ping'),
  sendToPython: (data: any) => ipcRenderer.send('to-python', data),
  onPythonData: (callback: (data: any) => void) => {
    ipcRenderer.on('python-data', (_event, value) => callback(value))
  }
})

console.log('[Preload] electronAPI exposed')
