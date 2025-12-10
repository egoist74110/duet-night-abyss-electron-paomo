<!--
  游戏窗口捕获调试组件
  专门用于调试游戏窗口的捕获和连接功能
-->
<template>
  <div class="window-capture-debug">
    <div class="debug-header">
      <h3>🎮 游戏窗口捕获调试</h3>
      <p>用于调试游戏窗口的检测、连接和捕获功能</p>
    </div>

    <!-- 当前连接状态 -->
    <div class="connection-status">
      <div class="status-item">
        <span class="status-label">连接状态:</span>
        <span :class="['status-value', store.gameWindowConnected ? 'connected' : 'disconnected']">
          {{ store.gameWindowConnected ? '✅ 已连接' : '❌ 未连接' }}
        </span>
      </div>
      
      <div v-if="store.gameWindowConnected && store.pythonData?.window_title" class="status-item">
        <span class="status-label">当前窗口:</span>
        <span class="status-value">{{ store.pythonData.window_title }}</span>
      </div>
    </div>

    <!-- 调试操作按钮 -->
    <div class="debug-actions">
      <el-button 
        type="primary" 
        @click="testWindowCapture"
        :loading="testing"
      >
        {{ testing ? '正在测试...' : '🔍 测试窗口捕获' }}
      </el-button>
      
      <el-button 
        type="success" 
        @click="testWindowActivation"
        :disabled="!store.gameWindowConnected"
      >
        🔝 测试窗口置顶
      </el-button>
      
      <el-button 
        type="warning" 
        @click="captureScreenshot"
        :disabled="!store.gameWindowConnected"
      >
        📸 捕获窗口截图
      </el-button>
      
      <el-button 
        type="info" 
        @click="clearDebugLog"
      >
        🗑️ 清空日志
      </el-button>
    </div>

    <!-- 调试日志 -->
    <div class="debug-log">
      <div class="log-header">
        <h4>调试日志</h4>
        <span class="log-count">{{ debugLogs.length }} 条记录</span>
      </div>
      
      <div class="log-content" ref="logContainer">
        <div 
          v-for="(log, index) in debugLogs" 
          :key="index"
          :class="['log-item', `log-${log.type}`]"
        >
          <span class="log-time">{{ log.time }}</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
        
        <div v-if="debugLogs.length === 0" class="no-logs">
          点击上方按钮开始调试...
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { ElButton } from 'element-plus'
import { message } from '@/utils/message'
import { useGameStore } from '@/store/gameStore'

const store = useGameStore()

// 调试状态
const testing = ref(false)
const logContainer = ref<HTMLElement>()

// 调试日志接口
interface DebugLog {
  time: string
  type: 'info' | 'success' | 'error' | 'warn'
  message: string
}

const debugLogs = ref<DebugLog[]>([])

/**
 * 添加调试日志
 * @param type 日志类型
 * @param message 日志消息
 */
function addDebugLog(type: DebugLog['type'], message: string) {
  const now = new Date()
  const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`
  
  debugLogs.value.push({
    time,
    type,
    message
  })

  // 限制日志条数，避免内存占用过多
  if (debugLogs.value.length > 100) {
    debugLogs.value.shift()
  }

  // 自动滚动到底部，方便查看最新日志
  nextTick(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  })
}

/**
 * 测试窗口捕获功能
 * 这个函数会测试窗口检测、连接等核心功能
 */
async function testWindowCapture() {
  if (testing.value) return
  
  testing.value = true
  addDebugLog('info', '开始测试窗口捕获功能...')
  
  try {
    // 如果已经连接了窗口，先测试当前连接
    if (store.gameWindowConnected) {
      addDebugLog('info', '当前已连接窗口，测试连接状态...')
      
      // 发送ping命令测试连接
      window.electronAPI.sendToPython({ action: 'ping' })
      addDebugLog('success', 'Python连接测试完成')
      
    } else {
      addDebugLog('info', '当前未连接窗口，开始自动检测...')
      
      // 自动检测游戏窗口
      window.electronAPI.sendToPython({
        action: 'detect_window',
        keyword: store.serverKeyword
      })
      
      addDebugLog('info', `正在搜索关键词: "${store.serverKeyword}"`)
    }
    
  } catch (error) {
    addDebugLog('error', `测试失败: ${error}`)
    message.error('窗口捕获测试失败')
  } finally {
    // 3秒后重置测试状态
    setTimeout(() => {
      testing.value = false
    }, 3000)
  }
}

/**
 * 测试窗口激活(置顶)功能
 */
function testWindowActivation() {
  if (!store.gameWindowConnected) {
    message.error('请先连接游戏窗口')
    return
  }
  
  addDebugLog('info', '测试窗口置顶功能...')
  
  // 发送窗口激活命令
  window.electronAPI.sendToPython({ action: 'activate_window' })
  
  message.info('正在测试窗口置顶，请观察游戏窗口是否被置顶')
}

/**
 * 捕获窗口截图
 * 用于测试窗口捕获是否正常工作
 */
function captureScreenshot() {
  if (!store.gameWindowConnected) {
    message.error('请先连接游戏窗口')
    return
  }
  
  addDebugLog('info', '正在捕获窗口截图...')
  
  // 这里可以添加截图捕获的逻辑
  // 目前先记录日志
  addDebugLog('info', '截图功能开发中...')
  message.info('截图功能开发中，敬请期待')
}

/**
 * 清空调试日志
 */
function clearDebugLog() {
  debugLogs.value = []
  message.info('调试日志已清空')
}

// 监听Python数据，处理调试相关的响应
watch(() => store.pythonData, (data) => {
  if (!data) return

  switch (data.type) {
    case 'windows_found':
      handleWindowsFound(data.data)
      break
      
    case 'window_set':
      handleWindowSet(data.data)
      break
      
    case 'window_activated':
      handleWindowActivated(data.data)
      break
      
    case 'log':
      // 显示Python的日志信息
      if (data.data.level === 'INFO') {
        addDebugLog('info', data.data.message)
      } else if (data.data.level === 'ERROR') {
        addDebugLog('error', data.data.message)
      } else if (data.data.level === 'WARN') {
        addDebugLog('warn', data.data.message)
      }
      break
  }
}, { deep: true })

/**
 * 处理窗口检测结果
 */
function handleWindowsFound(data: any) {
  const windowCount = data.count || 0
  
  if (windowCount > 0) {
    addDebugLog('success', `找到 ${windowCount} 个窗口`)
    
    // 显示找到的窗口
    data.windows.forEach((window: any, index: number) => {
      addDebugLog('info', `窗口 ${index + 1}: ${window.title}`)
    })
    
    message.success(`找到 ${windowCount} 个窗口，请在窗口检测面板中选择`)
  } else {
    addDebugLog('warn', '未找到任何窗口')
    message.warning('未找到游戏窗口，请确保游戏正在运行')
  }
}

/**
 * 处理窗口连接结果
 */
function handleWindowSet(data: any) {
  if (data.title) {
    addDebugLog('success', `成功连接到窗口: ${data.title}`)
    message.success('窗口连接成功')
  } else {
    addDebugLog('error', '窗口连接失败')
    message.error('窗口连接失败')
  }
}

/**
 * 处理窗口激活结果
 */
function handleWindowActivated(data: any) {
  if (data.success) {
    addDebugLog('success', '窗口置顶成功')
    message.success('窗口已置顶')
  } else {
    addDebugLog('error', `窗口置顶失败: ${data.error || '未知错误'}`)
    message.error('窗口置顶失败')
  }
}
</script>

<style scoped>
.window-capture-debug {
  padding: 20px;
  background: white;
  border-radius: 8px;
  margin: 10px 0;
}

.debug-header {
  text-align: center;
  margin-bottom: 20px;
}

.debug-header h3 {
  margin: 0 0 8px 0;
  color: #333;
  font-size: 18px;
}

.debug-header p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.connection-status {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 15px;
  margin-bottom: 20px;
  border-left: 4px solid #007bff;
}

.status-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.status-item:last-child {
  margin-bottom: 0;
}

.status-label {
  font-weight: bold;
  color: #333;
  min-width: 80px;
}

.status-value {
  color: #666;
}

.status-value.connected {
  color: #28a745;
  font-weight: bold;
}

.status-value.disconnected {
  color: #dc3545;
  font-weight: bold;
}

.debug-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: center;
  margin-bottom: 20px;
}

.debug-log {
  background: #f8f9fa;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #dee2e6;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #e9ecef;
  border-bottom: 1px solid #dee2e6;
}

.log-header h4 {
  margin: 0;
  color: #333;
  font-size: 14px;
}

.log-count {
  color: #666;
  font-size: 12px;
}

.log-content {
  max-height: 300px;
  overflow-y: auto;
  padding: 12px;
}

.log-item {
  display: flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 4px;
  margin-bottom: 6px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.log-info {
  background: #e3f2fd;
  border-left: 3px solid #2196f3;
}

.log-success {
  background: #e8f5e8;
  border-left: 3px solid #4caf50;
}

.log-error {
  background: #ffebee;
  border-left: 3px solid #f44336;
}

.log-warn {
  background: #fff3e0;
  border-left: 3px solid #ff9800;
}

.log-time {
  color: #666;
  margin-right: 12px;
  min-width: 50px;
  font-weight: bold;
}

.log-message {
  color: #333;
  flex: 1;
}

.no-logs {
  text-align: center;
  color: #999;
  padding: 20px;
  font-style: italic;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .window-capture-debug {
    padding: 15px;
  }
  
  .debug-actions {
    flex-direction: column;
  }
  
  .debug-actions .el-button {
    width: 100%;
  }
  
  .status-item {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .status-label {
    margin-bottom: 4px;
  }
}
</style>