/**
 * 窗口检测相关的Hook
 * 负责游戏窗口的检测、连接和管理功能
 */
import { ref, computed } from 'vue'
import { useGameStore } from '@/store/gameStore'
import { message } from '@/utils/message'

export function useWindowDetection() {
  const store = useGameStore()
  
  // 窗口检测相关状态
  const detectingWindow = ref(false)
  const gameWindowConnected = ref(false)
  const gameWindowTitle = ref('')
  const availableWindows = ref<Array<{ hwnd: number, title: string }>>([])
  const selectedWindowHwnd = ref<number | null>(null)
  const pendingStartScript = ref(false)  // 标志位:检测窗口后是否需要启动脚本

  // 计算属性：窗口连接状态
  const windowStatus = computed(() => ({
    connected: gameWindowConnected.value,
    title: gameWindowTitle.value,
    statusText: gameWindowConnected.value ? '已连接' : '未连接',
    statusType: gameWindowConnected.value ? 'success' : 'danger'
  }))

  /**
   * 手动检测游戏窗口(显示所有窗口)
   */
  function detectGameWindow() {
    detectingWindow.value = true
    availableWindows.value = []
    window.electronAPI.sendToPython({
      action: 'detect_window',
      keyword: ''  // 空字符串表示查找所有窗口
    })
  }

  /**
   * 自动检测游戏窗口(根据服务器类型自动搜索并连接)
   */
  function autoDetectGameWindow() {
    detectingWindow.value = true
    availableWindows.value = []

    const keyword = store.serverKeyword
    console.log(`Auto detecting window with keyword: ${keyword}`)

    window.electronAPI.sendToPython({
      action: 'detect_window',
      keyword: keyword
    })
  }

  /**
   * 连接到选中的窗口
   */
  function connectToWindow() {
    if (selectedWindowHwnd.value) {
      window.electronAPI.sendToPython({
        action: 'set_window',
        hwnd: selectedWindowHwnd.value
      })
    } else {
      message.warning('请先选择一个窗口')
    }
  }

  /**
   * 手动置顶窗口
   */
  function activateWindow() {
    if (!gameWindowConnected.value) {
      message.warning('请先连接窗口')
      return
    }

    console.log('手动置顶窗口...')
    window.electronAPI.sendToPython({
      action: 'activate_window'
    })
    message.info('正在置顶窗口...')
  }

  /**
   * 取消窗口置顶
   */
  function deactivateTopmost() {
    if (!gameWindowConnected.value) {
      message.warning('请先连接窗口')
      return
    }

    console.log('取消窗口置顶...')
    window.electronAPI.sendToPython({
      action: 'deactivate_topmost'
    })
    message.info('正在取消置顶...')
  }

  /**
   * 处理窗口检测响应
   */
  function handleWindowsFound(data: any) {
    availableWindows.value = data.windows || []
    detectingWindow.value = false

    // 判断是否为自动检测(有关键词搜索)
    const isAutoDetect = availableWindows.value.length > 0 &&
      availableWindows.value.every(w =>
        w.title.includes(store.serverKeyword)
      )

    if (availableWindows.value.length > 0) {
      message.close();
      if (isAutoDetect) {
        // 自动检测:智能选择游戏窗口
        // 过滤掉自己的应用程序窗口(包含"Automator"的)
        const gameWindows = availableWindows.value.filter(w =>
          !w.title.includes('Automator')
        )

        if (gameWindows.length > 0) {
          // 选择第一个游戏窗口
          const targetWindow = gameWindows[0]
          selectedWindowHwnd.value = targetWindow.hwnd
          message.success(`找到游戏窗口: ${targetWindow.title}`)

          console.log(`自动选择窗口: ${targetWindow.title} (hwnd=${targetWindow.hwnd})`)
          console.log(`过滤掉 ${availableWindows.value.length - gameWindows.length} 个非游戏窗口`)

          // 自动连接
          window.electronAPI.sendToPython({
            action: 'set_window',
            hwnd: targetWindow.hwnd
          })
        } else {
          // 所有窗口都是Automator,提示用户
          message.warning('找到的窗口都是应用程序本身,请确保游戏已启动')
          console.warn('所有找到的窗口:', availableWindows.value)
        }
      } else {
        // 手动检测:仅显示找到的窗口数量
        message.success(`找到 ${availableWindows.value.length} 个窗口`)
      }
    } else {
      // 未找到窗口
      if (isAutoDetect) {
        message.error(`未找到游戏窗口,请确保游戏已启动 (搜索: ${store.serverKeyword})`)
      } else {
        message.warning('未找到窗口，请确保游戏已启动')
      }
    }
  }

  /**
   * 处理窗口连接响应
   */
  function handleWindowSet(data: any) {
    gameWindowConnected.value = true
    gameWindowTitle.value = data.title
    message.success(`已连接到窗口: ${data.title}`)

    // 如果有待进入脚本模式的标志,连接成功后自动进入
    if (pendingStartScript.value) {
      pendingStartScript.value = false
      console.log('Window connected, now entering script mode...')
      return true // 返回true表示需要进入脚本模式
    }
    return false
  }

  /**
   * 处理窗口激活响应
   */
  function handleWindowActivated(data: any) {
    if (data.success) {
      console.log('窗口已成功置顶')
      message.success('窗口已置顶(保持在最前面)')
    } else {
      console.warn('窗口置顶失败:', data.error)
      message.warning('窗口置顶失败，请查看日志')
    }
  }

  /**
   * 处理取消置顶响应
   */
  function handleTopmostDeactivated(data: any) {
    if (data.success) {
      console.log('窗口置顶已取消')
      message.success('窗口置顶已取消')
    } else {
      console.warn('取消置顶失败:', data.error)
      message.warning('取消置顶失败')
    }
  }

  /**
   * 设置待启动脚本标志
   */
  function setPendingStartScript(pending: boolean) {
    pendingStartScript.value = pending
  }

  return {
    // 状态
    detectingWindow,
    gameWindowConnected,
    gameWindowTitle,
    availableWindows,
    selectedWindowHwnd,
    pendingStartScript,
    windowStatus,
    
    // 方法
    detectGameWindow,
    autoDetectGameWindow,
    connectToWindow,
    activateWindow,
    deactivateTopmost,
    handleWindowsFound,
    handleWindowSet,
    handleWindowActivated,
    handleTopmostDeactivated,
    setPendingStartScript
  }
}