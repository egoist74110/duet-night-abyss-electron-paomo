<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowUp, ArrowDown } from '@element-plus/icons-vue'


/**
 * 角色材料副本配置接口
 */
interface MaterialDungeonConfig {
  dungeonType: string         // 副本类型(必需，用于确定开始和结束脚本)
  timeout: number             // 超时时间(秒)
  materialSequence: Array<{   // 刷本顺序配置
    material: string          // 材料属性(光/暗/水/电/火/风)
    times: number            // 刷取次数
    dungeonSequence: number  // 每次进副本打多少轮次(1-99)
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

// 默认配置 - 默认只刷火循环
const defaultConfig: MaterialDungeonConfig = {
  dungeonType: 'role-material', // 角色材料副本类型
  timeout: 300,                 // 5分钟超时
  materialSequence: [
    { 
      material: '火', 
      times: 1, 
      dungeonSequence: 10 // 每次进副本打10轮次
    }
  ]
}

// 本地配置状态
const config = ref<MaterialDungeonConfig>({ 
  ...defaultConfig,
  ...props.modelValue 
})

// 选中的材料列表 - 用于多选下拉框
const selectedMaterials = ref<string[]>([])

// 监听配置变化，实时同步到父组件
watch(config, (newValue) => {
  emit('update:modelValue', newValue)
}, { deep: true })

// 监听props变化，同步更新选中的材料列表
watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    config.value = { ...defaultConfig, ...newValue }
    initSelectedMaterials()
  }
}, { immediate: true })

// 组件挂载时初始化选中的材料列表
onMounted(() => {
  initSelectedMaterials()
})

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
 * 初始化选中的材料列表
 */
function initSelectedMaterials() {
  selectedMaterials.value = config.value.materialSequence.map(item => item.material)
}

/**
 * 处理材料选择变化
 * 当用户在多选下拉框中选择或取消材料时触发
 */
function handleMaterialSelectionChange(newSelection: string[]) {
  const currentMaterials = config.value.materialSequence.map(item => item.material)
  
  // 检查是否试图删除所有材料（至少保留一个）
  if (newSelection.length === 0) {
    ElMessage.warning('至少需要选择一种材料属性！')
    // 恢复之前的选择状态
    selectedMaterials.value = [...currentMaterials]
    return
  }
  
  // 找出新增的材料
  const addedMaterials = newSelection.filter(material => !currentMaterials.includes(material))
  
  // 找出删除的材料
  const removedMaterials = currentMaterials.filter(material => !newSelection.includes(material))
  
  // 添加新选择的材料
  addedMaterials.forEach(material => {
    config.value.materialSequence.push({
      material: material,
      times: 1,
      dungeonSequence: 10 // 默认每次打10轮次
    })
  })
  
  // 删除取消选择的材料
  removedMaterials.forEach(material => {
    const index = config.value.materialSequence.findIndex(item => item.material === material)
    if (index !== -1) {
      config.value.materialSequence.splice(index, 1)
    }
  })
  
  // 按照materialOptions的顺序重新排序materialSequence
  const orderedSequence = materialOptions
    .filter(option => newSelection.includes(option.value))
    .map(option => {
      const existingItem = config.value.materialSequence.find(item => item.material === option.value)
      return existingItem || { material: option.value, times: 1, dungeonSequence: 10 }
    })
  
  config.value.materialSequence = orderedSequence
}

/**
 * 获取刷本顺序的文字描述
 */
const sequenceDescription = computed(() => {
  if (config.value.materialSequence.length === 0) return '未配置'
  
  const items = config.value.materialSequence.map(item => 
    `${item.material}${item.times}次(${item.dungeonSequence}轮)`
  )
  return `循环顺序：${items.join(' → ')} → 重复...`
})

/**
 * 计算总的刷本次数（一个完整循环）
 */
const totalTimesPerCycle = computed(() => {
  return config.value.materialSequence.reduce((sum, item) => sum + item.times, 0)
})



/**
 * 副本类型选项 - 用于确定开始和结束脚本
 */
const dungeonTypeOptions = [
  { 
    label: '角色材料副本', 
    value: 'role-material',
    description: '角色升级材料副本，包含光、暗、水、电、火、风六种属性材料'
  },
  // 未来可以添加更多副本类型
  // { label: '武器材料副本', value: 'weapon-material', description: '武器升级材料副本' },
  // { label: '经验副本', value: 'exp-dungeon', description: '角色经验副本' }
]



/**
 * 向上移动材料配置项
 * @param index 当前项的索引
 */
function moveItemUp(index: number) {
  if (index > 0) {
    // 添加移动动画效果
    addMoveAnimation(index)
    
    // 延迟执行移动操作，让动画效果更明显
    setTimeout(() => {
      const item = config.value.materialSequence[index]
      config.value.materialSequence.splice(index, 1)
      config.value.materialSequence.splice(index - 1, 0, item)
      
      // 同步更新selectedMaterials的顺序
      updateSelectedMaterialsOrder()
    }, 150)
  }
}

/**
 * 向下移动材料配置项
 * @param index 当前项的索引
 */
function moveItemDown(index: number) {
  if (index < config.value.materialSequence.length - 1) {
    // 添加移动动画效果
    addMoveAnimation(index)
    
    // 延迟执行移动操作，让动画效果更明显
    setTimeout(() => {
      const item = config.value.materialSequence[index]
      config.value.materialSequence.splice(index, 1)
      config.value.materialSequence.splice(index + 1, 0, item)
      
      // 同步更新selectedMaterials的顺序
      updateSelectedMaterialsOrder()
    }, 150)
  }
}

/**
 * 添加移动动画效果
 * @param index 要添加动画的项索引
 */
function addMoveAnimation(index: number) {
  // 通过DOM操作添加动画类
  const sequenceItems = document.querySelectorAll('.sequence-item')
  const targetItem = sequenceItems[index] as HTMLElement
  
  if (targetItem) {
    targetItem.classList.add('moving')
    
    // 动画结束后移除类
    setTimeout(() => {
      targetItem.classList.remove('moving')
    }, 300)
  }
}

/**
 * 更新selectedMaterials的顺序，与materialSequence保持一致
 */
function updateSelectedMaterialsOrder() {
  selectedMaterials.value = config.value.materialSequence.map(item => item.material)
}

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
      
      <!-- 副本类型配置 -->
      <el-form-item label="副本类型">
        <el-select 
          v-model="config.dungeonType" 
          placeholder="选择副本类型"
          style="width: 200px;"
        >
          <el-option
            v-for="option in dungeonTypeOptions"
            :key="option.value"
            :label="option.label"
            :value="option.value"
          >
            <div>
              <div>{{ option.label }}</div>
              <div style="font-size: 12px; color: #999;">{{ option.description }}</div>
            </div>
          </el-option>
        </el-select>
        <span class="form-item-tip">选择要刷取的副本类型，不同类型有不同的开始和结束脚本</span>
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
          <!-- 材料选择器 -->
          <div class="material-selector">
            <el-select
              v-model="selectedMaterials"
              multiple
              placeholder="选择要刷取的材料属性"
              style="width: 100%; margin-bottom: 16px;"
              @change="handleMaterialSelectionChange"
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
          </div>

          <!-- 顺序描述 -->
          <div class="sequence-description" v-if="config.materialSequence.length > 0">
            <el-text type="primary">{{ sequenceDescription }}</el-text>
            <el-text type="info" size="small">（每个循环共 {{ totalTimesPerCycle }} 次副本）</el-text>
          </div>

          <!-- 配置列表 -->
          <div class="sequence-list" v-if="config.materialSequence.length > 0">
            <div 
              v-for="(item, index) in config.materialSequence" 
              :key="item.material"
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
              
              <!-- 材料名称显示 -->
              <div class="material-name">
                <el-text type="primary" size="large">{{ item.material }}</el-text>
              </div>

              <!-- 刷取次数设置 -->
              <div class="config-group">
                <span class="config-label">刷取次数:</span>
                <el-input-number 
                  v-model="item.times" 
                  :min="1" 
                  :max="99"
                  :step="1"
                  controls-position="right"
                  style="width: 80px;"
                />
                <span class="times-label">次</span>
              </div>

              <!-- 每次副本轮次设置 -->
              <div class="config-group">
                <span class="config-label">副本轮次:</span>
                <el-input-number 
                  v-model="item.dungeonSequence" 
                  :min="1" 
                  :max="99"
                  :step="1"
                  controls-position="right"
                  style="width: 80px;"
                />
                <span class="times-label">轮</span>
              </div>

              <!-- 上下移动按钮 -->
              <div class="move-buttons" v-if="config.materialSequence.length > 1">
                <el-button
                  type="text"
                  size="small"
                  :disabled="index === 0"
                  @click="moveItemUp(index)"
                  class="move-button move-up"
                  title="向上移动"
                >
                  <el-icon><ArrowUp /></el-icon>
                </el-button>
                <el-button
                  type="text"
                  size="small"
                  :disabled="index === config.materialSequence.length - 1"
                  @click="moveItemDown(index)"
                  class="move-button move-down"
                  title="向下移动"
                >
                  <el-icon><ArrowDown /></el-icon>
                </el-button>
              </div>
            </div>
          </div>

          <!-- 未选择材料时的提示 -->
          <div v-else class="empty-tip">
            <el-text type="info">请在上方多选框中选择要刷取的材料属性</el-text>
          </div>
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
            <li><strong>副本类型</strong>：选择要刷取的副本类型，决定脚本的开始和结束逻辑</li>
            <li><strong>刷本顺序</strong>：按顺序刷取不同属性的材料副本，每种材料最多配置一个</li>
            <li><strong>刷取次数</strong>：每种材料副本连续刷取的次数（1-99次）</li>
            <li><strong>副本轮次</strong>：每次进入副本后刷取的轮次数（1-99轮），推荐10轮</li>
            <li><strong>循环执行</strong>：完成所有配置的副本后，重新从第一个开始循环</li>
          </ul>

          <p><strong>使用示例：</strong></p>
          <ul>
            <li>火1次(10轮)：只刷火材料副本，每次进副本打10轮，循环执行（默认配置）</li>
            <li>火2次(10轮) → 水1次(15轮)：先刷2次火材料副本(每次10轮)，再刷1次水材料副本(每次15轮)，然后重复</li>
            <li>光1次(8轮) → 暗1次(12轮) → 电1次(10轮)：按顺序刷取三种材料，每种有不同的轮次设置</li>
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

.material-selector {
  margin-bottom: 16px;
}

.sequence-item {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
  padding: 16px;
  background-color: #fafafa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  flex-wrap: wrap;
  transition: all 0.3s ease;
  position: relative;
}

.sequence-item:hover {
  background-color: #f0f9ff;
  border-color: #409eff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

.material-name {
  min-width: 60px;
  font-weight: 600;
}

.config-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.config-label {
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}

.empty-tip {
  text-align: center;
  padding: 40px 20px;
  background-color: #f5f7fa;
  border-radius: 8px;
  border: 2px dashed #dcdfe6;
}

.move-buttons {
  display: flex;
  flex-direction: column;
  gap: 1px;
  margin-left: auto;
  align-items: center;
  flex-shrink: 0;
}

.move-button {
  width: 30px;
  height: 30px;
  padding: 0 !important;
  margin: 0;
  border-radius: 6px;
  transition: all 0.2s ease;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  border: 1px solid #dcdfe6;
  background-color: #ffffff;
  min-height: 30px;
}

.move-button:hover:not(:disabled) {
  background-color: #409eff;
  color: white;
  border-color: #409eff;
  transform: scale(1.08);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

.move-button:disabled {
  opacity: 0.35;
  cursor: not-allowed;
  background-color: #f5f7fa;
  border-color: #e4e7ed;
}

.move-button .el-icon {
  font-size: 16px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 确保按钮内容完全居中 */
.move-button > * {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

/* 特殊样式区分上下按钮 */
.move-up:hover:not(:disabled) {
  background-color: #67c23a;
  border-color: #67c23a;
}

.move-down:hover:not(:disabled) {
  background-color: #e6a23c;
  border-color: #e6a23c;
}

/* 列表项移动动画 */
.sequence-list {
  position: relative;
}

.sequence-item {
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* 移动时的动画效果 */
.sequence-item.moving {
  animation: moveItem 0.3s ease-in-out;
}

@keyframes moveItem {
  0% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-5px);
    box-shadow: 0 8px 25px rgba(64, 158, 255, 0.3);
  }
  100% {
    transform: translateY(0);
  }
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