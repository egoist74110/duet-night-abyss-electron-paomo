/**
 * Python数据处理相关的Hook
 * 负责处理来自Python后端的各种数据和事件
 */
import { useGameStore } from '@/store/gameStore'
import { message } from '@/utils/message'

export function usePythonData() {
  const store = useGameStore()

  /**
   * 处理来自Python的数据
   * @param data Python发送的数据
   * @param windowHandlers 窗口相关的处理函数
   * @param scriptHandlers 脚本相关的处理函数
   */
  function handlePythonData(
    data: any,
    windowHandlers: {
      handleWindowsFound: (data: any) => void
      handleWindowSet: (data: any) => boolean
      handleWindowActivated: (data: any) => void
      handleTopmostDeactivated: (data: any) => void
    },
    scriptHandlers: {
      onWindowConnected: () => void
    }
  ) {
    try {
      // 处理日志消息
      if (data.type === 'log') {
        store.addLog(data.data)
      }
      // 处理窗口检测响应
      else if (data.type === 'windows_found') {
        windowHandlers.handleWindowsFound(data.data)
      }
      // 处理窗口连接响应
      else if (data.type === 'window_set') {
        const shouldContinueInitialization = windowHandlers.handleWindowSet(data.data)
        
        // 如果需要继续脚本初始化流程，调用窗口连接后的处理方法
        if (shouldContinueInitialization) {
          console.log('Window connected during initialization, continuing...')
          scriptHandlers.onWindowConnected()
        }
      }
      // 处理窗口激活响应
      else if (data.type === 'window_activated') {
        windowHandlers.handleWindowActivated(data.data)
      }
      // 处理取消置顶响应
      else if (data.type === 'topmost_deactivated') {
        windowHandlers.handleTopmostDeactivated(data.data)
      }
      // 未知消息类型
      else {
        console.warn('Unknown Python data type:', data.type, data)
        // 不再显示错误消息，因为可能有其他类型的数据
      }
    } catch (error) {
      console.error('Error handling Python data:', error, data)
      message.error('处理Python数据时出错')
    }
  }

  return {
    handlePythonData
  }
}