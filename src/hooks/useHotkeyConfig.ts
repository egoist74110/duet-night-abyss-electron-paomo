/**
 * 快捷键配置相关的Hook
 * 负责快捷键的配置、保存和键盘事件处理
 */
import { useGameStore } from '@/store/gameStore'
import { message } from '@/utils/message'

export function useHotkeyConfig() {
  const store = useGameStore()

  /**
   * 处理键盘事件,捕获快捷键
   * @param event 键盘事件
   * @param type 快捷键类型 ('start' | 'stop')
   */
  function handleKeyDown(event: KeyboardEvent, type: 'start' | 'stop') {
    event.preventDefault()

    const keys: string[] = []

    // 修饰键
    if (event.ctrlKey || event.metaKey) keys.push('CommandOrControl')
    if (event.altKey) keys.push('Alt')
    if (event.shiftKey) keys.push('Shift')

    // 主键
    const key = event.key
    if (key && key !== 'Control' && key !== 'Meta' && key !== 'Alt' && key !== 'Shift') {
      // 特殊键映射
      const keyMap: Record<string, string> = {
        ' ': 'Space',
        'ArrowUp': 'Up',
        'ArrowDown': 'Down',
        'ArrowLeft': 'Left',
        'ArrowRight': 'Right'
      }
      keys.push(keyMap[key] || key.toUpperCase())
    }

    if (keys.length > 0) {
      const hotkey = keys.join('+')
      if (type === 'start') {
        store.startHotkey = hotkey
      } else {
        store.stopHotkey = hotkey
      }
    }
  }

  /**
   * 保存快捷键配置
   */
  async function saveConfig() {
    if (!store.startHotkey || !store.stopHotkey) {
      message.warning('请先配置开始和停止快捷键')
      return false
    }

    const success = await store.saveConfig()
    if (success) {
      message.success('配置保存成功!快捷键已注册')
      return true
    } else {
      message.error('配置保存失败')
      return false
    }
  }

  /**
   * 处理服务器类型切换 - 自动保存配置
   */
  async function handleServerTypeChange() {
    console.log('Server type changed to:', store.serverType)
    await store.saveConfig()
    message.success(`服务器类型已切换为: ${store.serverType === 'cn' ? '国服' : '国际服'}`)
  }

  return {
    // 方法
    handleKeyDown,
    saveConfig,
    handleServerTypeChange
  }
}