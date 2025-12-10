<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { Plus, Delete } from '@element-plus/icons-vue'

/**
 * 角色材料副本配置接口
 */
interface MaterialDungeonConfig {
  maxRounds: number           // 每次进副本的轮次数(1-99)
  timeout: number             // 超时时间(秒)
  dungeonSequence: Array<{    // 刷本顺序配置
    material: string          // 材料属性(光/暗/水/电/火)
    times: number            // 刷取次数
  }>
}

// Props - 接收父组件传递的配置数据
const props = defineProps<{
  modelValue: MaterialDungeonConfig
}>()

// Emits - 定义向父组件发送的事件
const emit = defineEmits<{
  (e: 'update:modelValue', value: MaterialDungeonConfig): void
}>()

// 默认配置 - 用户一般默认刷火和水
const defaultConfig: MaterialDungeonConfig = {
  maxRounds: 10,
  timeout: 300,
  dungeonSequence: [
    { material: '火', times: 1 },
    { material: '水', times: 1 }
  ]
}

// 本地配置状态
const config = ref<MaterialDungeonConfig>({ 
  ...defaultConfig,
  ...props.modelValue 
})

// 监听配置变化，实时同步到父组件
watch(config, (newValue) => {
  emit('update:modelValue', newValue)
}, { deep: true })

// 材料属性选项 - 按用户使用频率排序，火和水优先
const materialOptions = [
  { label: '火', value: '火', color: '#FF4500', image: '/static/role-dungeon/火.png' },
  { label: '水', value: '水', color: '#1E90FF', image: '/static/role-dungeon/水.png' },
  { label: '光', value: '光', color: '#FFD700', image: '/static/role-dungeon/光.png' },
  { label: '暗', value: '暗', color: '#8B008B', image: '/static/role-dungeon/暗.png' },
  { label: '电', value: '电', color: '#9370DB', image: '/static/role-dungeon/电.png' },
  { label: '风', value: '风', color: '#00CED1', image: '/static/role-dungeon/风.png' },
]

/**
 * 添加新的刷本配置
 * 默认添加火属性材料，因为用户最常使用
 */
function addDungeonItem() {
  config.value.dungeonSequence.push({
    material: '火',
    times: 1
  })
}

/**
 * 删除刷本配置
 */
function removeDungeonItem(index: number) {
  if (config.value.dungeonSequence.length > 1) {
    config.value.dungeonSequence.splice(index, 1)
  }
}

/**
 * 获取刷本顺序的文字描述
 */
const sequenceDescription = computed(() => {
  if (config.value.dungeonSequence.length === 0) return '未配置'
  
  const items = config.value.dungeonSequence.map(item => `${item.material}${item.times}`)
  return `循环顺序：${items.join(' → ')} → 重复...`
})

/**
 * 计算总的刷本次数（一个完整循环）
 */
const totalTimesPerCycle = computed(() => {
  return config.value.dungeonSequence.reduce((sum, item) => sum + item.times, 0)
})

/**
 * 处理图片加载错误
 * 当图片加载失败时，使用颜色块作为备用显示
 */
function handleImageError(event: Event) {
  const img = event.target as HTMLImageElement
  console.warn('Material image failed to load:', img.src)
  // 可以在这里添加备用处理逻辑
}
</script>

<template>
  <el-card class="material-dungeon-config-card">
    <template #header>
      <div class="card-header">
        <span>角色材料副本脚本配置</span>
        <el-tag type="success" size="small">自动循环</el-tag>
      </div>
    </template>

    <el-form label-width="120px" label-position="left">
      
      <!-- 每次副本轮次配置 -->
      <el-form-item label="每次副本轮次">
        <el-input-number 
          v-model="config.maxRounds" 
          :min="1" 
          :max="99"
          :step="1"
          controls-position="right"
          style="width: 150px;"
        />
        <span class="form-item-tip">每次进入副本刷取的轮次数，一般设置10轮撤离</span>
      </el-form-item>

      <!-- 超时时间配置 -->
      <el-form-item label="超时时间">
        <el-input-number 
          v-model="config.timeout" 
          :min="60" 
          :max="3600"
          :step="30"
          controls-position="right"
          style="width: 150px;"
        />
        <span class="form-item-tip">秒，超过此时间未检测到变化将停止脚本</span>
      </el-form-item>

      <!-- 刷本顺序配置 -->
      <el-form-item label="刷本顺序">
        <div class="dungeon-sequence-config">
          <!-- 顺序描述 -->
          <div class="sequence-description">
            <el-text type="primary">{{ sequenceDescription }}</el-text>
            <el-text type="info" size="small">（每个循环共 {{ totalTimesPerCycle }} 次副本,不设置就一直刷）</el-text>
          </div>

          <!-- 配置列表 -->
          <div class="sequence-list">
            <div 
              v-for="(item, index) in config.dungeonSequence" 
              :key="index"
              class="sequence-item"
            >
              <span class="item-index">{{ index + 1 }}.</span>
              
              <!-- 当前选中材料的图片预览 -->
              <div class="current-material-preview">
                <img 
                  :src="materialOptions.find(opt => opt.value === item.material)?.image || ''" 
                  :alt="item.material"
                  class="current-material-image"
                  @error="handleImageError"
                />
              </div>
              
              <!-- 材料选择 -->
              <el-select 
                v-model="item.material" 
                placeholder="选择材料"
                style="width: 120px;"
              >
                <el-option
                  v-for="option in materialOptions"
                  :key="option.value"
                  :label="option.label"
                  :value="option.value"
                >
                  <div class="material-option">
                    <img 
                      :src="option.image" 
                      :alt="option.label"
                      class="material-image"
                      @error="handleImageError"
                    />
                    <span>{{ option.label }}</span>
                  </div>
                </el-option>
              </el-select>

              <!-- 次数设置 -->
              <el-input-number 
                v-model="item.times" 
                :min="1" 
                :max="99"
                :step="1"
                controls-position="right"
                style="width: 100px;"
              />
              <span class="times-label">次</span>

              <!-- 删除按钮 -->
              <el-button 
                type="danger" 
                size="small" 
                :icon="Delete"
                :disabled="config.dungeonSequence.length <= 1"
                @click="removeDungeonItem(index)"
              >
                删除
              </el-button>
            </div>
          </div>

          <!-- 添加按钮 -->
          <el-button 
            type="primary" 
            size="small" 
            :icon="Plus"
            @click="addDungeonItem"
          >
            添加刷本配置
          </el-button>
        </div>
      </el-form-item>

      <!-- 脚本说明 -->
      <el-divider content-position="left">脚本说明</el-divider>

      <el-form-item>
        <div class="script-description">
          <p><strong>脚本功能：</strong></p>
          <ol>
            <li>按照配置的顺序循环刷取角色材料副本</li>
            <li>每次进入副本刷取指定轮次后自动撤离</li>
            <li>完成一个完整循环后重新开始</li>
            <li>异常情况自动处理，超时自动停止</li>
          </ol>
          
          <p><strong>配置说明：</strong></p>
          <ul>
            <li><strong>每次副本轮次</strong>：每次进入副本后刷取的轮次数，推荐10轮</li>
            <li><strong>刷本顺序</strong>：按顺序刷取不同属性的材料副本，可自定义次数</li>
            <li><strong>循环执行</strong>：完成所有配置的副本后，重新从第一个开始循环</li>
          </ul>

          <p><strong>使用示例：</strong></p>
          <ul>
            <li>火1水1：先刷1次火材料副本，再刷1次水材料副本，然后重复（默认配置）</li>
            <li>火2水1：先刷2次火材料副本，再刷1次水材料副本，然后重复</li>
            <li>光1暗1电1：先刷1次光材料副本，再刷1次暗材料副本，再刷1次电材料副本，然后重复</li>
          </ul>
          
          <p><strong>支持的材料属性：</strong></p>
          <ul>
            <li>光、暗、水、电、火、风（共6种属性材料）</li>
            <li>每种材料都有对应的图标显示，方便识别</li>
          </ul>
        </div>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<style scoped>
.material-dungeon-config-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  font-size: 16px;
}

.form-item-tip {
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
}

.dungeon-sequence-config {
  width: 100%;
}

.sequence-description {
  margin-bottom: 16px;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 6px;
  border-left: 4px solid #409eff;
}

.sequence-list {
  margin-bottom: 16px;
}

.sequence-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding: 12px;
  background-color: #fafafa;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
}

.item-index {
  font-weight: 600;
  color: #606266;
  min-width: 20px;
}

.material-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.material-image {
  width: 20px;
  height: 20px;
  object-fit: contain;
  border-radius: 4px;
}

.current-material-preview {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background-color: #f5f7fa;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  flex-shrink: 0;
}

.current-material-image {
  width: 32px;
  height: 32px;
  object-fit: contain;
}

.times-label {
  font-size: 14px;
  color: #606266;
}

.script-description {
  font-size: 13px;
  line-height: 1.8;
  color: #606266;
}

.script-description ol,
.script-description ul {
  margin: 8px 0 16px 0;
  padding-left: 20px;
}

.script-description li {
  margin: 4px 0;
}

.script-description p {
  margin: 0 0 8px 0;
}

.script-description strong {
  color: #303133;
}

:deep(.el-divider__text) {
  font-weight: 600;
  color: #606266;
}
</style>