import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useGameStore = defineStore('game', () => {
  const isRunning = ref(false)
  const logs = ref<{ level: string; message: string; timestamp: number }[]>([])

  // 快捷键配置
  const startHotkey = ref('')
  const stopHotkey = ref('')

  // 服务器类型配置
  const serverType = ref<'cn' | 'global'>('cn') // 默认国服

  // 计算属性:是否已配置快捷键
  const isHotkeyConfigured = computed(() => {
    return startHotkey.value.trim() !== '' && stopHotkey.value.trim() !== ''
  })

  // 计算属性:根据服务器类型获取搜索关键词
  const serverKeyword = computed(() => {
    return serverType.value === 'cn' ? '二重螺旋' : 'Duet Night Abyss'
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
      stopScript()
    } else {
      startScript()
    }
    return true
  }

  function startScript() {
    // 检查是否已配置快捷键
    if (!isHotkeyConfigured.value) {
      console.warn('Hotkeys not configured')
      return false
    }

    if (isRunning.value) {
      console.warn('Script is already running')
      return false
    }

    isRunning.value = true
    window.electronAPI.sendToPython({ action: 'start_script' })
    console.log('Script started')
    return true
  }

  function stopScript() {
    if (!isRunning.value) {
      console.warn('Script is not running')
      // 即使前端认为没有运行，也发送停止命令到Python，以防状态不同步
    }

    isRunning.value = false
    window.electronAPI.sendToPython({ action: 'stop_script' })
    console.log('Script stopped')
    return true
  }

  // 脚本配置
  const selectedScript = ref('fire10') // 当前选择的脚本
  const scriptConfigs = ref<Record<string, any>>({
    fire10: {
      maxRounds: 10,
      timeout: 300,
      dungeonType: 'default'
    }
  })

  // 可用脚本列表
  const availableScripts = [
    {
      id: 'fire10',
      name: '火10',
      description: '火10副本自动化脚本',
      type: 'dungeon' // 副本类型脚本
    }
    // 未来添加更多脚本
  ]

  // 获取当前脚本配置
  const currentScriptConfig = computed(() => {
    return scriptConfigs.value[selectedScript.value] || {}
  })

  // 更新脚本配置
  function updateScriptConfig(scriptId: string, config: any) {
    scriptConfigs.value[scriptId] = config
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
    serverType,
    serverKeyword,
    selectedScript,
    scriptConfigs,
    availableScripts,
    currentScriptConfig,
    addLog,
    loadConfig,
    saveConfig,
    toggleScript,
    startScript,
    stopScript,
    updateScriptConfig,
    ping
  }
})
