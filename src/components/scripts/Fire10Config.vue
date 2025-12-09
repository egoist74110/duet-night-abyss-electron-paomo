<script setup lang="ts">
import { ref, watch } from 'vue'

// 定义配置接口
interface Fire10Config {
  maxRounds: number           // 最大循环轮次
  timeout: number             // 超时时间(秒)
  dungeonType: string         // 副本类型
}

// Props
const props = defineProps<{
  modelValue: Fire10Config
}>()

// Emits
const emit = defineEmits<{
  (e: 'update:modelValue', value: Fire10Config): void
}>()

// 本地配置
const config = ref<Fire10Config>({ ...props.modelValue })

// 监听配置变化，同步到父组件
watch(config, (newValue) => {
  emit('update:modelValue', newValue)
}, { deep: true })

// 副本类型选项
const dungeonTypes = [
  { label: '默认', value: 'default' },
]
</script>

<template>
  <el-card class="fire10-config-card">
    <template #header>
      <div class="card-header">
        <span>🔥 火10 脚本配置</span>
      </div>
    </template>

    <el-form label-width="140px" label-position="left">
      <!-- 基础配置 -->
      <el-form-item label="循环轮次">
        <el-input-number 
          v-model="config.maxRounds" 
          :min="1" 
          :max="99999999"
          :step="1"
          controls-position="right"
          style="width: 200px;"
        />
        <span class="form-item-tip">设置自动循环的次数（最多99999999次）</span>
      </el-form-item>

      <el-form-item label="副本类型">
        <el-select v-model="config.dungeonType" placeholder="请选择副本类型" style="width: 200px;">
          <el-option
            v-for="item in dungeonTypes"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
        <span class="form-item-tip">选择要刷的副本类型</span>
      </el-form-item>

      <el-form-item label="超时时间">
        <el-input-number 
          v-model="config.timeout" 
          :min="60" 
          :max="3600"
          :step="30"
          controls-position="right"
          style="width: 200px;"
        />
        <span class="form-item-tip">秒，超过此时间未检测到变化将停止脚本</span>
      </el-form-item>

    </el-form>
  </el-card>
</template>

<style scoped>
.fire10-config-card {
  margin-bottom: 20px;
}

.card-header {
  font-weight: 600;
  font-size: 16px;
}

.form-item-tip {
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
}

.script-description {
  font-size: 13px;
  line-height: 1.8;
}

.script-description ol {
  margin: 8px 0 0 0;
  padding-left: 20px;
}

.script-description li {
  margin: 4px 0;
}

.script-description p {
  margin: 0;
}

:deep(.el-divider__text) {
  font-weight: 600;
  color: #606266;
}
</style>
