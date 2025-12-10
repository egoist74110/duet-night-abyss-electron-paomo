<!--
  管理员权限提示组件
  只在用户没有管理员权限时显示，提供获取权限的指导
-->
<template>
  <!-- 只在没有管理员权限时显示 -->
  <el-card v-if="!store.hasAdminPrivileges" class="admin-warning-card">
    <template #header>
      <div class="card-header">
        <el-icon class="warning-icon"><Warning /></el-icon>
        <span>需要管理员权限</span>
      </div>
    </template>

    <!-- 权限警告信息 -->
    <el-alert 
      title="⚠️ 当前以普通权限运行，部分功能可能受限" 
      type="warning" 
      :closable="false"
      style="margin-bottom: 16px;"
    >
      <template #default>
        <p>{{ currentPlatformMessage }}</p>
        <ul>
          <li>❌ 窗口置顶可能失败</li>
          <li>❌ 全局快捷键可能无效</li>
          <li>❌ 鼠标键盘操作可能被阻止</li>
        </ul>
      </template>
    </el-alert>

    <!-- 操作按钮 -->
    <el-space>
      <el-button 
        type="warning" 
        @click="handleRequestPrivileges"
      >
        <el-icon><Key /></el-icon>
        获取{{ currentPlatform === 'win32' ? '管理员' : '系统' }}权限
      </el-button>
      
      <el-button 
        type="primary" 
        :loading="store.checkingAdminPrivileges"
        @click="handleCheckPrivileges"
      >
        <el-icon><Refresh /></el-icon>
        重新检查权限
      </el-button>
    </el-space>

    <!-- 权限设置说明 -->
    <div class="privilege-info">
      <el-collapse>
        <el-collapse-item title="💡 如何设置权限？" name="help">
          <div class="help-content">
            <div v-if="currentPlatform === 'win32'">
              <h4>Windows 系统权限设置：</h4>
              <ol>
                <li><strong>方法一（推荐）：</strong>右键桌面快捷方式 → 属性 → 兼容性 → 勾选"以管理员身份运行此程序"</li>
                <li><strong>方法二：</strong>双击运行项目根目录的 <code>以管理员身份运行.bat</code> 文件</li>
                <li><strong>方法三：</strong>点击上方"获取管理员权限"按钮，选择"以管理员身份重启"</li>
              </ol>
            </div>
            
            <div v-else-if="currentPlatform === 'darwin'">
              <h4>macOS 系统权限设置：</h4>
              <ol>
                <li>系统偏好设置 → 安全性与隐私 → 隐私</li>
                <li>在"辅助功能"中添加 {{ appName }}</li>
                <li>在"屏幕录制"中添加 {{ appName }}（如需要）</li>
                <li>重启应用程序使权限生效</li>
              </ol>
            </div>
            
            <div v-else>
              <h4>Linux 系统权限设置：</h4>
              <ol>
                <li>使用 <code>sudo {{ appName.toLowerCase() }}</code> 运行应用程序</li>
                <li>或将用户添加到相应的用户组中：<code>sudo usermod -a -G input $USER</code></li>
                <li>注销并重新登录使权限生效</li>
              </ol>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { Warning, Refresh, Key } from '@element-plus/icons-vue'
import { useGameStore } from '@/store/gameStore'
import { message } from '@/utils/message'

// 使用store
const store = useGameStore()

// 计算当前平台
const currentPlatform = computed(() => {
  // 通过userAgent判断平台，因为前端无法直接获取process.platform
  const userAgent = navigator.userAgent.toLowerCase()
  if (userAgent.includes('win')) return 'win32'
  if (userAgent.includes('mac')) return 'darwin'
  return 'linux'
})

// 计算应用名称
const appName = computed(() => {
  return store.projectConfig?.name || 'DNA Automator'
})

// 计算当前平台的权限说明信息
const currentPlatformMessage = computed(() => {
  if (!store.projectConfig) return '需要系统权限才能正常工作'
  
  const platformConfig = store.projectConfig.platforms[currentPlatform.value]
  return platformConfig?.adminMessage || '需要系统权限才能正常工作'
})

/**
 * 处理检查权限按钮点击
 */
async function handleCheckPrivileges() {
  console.log('Checking admin privileges...')
  const hasAdmin = await store.checkAdminPrivileges()
  
  if (hasAdmin) {
    message.success('✅ 检测到管理员权限，所有功能可正常使用')
  } else {
    message.warning('⚠️ 当前为普通权限，部分功能可能受限')
  }
}

/**
 * 处理请求权限按钮点击
 */
async function handleRequestPrivileges() {
  console.log('Requesting admin privileges...')
  const success = await store.requestAdminPrivileges()
  
  if (success) {
    message.success('权限请求已处理，请按照提示操作')
  } else {
    message.info('权限请求已取消')
  }
}

// 组件挂载时加载项目配置和检查权限
onMounted(async () => {
  console.log('AdminPrivileges component mounted, loading config and checking privileges...')
  
  // 先加载项目配置
  await store.loadProjectConfig()
  
  // 然后检查权限
  await handleCheckPrivileges()
})
</script>

<style scoped>
.admin-warning-card {
  margin-bottom: 20px;
  border: 1px solid #e6a23c;
  background: #fdf6ec;
}

.card-header {
  font-weight: 600;
  font-size: 16px;
  display: flex;
  align-items: center;
  color: #e6a23c;
}

.warning-icon {
  margin-right: 8px;
  color: #e6a23c;
}

.privilege-status ul {
  margin: 8px 0 0 0;
  padding-left: 20px;
}

.privilege-status li {
  margin: 4px 0;
  font-size: 14px;
}

.privilege-info {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

.help-content {
  font-size: 14px;
  line-height: 1.6;
}

.help-content h4 {
  margin: 16px 0 8px 0;
  color: #409eff;
  font-size: 15px;
}

.help-content ol {
  margin: 8px 0;
  padding-left: 20px;
}

.help-content li {
  margin: 8px 0;
}

.help-content code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
}
</style>