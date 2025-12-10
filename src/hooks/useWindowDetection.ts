/**
 * 窗口检测相关的Hook
 * 负责游戏窗口的检测、连接和管理功能
 */
import { ref, computed } from 'vue'
import { useGameStore } from '@/store/gameStore'
import { message } from '@/utils/message'

export function useWindowDetection() {
  const store = useGameStore()
  
  // 窗口检测状态和连接状态现在从 store 中获取
  // const detectingWindow = ref(false) // 已移动到 store 中
  // const connectingWindow = ref(false) // 已移动到 store 中
  const gameWindowConnected = ref(false)
  const gameWindowTitle = ref('')
  // availableWindows 和 selectedWindowHwnd 现在从 store 中获取
  const pendingStartScript = ref(false)  // 标志位:检测窗口后是否需要启动脚本
  
  // 移除了复杂的超时定时器逻辑，简化为直接等待后端响应

  // 计算属性：窗口连接状态
  const windowStatus = computed(() => ({
    connected: gameWindowConnected.value,
    title: gameWindowTitle.value,
    statusText: gameWindowConnected.value ? '已连接' : '未连接',
    statusType: gameWindowConnected.value ? 'success' : 'danger'
  }))

  /**
   * 重置检测状态
   * 简单直接地重置检测状态
   */
  function resetDetectingState() {
    console.log('[RESET] 重置窗口检测状态')
    store.setDetectingWindow(false)
  }

  // 删除了复杂的超时定时器逻辑，简化为直接等待后端响应

  /**
   * 手动检测游戏窗口(显示所有窗口)
   * 发送检测请求后等待后端响应，不提前显示任何结果提示
   */
  function detectGameWindow() {
    console.log('[DETECT] 开始手动窗口检测...')
    
    // 重置状态，准备新的检测
    store.setDetectingWindow(true)
    store.clearAvailableWindows()
    
    // 显示检测中的提示信息
    message.info('正在检测窗口，请稍候...', { duration: 0 }) // duration: 0表示不自动关闭
    
    try {
      console.log('[DETECT] 发送窗口检测命令到Python后端...')
      window.electronAPI.sendToPython({
        action: 'detect_window',
        keyword: ''  // 空字符串表示查找所有窗口
      })
      console.log('[DETECT] 窗口检测命令已发送，等待后端响应...')
    } catch (error) {
      console.error('[DETECT] 发送窗口检测命令失败:', error)
      message.close() // 关闭检测中的提示
      message.error('发送窗口检测命令失败，请检查Python后端连接')
      resetDetectingState()
    }
  }

  /**
   * 自动检测游戏窗口(根据服务器类型自动搜索并连接)
   * 发送检测请求后等待后端响应，不提前显示任何结果提示
   */
  function autoDetectGameWindow() {
    const keyword = store.serverKeyword
    console.log(`[AUTO-DETECT] 开始自动窗口检测，搜索关键词: ${keyword}`)
    
    // 重置状态，准备新的检测
    store.setDetectingWindow(true)
    store.clearAvailableWindows()
    
    // 显示检测中的提示信息
    message.info(`正在自动检测游戏窗口 (${keyword})，请稍候...`, { duration: 0 }) // duration: 0表示不自动关闭

    try {
      console.log('[AUTO-DETECT] 发送自动窗口检测命令到Python后端...')
      window.electronAPI.sendToPython({
        action: 'detect_window',
        keyword: keyword
      })
      console.log('[AUTO-DETECT] 自动窗口检测命令已发送，等待后端响应...')
    } catch (error) {
      console.error('[AUTO-DETECT] 发送自动窗口检测命令失败:', error)
      message.close() // 关闭检测中的提示
      message.error('发送自动窗口检测命令失败，请检查Python后端连接')
      resetDetectingState()
      
      // 如果是在初始化过程中，取消初始化
      if (pendingStartScript.value) {
        pendingStartScript.value = false
        store.cancelScriptInitialization()
        console.log('[AUTO-DETECT] 命令发送失败，取消脚本初始化')
      }
    }
  }

  /**
   * 连接到选中的窗口
   * 添加了 loading 状态处理，在连接过程中显示加载提示
   */
  function connectToWindow() {
    if (store.selectedWindowHwnd) {
      console.log('[CONNECT] 开始连接到选中的窗口...')
      
      // 设置连接中的loading状态
      store.setConnectingWindow(true)
      console.log('[CONNECT] 设置连接loading状态为true')
      
      // 显示连接中的提示信息
      message.info('正在连接到窗口，请稍候...', { duration: 0 }) // duration: 0表示不自动关闭
      
      try {
        console.log(`[CONNECT] 发送窗口连接命令到Python后端，hwnd: ${store.selectedWindowHwnd}`)
        window.electronAPI.sendToPython({
          action: 'set_window',
          hwnd: store.selectedWindowHwnd
        })
        console.log('[CONNECT] 窗口连接命令已发送，等待后端响应...')
      } catch (error) {
        console.error('[CONNECT] 发送窗口连接命令失败:', error)
        // 发送失败时重置loading状态
        store.setConnectingWindow(false)
        console.log('[CONNECT] 发送失败，重置连接loading状态为false')
        message.close() // 关闭连接中的提示
        message.error('发送窗口连接命令失败，请检查Python后端连接')
      }
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
   * 这是后端返回窗口检测结果时的处理函数
   * 收到后端响应后立即结束检测状态，然后处理具体结果
   */
  function handleWindowsFound(data: any) {
    console.log('[RESPONSE] 收到后端窗口检测响应:', data)
    console.log(`[RESPONSE] 后端返回 ${data.windows?.length || 0} 个窗口`)
    
    // ===== 第一步：立即结束检测状态 =====
    console.log(`[RESPONSE] 当前检测状态: ${store.detectingWindow}`)
    
    // 关闭检测中的提示信息
    message.close()
    console.log('[RESPONSE] 已关闭检测中的提示信息')
    
    // 重置检测状态
    store.setDetectingWindow(false)
    console.log(`[RESPONSE] 检测状态已重置为: ${store.detectingWindow}`)
    
    // ===== 第二步：处理检测结果 =====
    // 添加详细的调试信息
    console.log('[DEBUG] 原始数据结构:', JSON.stringify(data, null, 2))
    console.log('[DEBUG] data.windows 类型:', typeof data.windows)
    console.log('[DEBUG] data.windows 是否为数组:', Array.isArray(data.windows))
    console.log('[DEBUG] data.windows 内容:', data.windows)
    
    // 更新可用窗口列表 - 使用store方法确保响应式更新
    const windowsArray = data.windows || []
    console.log('[DEBUG] 准备赋值的数组:', windowsArray)
    console.log('[DEBUG] 赋值前 store.availableWindows 长度:', store.availableWindows.length)
    
    // 使用store方法更新，确保响应式生效
    store.setAvailableWindows(windowsArray)
    
    console.log('[DEBUG] 赋值后 store.availableWindows 长度:', store.availableWindows.length)
    console.log('[DEBUG] 赋值后 store.availableWindows 内容:', store.availableWindows)

    // 判断是否为自动检测(在初始化过程中且有待启动脚本标志)
    const isAutoDetectDuringInit = pendingStartScript.value

    // 判断是否找到了游戏相关窗口
    const hasGameWindows = store.availableWindows.some(w =>
      w.title.includes(store.serverKeyword)
    )

    // 根据后端实际返回的结果进行处理
    if (store.availableWindows.length > 0) {
      console.log('[RESPONSE] 后端成功找到窗口，开始处理结果')
      
      if (isAutoDetectDuringInit && hasGameWindows) {
        // 自动检测模式：智能选择游戏窗口
        console.log('[RESPONSE] 自动检测模式：筛选游戏窗口')
        
        // 过滤掉自己的应用程序窗口(包含"Automator"的)
        const gameWindows = store.availableWindows.filter(w =>
          !w.title.includes('Automator')
        )

        if (gameWindows.length > 0) {
          // 选择第一个游戏窗口
          const targetWindow = gameWindows[0]
          store.setSelectedWindowHwnd(targetWindow.hwnd)
          message.success(`自动检测成功！找到游戏窗口: ${targetWindow.title}`)

          console.log(`[RESPONSE] 自动选择窗口: ${targetWindow.title} (hwnd=${targetWindow.hwnd})`)
          console.log(`[RESPONSE] 过滤掉 ${store.availableWindows.length - gameWindows.length} 个非游戏窗口`)

          // 自动连接到游戏窗口
          window.electronAPI.sendToPython({
            action: 'set_window',
            hwnd: targetWindow.hwnd
          })
        } else {
          // 所有窗口都是Automator应用程序本身
          console.warn('[RESPONSE] 找到的窗口都是应用程序本身:', store.availableWindows)
          message.error('检测到的窗口都是应用程序本身，请确保游戏已启动')
          
          // 如果是在初始化过程中，取消初始化
          if (pendingStartScript.value) {
            pendingStartScript.value = false
            store.cancelScriptInitialization()
            console.log('[RESPONSE] 自动检测失败：只找到应用程序窗口，取消脚本初始化')
          }
        }
      } else if (isAutoDetectDuringInit && !hasGameWindows) {
        // 自动检测过程中找到了窗口，但都不是游戏窗口
        console.warn('[RESPONSE] 找到窗口但都不是游戏窗口:', store.availableWindows)
        message.error(`检测到 ${store.availableWindows.length} 个窗口，但都不是游戏窗口 (搜索关键词: ${store.serverKeyword})`)
        
        // 取消初始化
        pendingStartScript.value = false
        store.cancelScriptInitialization()
        console.log('[RESPONSE] 自动检测失败：找到窗口但都不是游戏窗口，取消脚本初始化')
      } else {
        // 手动检测模式：仅显示找到的窗口数量，让用户手动选择
        console.log('[RESPONSE] 手动检测模式：显示所有找到的窗口供用户选择')
        message.success(`检测成功！找到 ${store.availableWindows.length} 个窗口，请从下方列表中选择`)
      }
    } else {
      // 后端返回空窗口列表 - 这是后端的真实结果，不是前端的假设
      console.warn('[RESPONSE] 后端确认：未找到任何窗口')
      if (isAutoDetectDuringInit) {
        message.error(`未检测到任何游戏窗口，请确保游戏已启动 (搜索关键词: ${store.serverKeyword})`)
        
        // 取消初始化
        pendingStartScript.value = false
        store.cancelScriptInitialization()
        console.log('[RESPONSE] 自动检测失败：后端确认未找到任何窗口，取消脚本初始化')
      } else {
        message.warning('未检测到任何窗口，请确保游戏已启动')
      }
      
    }
  }

  /**
   * 处理窗口连接响应
   * 处理后端返回的窗口连接结果，关闭 loading 提示并更新连接状态
   */
  function handleWindowSet(data: any) {
    console.log('[RESPONSE] 收到后端窗口连接响应:', data)
    
    // 重置连接中的loading状态
    store.setConnectingWindow(false)
    console.log('[RESPONSE] 重置连接loading状态为false')
    
    // 关闭连接中的提示信息
    message.close()
    console.log('[RESPONSE] 已关闭连接中的提示信息')
    
    // 更新窗口连接状态
    gameWindowConnected.value = true
    gameWindowTitle.value = data.title
    
    // 显示连接成功消息
    message.success(`已连接到窗口: ${data.title}`)
    console.log(`[RESPONSE] 窗口连接成功: ${data.title}`)

    // 如果有待进入脚本模式的标志,连接成功后继续初始化流程
    if (pendingStartScript.value) {
      pendingStartScript.value = false
      console.log('[RESPONSE] 窗口连接成功，继续脚本初始化流程...')
      return true // 返回true表示需要继续脚本初始化流程
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

  /**
   * 清理资源
   * 在组件卸载时调用
   */
  function cleanup() {
    console.log('Window detection hook cleanup completed')
  }

  return {
    // 状态 - 直接返回响应式引用，不要包装
    gameWindowConnected,
    gameWindowTitle,
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
    setPendingStartScript,
    resetDetectingState,
    cleanup
  }
}