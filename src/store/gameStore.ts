import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useGameStore = defineStore('game', () => {
  const isRunning = ref(false)
  const logs = ref<{ level: string; message: string; timestamp: number }[]>([])

  function addLog(log: { level: string; message: string; timestamp: number }) {
    logs.value.push(log)
    if (logs.value.length > 1000) {
      logs.value.shift()
    }
  }

  function toggleScript() {
    if (isRunning.value) {
      // For now, we don't have a stop command in Python, but we can simulate state toggle
      // In reality, we might send a 'stop' command
      isRunning.value = false
      window.electronAPI.sendToPython({ action: 'stop_script' })
    } else {
      isRunning.value = true
      window.electronAPI.sendToPython({ action: 'start_script' })
    }
  }

  function ping() {
    window.electronAPI.sendToPython({ action: 'ping' })
  }

  return {
    isRunning,
    logs,
    addLog,
    toggleScript,
    ping
  }
})
