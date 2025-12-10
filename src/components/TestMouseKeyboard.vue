<!--
  简化的图像识别测试组件
  直接显示所有副本图片，点击后测试后端识别和点击功能
-->
<template>
  <div class="test-container">
    <div class="test-header">
      <h3>🧪 图像识别测试</h3>
      <p>点击下方图片测试后端识别和自动点击功能</p>
    </div>

    <!-- 副本图片展示区域 -->
    <div class="images-grid">
      <div 
        v-for="(dungeon, key) in dungeonImages" 
        :key="key"
        class="image-item"
        @click="testDungeonRecognition(key, dungeon)"
      >
        <div class="image-wrapper">
          <img 
            :src="dungeon.imagePath" 
            :alt="dungeon.name"
            @error="handleImageError"
          />
        </div>
        <div class="image-name">{{ dungeon.name }}</div>
        <div class="image-path">{{ dungeon.imagePath }}</div>
      </div>

      <!-- 开始挑战按钮 -->
      <div 
        class="image-item challenge-item"
        @click="testChallengeRecognition"
      >
        <div class="image-wrapper" style="width: 200px;height: 200px;">
          <img 
          style="max-width: 100%;max-height: 100%;"
            :src="challengeButtonConfig.imagePath" 
            alt="开始挑战"
            @error="handleImageError"
          />
        </div>
        <div class="image-name">开始挑战</div>
        <div class="image-path">{{ challengeButtonConfig.imagePath }}</div>
      </div>
    </div>

    <!-- 测试按钮 -->
    <div class="test-buttons">
      <el-button 
        type="primary" 
        size="large"
        @click="testFullSequence"
        :loading="testing"
      >
        {{ testing ? '正在测试完整流程...' : '🚀 测试完整流程（副本+开始挑战）' }}
      </el-button>
      
      <el-button 
        type="warning" 
        size="large"
        @click="debugMousePosition('fire', dungeonImages.fire)"
      >
        🎯 调试火副本鼠标位置
      </el-button>
      
      <el-button 
        type="warning" 
        size="large"
        @click="debugMousePosition('challenge', challengeButtonConfig)"
      >
        🎯 调试开始挑战位置
      </el-button>
      
      <el-button 
        type="success" 
        size="large"
        @click="testScreenCenter"
      >
        📍 测试屏幕中心点击
      </el-button>
      
      <el-button 
        type="info" 
        size="large"
        @click="openDebugWindow"
      >
        🔍 打开实时调试窗口
      </el-button>
      
      <el-button 
        type="primary" 
        size="large"
        @click="runComprehensiveTest"
        :loading="comprehensiveTesting"
      >
        {{ comprehensiveTesting ? '正在全面测试...' : '🧪 全面识别测试（推荐）' }}
      </el-button>
      
      <el-button 
        type="danger" 
        size="large"
        @click="runCoordinateDebugTest"
        :loading="coordinateDebugging"
      >
        {{ coordinateDebugging ? '正在调试坐标...' : '🎯 坐标精度调试（解决点击问题）' }}
      </el-button>
      
      <el-button 
        type="warning" 
        size="large"
        @click="testCoordinateConversion"
      >
        🔧 测试坐标转换修复
      </el-button>
      
      <el-button 
        type="success" 
        size="large"
        @click="runVisualMouseTest"
      >
        👁️ 可视化鼠标测试（观察鼠标移动）
      </el-button>
      
      <el-button 
        type="primary" 
        size="large"
        @click="testOriginalCoordinates"
        :loading="originalCoordinatesTesting"
      >
        {{ originalCoordinatesTesting ? '正在测试原始坐标...' : '🎯 测试原始坐标修复（验证你的建议）' }}
      </el-button>
      
      <el-button 
        type="success" 
        size="large"
        @click="debugWindowDetection"
        :loading="windowDebugging"
      >
        {{ windowDebugging ? '正在调试窗口检测...' : '🔍 调试窗口检测功能' }}
      </el-button>
    </div>

    <!-- 测试日志 -->
    <div class="test-log">
      <div class="log-header">
        <h4>测试日志</h4>
        <el-button size="small" @click="clearLog">清空</el-button>
      </div>
      <div class="log-content" ref="logContainer">
        <div 
          v-for="(log, index) in testLogs" 
          :key="index"
          :class="['log-item', `log-${log.type}`]"
        >
          <span class="log-time">{{ log.time }}</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
        
        <div v-if="testLogs.length === 0" class="no-logs">
          点击上方图片开始测试...
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { ElButton } from 'element-plus'
import { message } from '@/utils/message'
import { useGameStore } from '@/store/gameStore'

const store = useGameStore()

// 副本图片配置
const dungeonImages = ref({
  fire: {
    name: '火副本',
    imagePath: 'static/dungeon/火.png'
  },
  water: {
    name: '水副本',
    imagePath: 'static/dungeon/水.png'
  },
  wind: {
    name: '风副本',
    imagePath: 'static/dungeon/风.png'
  },
  electric: {
    name: '电副本',
    imagePath: 'static/dungeon/电.png'
  },
  dark: {
    name: '暗副本',
    imagePath: 'static/dungeon/暗.png'
  },
  light: {
    name: '光副本',
    imagePath: 'static/dungeon/光.png'
  }
})

// 开始挑战按钮配置
const challengeButtonConfig = ref({
  name: '开始挑战',
  imagePath: 'static/dungeon/开始挑战.png'
})

// 测试状态
const testing = ref(false)
const comprehensiveTesting = ref(false) // 全面测试状态
const coordinateDebugging = ref(false) // 坐标调试状态
const originalCoordinatesTesting = ref(false) // 原始坐标测试状态
const windowDebugging = ref(false) // 窗口调试状态
const logContainer = ref<HTMLElement>()
const showDebugPanel = ref(false) // 调试面板显示状态

// 移除未使用的接口定义

// 移除未使用的变量
const lastClickResult = ref<any>(null)

// 测试日志
interface TestLog {
  time: string
  type: 'info' | 'success' | 'error' | 'warn'
  message: string
}

const testLogs = ref<TestLog[]>([])

/**
 * 添加测试日志
 */
function addLog(type: TestLog['type'], message: string) {
  const now = new Date()
  const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`
  
  testLogs.value.push({
    time,
    type,
    message
  })

  // 限制日志条数
  if (testLogs.value.length > 50) {
    testLogs.value.shift()
  }

  // 自动滚动到底部
  nextTick(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  })
}

/**
 * 测试单个副本识别
 */
function testDungeonRecognition(_dungeonKey: string, dungeon: any) {
  // _dungeonKey 参数用于标识副本类型，这里主要使用dungeon对象
  if (!store.gameWindowConnected) {
    message.error('请先连接游戏窗口')
    addLog('error', '测试失败：未连接游戏窗口')
    return
  }

  addLog('info', `开始测试 ${dungeon.name} 识别...`)
  message.info(`正在测试 ${dungeon.name} 识别和点击`)

  // 发送测试命令到Python后端
  window.electronAPI.sendToPython({
    action: 'test_image_recognition_click',
    target_image: dungeon.imagePath,
    target_name: dungeon.name
  })
}

/**
 * 测试开始挑战按钮识别
 */
function testChallengeRecognition() {
  if (!store.gameWindowConnected) {
    message.error('请先连接游戏窗口')
    addLog('error', '测试失败：未连接游戏窗口')
    return
  }

  addLog('info', '开始测试 开始挑战按钮 识别...')
  message.info('正在测试开始挑战按钮识别和点击')

  // 发送测试命令到Python后端
  window.electronAPI.sendToPython({
    action: 'test_image_recognition_click',
    target_image: challengeButtonConfig.value.imagePath,
    target_name: '开始挑战按钮'
  })
}

/**
 * 测试完整流程（副本 + 开始挑战）
 */
async function testFullSequence() {
  if (!store.gameWindowConnected) {
    message.error('请先连接游戏窗口')
    addLog('error', '测试失败：未连接游戏窗口')
    return
  }

  testing.value = true
  addLog('info', '开始测试完整流程：火副本 + 开始挑战')
  message.info('正在测试完整点击流程，请观察游戏窗口')

  try {
    // 发送完整流程测试命令到Python后端
    window.electronAPI.sendToPython({
      action: 'test_full_click_sequence',
      dungeon_image: dungeonImages.value.fire.imagePath,
      challenge_image: challengeButtonConfig.value.imagePath,
      dungeon_name: '火副本'
    })
  } catch (error) {
    console.error('测试完整流程失败:', error)
    addLog('error', `测试失败: ${error}`)
    message.error('测试失败')
  } finally {
    // 3秒后重置测试状态
    setTimeout(() => {
      testing.value = false
    }, 3000)
  }
}

/**
 * 调试鼠标位置（只移动不点击）
 */
function debugMousePosition(_dungeonKey: string, dungeon: any) {
  if (!store.gameWindowConnected) {
    message.error('请先连接游戏窗口')
    addLog('error', '调试失败：未连接游戏窗口')
    return
  }

  addLog('info', `调试 ${dungeon.name} 鼠标位置...`)
  message.info(`正在调试 ${dungeon.name} 鼠标位置，观察鼠标是否移动到正确位置`)

  // 发送调试命令到Python后端
  window.electronAPI.sendToPython({
    action: 'debug_click_position',
    target_image: dungeon.imagePath,
    target_name: dungeon.name
  })
}

/**
 * 清空日志
 */
function clearLog() {
  testLogs.value = []
  message.info('日志已清空')
}

/**
 * 测试屏幕中心点击
 */
function testScreenCenter() {
  if (!store.gameWindowConnected) {
    message.error('请先连接游戏窗口')
    addLog('error', '测试失败：未连接游戏窗口')
    return
  }

  showDebugPanel.value = true
  addLog('info', '测试屏幕中心点击...')
  message.info('正在测试屏幕中心点击，观察鼠标位置')

  // 发送屏幕中心测试命令
  window.electronAPI.sendToPython({
    action: 'click_screen_center'
  })
}

/**
 * 打开实时调试窗口
 */
function openDebugWindow() {
  addLog('info', '正在打开实时调试窗口...')
  message.info('正在打开Python实时调试窗口，请稍候...')

  // 发送打开调试窗口命令
  window.electronAPI.sendToPython({
    action: 'open_debug_window'
  })
}

/**
 * 运行全面识别测试 - 这是解决识别率低问题的关键功能
 */
function runComprehensiveTest() {
  if (!store.gameWindowConnected) {
    message.error('请先连接游戏窗口')
    addLog('error', '全面测试失败：未连接游戏窗口')
    return
  }

  comprehensiveTesting.value = true
  addLog('info', '🧪 开始全面图像识别测试...')
  addLog('info', '这将测试所有副本图片在不同阈值下的识别效果')
  message.info('正在进行全面识别测试，这将帮助找到最佳的识别参数')

  try {
    // 发送全面测试命令到Python后端
    window.electronAPI.sendToPython({
      action: 'comprehensive_recognition_test'
    })
  } catch (error) {
    console.error('全面测试失败:', error)
    addLog('error', `全面测试失败: ${error}`)
    message.error('全面测试失败')
    comprehensiveTesting.value = false
  }
}

/**
 * 运行坐标调试测试 - 专门解决鼠标点击位置不准确问题
 */
function runCoordinateDebugTest() {
  if (!store.gameWindowConnected) {
    message.error('请先连接游戏窗口')
    addLog('error', '坐标调试失败：未连接游戏窗口')
    return
  }

  coordinateDebugging.value = true
  addLog('info', '🎯 开始坐标精度调试测试...')
  addLog('info', '这将测试图像识别 → 坐标转换 → 鼠标移动 → 点击的完整流程')
  message.info('正在进行坐标调试，这将帮助解决鼠标点击位置不准确的问题')

  try {
    // 使用火副本作为测试目标（因为识别效果最好）
    window.electronAPI.sendToPython({
      action: 'coordinate_debug_test',
      target_image: dungeonImages.value.fire.imagePath,
      target_name: dungeonImages.value.fire.name
    })
  } catch (error) {
    console.error('坐标调试失败:', error)
    addLog('error', `坐标调试失败: ${error}`)
    message.error('坐标调试失败')
    coordinateDebugging.value = false
  }
}

/**
 * 测试坐标转换修复效果
 */
function testCoordinateConversion() {
  if (!store.gameWindowConnected) {
    message.error('请先连接游戏窗口')
    addLog('error', '坐标转换测试失败：未连接游戏窗口')
    return
  }

  addLog('info', '🔧 测试坐标转换修复效果...')
  addLog('info', '这将验证Retina显示器的坐标缩放是否正确')
  message.info('正在测试坐标转换修复，请查看日志')

  try {
    window.electronAPI.sendToPython({
      action: 'test_coordinate_conversion'
    })
  } catch (error) {
    console.error('坐标转换测试失败:', error)
    addLog('error', `坐标转换测试失败: ${error}`)
    message.error('坐标转换测试失败')
  }
}

/**
 * 运行可视化鼠标测试 - 让用户能直观看到鼠标是否真的移动了
 */
function runVisualMouseTest() {
  addLog('info', '👁️ 开始可视化鼠标测试...')
  addLog('info', '请观察鼠标移动：先到左上角，再到屏幕中心，最后闪烁')
  message.info('正在进行可视化鼠标测试，请观察鼠标移动！')

  try {
    // 测试移动到屏幕中心
    window.electronAPI.sendToPython({
      action: 'visual_mouse_test',
      x: 960,  // 屏幕中心X
      y: 540   // 屏幕中心Y
    })
  } catch (error) {
    console.error('可视化鼠标测试失败:', error)
    addLog('error', `可视化鼠标测试失败: ${error}`)
    message.error('可视化鼠标测试失败')
  }
}

/**
 * 测试原始坐标 - 按用户建议，不进行缩放转换
 */
function testOriginalCoordinates() {
  if (!store.gameWindowConnected) {
    message.error('请先连接游戏窗口')
    addLog('error', '原始坐标测试失败：未连接游戏窗口')
    return
  }

  originalCoordinatesTesting.value = true
  addLog('info', '🎯 测试原始坐标修复（验证你的建议）...')
  addLog('info', '将进行实际图像识别，然后直接使用原始坐标进行点击测试')
  message.info('正在测试原始坐标修复，请观察鼠标是否移动到正确的图标位置！')

  try {
    window.electronAPI.sendToPython({
      action: 'test_original_coordinates',
      target_image: dungeonImages.value.fire.imagePath  // 使用火副本进行测试
    })
  } catch (error) {
    console.error('原始坐标测试失败:', error)
    addLog('error', `原始坐标测试失败: ${error}`)
    message.error('原始坐标测试失败')
    originalCoordinatesTesting.value = false
  }
}

/**
 * 调试窗口检测功能
 */
function debugWindowDetection() {
  windowDebugging.value = true
  addLog('info', '🔍 开始调试窗口检测功能...')
  addLog('info', '这将检查窗口枚举、权限和AppleScript执行情况')
  message.info('正在调试窗口检测功能，请查看日志输出')

  try {
    window.electronAPI.sendToPython({
      action: 'debug_window_detection'
    })
  } catch (error) {
    console.error('窗口检测调试失败:', error)
    addLog('error', `窗口检测调试失败: ${error}`)
    message.error('窗口检测调试失败')
    windowDebugging.value = false
  }
}

// 移除了未使用的调试函数，保持代码简洁

/**
 * 处理图片加载错误
 */
function handleImageError(event: Event) {
  const img = event.target as HTMLImageElement
  console.warn('图片加载失败:', img.src)
  addLog('warn', `图片加载失败: ${img.src}`)
}

// 监听Python数据，处理测试结果
import { watch } from 'vue'

watch(() => store.pythonData, (data) => {
  if (!data) return

  switch (data.type) {
    case 'test_recognition_result':
      handleTestResult(data.data)
      break
      
    case 'test_full_sequence_result':
      handleFullSequenceResult(data.data)
      break
      
    case 'debug_position_result':
      handleDebugPositionResult(data.data)
      break
      
    case 'center_click_result':
      handleCenterClickResult(data.data)
      break
      
    case 'simulate_click_result':
      handleSimulateClickResult(data.data)
      break
      
    case 'offset_click_result':
      handleOffsetClickResult(data.data)
      break
      
    case 'debug_window_opened':
      handleDebugWindowOpened(data.data)
      break
      
    case 'comprehensive_test_result':
      handleComprehensiveTestResult(data.data)
      break
      
    case 'coordinate_debug_result':
      handleCoordinateDebugResult(data.data)
      break
      
    case 'quick_position_result':
      handleQuickPositionResult(data.data)
      break
      
    case 'coordinate_conversion_test':
      handleCoordinateConversionTest(data.data)
      break
      
    case 'visual_mouse_test_result':
      handleVisualMouseTestResult(data.data)
      break
      
    case 'original_coordinates_test':
      handleOriginalCoordinatesTest(data.data)
      break
      
    case 'window_detection_debug':
      handleWindowDetectionDebug(data.data)
      break
      
    case 'log':
      // 显示Python日志
      if (data.data.message.includes('✅') || data.data.message.includes('❌') || data.data.message.includes('🎉')) {
        const logType = data.data.message.includes('❌') ? 'error' : 
                       data.data.message.includes('✅') || data.data.message.includes('🎉') ? 'success' : 'info'
        addLog(logType, data.data.message)
      }
      break
  }
}, { deep: true })

/**
 * 处理单个测试结果
 */
function handleTestResult(result: any) {
  const targetName = result.target_name || '目标'
  
  if (result.error) {
    addLog('error', `${targetName} 测试失败: ${result.error}`)
    message.error(`${targetName} 测试失败`)
  } else if (result.found) {
    if (result.clicked) {
      addLog('success', `${targetName} 识别并点击成功！位置: (${result.position[0]}, ${result.position[1]})`)
      message.success(`${targetName} 识别并点击成功！`)
    } else {
      addLog('warn', `${targetName} 识别成功但点击失败`)
      message.warning(`${targetName} 识别成功但点击失败`)
    }
  } else {
    addLog('warn', `${targetName} 未识别到，置信度: ${(result.confidence * 100).toFixed(1)}%`)
    message.warning(`${targetName} 未识别到`)
  }
}

/**
 * 处理完整流程测试结果
 */
function handleFullSequenceResult(result: any) {
  testing.value = false
  
  if (result.error) {
    addLog('error', `完整流程测试失败: ${result.error}`)
    message.error('完整流程测试失败')
  } else if (result.sequence_completed) {
    addLog('success', '🎉 完整流程测试成功！副本和开始挑战都已点击')
    message.success('完整流程测试成功！')
  } else {
    let status = '完整流程测试部分成功: '
    if (result.dungeon_found && result.dungeon_clicked) {
      status += '副本已点击 '
    }
    if (result.challenge_found && result.challenge_clicked) {
      status += '开始挑战已点击'
    }
    
    addLog('warn', status)
    message.warning('完整流程测试部分成功')
  }
}

/**
 * 处理调试位置结果
 */
function handleDebugPositionResult(result: any) {
  const targetName = result.target_name || '目标'
  
  if (result.error) {
    addLog('error', `${targetName} 位置调试失败: ${result.error}`)
    message.error(`${targetName} 位置调试失败`)
  } else if (result.found) {
    const original = result.original_position
    const converted = result.converted_position
    addLog('success', `${targetName} 位置调试成功！原始坐标: (${original[0]}, ${original[1]}), 转换后: (${converted[0]}, ${converted[1]})`)
    message.success(`${targetName} 鼠标已移动到目标位置，请检查位置是否正确`)
  } else {
    addLog('warn', `${targetName} 未识别到，无法调试位置`)
    message.warning(`${targetName} 未识别到`)
  }
}

/**
 * 处理屏幕中心点击结果
 */
function handleCenterClickResult(result: any) {
  if (result.error) {
    addLog('error', `屏幕中心点击测试失败: ${result.error}`)
    message.error('屏幕中心点击测试失败')
  } else {
    lastClickResult.value = result
    const target = result.target_center
    const actual = result.actual_position
    const offset = result.offset
    
    addLog('success', `屏幕中心点击测试完成！`)
    addLog('info', `屏幕尺寸: ${result.screen_size[0]}x${result.screen_size[1]}`)
    addLog('info', `目标中心: (${target[0]}, ${target[1]})`)
    addLog('info', `实际位置: (${actual[0]}, ${actual[1]})`)
    addLog('info', `位置偏差: X=${offset[0]}, Y=${offset[1]}`)
    
    if (Math.abs(offset[0]) <= 2 && Math.abs(offset[1]) <= 2) {
      message.success('屏幕中心点击非常准确！')
    } else {
      message.warning(`屏幕中心点击有偏差，X=${offset[0]}, Y=${offset[1]}`)
    }
  }
}

/**
 * 处理模拟点击结果
 */
function handleSimulateClickResult(result: any) {
  if (result.error) {
    addLog('error', `模拟点击失败: ${result.error}`)
  } else {
    lastClickResult.value = result
    const target = result.target_position
    const actual = result.actual_position
    const offset = result.offset
    
    addLog('info', `模拟点击完成: 目标(${target[0]}, ${target[1]}), 实际(${actual[0]}, ${actual[1]}), 偏差(${offset[0]}, ${offset[1]})`)
  }
}

/**
 * 处理偏移点击结果
 */
function handleOffsetClickResult(result: any) {
  if (result.error) {
    addLog('error', `偏移点击测试失败: ${result.error}`)
    message.error('偏移点击测试失败')
  } else {
    lastClickResult.value = result
    const base = result.base_position
    const appliedOffset = result.applied_offset
    const target = result.target_position
    const actual = result.actual_position
    const actualOffset = result.actual_offset
    
    addLog('success', `偏移点击测试完成！`)
    addLog('info', `基础位置: (${base[0]}, ${base[1]})`)
    addLog('info', `应用偏移: (${appliedOffset[0]}, ${appliedOffset[1]})`)
    addLog('info', `目标位置: (${target[0]}, ${target[1]})`)
    addLog('info', `实际位置: (${actual[0]}, ${actual[1]})`)
    addLog('info', `实际偏差: X=${actualOffset[0]}, Y=${actualOffset[1]}`)
    
    if (Math.abs(actualOffset[0]) <= 2 && Math.abs(actualOffset[1]) <= 2) {
      message.success('偏移点击非常准确！')
    } else {
      message.warning(`偏移点击仍有偏差，建议继续调整`)
    }
  }
}

/**
 * 处理调试窗口打开结果
 */
function handleDebugWindowOpened(result: any) {
  if (result.error) {
    addLog('error', `调试窗口打开失败: ${result.error}`)
    
    // 如果有替代方案，显示给用户
    if (result.alternatives && result.alternatives.length > 0) {
      addLog('info', '建议使用以下替代方案:')
      result.alternatives.forEach((alt: string, index: number) => {
        addLog('info', `${index + 1}. ${alt}`)
      })
      
      message.error('调试窗口不支持，请查看日志中的替代方案')
    } else {
      message.error('调试窗口打开失败')
    }
  } else {
    // 根据调试器类型显示不同的成功消息
    if (result.type === 'console') {
      addLog('success', '控制台调试器已启动！')
      addLog('info', '调试信息已输出到Python控制台')
      addLog('info', '请查看终端/命令行窗口中的调试输出')
      if (result.message) {
        addLog('info', result.message)
      }
      message.success('控制台调试器已启动，请查看Python控制台输出')
    } else if (result.type === 'simple') {
      addLog('success', '简化调试窗口已打开！')
      message.success('简化调试窗口已打开，请查看Python窗口')
    } else if (result.type === 'full') {
      addLog('success', '完整调试窗口已打开！')
      message.success('完整调试窗口已打开，请查看Python窗口')
    } else {
      addLog('success', '调试功能已启动！')
      message.success('调试功能已启动，请查看相关输出')
    }
  }
}

/**
 * 处理全面测试结果 - 这是解决识别率问题的核心功能
 */
function handleComprehensiveTestResult(result: any) {
  comprehensiveTesting.value = false
  
  if (result.error) {
    addLog('error', `全面测试失败: ${result.error}`)
    message.error('全面测试失败')
    return
  }

  addLog('success', '🎉 全面识别测试完成！')
  
  // 显示截图信息
  if (result.screenshot_info) {
    const info = result.screenshot_info
    addLog('info', `📸 截图信息: ${info.width}x${info.height}, ${info.channels}通道`)
  }
  
  // 显示测试结果统计
  const templateTests = result.template_tests || {}
  const templateCount = Object.keys(templateTests).length
  addLog('info', `📊 测试了 ${templateCount} 个模板图像`)
  
  // 显示每个模板的最佳结果
  for (const [templateName, templateResult] of Object.entries(templateTests)) {
    const bestResult = (templateResult as any).best_result
    if (bestResult) {
      const confidence = bestResult.confidence
      const threshold = bestResult.threshold
      const found = bestResult.found
      
      if (found) {
        addLog('success', `✅ ${templateName}: 识别成功 (置信度: ${confidence.toFixed(3)}, 阈值: ${threshold})`)
      } else {
        addLog('warn', `⚠️ ${templateName}: 识别失败 (最高置信度: ${confidence.toFixed(3)})`)
      }
    } else {
      addLog('error', `❌ ${templateName}: 无法识别`)
    }
  }
  
  // 显示优化建议
  const recommendations = result.recommendations || []
  if (recommendations.length > 0) {
    addLog('info', '💡 优化建议:')
    
    let excellentCount = 0
    let goodCount = 0
    let warningCount = 0
    let errorCount = 0
    
    recommendations.forEach((rec: any) => {
      const iconMap: Record<string, string> = {
        'excellent': '🌟',
        'good': '✅', 
        'warning': '⚠️',
        'error': '❌',
        'tip': '💡'
      }
      const icon = iconMap[rec.type] || '📌'
      
      addLog('info', `   ${icon} ${rec.message}`)
      
      // 统计各类结果
      if (rec.type === 'excellent') excellentCount++
      else if (rec.type === 'good') goodCount++
      else if (rec.type === 'warning') warningCount++
      else if (rec.type === 'error') errorCount++
    })
    
    // 显示总结
    addLog('info', `📈 测试总结: 优秀${excellentCount}个, 良好${goodCount}个, 需优化${warningCount}个, 失败${errorCount}个`)
    
    // 根据结果给出总体建议
    if (excellentCount + goodCount >= templateCount * 0.7) {
      addLog('success', '🎉 总体识别效果良好！当前配置可以正常使用')
      message.success('识别测试完成！大部分模板识别效果良好')
    } else if (excellentCount + goodCount >= templateCount * 0.5) {
      addLog('warn', '⚠️ 识别效果一般，建议根据上述建议优化部分模板')
      message.warning('识别测试完成！部分模板需要优化')
    } else {
      addLog('error', '❌ 识别效果较差，建议重新制作模板图像或调整游戏设置')
      message.error('识别测试完成！多数模板识别效果不佳，需要优化')
    }
  }
  
  addLog('info', '💾 详细测试结果已保存到 debug_results/recognition_debug_results.json')
}

/**
 * 处理坐标调试结果 - 专门解决点击位置问题
 */
function handleCoordinateDebugResult(result: any) {
  coordinateDebugging.value = false
  
  if (result.error) {
    addLog('error', `坐标调试失败: ${result.error}`)
    message.error('坐标调试失败')
    return
  }

  addLog('success', '🎯 坐标精度调试完成！')
  
  // 显示基本信息
  addLog('info', `📱 测试平台: ${result.platform}`)
  addLog('info', `📺 屏幕尺寸: ${result.screen_info.width}x${result.screen_info.height}`)
  
  const tests = result.tests || {}
  
  // 显示图像识别结果
  if (tests.recognition) {
    const recognition = tests.recognition
    if (recognition.found) {
      addLog('success', `✅ 图像识别: 成功识别到${result.template_name}`)
      addLog('info', `   📍 识别位置: (${recognition.position[0]}, ${recognition.position[1]})`)
      addLog('info', `   🎯 置信度: ${recognition.confidence.toFixed(3)}`)
    } else {
      addLog('error', `❌ 图像识别: 未能识别到${result.template_name}`)
      return
    }
  }
  
  // 显示坐标转换结果
  if (tests.conversion) {
    const conversion = tests.conversion
    if (conversion.screen_coords) {
      const [screenX, screenY] = conversion.screen_coords
      addLog('info', `🔄 坐标转换: (${conversion.relative_coords[0]}, ${conversion.relative_coords[1]}) → (${screenX}, ${screenY})`)
      addLog('info', `   📏 范围检查: ${conversion.in_bounds ? '✅ 在屏幕范围内' : '❌ 超出屏幕范围'}`)
    }
  }
  
  // 显示鼠标移动精度
  if (tests.movement) {
    const movement = tests.movement
    const accuracy = movement.accuracy
    const level = movement.accuracy_level
    
    if (level === '优秀') {
      addLog('success', `✅ 鼠标移动: ${level} (误差 ${accuracy.toFixed(1)} 像素)`)
    } else if (level === '良好') {
      addLog('info', `🟢 鼠标移动: ${level} (误差 ${accuracy.toFixed(1)} 像素)`)
    } else {
      addLog('warn', `⚠️ 鼠标移动: ${level} (误差 ${accuracy.toFixed(1)} 像素)`)
    }
  }
  
  // 显示点击结果
  if (tests.click) {
    const click = tests.click
    if (click.success) {
      addLog('success', `✅ 点击测试: 成功 (误差 ${click.accuracy.toFixed(1)} 像素)`)
    } else {
      addLog('error', `❌ 点击测试: 失败`)
    }
  }
  
  // 显示修复建议
  const recommendations = result.recommendations || []
  if (recommendations.length > 0) {
    addLog('info', '💡 诊断建议:')
    
    let successCount = 0
    let errorCount = 0
    let fixCount = 0
    
    recommendations.forEach((rec: any) => {
      const iconMap: Record<string, string> = {
        'success': '✅',
        'good': '🟢',
        'warning': '⚠️',
        'error': '❌',
        'fix': '🔧',
        'tip': '💡'
      }
      const icon = iconMap[rec.type] || '📌'
      
      addLog('info', `   ${icon} ${rec.message}`)
      
      if (rec.type === 'success' || rec.type === 'good') successCount++
      else if (rec.type === 'error') errorCount++
      else if (rec.type === 'fix') fixCount++
    })
    
    // 总结和建议
    if (result.success) {
      addLog('success', '🎉 坐标系统工作正常！点击位置应该是准确的')
      message.success('坐标调试完成！系统工作正常')
    } else if (errorCount === 0 && fixCount > 0) {
      addLog('warn', '⚠️ 坐标系统基本正常，但有优化空间')
      message.warning('坐标调试完成！系统基本正常，请查看优化建议')
    } else {
      addLog('error', '❌ 发现坐标问题，需要修复')
      message.error('坐标调试完成！发现问题，请查看修复建议')
    }
  }
  
  addLog('info', '💾 详细调试结果已保存到本地文件')
}

/**
 * 处理快速位置测试结果
 */
function handleQuickPositionResult(result: any) {
  if (result.error) {
    addLog('error', `快速位置测试失败: ${result.error}`)
    return
  }

  const [targetX, targetY] = result.target
  const [actualX, actualY] = result.actual
  const [errorX, errorY] = result.error
  const totalError = result.total_error
  const level = result.accuracy_level

  addLog('info', `🎯 快速位置测试结果:`)
  addLog('info', `   目标位置: (${targetX}, ${targetY})`)
  addLog('info', `   实际位置: (${actualX}, ${actualY})`)
  addLog('info', `   位置误差: X=${errorX}, Y=${errorY}`)
  addLog('info', `   总误差: ${totalError.toFixed(1)} 像素`)
  
  if (level === 'excellent') {
    addLog('success', `   精度评级: ✅ 优秀`)
  } else if (level === 'good') {
    addLog('info', `   精度评级: 🟢 良好`)
  } else {
    addLog('warn', `   精度评级: ⚠️ 需要优化`)
  }
}

/**
 * 处理坐标转换测试结果
 */
function handleCoordinateConversionTest(result: any) {
  if (result.error) {
    addLog('error', `坐标转换测试失败: ${result.error}`)
    return
  }

  const { screenshot_size, logical_size, scale_factors, test_results } = result

  addLog('success', '🔧 坐标转换测试完成！')
  addLog('info', `📸 实际截图尺寸: ${screenshot_size[0]}x${screenshot_size[1]}`)
  addLog('info', `📺 逻辑屏幕尺寸: ${logical_size[0]}x${logical_size[1]}`)
  addLog('info', `📏 缩放比例: X=${scale_factors[0].toFixed(2)}, Y=${scale_factors[1].toFixed(2)}`)

  // 检查是否检测到高DPI
  const isHighDPI = scale_factors[0] > 1.5 || scale_factors[1] > 1.5
  if (isHighDPI) {
    addLog('info', '🖥️ 检测到高DPI显示器 (Retina)')
  } else {
    addLog('info', '🖥️ 标准DPI显示器')
  }

  addLog('info', '🧪 坐标转换测试结果:')
  
  let correctConversions = 0
  test_results.forEach((test: any, index: number) => {
    const [relX, relY] = test.relative
    const [screenX, screenY] = test.screen
    const inBounds = test.in_bounds

    addLog('info', `   测试点${index + 1}: (${relX}, ${relY}) → (${screenX}, ${screenY})`)
    
    if (inBounds) {
      addLog('success', `     ✅ 转换正确，坐标在屏幕范围内`)
      correctConversions++
    } else {
      addLog('error', `     ❌ 转换错误，坐标超出屏幕范围`)
    }
  })

  // 总结
  if (correctConversions === test_results.length) {
    addLog('success', '🎉 所有坐标转换测试通过！修复生效')
    message.success('坐标转换修复成功！现在应该能正确点击了')
  } else {
    addLog('warn', `⚠️ ${correctConversions}/${test_results.length} 个测试通过，可能还需要进一步调整`)
    message.warning('坐标转换部分修复，可能需要进一步调整')
  }

  // 给出使用建议
  if (isHighDPI && correctConversions === test_results.length) {
    addLog('info', '💡 建议：现在可以重新测试图像识别点击功能')
  }
}

/**
 * 处理可视化鼠标测试结果
 */
function handleVisualMouseTestResult(result: any) {
  if (result.error) {
    addLog('error', `可视化鼠标测试失败: ${result.error}`)
    message.error('可视化鼠标测试失败')
    return
  }

  const { target, before, corner, after, error, total_error, success } = result

  addLog('success', '👁️ 可视化鼠标测试完成！')
  addLog('info', `🎯 目标位置: (${target[0]}, ${target[1]})`)
  addLog('info', `📍 移动前位置: (${before[0]}, ${before[1]})`)
  addLog('info', `📍 左上角位置: (${corner[0]}, ${corner[1]})`)
  addLog('info', `📍 移动后位置: (${after[0]}, ${after[1]})`)
  addLog('info', `📏 位置误差: X=${error[0]}, Y=${error[1]}`)
  addLog('info', `📏 总误差: ${total_error.toFixed(1)} 像素`)

  if (success) {
    addLog('success', '✅ 鼠标移动测试成功！鼠标能够正确移动到目标位置')
    message.success('鼠标移动正常！如果你看到了鼠标移动和闪烁，说明鼠标控制功能正常')
  } else {
    addLog('error', '❌ 鼠标移动测试失败！鼠标没有移动到正确位置')
    message.error('鼠标移动异常！可能是权限问题或系统限制')
  }

  // 给出诊断建议
  if (!success) {
    addLog('info', '💡 可能的解决方案:')
    addLog('info', '   1. 确保应用有辅助功能权限 (macOS)')
    addLog('info', '   2. 确保应用以管理员权限运行 (Windows)')
    addLog('info', '   3. 检查是否有其他软件阻止鼠标移动')
    addLog('info', '   4. 尝试重启应用或系统')
  } else {
    addLog('info', '💡 鼠标移动正常，问题可能在于:')
    addLog('info', '   1. 图像识别的坐标计算')
    addLog('info', '   2. 坐标转换逻辑')
    addLog('info', '   3. 游戏窗口的实际位置')
  }
}

/**
 * 处理原始坐标测试结果
 */
function handleOriginalCoordinatesTest(result: any) {
  originalCoordinatesTesting.value = false
  
  if (result.error) {
    addLog('error', `原始坐标测试失败: ${result.error}`)
    message.error('原始坐标测试失败')
    return
  }

  const { original, test_coords, before, after, error, total_error, screen_size, screenshot_size, within_bounds, confidence, success } = result

  addLog('success', '🎯 原始坐标测试完成！')
  addLog('info', `📸 图像识别: 位置(${original[0]}, ${original[1]}), 置信度: ${confidence.toFixed(3)}`)
  addLog('info', `📺 逻辑屏幕尺寸: ${screen_size[0]}x${screen_size[1]}`)
  addLog('info', `📸 截图尺寸: ${screenshot_size[0]}x${screenshot_size[1]}`)
  addLog('info', `🎯 测试坐标: (${test_coords[0]}, ${test_coords[1]})`)
  addLog('info', `📍 移动前位置: (${before[0]}, ${before[1]})`)
  addLog('info', `📍 移动后位置: (${after[0]}, ${after[1]})`)
  addLog('info', `📏 位置误差: X=${error[0]}, Y=${error[1]}, 总误差=${total_error.toFixed(1)}像素`)
  addLog('info', `📏 坐标范围检查: ${within_bounds ? '✅ 在范围内' : '❌ 超出范围'}`)

  if (success) {
    addLog('success', '🎉 原始坐标测试成功！你的建议是正确的')
    message.success('原始坐标修复成功！如果鼠标移动到了正确的图标位置，说明修复生效了')
    
    addLog('info', '💡 结论：macOS HiDPI环境下直接使用原始坐标是正确的')
    addLog('info', '   ✅ 坐标转换逻辑已修复')
    addLog('info', '   ✅ 现在可以正常进行图像识别点击了')
  } else if (!within_bounds) {
    addLog('warn', '⚠️ 原始坐标超出屏幕范围，已自动缩放')
    if (total_error <= 10) {
      addLog('success', '✅ 缩放后的坐标测试成功')
      message.success('缩放后坐标正确，系统会自动处理超出范围的坐标')
    } else {
      addLog('error', '❌ 即使缩放后坐标仍然不准确')
      message.error('坐标转换仍有问题，需要进一步调试')
    }
  } else {
    addLog('error', '❌ 原始坐标测试失败，鼠标没有移动到正确位置')
    message.error('原始坐标也不正确，问题可能更复杂')
    
    addLog('info', '💡 可能的原因:')
    addLog('info', '   1. 图像识别的坐标计算有误')
    addLog('info', '   2. 鼠标控制权限问题')
    addLog('info', '   3. 系统特殊设置影响')
  }
}

/**
 * 处理窗口检测调试结果
 */
function handleWindowDetectionDebug(result: any) {
  windowDebugging.value = false
  
  if (result.error) {
    addLog('error', `窗口检测调试失败: ${result.error}`)
    message.error('窗口检测调试失败')
    return
  }

  addLog('success', '🔍 窗口检测调试完成！')
  addLog('info', `📱 平台: ${result.platform}`)
  addLog('info', `📊 找到窗口数量: ${result.count}`)

  if (result.count > 0) {
    addLog('success', '✅ 窗口检测功能正常')
    message.success(`窗口检测正常！找到 ${result.count} 个窗口`)
    
    addLog('info', '💡 窗口检测功能已修复：')
    addLog('info', '   ✅ 现在会获取所有窗口供用户选择')
    addLog('info', '   ✅ 不再进行过滤或限制')
    addLog('info', '   ✅ 可以重新尝试手动窗口检测')
  } else {
    addLog('warn', '⚠️ 未找到任何窗口')
    message.warning('未找到窗口，可能是权限问题')
    
    addLog('info', '💡 可能的解决方案:')
    addLog('info', '   1. 检查辅助功能权限 (macOS)')
    addLog('info', '   2. 确保有其他应用程序在运行')
    addLog('info', '   3. 重启应用或系统')
  }
}
</script>

<style scoped>
.test-container {
  padding: 20px;
  background: white;
  border-radius: 8px;
  margin: 10px 0;
}

.test-header {
  text-align: center;
  margin-bottom: 30px;
}

.test-header h3 {
  margin: 0 0 10px 0;
  color: #333;
}

.test-header p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.image-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 15px;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fafafa;
}

.image-item:hover {
  border-color: #409eff;
  background: #f0f9ff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
}

.challenge-item {
  border-color: #67c23a;
}

.challenge-item:hover {
  border-color: #67c23a;
  background: #f0f9ff;
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.2);
}

.image-wrapper {
  width: 60px;
  height: 60px;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  background: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.image-wrapper img {
  max-width: 50px;
  max-height: 50px;
  object-fit: contain;
}

.image-name {
  font-weight: bold;
  color: #333;
  margin-bottom: 5px;
  text-align: center;
}

.image-path {
  color: #666;
  font-size: 12px;
  text-align: center;
  word-break: break-all;
}

.test-buttons {
  display: flex;
  flex-wrap:wrap-reverse;
  justify-content: center;
  margin-bottom: 30px;
  .el-button{
    margin-bottom: 10px;
  }
}

.test-log {
  background: #f8f9fa;
  border-radius: 8px;
  overflow: hidden;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: #e9ecef;
  border-bottom: 1px solid #dee2e6;
}

.log-header h4 {
  margin: 0;
  color: #333;
}

.log-content {
  max-height: 300px;
  overflow-y: auto;
  padding: 15px;
}

.log-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 4px;
  margin-bottom: 8px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

.log-info {
  background: #e3f2fd;
  border-left: 4px solid #2196f3;
}

.log-success {
  background: #e8f5e8;
  border-left: 4px solid #4caf50;
}

.log-error {
  background: #ffebee;
  border-left: 4px solid #f44336;
}

.log-warn {
  background: #fff3e0;
  border-left: 4px solid #ff9800;
}

.log-time {
  color: #666;
  margin-right: 15px;
  min-width: 60px;
  font-weight: bold;
}

.log-message {
  color: #333;
  flex: 1;
}

.no-logs {
  text-align: center;
  color: #999;
  padding: 30px;
  font-style: italic;
}

/* 坐标调试面板样式 */
.coordinate-debug-panel {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  margin: 20px 0;
  overflow: hidden;
}

.debug-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: #e9ecef;
  border-bottom: 1px solid #dee2e6;
}

.debug-header h4 {
  margin: 0;
  color: #333;
}

.debug-content {
  padding: 20px;
}

.current-position {
  margin-bottom: 20px;
  padding: 15px;
  background: #e3f2fd;
  border-radius: 6px;
  border-left: 4px solid #2196f3;
}

.current-position h5 {
  margin: 0 0 10px 0;
  color: #1976d2;
}

.position-info {
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

.position-info div {
  margin: 5px 0;
  color: #333;
}

.manual-offset {
  margin-bottom: 20px;
  padding: 15px;
  background: #fff3e0;
  border-radius: 6px;
  border-left: 4px solid #ff9800;
}

.manual-offset h5 {
  margin: 0 0 15px 0;
  color: #f57c00;
}

.offset-controls {
  display: flex;
  gap: 20px;
  margin-bottom: 15px;
}

.offset-input {
  display: flex;
  align-items: center;
  gap: 10px;
}

.offset-input label {
  min-width: 50px;
  font-weight: bold;
  color: #333;
}

.offset-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.quick-adjustments {
  padding: 15px;
  background: #e8f5e8;
  border-radius: 6px;
  border-left: 4px solid #4caf50;
}

.quick-adjustments h5 {
  margin: 0 0 15px 0;
  color: #388e3c;
}

.quick-buttons {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.quick-buttons .el-button {
  font-size: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .test-container {
    padding: 15px;
  }
  
  .images-grid {
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 15px;
  }
  
  .image-wrapper {
    width: 50px;
    height: 50px;
  }
  
  .image-wrapper img {
    max-width: 40px;
    max-height: 40px;
  }
  
  .log-item {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .log-time {
    min-width: auto;
    margin-bottom: 5px;
  }
  
  .offset-controls {
    flex-direction: column;
    gap: 10px;
  }
  
  .quick-buttons {
    grid-template-columns: 1fr;
  }
  
  .debug-content {
    padding: 15px;
  }
}
</style>