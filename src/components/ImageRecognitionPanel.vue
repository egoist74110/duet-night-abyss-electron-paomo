<!--
  图像识别控制面板组件
  用于启动/停止图像识别系统，显示运行状态和统计信息
-->
<template>
  <div class="recognition-panel">
    <div class="panel-header">
      <h3>🎯 图像识别系统</h3>
      <div class="status-indicator">
        <div :class="['status-dot', { active: recognitionStatus.isRunning }]"></div>
        <span class="status-text">
          {{ recognitionStatus.isRunning ? '运行中' : '已停止' }}
        </span>
      </div>
    </div>

    <!-- 系统状态 -->
    <div class="system-status">
      <div class="status-card">
        <div class="card-header">
          <h4>系统状态</h4>
          <el-button 
            size="small" 
            type="info" 
            @click="refreshStatus"
            :loading="refreshing"
          >
            🔄 刷新
          </el-button>
        </div>
        
        <div class="status-grid">
          <div class="status-item">
            <div class="status-label">运行状态:</div>
            <div :class="['status-value', recognitionStatus.isRunning ? 'running' : 'stopped']">
              {{ recognitionStatus.isRunning ? '🟢 运行中' : '🔴 已停止' }}
            </div>
          </div>
          
          <div class="status-item">
            <div class="status-label">当前副本:</div>
            <div class="status-value">
              {{ recognitionStatus.currentDungeon || '无' }}
            </div>
          </div>
          
          <div class="status-item">
            <div class="status-label">启用副本:</div>
            <div class="status-value">
              {{ enabledDungeons.length }} / {{ Object.keys(dungeonConfigs).length }}
            </div>
          </div>
          
          <div class="status-item">
            <div class="status-label">识别间隔:</div>
            <div class="status-value">
              {{ recognitionInterval / 1000 }}秒
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 统计信息 -->
    <div class="statistics">
      <div class="stats-card">
        <div class="card-header">
          <h4>运行统计</h4>
          <el-button 
            size="small" 
            @click="resetStatistics"
            :disabled="recognitionStatus.isRunning"
          >
            🔄 重置
          </el-button>
        </div>
        
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-number">{{ getStatistics.recognitionCount }}</div>
            <div class="stat-label">识别次数</div>
          </div>
          
          <div class="stat-item">
            <div class="stat-number">{{ getStatistics.clickCount }}</div>
            <div class="stat-label">点击次数</div>
          </div>
          
          <div class="stat-item">
            <div class="stat-number">{{ formatRunningTime(getStatistics.runningTime) }}</div>
            <div class="stat-label">运行时间</div>
          </div>
          
          <div class="stat-item">
            <div class="stat-number">{{ calculateSuccessRate() }}%</div>
            <div class="stat-label">成功率</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 启用的副本列表 -->
    <div class="enabled-dungeons" v-if="enabledDungeons.length > 0">
      <div class="card-header">
        <h4>启用的副本</h4>
      </div>
      <div class="dungeons-list">
        <div 
          v-for="dungeon in enabledDungeons" 
          :key="dungeon.key"
          :class="['dungeon-chip', { current: recognitionStatus.currentDungeon === dungeon.name }]"
        >
          <img 
            :src="dungeon.imagePath" 
            :alt="dungeon.name"
            class="dungeon-icon"
            @error="handleImageError"
          />
          <span class="dungeon-name">{{ dungeon.name }}</span>
          <div v-if="recognitionStatus.currentDungeon === dungeon.name" class="current-indicator">
            ⚡
          </div>
        </div>
      </div>
    </div>

    <!-- 控制按钮 -->
    <div class="control-buttons">
      <el-button 
        v-if="!recognitionStatus.isRunning"
        type="primary" 
        size="large"
        @click="handleStartRecognition"
        :disabled="!canStart"
      >
        🚀 启动图像识别
      </el-button>
      
      <el-button 
        v-else
        type="danger" 
        size="large"
        @click="handleStopRecognition"
      >
        ⏹️ 停止图像识别
      </el-button>
      
      <el-button 
        size="large"
        @click="showConfig = !showConfig"
      >
        ⚙️ {{ showConfig ? '隐藏配置' : '显示配置' }}
      </el-button>
    </div>

    <!-- 配置面板 -->
    <div v-if="showConfig" class="config-panel">
      <ImageRecognitionConfig />
    </div>

    <!-- 实时日志 -->
    <div class="real-time-log">
      <div class="card-header">
        <h4>实时日志</h4>
        <div class="log-controls">
          <el-button size="small" @click="clearLog">清空</el-button>
          <el-button 
            size="small" 
            :type="autoScroll ? 'primary' : 'default'"
            @click="autoScroll = !autoScroll"
          >
            {{ autoScroll ? '🔒 自动滚动' : '🔓 手动滚动' }}
          </el-button>
        </div>
      </div>
      
      <div class="log-content" ref="logContainer">
        <div 
          v-for="(log, index) in recentLogs" 
          :key="index"
          :class="['log-item', `log-${log.level.toLowerCase()}`]"
        >
          <span class="log-time">{{ formatLogTime(log.timestamp) }}</span>
          <span class="log-level">{{ log.level }}</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
        
        <div v-if="recentLogs.length === 0" class="no-logs">
          暂无日志信息
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue'
import { ElButton } from 'element-plus'
import { useImageRecognition } from '@/hooks/useImageRecognition'
import { useGameStore } from '@/store/gameStore'
import { message } from '@/utils/message'
import ImageRecognitionConfig from './ImageRecognitionConfig.vue'

// 使用相关Hook和Store
const {
  recognitionStatus,
  dungeonConfigs,
  recognitionInterval,
  enabledDungeons,
  hasEnabledDungeons,
  getStatistics,
  startImageRecognition,
  stopImageRecognition,
  resetStatistics,
  handleRecognitionResult,
  handleRecognitionError
} = useImageRecognition()

const store = useGameStore()

// 组件状态
const showConfig = ref(false)
const refreshing = ref(false)
const autoScroll = ref(true)
const logContainer = ref<HTMLElement>()

// 日志相关
const recentLogs = ref<Array<{
  timestamp: number
  level: string
  message: string
}>>([])

// 计算属性：是否可以启动
const canStart = computed(() => {
  return hasEnabledDungeons.value && store.gameWindowConnected
})

/**
 * 启动图像识别
 */
async function handleStartRecognition() {
  if (!store.gameWindowConnected) {
    message.error('请先连接游戏窗口')
    return
  }

  if (!hasEnabledDungeons.value) {
    message.error('请至少启用一个副本类型')
    return
  }

  const success = await startImageRecognition()
  if (success) {
    addLog('INFO', '图像识别系统启动成功')
  }
}

/**
 * 停止图像识别
 */
async function handleStopRecognition() {
  const success = await stopImageRecognition()
  if (success) {
    addLog('INFO', '图像识别系统已停止')
  }
}

/**
 * 刷新状态
 */
async function refreshStatus() {
  refreshing.value = true
  
  try {
    // 发送状态查询命令到后端
    window.electronAPI.sendToPython({
      action: 'get_recognition_status'
    })
    
    addLog('INFO', '状态刷新请求已发送')
  } catch (error) {
    console.error('刷新状态失败:', error)
    message.error('刷新状态失败')
  } finally {
    setTimeout(() => {
      refreshing.value = false
    }, 1000)
  }
}

/**
 * 计算成功率
 */
function calculateSuccessRate(): number {
  const stats = getStatistics.value
  if (stats.recognitionCount === 0) return 0
  return Math.round((stats.clickCount / stats.recognitionCount) * 100)
}

/**
 * 格式化运行时间
 */
function formatRunningTime(seconds: number): string {
  if (seconds < 60) {
    return `${seconds}秒`
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}分${remainingSeconds}秒`
  } else {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return `${hours}时${minutes}分`
  }
}

/**
 * 格式化日志时间
 */
function formatLogTime(timestamp: number): string {
  const date = new Date(timestamp * 1000)
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`
}

/**
 * 添加日志
 */
function addLog(level: string, message: string) {
  recentLogs.value.push({
    timestamp: Date.now() / 1000,
    level,
    message
  })

  // 限制日志数量
  if (recentLogs.value.length > 100) {
    recentLogs.value.shift()
  }

  // 自动滚动到底部
  if (autoScroll.value) {
    nextTick(() => {
      if (logContainer.value) {
        logContainer.value.scrollTop = logContainer.value.scrollHeight
      }
    })
  }
}

/**
 * 清空日志
 */
function clearLog() {
  recentLogs.value = []
  message.info('日志已清空')
}

/**
 * 处理图片加载错误
 */
function handleImageError(event: Event) {
  const img = event.target as HTMLImageElement
  console.warn('图片加载失败:', img.src)
}

// 监听Python数据，处理图像识别相关的响应
watch(() => store.pythonData, (data) => {
  if (!data) return

  switch (data.type) {
    case 'recognition_result':
      handleRecognitionResult(data.data)
      addLog('INFO', `识别结果: ${data.data.found ? '找到目标' : '未找到目标'}`)
      break
      
    case 'recognition_error':
      handleRecognitionError(data.data)
      addLog('ERROR', `识别错误: ${data.data.message}`)
      break
      
    case 'recognition_click':
      addLog('SUCCESS', `执行点击: (${data.data.x}, ${data.data.y})`)
      break
      
    case 'recognition_status':
      addLog('INFO', `系统状态: ${data.data.status}`)
      break
      
    case 'log':
      // 过滤图像识别相关的日志
      if (data.data.message.includes('识别') || data.data.message.includes('recognition')) {
        addLog(data.data.level, data.data.message)
      }
      break
  }
}, { deep: true })
</script>

<style scoped>
.recognition-panel {
  padding: 20px;
  background: white;
  border-radius: 8px;
  margin: 10px 0;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #f0f0f0;
}

.panel-header h3 {
  margin: 0;
  color: #333;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #ccc;
  transition: all 0.3s ease;
}

.status-dot.active {
  background: #67c23a;
  box-shadow: 0 0 8px rgba(103, 194, 58, 0.5);
}

.status-text {
  font-weight: 500;
  color: #666;
}

.system-status,
.statistics,
.enabled-dungeons,
.real-time-log {
  margin-bottom: 20px;
}

.status-card,
.stats-card {
  border: 1px solid #e9ecef;
  border-radius: 6px;
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

.card-header h4 {
  margin: 0;
  color: #333;
  font-size: 16px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  padding: 20px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-label {
  color: #666;
  font-size: 14px;
}

.status-value {
  font-weight: bold;
  color: #333;
}

.status-value.running {
  color: #67c23a;
}

.status-value.stopped {
  color: #f56c6c;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 20px;
  padding: 20px;
}

.stat-item {
  text-align: center;
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 5px;
}

.stat-label {
  color: #666;
  font-size: 14px;
}

.dungeons-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 20px;
}

.dungeon-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f0f9ff;
  border: 1px solid #409eff;
  border-radius: 20px;
  font-size: 14px;
  transition: all 0.3s ease;
  position: relative;
}

.dungeon-chip.current {
  background: #67c23a;
  color: white;
  border-color: #67c23a;
  box-shadow: 0 2px 8px rgba(103, 194, 58, 0.3);
}

.dungeon-icon {
  width: 20px;
  height: 20px;
  object-fit: contain;
}

.dungeon-name {
  font-weight: 500;
}

.current-indicator {
  position: absolute;
  top: -5px;
  right: -5px;
  font-size: 12px;
}

.control-buttons {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.config-panel {
  margin-bottom: 20px;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  overflow: hidden;
}

.log-content {
  max-height: 300px;
  overflow-y: auto;
  padding: 15px;
  background: #fafafa;
}

.log-controls {
  display: flex;
  gap: 10px;
}

.log-item {
  display: flex;
  align-items: center;
  padding: 5px 10px;
  margin-bottom: 5px;
  border-radius: 4px;
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
  margin-right: 10px;
  min-width: 60px;
}

.log-level {
  color: #333;
  font-weight: bold;
  margin-right: 10px;
  min-width: 60px;
}

.log-message {
  color: #555;
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
  .recognition-panel {
    padding: 15px;
  }
  
  .panel-header {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
  
  .status-grid,
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .control-buttons {
    flex-direction: column;
  }
  
  .dungeons-list {
    justify-content: center;
  }
  
  .log-item {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .log-time,
  .log-level {
    min-width: auto;
  }
}
</style>