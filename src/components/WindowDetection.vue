<!--
  窗口检测组件
  负责游戏窗口的检测、连接和管理
-->
<template>
  <el-card class="window-detection-card">
    <template #header>
      <div class="card-header">
        <span>游戏窗口检测</span>
        <el-tag :type="windowStatus.statusType" size="small" style="margin-left: 10px;">
          {{ windowStatus.statusText }}
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

      <!-- 当前连接的窗口 -->
      <el-form-item label="当前窗口">
        <el-input v-model="windowStatus.title" placeholder="未连接到游戏窗口" readonly />
      </el-form-item>

      <!-- 窗口检测按钮 -->
      <el-form-item label="检测窗口">
        <el-space>
          <el-button 
            type="success" 
            @click="autoDetectGameWindow" 
            :loading="detectingWindow"
          >
            {{ detectingWindow ? '检测中...' : '自动检测窗口' }}
          </el-button>
          <el-button 
            type="primary" 
            @click="detectGameWindow" 
            :loading="detectingWindow"
          >
            {{ detectingWindow ? '检测中...' : '手动检测窗口' }}
          </el-button>
        </el-space>
        <div class="form-item-tip">
          自动检测:根据服务器类型自动搜索并连接 | 手动检测:显示所有窗口
        </div>
      </el-form-item>

      <!-- 窗口选择列表 -->
      <el-form-item v-if="availableWindows.length > 0" label="选择窗口">
        <el-select 
          v-model="selectedWindowHwnd" 
          placeholder="请选择要连接的窗口" 
          style="width: 100%;" 
          filterable
        >
          <el-option 
            v-for="window in availableWindows" 
            :key="window.hwnd" 
            :label="window.title"
            :value="window.hwnd" 
          />
        </el-select>
      </el-form-item>

      <!-- 连接窗口按钮 -->
      <el-form-item v-if="availableWindows.length > 0">
        <el-button 
          type="success" 
          @click="connectToWindow" 
          :disabled="!selectedWindowHwnd"
        >
          连接到窗口
        </el-button>
      </el-form-item>

      <!-- 窗口置顶控制 -->
      <el-form-item v-if="windowStatus.connected" label="窗口置顶">
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
</template>

<script setup lang="ts">
import { useGameStore } from '@/store/gameStore'
import { useWindowDetection } from '@/hooks/useWindowDetection'
import { useHotkeyConfig } from '@/hooks/useHotkeyConfig'

// 使用相关hooks
const store = useGameStore()
const { handleServerTypeChange } = useHotkeyConfig()
const {
  detectingWindow,
  availableWindows,
  selectedWindowHwnd,
  windowStatus,
  detectGameWindow,
  autoDetectGameWindow,
  connectToWindow,
  activateWindow,
  deactivateTopmost,
  setPendingStartScript
} = useWindowDetection()

// 暴露给父组件使用的方法
defineExpose({
  autoDetectGameWindow,
  setPendingStartScript
})
</script>

<style scoped>
.window-detection-card {
  margin-bottom: 20px;
}

.card-header {
  font-weight: 600;
  font-size: 16px;
}

.form-item-tip {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}
</style>