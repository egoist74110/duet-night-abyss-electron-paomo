import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useGameStore = defineStore('game', () => {
  const isRunning = ref(false)
  const logs = ref<{ level: string; message: string; timestamp: number }[]>([])
  
  // 快捷键配置
  const startHotkey = ref('')
  const stopHotkey = ref('')

  // 计算属性:是否已配置快捷键
  const isHotkeyConfigured = computed(() => {
    return startHotkey.value.trim() !== '' && stopHotkey.value.trim() !== ''
  })

  function addLog(log: { level: string; message: string; timestamp: number }) {
    logs.value.push(log)
    if (logs.value.length > 1000) {
      logs.value.shift()
    }
  }

  // 加载配置
  async function loadConfig() {
    try {
      const config = await window.electronAPI.loadConfig()
      startHotkey.value = config.hotkeys.start || ''
      stopHotkey.value = config.hotkeys.stop || ''
      console.log('Config loaded:', config)
    } catch (error) {
      console.error('Failed to load config:', error)
    }
  }

  // 保存配置
  async function saveConfig() {
    try {
      const config = {
        hotkeys: {
          start: startHotkey.value,
          stop: stopHotkey.value
        }
      }
      const success = await window.electronAPI.saveConfig(config)
      if (success) {
        console.log('Config saved successfully')
        return true
      } else {
        console.error('Failed to save config')
        return false
      }
    } catch (error) {
      console.error('Failed to save config:', error)
      return false
    }
  }

  function toggleScript() {
    // 检查是否已配置快捷键
    if (!isHotkeyConfigured.value) {
      console.warn('Hotkeys not configured')
      return false
    }

    if (isRunning.value) {
      isRunning.value = false
      window.electronAPI.sendToPython({ action: 'stop_script' })
    } else {
      isRunning.value = true
      window.electronAPI.sendToPython({ action: 'start_script' })
    }
    return true
  }

  function ping() {
    window.electronAPI.sendToPython({ action: 'ping' })
  }

  return {
    isRunning,
    logs,
    startHotkey,
    stopHotkey,
    isHotkeyConfigured,
    addLog,
    loadConfig,
    saveConfig,
    toggleScript,
    ping
  }
})
