export {}

declare global {
  interface Window {
    electronAPI: {
      ping: () => Promise<string>
      sendToPython: (data: any) => void
      onPythonData: (callback: (data: any) => void) => void
      // 配置相关方法
      saveConfig: (config: { hotkeys: { start: string; stop: string } }) => Promise<boolean>
      loadConfig: () => Promise<{ hotkeys: { start: string; stop: string } }>
      onHotkeyTriggered: (callback: (action: 'start' | 'stop') => void) => void
    }
  }
}
