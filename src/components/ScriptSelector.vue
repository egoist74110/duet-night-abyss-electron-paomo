<!--
  脚本选择组件
  负责脚本类型的选择和配置
-->
<template>
  <el-card class="script-selector-card">
    <template #header>
      <div class="card-header">
        <span>脚本选择</span>
      </div>
    </template>

    <el-form label-width="140px">
      <el-form-item label="选择脚本">
        <el-select 
          v-model="store.selectedScript" 
          placeholder="请选择脚本" 
          style="width: 100%;"
        >
          <el-option 
            v-for="script in store.availableScripts" 
            :key="script.id" 
            :label="script.name"
            :value="script.id"
          >
            <span style="float: left">{{ script.name }}</span>
            <span style="float: right; color: #8492a6; font-size: 13px">{{ script.description }}</span>
          </el-option>
        </el-select>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { useGameStore } from '@/store/gameStore'

// 使用游戏状态store
const store = useGameStore()
</script>

<style scoped>
.script-selector-card {
  margin-bottom: 20px;
}

.card-header {
  font-weight: 600;
  font-size: 16px;
}
</style>