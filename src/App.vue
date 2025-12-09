<script setup lang="ts">
import { NConfigProvider, NGlobalStyle, NMessageProvider, darkTheme, NCard, NButton, NSpace, NLog, NTag, NLayout, NLayoutHeader, NLayoutContent } from 'naive-ui'
import { useGameStore } from '@/store/gameStore'
import { onMounted, computed } from 'vue'

const store = useGameStore()

onMounted(() => {
  // 监听来自 Python 的数据
  window.electronAPI.onPythonData((data) => {
    if (data.type === 'log') {
      store.addLog(data.data)
    }
  })
})

const logString = computed(() => {
  return store.logs.map(l => `[${new Date(l.timestamp * 1000).toLocaleTimeString()}] [${l.level}] ${l.message}`).join('\n')
})
</script>

<template>
  <n-config-provider :theme="darkTheme">
    <n-global-style />
    <n-message-provider>
      <n-layout class="app-layout">
        <n-layout-header bordered class="header">
          <n-space justify="space-between" align="center" style="height: 100%; padding: 0 20px;">
            <h2 style="margin: 0;">DNA Automator</h2>
            <n-space>
               <n-tag :type="store.isRunning ? 'success' : 'error'">
                {{ store.isRunning ? 'Running' : 'Stopped' }}
              </n-tag>
            </n-space>
          </n-space>
        </n-layout-header>

        <n-layout-content content-style="padding: 24px;">
          <n-space vertical size="large">
            <n-card title="Control Panel">
              <n-space>
                <n-button type="primary" @click="store.toggleScript">
                  {{ store.isRunning ? 'Stop Script' : 'Start Script' }}
                </n-button>
                <n-button @click="store.ping">Ping Python</n-button>
              </n-space>
            </n-card>

            <n-card title="Logs" style="height: 400px;">
              <n-log
                :log="logString"
                :rows="20"
                style="height: 350px;"
              />
            </n-card>
          </n-space>
        </n-layout-content>
      </n-layout>
    </n-message-provider>
  </n-config-provider>
</template>

<style>
.app-layout {
  height: 100vh;
}
.header {
  height: 60px;
}
</style>
