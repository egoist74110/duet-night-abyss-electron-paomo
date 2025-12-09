export {}

declare global {
  interface Window {
    electronAPI: {
      ping: () => Promise<string>
      sendToPython: (data: any) => void
      onPythonData: (callback: (data: any) => void) => void
    }
  }
}
