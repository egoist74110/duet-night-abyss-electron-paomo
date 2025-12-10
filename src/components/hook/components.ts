import { defineAsyncComponent } from "vue";

/**
 * 脚本组件映射表
 * 用于动态加载不同的脚本配置组件
 */
export const components: Record<string, any> = {
    // 角色材料副本脚本组件
    "material-dungeon": defineAsyncComponent(() => import("@/components/scripts/role-dungeon/index.vue"))
}