<!--
  脚本控制面板组件
  负责脚本的启动和停止控制
-->
<template>
  <el-card class="control-card">
    <template #header>
      <div class="card-header">
        <span>控制面板</span>
        <el-tag v-if="store.isInitializing" type="warning" size="small" style="margin-left: 10px;">
          初始化中
        </el-tag>
        <el-tag v-else-if="store.isScriptMode" type="success" size="small" style="margin-left: 10px;">
          脚本运行模式
        </el-tag>
        <el-tag v-else type="info" size="small" style="margin-left: 10px;">
          空闲状态
        </el-tag>
      </div>
    </template>

    <!-- 状态提示 -->
    <el-alert 
      v-if="store.isInitializing" 
      title="正在进行脚本初始化流程，请稍候..." 
      type="warning" 
      :closable="false"
      style="margin-bottom: 20px;" 
    />
    <el-alert 
      v-else-if="store.isScriptMode" 
      title="当前处于脚本运行模式，按下停止快捷键可停止脚本并退出此模式" 
      type="success" 
      :closable="false"
      style="margin-bottom: 20px;" 
    />

    <!-- 控制按钮 -->
    <el-space>
      <el-button 
        v-if="!store.isScriptMode && !store.isInitializing" 
        type="primary" 
        size="large" 
        :disabled="!store.isHotkeyConfigured"
        @click="handleStartListeningClick"
      >
        脚本，启动！
      </el-button>
      <el-button 
        v-else-if="store.isInitializing" 
        type="warning" 
        size="large" 
        :loading="true"
        @click="handleStopListening"
      >
        取消初始化
      </el-button>
      <el-button 
        v-else 
        type="danger" 
        size="large" 
        @click="handleStopListening"
      >
        停止脚本
      </el-button>
    </el-space>

    <!-- 控制提示信息 -->
    <div class="control-tip">
      <p v-if="!store.isScriptMode && !store.isInitializing">
        点击"脚本，启动！"后，将开始初始化流程：检测窗口 → 置顶窗口 → 进入脚本运行模式
      </p>
      <p v-else-if="store.isInitializing">
        正在进行脚本初始化，包括窗口检测、窗口置顶等步骤...
      </p>
      <p v-else>
        脚本运行模式已激活，正在监听停止快捷键: <strong>{{ store.stopHotkey }}</strong>
      </p>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { useGameStore } from '@/store/gameStore'
import { useScriptControl } from '@/hooks/useScriptControl'

// 定义组件接收的props
interface Props {
  gameWindowConnected: boolean
  autoDetectGameWindow: () => void
  setPendingStartScript: (pending: boolean) => void
}

const props = defineProps<Props>()

// 使用相关hooks
const store = useGameStore()
const { handleStartListening, handleStopListening } = useScriptControl()

/**
 * 处理开始监听按钮点击
 */
function handleStartListeningClick() {
  handleStartListening(
    props.gameWindowConnected,
    props.autoDetectGameWindow,
    props.setPendingStartScript
  )
}
</script>

<style scoped>
.control-card {
  margin-bottom: 20px;
}

.card-header {
  font-weight: 600;
  font-size: 16px;
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