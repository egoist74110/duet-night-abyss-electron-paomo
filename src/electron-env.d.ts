export { }

declare global {
  interface Window {
    electronAPI: {
      ping: () => Promise<string>
      sendToPython: (data: any) => void
      onPythonData: (callback: (data: any) => void) => void
      // 配置相关方法
      saveConfig: (config: { hotkeys: { start: string; stop: string }; serverType?: 'cn' | 'global' }) => Promise<boolean>
      loadConfig: () => Promise<{ hotkeys: { start: string; stop: string }; serverType?: 'cn' | 'global' }>
      onHotkeyTriggered: (callback: (action: 'start' | 'stop') => void) => void
      onHotkeyRegistrationResult: (callback: (results: {
        start: { success: boolean; key: string }
        stop: { success: boolean; key: string }
      }) => void) => void
      // 脚本运行模式相关方法
      enterScriptMode: (stopKey: string) => Promise<boolean>
      exitScriptMode: () => Promise<boolean>
    }
  }
}
