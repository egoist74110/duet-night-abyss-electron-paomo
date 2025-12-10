<!--
  主应用组件 - 重构后的模块化版本
  使用hooks管理逻辑，组件负责视图展示
-->
<script setup lang="ts">
import { ElConfigProvider } from 'element-plus'
import { onMounted } from 'vue'
import { useGameStore } from '@/store/gameStore'

// 导入模块化组件
import AppHeader from '@/components/AppHeader.vue'
import ControlPanel from '@/components/ControlPanel.vue'
import HotkeyConfig from '@/components/HotkeyConfig.vue'
import WindowDetection from '@/components/WindowDetection.vue'
import ScriptSelector from '@/components/ScriptSelector.vue'
import LogPanel from '@/components/LogPanel.vue'
import Fire10Config from '@/components/scripts/Fire10Config.vue'

// 导入hooks
import { useWindowDetection } from '@/hooks/useWindowDetection'
import { useScriptControl } from '@/hooks/useScriptControl'
import { usePythonData } from '@/hooks/usePythonData'

// 使用store和hooks
const store = useGameStore()
const windowDetection = useWindowDetection()
const scriptControl = useScriptControl()
const pythonData = usePythonData()

// 窗口检测组件的引用（暂时保留，未来可能需要）
// const windowDetectionRef = ref<InstanceType<typeof WindowDetection>>()

/**
 * 组件挂载时的初始化逻辑
 */
onMounted(async () => {
  // 加载配置
  await store.loadConfig()

  // 监听来自Python的数据 - 统一处理所有类型的Python数据
  window.electronAPI.onPythonData((data) => {
    pythonData.handlePythonData(
      data,
      {
        handleWindowsFound: windowDetection.handleWindowsFound,
        handleWindowSet: windowDetection.handleWindowSet,
        handleWindowActivated: windowDetection.handleWindowActivated,
        handleTopmostDeactivated: windowDetection.handleTopmostDeactivated
      },
      {
        delayedEnterScriptMode: scriptControl.delayedEnterScriptMode
      }
    )
  })

  // 监听快捷键触发 - 只在脚本运行模式下监听停止快捷键
  window.electronAPI.onHotkeyTriggered((action) => {
    scriptControl.handleHotkeyTriggered(action)
  })
})
</script>

<template>
  <el-config-provider>
    <div class="app-container">
      <!-- 顶部导航栏 -->
      <AppHeader />

      <!-- 主内容区 -->
      <div class="main-content">
        <!-- 控制面板 -->
        <ControlPanel 
          :game-window-connected="windowDetection.gameWindowConnected.value"
          :auto-detect-game-window="windowDetection.autoDetectGameWindow"
          :set-pending-start-script="windowDetection.setPendingStartScript"
        />

        <!-- 快捷键配置面板 -->
        <HotkeyConfig />

        <!-- 窗口检测面板 -->
        <WindowDetection />

        <!-- 脚本选择面板 -->
        <ScriptSelector />

        <!-- 脚本配置面板 - 动态渲染 -->
        <Fire10Config v-if="store.selectedScript === 'fire10'" v-model="store.scriptConfigs.fire10" />

        <!-- 日志面板 -->
        <LogPanel />
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

.main-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}
</style>
