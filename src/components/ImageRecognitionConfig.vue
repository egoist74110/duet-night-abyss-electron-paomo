<!--
  图像识别配置组件
  用于配置副本类型、识别间隔等参数
-->
<template>
  <div class="recognition-config">
    <div class="config-header">
      <h3>🎯 图像识别配置</h3>
      <p>配置要识别的副本类型和识别参数</p>
    </div>

    <!-- 副本类型配置 -->
    <div class="dungeon-config">
      <h4>副本类型选择</h4>
      <div class="dungeon-grid">
        <div 
          v-for="(config, key) in dungeonConfigs" 
          :key="key"
          :class="['dungeon-item', { active: config.enabled }]"
          @click="toggleDungeonEnabled(key)"
        >
          <div class="dungeon-icon">
            <img 
              :src="config.imagePath" 
              :alt="config.name"
              @error="handleImageError"
            />
          </div>
          <div class="dungeon-name">{{ config.name }}</div>
          <div class="dungeon-status">
            <el-switch 
              v-model="config.enabled"
              @change="() => toggleDungeonEnabled(key)"
            />
          </div>
        </div>
      </div>
      
      <div class="dungeon-summary">
        <span class="summary-text">
          已启用 {{ enabledDungeons.length }} / {{ Object.keys(dungeonConfigs).length }} 个副本类型
        </span>
        <el-button 
          size="small" 
          type="primary" 
          @click="enableAllDungeons"
        >
          全部启用
        </el-button>
        <el-button 
          size="small" 
          @click="disableAllDungeons"
        >
          全部禁用
        </el-button>
      </div>
    </div>

    <!-- 开始挑战按钮配置 -->
    <div class="challenge-config">
      <h4>开始挑战按钮</h4>
      <div class="challenge-item">
        <div class="challenge-preview">
          <img 
            :src="startChallengeConfig.imagePath" 
            alt="开始挑战"
            @error="handleImageError"
          />
        </div>
        <div class="challenge-info">
          <div class="challenge-name">开始挑战按钮</div>
          <div class="challenge-path">{{ startChallengeConfig.imagePath }}</div>
        </div>
        <div class="challenge-status">
          <el-switch 
            v-model="startChallengeConfig.enabled"
            disabled
          />
          <span class="status-text">必需</span>
        </div>
      </div>
    </div>

    <!-- 识别参数配置 -->
    <div class="params-config">
      <h4>识别参数</h4>
      <div class="param-item">
        <label class="param-label">识别间隔:</label>
        <div class="param-control">
          <el-slider
            v-model="recognitionInterval"
            :min="1000"
            :max="10000"
            :step="500"
            :format-tooltip="formatIntervalTooltip"
            @change="handleIntervalChange"
          />
          <span class="param-value">{{ recognitionInterval / 1000 }}秒</span>
        </div>
      </div>
      
      <div class="param-item">
        <label class="param-label">识别精度:</label>
        <div class="param-control">
          <el-select v-model="recognitionAccuracy" @change="handleAccuracyChange">
            <el-option label="高精度 (慢)" value="high" />
            <el-option label="标准精度" value="normal" />
            <el-option label="快速识别 (低精度)" value="fast" />
          </el-select>
        </div>
      </div>

      <div class="param-item">
        <label class="param-label">点击延迟:</label>
        <div class="param-control">
          <el-slider
            v-model="clickDelay"
            :min="100"
            :max="2000"
            :step="100"
            :format-tooltip="formatDelayTooltip"
          />
          <span class="param-value">{{ clickDelay }}毫秒</span>
        </div>
      </div>
    </div>

    <!-- 高级配置 -->
    <div class="advanced-config">
      <el-collapse>
        <el-collapse-item title="高级配置" name="advanced">
          <div class="advanced-content">
            <div class="param-item">
              <label class="param-label">匹配阈值:</label>
              <div class="param-control">
                <el-slider
                  v-model="matchThreshold"
                  :min="0.5"
                  :max="1.0"
                  :step="0.05"
                  :format-tooltip="formatThresholdTooltip"
                />
                <span class="param-value">{{ (matchThreshold * 100).toFixed(0) }}%</span>
              </div>
            </div>

            <div class="param-item">
              <label class="param-label">最大重试次数:</label>
              <div class="param-control">
                <el-input-number
                  v-model="maxRetries"
                  :min="1"
                  :max="10"
                  size="small"
                />
              </div>
            </div>

            <div class="param-item">
              <label class="param-label">调试模式:</label>
              <div class="param-control">
                <el-switch 
                  v-model="debugMode"
                  active-text="开启"
                  inactive-text="关闭"
                />
                <span class="param-desc">开启后会保存识别过程的截图</span>
              </div>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>

    <!-- 配置操作 -->
    <div class="config-actions">
      <el-button type="primary" @click="saveConfig">
        💾 保存配置
      </el-button>
      <el-button @click="loadConfig">
        📁 加载配置
      </el-button>
      <el-button @click="resetConfig">
        🔄 重置为默认
      </el-button>
      <el-button type="success" @click="testConfig">
        🧪 测试配置
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElButton, ElSwitch, ElSlider, ElSelect, ElOption, ElCollapse, ElCollapseItem, ElInputNumber } from 'element-plus'
import { useImageRecognition } from '@/hooks/useImageRecognition'
import { message } from '@/utils/message'

// 使用图像识别Hook
const {
  dungeonConfigs,
  startChallengeConfig,
  recognitionInterval,
  enabledDungeons,
  toggleDungeonEnabled,
  setRecognitionInterval
} = useImageRecognition()

// 额外的配置参数
const recognitionAccuracy = ref<'high' | 'normal' | 'fast'>('normal')
const clickDelay = ref(500) // 点击延迟，毫秒
const matchThreshold = ref(0.65) // 匹配阈值，0.5-1.0 (游戏界面推荐0.6-0.7)
const maxRetries = ref(3) // 最大重试次数
const debugMode = ref(false) // 调试模式

// 移除未使用的函数，直接在模板中调用toggleDungeonEnabled

/**
 * 启用所有副本
 */
function enableAllDungeons() {
  Object.keys(dungeonConfigs.value).forEach(key => {
    dungeonConfigs.value[key].enabled = true
  })
  message.success('已启用所有副本类型')
}

/**
 * 禁用所有副本
 */
function disableAllDungeons() {
  Object.keys(dungeonConfigs.value).forEach(key => {
    dungeonConfigs.value[key].enabled = false
  })
  message.info('已禁用所有副本类型')
}

/**
 * 处理识别间隔变化
 */
function handleIntervalChange(value: number | number[]) {
  // Element Plus的slider可能返回数组或单个数值，这里只处理单个数值
  const intervalValue = Array.isArray(value) ? value[0] : value
  setRecognitionInterval(intervalValue)
}

/**
 * 处理识别精度变化
 */
function handleAccuracyChange(value: string) {
  console.log('识别精度已更改为:', value)
  message.info(`识别精度已设置为: ${getAccuracyText(value)}`)
}

/**
 * 获取精度文本
 */
function getAccuracyText(accuracy: string): string {
  const map = {
    high: '高精度',
    normal: '标准精度',
    fast: '快速识别'
  }
  return map[accuracy as keyof typeof map] || '标准精度'
}

/**
 * 格式化间隔提示
 */
function formatIntervalTooltip(value: number): string {
  return `${value / 1000}秒`
}

/**
 * 格式化延迟提示
 */
function formatDelayTooltip(value: number): string {
  return `${value}毫秒`
}

/**
 * 格式化阈值提示
 */
function formatThresholdTooltip(value: number): string {
  return `${(value * 100).toFixed(0)}%`
}

/**
 * 处理图片加载错误
 */
function handleImageError(event: Event) {
  const img = event.target as HTMLImageElement
  console.warn('图片加载失败:', img.src)
  // 可以设置一个默认图片
  img.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjQwIiBoZWlnaHQ9IjQwIiBmaWxsPSIjRjVGNUY1Ii8+CjxwYXRoIGQ9Ik0yMCAzMEMyNS41MjI5IDMwIDMwIDI1LjUyMjkgMzAgMjBDMzAgMTQuNDc3MSAyNS41MjI5IDEwIDIwIDEwQzE0LjQ3NzEgMTAgMTAgMTQuNDc3MSAxMCAyMEMxMCAyNS41MjI5IDE0LjQ3NzEgMzAgMjAgMzBaIiBzdHJva2U9IiNDQ0NDQ0MiIHN0cm9rZS13aWR0aD0iMiIvPgo8L3N2Zz4K'
}

/**
 * 保存配置
 */
async function saveConfig() {
  try {
    const config = {
      dungeons: dungeonConfigs.value,
      startChallenge: startChallengeConfig.value,
      recognitionInterval: recognitionInterval.value,
      recognitionAccuracy: recognitionAccuracy.value,
      clickDelay: clickDelay.value,
      matchThreshold: matchThreshold.value,
      maxRetries: maxRetries.value,
      debugMode: debugMode.value
    }

    // 发送保存配置命令到后端
    window.electronAPI.sendToPython({
      action: 'save_recognition_config',
      config: config
    })

    message.success('配置已保存')
    console.log('图像识别配置已保存:', config)
  } catch (error) {
    console.error('保存配置失败:', error)
    message.error('保存配置失败')
  }
}

/**
 * 加载配置
 */
async function loadConfig() {
  try {
    // 发送加载配置命令到后端
    window.electronAPI.sendToPython({
      action: 'load_recognition_config'
    })

    message.info('正在加载配置...')
  } catch (error) {
    console.error('加载配置失败:', error)
    message.error('加载配置失败')
  }
}

/**
 * 重置配置为默认值
 */
function resetConfig() {
  // 重置副本配置
  Object.keys(dungeonConfigs.value).forEach(key => {
    dungeonConfigs.value[key].enabled = key === 'fire' // 只启用火副本
  })

  // 重置其他参数
  recognitionInterval.value = 2000
  recognitionAccuracy.value = 'normal'
  clickDelay.value = 500
  matchThreshold.value = 0.65
  maxRetries.value = 3
  debugMode.value = false

  message.success('配置已重置为默认值')
}

/**
 * 测试配置
 */
async function testConfig() {
  try {
    if (enabledDungeons.value.length === 0) {
      message.warning('请至少启用一个副本类型')
      return
    }

    // 发送测试配置命令到后端
    window.electronAPI.sendToPython({
      action: 'test_recognition_config',
      config: {
        dungeons: enabledDungeons.value,
        startChallenge: startChallengeConfig.value,
        recognitionAccuracy: recognitionAccuracy.value,
        matchThreshold: matchThreshold.value,
        debugMode: debugMode.value
      }
    })

    message.info('正在测试配置，请查看日志...')
  } catch (error) {
    console.error('测试配置失败:', error)
    message.error('测试配置失败')
  }
}
</script>

<style scoped>
.recognition-config {
  padding: 20px;
  background: white;
  border-radius: 8px;
  margin: 10px 0;
}

.config-header {
  text-align: center;
  margin-bottom: 30px;
}

.config-header h3 {
  margin: 0 0 10px 0;
  color: #333;
}

.config-header p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.dungeon-config,
.challenge-config,
.params-config,
.advanced-config {
  margin-bottom: 30px;
}

.dungeon-config h4,
.challenge-config h4,
.params-config h4 {
  margin: 0 0 15px 0;
  color: #333;
  font-size: 16px;
  border-bottom: 2px solid #f0f0f0;
  padding-bottom: 8px;
}

.dungeon-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
}

.dungeon-item {
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

.dungeon-item:hover {
  border-color: #409eff;
  background: #f0f9ff;
}

.dungeon-item.active {
  border-color: #67c23a;
  background: #f0f9ff;
  box-shadow: 0 2px 8px rgba(103, 194, 58, 0.2);
}

.dungeon-icon {
  width: 40px;
  height: 40px;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dungeon-icon img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.dungeon-name {
  font-weight: bold;
  color: #333;
  margin-bottom: 10px;
}

.dungeon-status {
  display: flex;
  align-items: center;
}

.dungeon-summary {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
}

.summary-text {
  flex: 1;
  color: #666;
  font-size: 14px;
}

.challenge-item {
  display: flex;
  align-items: center;
  padding: 15px;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  background: #fafafa;
}

.challenge-preview {
  width: 60px;
  height: 40px;
  margin-right: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.challenge-preview img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.challenge-info {
  flex: 1;
}

.challenge-name {
  font-weight: bold;
  color: #333;
  margin-bottom: 5px;
}

.challenge-path {
  color: #666;
  font-size: 12px;
}

.challenge-status {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-text {
  color: #666;
  font-size: 12px;
}

.param-item {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.param-label {
  min-width: 100px;
  color: #333;
  font-weight: 500;
}

.param-control {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 15px;
}

.param-value {
  min-width: 60px;
  color: #409eff;
  font-weight: bold;
}

.param-desc {
  color: #666;
  font-size: 12px;
  margin-left: 10px;
}

.advanced-content {
  padding: 15px 0;
}

.config-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
  padding-top: 20px;
  border-top: 1px solid #e9ecef;
  flex-wrap: wrap;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .recognition-config {
    padding: 15px;
  }
  
  .dungeon-grid {
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
    gap: 10px;
  }
  
  .param-item {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .param-label {
    min-width: auto;
    margin-bottom: 10px;
  }
  
  .param-control {
    width: 100%;
  }
  
  .config-actions {
    flex-direction: column;
  }
  
  .dungeon-summary {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .challenge-item {
    flex-direction: column;
    text-align: center;
  }
  
  .challenge-preview {
    margin-right: 0;
    margin-bottom: 10px;
  }
}
</style>