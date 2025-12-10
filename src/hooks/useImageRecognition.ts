/**
 * 图像识别系统Hook
 * 负责全局静默图像识别和自动点击功能
 */
import { ref, computed } from 'vue'
import { useGameStore } from '@/store/gameStore'
import { message } from '@/utils/message'

// 副本类型配置
export interface DungeonConfig {
  name: string           // 副本名称
  imagePath: string      // 图片路径
  enabled: boolean       // 是否启用
}

// 图像识别状态
export interface RecognitionStatus {
  isRunning: boolean           // 是否正在运行
  currentDungeon: string | null // 当前识别的副本
  lastRecognitionTime: number  // 上次识别时间
  recognitionCount: number     // 识别次数
  clickCount: number          // 点击次数
}

export function useImageRecognition() {
  const store = useGameStore()
  
  // 图像识别状态
  const recognitionStatus = ref<RecognitionStatus>({
    isRunning: false,
    currentDungeon: null,
    lastRecognitionTime: 0,
    recognitionCount: 0,
    clickCount: 0
  })

  // 副本配置
  const dungeonConfigs = ref<Record<string, DungeonConfig>>({
    fire: {
      name: '火',
      imagePath: 'static/dungeon/火.png',
      enabled: true
    },
    water: {
      name: '水',
      imagePath: 'static/dungeon/水.png',
      enabled: false
    },
    wind: {
      name: '风',
      imagePath: 'static/dungeon/风.png',
      enabled: false
    },
    electric: {
      name: '电',
      imagePath: 'static/dungeon/电.png',
      enabled: false
    },
    dark: {
      name: '暗',
      imagePath: 'static/dungeon/暗.png',
      enabled: false
    },
    light: {
      name: '光',
      imagePath: 'static/dungeon/光.png',
      enabled: false
    }
  })

  // 开始挑战按钮配置
  const startChallengeConfig = ref({
    imagePath: 'static/dungeon/开始挑战.png',
    enabled: true
  })

  // 识别间隔配置（毫秒）
  const recognitionInterval = ref(2000) // 2秒识别一次

  // 计算属性：启用的副本列表
  const enabledDungeons = computed(() => {
    return Object.entries(dungeonConfigs.value)
      .filter(([_, config]) => config.enabled)
      .map(([key, config]) => ({ key, ...config }))
  })

  // 计算属性：是否有启用的副本
  const hasEnabledDungeons = computed(() => {
    return enabledDungeons.value.length > 0
  })

  /**
   * 启动图像识别系统
   */
  async function startImageRecognition() {
    if (recognitionStatus.value.isRunning) {
      message.warning('图像识别系统已在运行中')
      return false
    }

    if (!hasEnabledDungeons.value) {
      message.error('请至少启用一个副本类型')
      return false
    }

    if (!store.gameWindowConnected) {
      message.error('请先连接游戏窗口')
      return false
    }

    console.log('启动图像识别系统...')
    console.log('启用的副本:', enabledDungeons.value.map(d => d.name).join(', '))

    try {
      // 发送启动命令到Python后端
      window.electronAPI.sendToPython({
        action: 'start_image_recognition',
        dungeons: enabledDungeons.value.map(d => ({
          key: d.key,
          name: d.name,
          imagePath: d.imagePath
        })),
        startChallenge: {
          imagePath: startChallengeConfig.value.imagePath
        },
        interval: recognitionInterval.value
      })

      // 更新状态
      recognitionStatus.value.isRunning = true
      recognitionStatus.value.recognitionCount = 0
      recognitionStatus.value.clickCount = 0
      recognitionStatus.value.lastRecognitionTime = Date.now()

      message.success('图像识别系统已启动')
      console.log('图像识别系统启动成功')
      return true

    } catch (error) {
      console.error('启动图像识别系统失败:', error)
      message.error('启动图像识别系统失败')
      return false
    }
  }

  /**
   * 停止图像识别系统
   */
  async function stopImageRecognition() {
    if (!recognitionStatus.value.isRunning) {
      message.warning('图像识别系统未在运行')
      return false
    }

    console.log('停止图像识别系统...')

    try {
      // 发送停止命令到Python后端
      window.electronAPI.sendToPython({
        action: 'stop_image_recognition'
      })

      // 更新状态
      recognitionStatus.value.isRunning = false
      recognitionStatus.value.currentDungeon = null

      message.success('图像识别系统已停止')
      console.log('图像识别系统停止成功')
      return true

    } catch (error) {
      console.error('停止图像识别系统失败:', error)
      message.error('停止图像识别系统失败')
      return false
    }
  }

  /**
   * 切换副本启用状态
   */
  function toggleDungeonEnabled(dungeonKey: string) {
    if (dungeonConfigs.value[dungeonKey]) {
      dungeonConfigs.value[dungeonKey].enabled = !dungeonConfigs.value[dungeonKey].enabled
      
      const config = dungeonConfigs.value[dungeonKey]
      const status = config.enabled ? '启用' : '禁用'
      message.info(`${config.name}副本已${status}`)
      
      console.log(`副本配置更新: ${config.name} -> ${status}`)
      
      // 如果识别系统正在运行，需要重新启动以应用新配置
      if (recognitionStatus.value.isRunning) {
        message.info('配置已更新，重新启动识别系统...')
        restartImageRecognition()
      }
    }
  }

  /**
   * 重新启动图像识别系统
   */
  async function restartImageRecognition() {
    console.log('重新启动图像识别系统...')
    await stopImageRecognition()
    
    // 等待一小段时间确保停止完成
    setTimeout(async () => {
      await startImageRecognition()
    }, 500)
  }

  /**
   * 设置识别间隔
   */
  function setRecognitionInterval(interval: number) {
    if (interval < 1000) {
      message.warning('识别间隔不能小于1秒')
      return
    }

    recognitionInterval.value = interval
    message.success(`识别间隔已设置为 ${interval / 1000} 秒`)

    // 如果识别系统正在运行，需要重新启动以应用新配置
    if (recognitionStatus.value.isRunning) {
      message.info('配置已更新，重新启动识别系统...')
      restartImageRecognition()
    }
  }

  /**
   * 处理来自Python的图像识别结果
   */
  function handleRecognitionResult(data: any) {
    console.log('收到图像识别结果:', data)
    
    recognitionStatus.value.recognitionCount++
    recognitionStatus.value.lastRecognitionTime = Date.now()

    if (data.found) {
      // 找到了目标图像
      const { dungeon, startChallenge, clickPosition } = data
      
      if (dungeon) {
        console.log(`识别到副本: ${dungeon.name}`)
        recognitionStatus.value.currentDungeon = dungeon.name
        message.info(`🎯 识别到副本: ${dungeon.name}`)
      }

      if (startChallenge) {
        console.log('识别到开始挑战按钮')
        message.info('🎯 识别到开始挑战按钮')
      }

      if (clickPosition) {
        console.log(`执行点击: (${clickPosition.x}, ${clickPosition.y})`)
        recognitionStatus.value.clickCount++
        message.success(`✅ 执行点击: (${clickPosition.x}, ${clickPosition.y})`)
      }

    } else {
      // 未找到目标图像
      recognitionStatus.value.currentDungeon = null
    }
  }

  /**
   * 处理图像识别错误
   */
  function handleRecognitionError(error: any) {
    console.error('图像识别错误:', error)
    message.error(`图像识别错误: ${error.message || error}`)
    
    // 如果是严重错误，停止识别系统
    if (error.critical) {
      recognitionStatus.value.isRunning = false
      recognitionStatus.value.currentDungeon = null
      message.error('图像识别系统已停止，请检查错误并重新启动')
    }
  }

  /**
   * 获取识别统计信息
   */
  const getStatistics = computed(() => {
    const runningTime = recognitionStatus.value.isRunning 
      ? Date.now() - recognitionStatus.value.lastRecognitionTime 
      : 0
    
    return {
      isRunning: recognitionStatus.value.isRunning,
      runningTime: Math.floor(runningTime / 1000), // 秒
      recognitionCount: recognitionStatus.value.recognitionCount,
      clickCount: recognitionStatus.value.clickCount,
      enabledDungeonsCount: enabledDungeons.value.length,
      currentDungeon: recognitionStatus.value.currentDungeon
    }
  })

  /**
   * 重置统计信息
   */
  function resetStatistics() {
    recognitionStatus.value.recognitionCount = 0
    recognitionStatus.value.clickCount = 0
    recognitionStatus.value.lastRecognitionTime = Date.now()
    message.info('统计信息已重置')
  }

  return {
    // 状态
    recognitionStatus,
    dungeonConfigs,
    startChallengeConfig,
    recognitionInterval,
    
    // 计算属性
    enabledDungeons,
    hasEnabledDungeons,
    getStatistics,
    
    // 方法
    startImageRecognition,
    stopImageRecognition,
    restartImageRecognition,
    toggleDungeonEnabled,
    setRecognitionInterval,
    handleRecognitionResult,
    handleRecognitionError,
    resetStatistics
  }
}