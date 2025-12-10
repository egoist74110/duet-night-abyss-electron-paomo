<!--
  日志面板组件
  负责显示运行日志
-->
<template>
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
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useGameStore } from '@/store/gameStore'

// 使用游戏状态store
const store = useGameStore()

// 计算属性：格式化日志字符串
const logString = computed(() => {
  return store.logs.map(l => 
    `[${new Date(l.timestamp * 1000).toLocaleTimeString()}] [${l.level}] ${l.message}`
  ).join('\n')
})
</script>

<style scoped>
.log-card {
  height: 500px;
  margin-bottom: 20px;
}

.card-header {
  font-weight: 600;
  font-size: 16px;
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