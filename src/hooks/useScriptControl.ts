/**
 * 脚本控制相关的Hook
 * 负责脚本的启动、停止和运行模式管理
 */
import { ref } from 'vue'
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
   * 开始监听 - 进入脚本运行模式
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

    // 1. 检查窗口是否连接
    if (!gameWindowConnected) {
      // 如果窗口未连接,自动检测并连接
      message.info('正在自动检测游戏窗口...')
      console.log('Window not connected, auto-detecting...')

      // 设置标志位,表示检测完成后需要进入脚本模式
      setPendingStartScript(true)

      // 执行自动检测
      autoDetectGameWindow()
      return
    }

    // 2. 激活窗口（置顶）
    console.log('Activating window before entering script mode...')
    window.electronAPI.sendToPython({
      action: 'activate_window'
    })

    // 3. 进入脚本运行模式
    setTimeout(async () => {
      const success = await store.enterScriptMode()
      if (success) {
        message.success('已进入脚本运行模式,现在可以按停止快捷键来停止脚本')
      } else {
        message.error('进入脚本运行模式失败,请检查快捷键配置')
      }
    }, 500)
  }

  /**
   * 停止监听 - 退出脚本运行模式
   */
  async function handleStopListening() {
    // 1. 取消窗口置顶
    console.log('Deactivating window topmost...')
    window.electronAPI.sendToPython({
      action: 'deactivate_topmost'
    })

    // 2. 退出脚本运行模式
    await store.exitScriptMode()

    message.info('已退出脚本运行模式,窗口置顶已取消')
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
   * 延迟进入脚本模式(用于窗口连接后自动进入)
   */
  async function delayedEnterScriptMode() {
    // 延迟一下再进入脚本模式,确保窗口连接完成
    setTimeout(() => {
      handleStartListening(true, () => {}, () => {})
    }, 300)
  }

  return {
    // 方法
    handleStopScriptByHotkey,
    handleStartListening,
    handleStopListening,
    handleHotkeyTriggered,
    delayedEnterScriptMode
  }
}