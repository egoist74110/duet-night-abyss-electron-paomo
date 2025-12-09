<script setup lang="ts">
import { ElConfigProvider, ElMessage } from 'element-plus'
import { useGameStore } from '@/store/gameStore'
import { onMounted, computed, ref } from 'vue'

const store = useGameStore()

// 快捷键输入框的聚焦状态
const startHotkeyFocused = ref(false)
const stopHotkeyFocused = ref(false)

onMounted(async () => {
  // 加载配置
  await store.loadConfig()
  
  // 监听来自 Python 的数据
  window.electronAPI.onPythonData((data) => {
    if (data.type === 'log') {
      store.addLog(data.data)
    }
  })

  // 监听快捷键触发
  window.electronAPI.onHotkeyTriggered((action) => {
    if (action === 'start') {
      handleStartScript()
    } else if (action === 'stop') {
      handleStopScript()
    }
  })
})

// 处理键盘事件,捕获快捷键
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

// 保存配置
async function handleSaveConfig() {
  if (!store.startHotkey || !store.stopHotkey) {
    ElMessage.warning('请先配置开始和停止快捷键')
    return
  }
  
  const success = await store.saveConfig()
  if (success) {
    ElMessage.success('配置保存成功!快捷键已注册')
  } else {
    ElMessage.error('配置保存失败')
  }
}

// 启动脚本
function handleStartScript() {
  if (!store.isHotkeyConfigured) {
    ElMessage.warning('请先配置并保存快捷键')
    return
  }
  if (!store.isRunning) {
    const success = store.toggleScript()
    if (success) {
      ElMessage.success('脚本已启动')
    }
  }
}

// 停止脚本
function handleStopScript() {
  if (store.isRunning) {
    store.toggleScript()
    ElMessage.info('脚本已停止')
  }
}

// 切换脚本状态
function handleToggleScript() {
  if (!store.isHotkeyConfigured) {
    ElMessage.warning('请先配置并保存快捷键')
    return
  }
  store.toggleScript()
}

const logString = computed(() => {
  return store.logs.map(l => `[${new Date(l.timestamp * 1000).toLocaleTimeString()}] [${l.level}] ${l.message}`).join('\n')
})
</script>

<template>
  <el-config-provider>
    <div class="app-container">
      <!-- 顶部导航栏 -->
      <div class="header">
        <h2>DNA Automator</h2>
        <el-tag :type="store.isRunning ? 'success' : 'danger'" size="large">
          {{ store.isRunning ? 'Running' : 'Stopped' }}
        </el-tag>
      </div>

      <!-- 主内容区 -->
      <div class="main-content">
        <!-- 快捷键配置面板 -->
        <el-card class="config-card">
          <template #header>
            <div class="card-header">
              <span>快捷键配置</span>
            </div>
          </template>
          
          <el-alert
            v-if="!store.isHotkeyConfigured"
            title="请先配置开始和停止脚本的快捷键,否则无法启动脚本"
            type="warning"
            :closable="false"
            style="margin-bottom: 20px;"
          />

          <el-form label-width="140px">
            <el-form-item label="开始脚本快捷键">
              <el-input
                v-model="store.startHotkey"
                placeholder="点击输入框后按下快捷键 (例如: Ctrl+F1)"
                readonly
                @focus="startHotkeyFocused = true"
                @blur="startHotkeyFocused = false"
                @keydown="handleKeyDown($event, 'start')"
                style="cursor: pointer;"
              />
            </el-form-item>

            <el-form-item label="停止脚本快捷键">
              <el-input
                v-model="store.stopHotkey"
                placeholder="点击输入框后按下快捷键 (例如: Ctrl+F2)"
                readonly
                @focus="stopHotkeyFocused = true"
                @blur="stopHotkeyFocused = false"
                @keydown="handleKeyDown($event, 'stop')"
                style="cursor: pointer;"
              />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="handleSaveConfig">
                保存配置
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 控制面板 -->
        <el-card class="control-card">
          <template #header>
            <div class="card-header">
              <span>控制面板</span>
            </div>
          </template>
          
          <el-space>
            <el-button
              type="primary"
              size="large"
              :disabled="!store.isHotkeyConfigured"
              @click="handleToggleScript"
            >
              {{ store.isRunning ? '停止脚本' : '启动脚本' }}
            </el-button>
            <el-button size="large" @click="store.ping">Ping Python</el-button>
          </el-space>
        </el-card>

        <!-- 日志面板 -->
        <el-card class="log-card">
          <template #header>
            <div class="card-header">
              <span>运行日志</span>
            </div>
          </template>
          
          <el-input
            v-model="logString"
            type="textarea"
            :rows="20"
            readonly
            class="log-textarea"
          />
        </el-card>
      </div>
    </div>
  </el-config-provider>
</template>

<style scoped>
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.header {
  height: 60px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.main-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.config-card,
.control-card,
.log-card {
  margin-bottom: 20px;
}

.card-header {
  font-weight: 600;
  font-size: 16px;
}

.log-card {
  height: 500px;
}

.log-textarea {
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

.log-textarea :deep(textarea) {
  background: #1e1e1e;
  color: #d4d4d4;
  font-family: 'Courier New', monospace;
}
</style>
