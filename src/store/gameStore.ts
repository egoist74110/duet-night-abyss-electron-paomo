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

  // 脚本运行模式状态 - 表示是否正在监听快捷键并准备运行脚本
  const isScriptMode = ref(false)

  // 脚本初始化状态 - 表示是否正在进行脚本初始化流程
  const isInitializing = ref(false)

  // 窗口检测状态 - 表示是否正在进行窗口检测
  const detectingWindow = ref(false)

  // 窗口连接状态 - 表示是否正在连接窗口
  const connectingWindow = ref(false)

  // 可用窗口列表 - 存储检测到的所有窗口
  const availableWindows = ref<Array<{ hwnd: number, title: string }>>([])

  // 选中的窗口句柄
  const selectedWindowHwnd = ref<number | null>(null)

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
      serverType.value = config.serverType || 'cn' // 加载服务器类型配置
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
        },
        serverType: serverType.value // 保存服务器类型配置
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

  // 开始脚本初始化流程
  async function startScriptInitialization() {
    if (!isHotkeyConfigured.value) {
      console.warn('Hotkeys not configured')
      return false
    }
    
    if (isInitializing.value) {
      console.warn('Script initialization already in progress')
      return false
    }
    
    console.log('Starting script initialization...')
    isInitializing.value = true
    return true
  }

  // 设置窗口检测状态
  function setDetectingWindow(detecting: boolean) {
    console.log(`[STORE] 设置窗口检测状态: ${detectingWindow.value} -> ${detecting}`)
    detectingWindow.value = detecting
  }

  // 设置窗口连接状态
  function setConnectingWindow(connecting: boolean) {
    console.log(`[STORE] 设置窗口连接状态: ${connectingWindow.value} -> ${connecting}`)
    connectingWindow.value = connecting
  }

  // 设置可用窗口列表
  function setAvailableWindows(windows: Array<{ hwnd: number, title: string }>) {
    console.log(`[STORE] 设置可用窗口列表: ${availableWindows.value.length} -> ${windows.length}`)
    console.log(`[STORE] 新窗口列表:`, windows)
    
    // 确保完全替换数组内容，触发响应式更新
    availableWindows.value.splice(0, availableWindows.value.length, ...windows)
    
    console.log(`[STORE] 设置完成，当前长度: ${availableWindows.value.length}`)
    console.log(`[STORE] 当前内容:`, availableWindows.value)
  }

  // 清空可用窗口列表
  function clearAvailableWindows() {
    console.log(`[STORE] 清空可用窗口列表`)
    // 使用splice确保响应式更新
    availableWindows.value.splice(0)
  }

  // 设置选中的窗口句柄
  function setSelectedWindowHwnd(hwnd: number | null) {
    console.log(`[STORE] 设置选中窗口: ${selectedWindowHwnd.value} -> ${hwnd}`)
    selectedWindowHwnd.value = hwnd
  }

  // 完成脚本初始化并进入脚本运行模式
  async function completeInitializationAndEnterScriptMode() {
    if (!isInitializing.value) {
      console.warn('No initialization in progress')
      return false
    }
    
    // 通知Electron主进程注册停止快捷键
    const success = await window.electronAPI.enterScriptMode(stopHotkey.value)
    
    if (success) {
      isInitializing.value = false
      isScriptMode.value = true
      console.log('Script initialization completed - now in script mode, listening for stop hotkey:', stopHotkey.value)
      return true
    } else {
      console.error('Failed to register stop hotkey')
      isInitializing.value = false
      return false
    }
  }

  // 取消脚本初始化
  function cancelScriptInitialization() {
    if (isInitializing.value) {
      console.log('Script initialization cancelled')
      isInitializing.value = false
    }
  }

  // 退出脚本运行模式 - 停止所有监听
  async function exitScriptMode() {
    // 通知Electron主进程注销所有快捷键
    await window.electronAPI.exitScriptMode()
    
    // 重置所有状态
    isScriptMode.value = false
    isInitializing.value = false
    isRunning.value = false
    console.log('Exited script mode - stopped all listeners and reset states')
    
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
    serverType,
    serverKeyword,
    isScriptMode,
    isInitializing,
    detectingWindow,
    connectingWindow,
    availableWindows,
    selectedWindowHwnd,
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
    startScriptInitialization,
    completeInitializationAndEnterScriptMode,
    cancelScriptInitialization,
    exitScriptMode,
    setDetectingWindow,
    setConnectingWindow,
    setAvailableWindows,
    clearAvailableWindows,
    setSelectedWindowHwnd,
    updateScriptConfig,
    ping
  }
})
