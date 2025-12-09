<script setup lang="ts">
import { ElConfigProvider } from 'element-plus'
import { useGameStore } from '@/store/gameStore'
import { onMounted, computed, ref } from 'vue'
import Fire10Config from '@/components/scripts/Fire10Config.vue'
import { message } from '@/utils/message'

const store = useGameStore()

// 快捷键输入框的聚焦状态 (暂未使用,预留给未来的UI增强功能)
// const startHotkeyFocused = ref(false)
// const stopHotkeyFocused = ref(false)

// 防抖：防止快捷键重复触发
let lastStopTrigger = 0
const DEBOUNCE_DELAY = 500 // 500ms内的重复触发将被忽略

onMounted(async () => {
  // 加载配置
  await store.loadConfig()

  // 注意: 不再自动监听快捷键,需要用户点击"开始监听"按钮

  // 监听来自 Python 的数据 - 统一处理所有类型的Python数据
  window.electronAPI.onPythonData((data) => {
    try {
      // 处理日志消息
      if (data.type === 'log') {
        store.addLog(data.data)
      }
      // 处理窗口检测响应
      else if (data.type === 'windows_found') {
        availableWindows.value = data.data.windows || []
        detectingWindow.value = false

        // 判断是否为自动检测(有关键词搜索)
        const isAutoDetect = availableWindows.value.length > 0 &&
          availableWindows.value.every(w =>
            w.title.includes(store.serverKeyword)
          )

        if (availableWindows.value.length > 0) {
          message.close();
          if (isAutoDetect) {
            // 自动检测:智能选择游戏窗口
            // 过滤掉自己的应用程序窗口(包含"Automator"的)
            const gameWindows = availableWindows.value.filter(w =>
              !w.title.includes('Automator')
            )

            if (gameWindows.length > 0) {
              // 选择第一个游戏窗口
              const targetWindow = gameWindows[0]
              selectedWindowHwnd.value = targetWindow.hwnd
              message.success(`找到游戏窗口: ${targetWindow.title}`)

              console.log(`自动选择窗口: ${targetWindow.title} (hwnd=${targetWindow.hwnd})`)
              console.log(`过滤掉 ${availableWindows.value.length - gameWindows.length} 个非游戏窗口`)

              // 自动连接
              window.electronAPI.sendToPython({
                action: 'set_window',
                hwnd: targetWindow.hwnd
              })
            } else {
              // 所有窗口都是Automator,提示用户
              message.warning('找到的窗口都是应用程序本身,请确保游戏已启动')
              console.warn('所有找到的窗口:', availableWindows.value)
            }
          } else {
            // 手动检测:仅显示找到的窗口数量
            message.success(`找到 ${availableWindows.value.length} 个窗口`)
          }
        } else {
          // 未找到窗口
          if (isAutoDetect) {
            message.error(`未找到游戏窗口,请确保游戏已启动 (搜索: ${store.serverKeyword})`)
          } else {
            message.warning('未找到窗口，请确保游戏已启动')
          }
        }
      }
      // 处理窗口连接响应
      else if (data.type === 'window_set') {
        gameWindowConnected.value = true
        gameWindowTitle.value = data.data.title
        message.success(`已连接到窗口: ${data.data.title}`)

        // 如果有待进入脚本模式的标志,连接成功后自动进入
        if (pendingStartScript.value) {
          pendingStartScript.value = false
          console.log('Window connected, now entering script mode...')

          // 延迟一下再进入脚本模式,确保窗口连接完成
          setTimeout(() => {
            handleStartListening()
          }, 300)
        }
      }
      // 处理窗口激活响应
      else if (data.type === 'window_activated') {
        if (data.data.success) {
          console.log('窗口已成功置顶')
          message.success('窗口已置顶(保持在最前面)')
        } else {
          console.warn('窗口置顶失败:', data.data.error)
          message.warning('窗口置顶失败，请查看日志')
        }
      }
      // 处理取消置顶响应
      else if (data.type === 'topmost_deactivated') {
        if (data.data.success) {
          console.log('窗口置顶已取消')
          message.success('窗口置顶已取消')
        } else {
          console.warn('取消置顶失败:', data.data.error)
          message.warning('取消置顶失败')
        }
      }
      // 未知消息类型
      else {
        message.error('游戏窗口选择失败，请尝试重新选择')
      }
    } catch (error) {
      console.error('Error handling Python data:', error, data)
      message.error('处理Python数据时出错')
    }
  })

  // 监听快捷键触发 - 只在脚本运行模式下监听停止快捷键
  window.electronAPI.onHotkeyTriggered((action) => {
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
  })
})

// 窗口检测相关状态
const detectingWindow = ref(false)
const gameWindowConnected = ref(false)
const gameWindowTitle = ref('')
const availableWindows = ref<Array<{ hwnd: number, title: string }>>([])
const selectedWindowHwnd = ref<number | null>(null)
const pendingStartScript = ref(false)  // 标志位:检测窗口后是否需要启动脚本

// 手动检测游戏窗口(显示所有窗口)
function detectGameWindow() {
  detectingWindow.value = true
  availableWindows.value = []
  window.electronAPI.sendToPython({
    action: 'detect_window',
    keyword: ''  // 空字符串表示查找所有窗口
  })
}

// 自动检测游戏窗口(根据服务器类型自动搜索并连接)
function autoDetectGameWindow() {
  detectingWindow.value = true
  availableWindows.value = []

  const keyword = store.serverKeyword
  console.log(`Auto detecting window with keyword: ${keyword}`)

  window.electronAPI.sendToPython({
    action: 'detect_window',
    keyword: keyword
  })
}

// 连接到选中的窗口
function connectToWindow() {
  if (selectedWindowHwnd.value) {
    window.electronAPI.sendToPython({
      action: 'set_window',
      hwnd: selectedWindowHwnd.value
    })
  } else {
    message.warning('请先选择一个窗口')
  }
}

// 手动置顶窗口
function activateWindow() {
  if (!gameWindowConnected.value) {
    message.warning('请先连接窗口')
    return
  }

  console.log('手动置顶窗口...')
  window.electronAPI.sendToPython({
    action: 'activate_window'
  })
  message.info('正在置顶窗口...')
}

// 取消窗口置顶
function deactivateTopmost() {
  if (!gameWindowConnected.value) {
    message.warning('请先连接窗口')
    return
  }

  console.log('取消窗口置顶...')
  window.electronAPI.sendToPython({
    action: 'deactivate_topmost'
  })
  message.info('正在取消置顶...')
}

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
    message.warning('请先配置开始和停止快捷键')
    return
  }

  const success = await store.saveConfig()
  if (success) {
    message.success('配置保存成功!快捷键已注册')
  } else {
    message.error('配置保存失败')
  }
}

// 停止脚本(通过快捷键触发)
async function handleStopScriptByHotkey() {
  console.log('Stop hotkey triggered - exiting script mode')

  // 1. 取消窗口置顶
  if (gameWindowConnected.value) {
    console.log('Deactivating window topmost...')
    window.electronAPI.sendToPython({
      action: 'deactivate_topmost'
    })
  }

  // 2. 退出脚本运行模式
  await store.exitScriptMode()

  message.info('脚本已停止,窗口置顶已取消,已退出脚本运行模式')
}

// 开始监听 - 进入脚本运行模式
async function handleStartListening() {
  if (!store.isHotkeyConfigured) {
    message.warning('请先配置并保存快捷键')
    return
  }

  // 1. 检查窗口是否连接
  if (!gameWindowConnected.value) {
    // 如果窗口未连接,自动检测并连接
    message.info('正在自动检测游戏窗口...')
    console.log('Window not connected, auto-detecting...')

    // 设置标志位,表示检测完成后需要进入脚本模式
    pendingStartScript.value = true

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

// 停止监听 - 退出脚本运行模式
async function handleStopListening() {
  // 1. 取消窗口置顶
  if (gameWindowConnected.value) {
    console.log('Deactivating window topmost...')
    window.electronAPI.sendToPython({
      action: 'deactivate_topmost'
    })
  }

  // 2. 退出脚本运行模式
  await store.exitScriptMode()

  message.info('已退出脚本运行模式,窗口置顶已取消')
}

const logString = computed(() => {
  return store.logs.map(l => `[${new Date(l.timestamp * 1000).toLocaleTimeString()}] [${l.level}] ${l.message}`).join('\n')
})

// 处理服务器类型切换 - 自动保存配置
async function handleServerTypeChange() {
  console.log('Server type changed to:', store.serverType)
  await store.saveConfig()
  message.success(`服务器类型已切换为: ${store.serverType === 'cn' ? '国服' : '国际服'}`)
}
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
        <!-- 控制面板 -->
        <el-card class="control-card">
          <template #header>
            <div class="card-header">
              <span>控制面板</span>
              <el-tag v-if="store.isScriptMode" type="success" size="small" style="margin-left: 10px;">
                脚本运行模式
              </el-tag>
            </div>
          </template>

          <el-alert v-if="store.isScriptMode" title="当前处于脚本运行模式,按下停止快捷键可停止脚本并退出此模式" type="success" :closable="false"
            style="margin-bottom: 20px;" />

          <el-space>
            <el-button v-if="!store.isScriptMode" type="primary" size="large" :disabled="!store.isHotkeyConfigured"
              @click="handleStartListening">
              脚本，启动！
            </el-button>
            <el-button v-else type="danger" size="large" @click="handleStopListening">
              停止监听
            </el-button>
          </el-space>

          <div class="control-tip">
            <p v-if="!store.isScriptMode">
              点击"启动"后,将进入脚本运行模式,此时可以按停止快捷键来停止脚本
            </p>
            <p v-else>
              当前正在监听停止快捷键: <strong>{{ store.stopHotkey }}</strong>
            </p>
          </div>
        </el-card>
        <!-- 快捷键配置面板 -->
        <el-card class="config-card">
          <template #header>
            <div class="card-header">
              <span>快捷键配置</span>
            </div>
          </template>

          <el-alert v-if="!store.isHotkeyConfigured" title="请先配置开始和停止脚本的快捷键,否则无法启动脚本" type="warning" :closable="false"
            style="margin-bottom: 20px;" />

          <el-form label-width="140px">
            <el-form-item label="开始脚本快捷键">
              <el-input v-model="store.startHotkey" placeholder="点击输入框后按下快捷键 (例如: Ctrl+F1)" readonly
                @keydown="handleKeyDown($event, 'start')" style="cursor: pointer;" />
            </el-form-item>

            <el-form-item label="停止脚本快捷键">
              <el-input v-model="store.stopHotkey" placeholder="点击输入框后按下快捷键 (例如: Ctrl+F2)" readonly
                @keydown="handleKeyDown($event, 'stop')" style="cursor: pointer;" />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="handleSaveConfig">
                保存配置
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 窗口检测面板 -->
        <el-card class="window-detection-card">
          <template #header>
            <div class="card-header">
              <span>游戏窗口检测</span>
              <el-tag :type="gameWindowConnected ? 'success' : 'danger'" size="small" style="margin-left: 10px;">
                {{ gameWindowConnected ? '已连接' : '未连接' }}
              </el-tag>
            </div>
          </template>

          <el-form label-width="140px">
            <!-- 服务器类型选择 -->
            <el-form-item label="服务器类型">
              <el-radio-group v-model="store.serverType" @change="handleServerTypeChange">
                <el-radio label="cn">国服 (二重螺旋)</el-radio>
                <el-radio label="global">国际服 (Duet Night Abyss)</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="当前窗口">
              <el-input v-model="gameWindowTitle" placeholder="未连接到游戏窗口" readonly />
            </el-form-item>

            <el-form-item label="检测窗口">
              <el-space>
                <el-button type="success" @click="autoDetectGameWindow" :loading="detectingWindow">
                  {{ detectingWindow ? '检测中...' : '自动检测窗口' }}
                </el-button>
                <el-button type="primary" @click="detectGameWindow" :loading="detectingWindow">
                  {{ detectingWindow ? '检测中...' : '手动检测窗口' }}
                </el-button>
              </el-space>
              <div class="form-item-tip">
                自动检测:根据服务器类型自动搜索并连接 | 手动检测:显示所有窗口
              </div>
            </el-form-item>

            <!-- 窗口列表 -->
            <el-form-item v-if="availableWindows.length > 0" label="选择窗口">
              <el-select v-model="selectedWindowHwnd" placeholder="请选择要连接的窗口" style="width: 100%;" filterable>
                <el-option v-for="window in availableWindows" :key="window.hwnd" :label="window.title"
                  :value="window.hwnd" />
              </el-select>
            </el-form-item>

            <el-form-item v-if="availableWindows.length > 0">
              <el-button type="success" @click="connectToWindow" :disabled="!selectedWindowHwnd">
                连接到窗口
              </el-button>
            </el-form-item>

            <el-form-item v-if="gameWindowConnected" label="窗口置顶">
              <el-space>
                <el-button type="primary" @click="activateWindow" size="small">
                  置顶窗口
                </el-button>
                <el-button type="default" @click="deactivateTopmost" size="small">
                  取消置顶
                </el-button>
              </el-space>
              <div class="form-item-tip">
                置顶:窗口会一直在最前面 | 取消置顶:恢复普通窗口
              </div>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 脚本选择面板 -->
        <el-card class="script-selector-card">
          <template #header>
            <div class="card-header">
              <span>脚本选择</span>
            </div>
          </template>

          <el-form label-width="140px">
            <el-form-item label="选择脚本">
              <el-select v-model="store.selectedScript" placeholder="请选择脚本" style="width: 100%;">
                <el-option v-for="script in store.availableScripts" :key="script.id" :label="script.name"
                  :value="script.id">
                  <span style="float: left">{{ script.name }}</span>
                  <span style="float: right; color: #8492a6; font-size: 13px">{{ script.description }}</span>
                </el-option>
              </el-select>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 脚本配置面板 - 动态渲染 -->
        <Fire10Config v-if="store.selectedScript === 'fire10'" v-model="store.scriptConfigs.fire10" />


        <!-- 日志面板 -->
        <el-card class="log-card">
          <template #header>
            <div class="card-header">
              <span>运行日志</span>
            </div>
          </template>

          <el-input v-model="logString" type="textarea" :rows="20" readonly class="log-textarea" />
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
.window-detection-card,
.script-selector-card,
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

.form-item-tip {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}

.control-tip {
  margin-top: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 14px;
  color: #606266;
}

.control-tip p {
  margin: 0;
}

.control-tip strong {
  color: #409eff;
  font-weight: 600;
}
</style>
