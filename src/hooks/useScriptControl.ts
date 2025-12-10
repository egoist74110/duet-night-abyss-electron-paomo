/**
 * 脚本控制相关的Hook
 * 负责脚本的启动、停止和运行模式管理
 */
// 导入Vue相关依赖 - 当前不需要ref，但保留以备将来使用
// import { ref } from 'vue'
import { useGameStore } from '@/store/gameStore'
import { message } from '@/utils/message'

export function useScriptControl() {
  const store = useGameStore()
  
  // 防抖：防止快捷键重复触发
  let lastStopTrigger = 0
  const DEBOUNCE_DELAY = 500 // 500ms内的重复触发将被忽略

  /**
   * 停止脚本(通过快捷键触发)
   */
  async function handleStopScriptByHotkey() {
    console.log('Stop hotkey triggered - exiting script mode')

    // 1. 取消窗口置顶
    window.electronAPI.sendToPython({
      action: 'deactivate_topmost'
    })

    // 2. 退出脚本运行模式
    await store.exitScriptMode()

    message.info('脚本已停止,窗口置顶已取消,已退出脚本运行模式')
  }

  /**
   * 开始脚本初始化流程
   * 这是整个脚本启动的入口点，会统一管理窗口检测和脚本启动的状态
   * @param gameWindowConnected 游戏窗口是否已连接
   * @param autoDetectGameWindow 自动检测窗口的函数
   * @param setPendingStartScript 设置待启动脚本标志的函数
   */
  async function handleStartListening(
    gameWindowConnected: boolean,
    autoDetectGameWindow: () => void,
    setPendingStartScript: (pending: boolean) => void
  ) {
    if (!store.isHotkeyConfigured) {
      message.warning('请先配置并保存快捷键')
      return
    }

    // 开始脚本初始化流程
    const initStarted = await store.startScriptInitialization()
    if (!initStarted) {
      return
    }

    message.info('开始脚本初始化流程...')

    // 1. 检查窗口是否连接
    if (!gameWindowConnected) {
      // 如果窗口未连接,自动检测并连接
      console.log('Step 1/3: 窗口未连接，开始自动检测游戏窗口...')
      message.info('步骤 1/3: 正在自动检测游戏窗口...')

      // 设置窗口检测状态为true（这是用户点击"脚本，启动！"按钮时的状态设置）
      store.setDetectingWindow(true)

      // 设置标志位,表示检测完成后需要继续初始化流程
      setPendingStartScript(true)

      // 执行自动检测
      autoDetectGameWindow()
      return
    }

    // 2. 窗口已连接，继续初始化流程
    await continueInitializationAfterWindowConnected()
  }

  /**
   * 窗口连接后继续初始化流程
   * 这个方法会在窗口检测完成后被调用
   */
  async function continueInitializationAfterWindowConnected() {
    if (!store.isInitializing) {
      console.log('No initialization in progress, skipping...')
      return
    }

    console.log('Step 2/3: 窗口已连接，开始置顶游戏窗口...')
    message.info('步骤 2/3: 正在置顶游戏窗口...')

    // 2. 激活窗口（置顶）
    window.electronAPI.sendToPython({
      action: 'activate_window'
    })

    // 3. 等待置顶完成后，进入脚本运行模式
    setTimeout(async () => {
      console.log('Step 3/3: 窗口置顶完成，进入脚本运行模式...')
      message.info('步骤 3/3: 正在进入脚本运行模式...')

      const success = await store.completeInitializationAndEnterScriptMode()
      if (success) {
        message.success('✅ 脚本初始化完成！现在可以按停止快捷键来停止脚本')
      } else {
        message.error('❌ 进入脚本运行模式失败，请检查快捷键配置')
      }
    }, 500)
  }

  /**
   * 停止监听 - 退出脚本运行模式或取消初始化
   */
  async function handleStopListening() {
    if (store.isInitializing) {
      // 如果正在初始化中，取消初始化
      console.log('Cancelling script initialization...')
      store.cancelScriptInitialization()
      message.info('已取消脚本初始化')
      return
    }

    if (store.isScriptMode) {
      // 如果在脚本运行模式，正常退出
      console.log('Exiting script mode...')
      
      // 1. 取消窗口置顶
      window.electronAPI.sendToPython({
        action: 'deactivate_topmost'
      })

      // 2. 退出脚本运行模式
      await store.exitScriptMode()

      message.info('已退出脚本运行模式，窗口置顶已取消')
    }
  }

  /**
   * 处理快捷键触发事件
   * @param action 快捷键动作
   */
  function handleHotkeyTriggered(action: string) {
    const now = Date.now()

    // 只处理停止快捷键,且只在脚本运行模式下
    if (action === 'stop' && store.isScriptMode) {
      // 防抖：如果距离上次触发不到500ms，忽略
      if (now - lastStopTrigger < DEBOUNCE_DELAY) {
        console.log('Stop hotkey debounced')
        return
      }
      lastStopTrigger = now
      handleStopScriptByHotkey()
    }
  }

  /**
   * 窗口连接完成后继续初始化流程
   * 这个方法会被窗口检测模块调用，当窗口成功连接后继续脚本初始化
   */
  async function onWindowConnected() {
    // 继续初始化流程
    await continueInitializationAfterWindowConnected()
  }

  return {
    // 方法
    handleStopScriptByHotkey,
    handleStartListening,
    handleStopListening,
    handleHotkeyTriggered,
    onWindowConnected,
    continueInitializationAfterWindowConnected
  }
}