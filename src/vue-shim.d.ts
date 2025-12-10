/**
 * Vue 3 类型声明文件
 * 告诉 TypeScript 如何处理 .vue 文件
 */

// 声明 .vue 文件模块
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  // 定义 Vue 组件的类型，包含任意的 props、emits 和 slots
  const component: DefineComponent<{}, {}, any>
  export default component
}

// 声明 Vite 的环境变量类型
/// <reference types="vite/client" />

// 扩展 ImportMeta 接口以支持 Vite 的环境变量
interface ImportMetaEnv {
  readonly VITE_APP_TITLE: string
  // 在这里添加更多环境变量类型
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}