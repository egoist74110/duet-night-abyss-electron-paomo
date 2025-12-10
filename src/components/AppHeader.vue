<!--
  应用顶部导航栏组件
  显示应用标题和运行状态
-->
<template>
  <div class="header">
    <h2>DNA Automator</h2>
    <el-tag :type="store.isRunning ? 'success' : 'danger'" size="large">
      {{ store.isRunning ? 'Running' : 'Stopped' }}
    </el-tag>
  </div>
</template>

<script setup lang="ts">
import { useGameStore } from '@/store/gameStore'

// 使用游戏状态store
const store = useGameStore()
</script>

<style scoped>
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
</style>