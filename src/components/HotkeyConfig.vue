<!--
  快捷键配置组件
  负责快捷键的设置和保存
-->
<template>
  <el-card class="config-card">
    <template #header>
      <div class="card-header">
        <span>快捷键配置</span>
      </div>
    </template>

    <!-- 配置提示 -->
    <el-alert 
      v-if="!store.isHotkeyConfigured" 
      title="请先配置开始和停止脚本的快捷键,否则无法启动脚本" 
      type="warning" 
      :closable="false"
      style="margin-bottom: 20px;" 
    />

    <!-- 快捷键配置表单 -->
    <el-form label-width="140px">
      <el-form-item label="开始脚本快捷键">
        <el-input 
          v-model="store.startHotkey" 
          placeholder="点击输入框后按下快捷键 (例如: Ctrl+F1)" 
          readonly
          @keydown="(e) => handleKeyDown(e, 'start')" 
          style="cursor: pointer;" 
        />
      </el-form-item>

      <el-form-item label="停止脚本快捷键">
        <el-input 
          v-model="store.stopHotkey" 
          placeholder="点击输入框后按下快捷键 (例如: Ctrl+F2)" 
          readonly
          @keydown="(e) => handleKeyDown(e, 'stop')" 
          style="cursor: pointer;" 
        />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="saveConfig">
          保存配置
        </el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { useGameStore } from '@/store/gameStore'
import { useHotkeyConfig } from '@/hooks/useHotkeyConfig'

// 使用相关hooks
const store = useGameStore()
const { handleKeyDown, saveConfig } = useHotkeyConfig()
</script>

<style scoped>
.config-card {
  margin-bottom: 20px;
}

.card-header {
  font-weight: 600;
  font-size: 16px;
}
</style>