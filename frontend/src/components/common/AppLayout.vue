<template>
  <div class="app-layout">
    <!-- PC 侧边栏（可折叠，移动端隐藏改用抽屉） -->
    <aside v-if="$slots.sidebar" class="sidebar-pc glass" :class="{ 'is-collapsed': sidebarCollapsed }">
      <slot name="sidebar" />
    </aside>

    <!-- 右侧区域：Header + Main -->
    <div class="app-layout__right">
      <main class="app-layout__main">
        <!-- 内容区：el-scrollbar 接管滚动，AppHeader sticky 固定顶部 -->
        <el-scrollbar>
          <div class="app-layout__sticky-header">
            <AppHeader :current-mode="currentMode" :title="title">
              <template #left>
                <!-- 桌面端：折叠/展开侧边栏 -->
                <button
                  v-if="$slots.sidebar"
                  class="collapse-btn icon-btn"
                  @click="appStore.toggleSidebar()"
                  :aria-label="sidebarCollapsed ? '展开侧边栏' : '折叠侧边栏'"
                  :title="sidebarCollapsed ? '展开侧边栏' : '折叠侧边栏'"
                >
                  <el-icon :size="18">
                    <Expand v-if="sidebarCollapsed" />
                    <Fold v-else />
                  </el-icon>
                </button>
                <!-- 移动端：打开抽屉 -->
                <button v-if="$slots.sidebar" class="menu-btn icon-btn" @click="emit('update:sidebar', true)" aria-label="打开侧边栏" title="打开侧边栏">
                  <el-icon :size="18"><Fold /></el-icon>
                </button>
                <slot name="header-left" />
              </template>
              <template #right>
                <button class="icon-btn" @click="settingsVisible = true" aria-label="配置" title="配置">
                  <el-icon :size="18"><Setting /></el-icon>
                </button>
                <slot name="header-right" />
              </template>
            </AppHeader>
          </div>
          <slot />
        </el-scrollbar>
        <!-- 固定底部区域（如 ChatInput） -->
        <div v-if="$slots.footer" class="app-layout__footer">
          <slot name="footer" />
        </div>
      </main>
    </div>

    <!-- 移动端抽屉 -->
    <el-drawer
      v-if="$slots.sidebar"
      :model-value="sidebar"
      @update:model-value="emit('update:sidebar', $event)"
      direction="ltr"
      size="260px"
      :show-close="false"
    >
      <slot name="sidebar" />
    </el-drawer>

    <!-- 配置弹窗：各视图通过插槽传入，布局管理可见性 -->
    <slot
      name="settings"
      :visible="settingsVisible"
      :set-visible="setVisible"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Fold, Expand, Setting } from '@element-plus/icons-vue'
import AppHeader from './AppHeader.vue'
import { useAppStore } from '../../stores/app'
import { storeToRefs } from 'pinia'

defineProps({
  currentMode: { type: String, required: true },
  title: { type: String, default: '' },
  sidebar: { type: Boolean, default: false },
})

const emit = defineEmits(['update:sidebar'])

const appStore = useAppStore()
const { sidebarCollapsed } = storeToRefs(appStore)
const settingsVisible = ref(false)
const setVisible = (v) => {
  settingsVisible.value = v
}
</script>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  position: relative;
  z-index: 1;
}

/* ---- 侧边栏 ---- */
.sidebar-pc {
  width: 248px;
  flex-shrink: 0;
  border-top: none;
  border-bottom: none;
  border-left: none;
  border-radius: 0;
  transition: width 0.25s ease;
}

.sidebar-pc.is-collapsed {
  width: 0;
  border-right-width: 0;
}

/* ---- 右侧区域 ---- */
.app-layout__right {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

/* ---- 主内容区 ---- */
.app-layout__main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

/* AppHeader sticky 固定在 el-scrollbar 顶部 */
.app-layout__sticky-header {
  position: sticky;
  top: 0;
  z-index: 10;
  flex-shrink: 0;
  padding: 16px 24px;
}

/* el-scrollbar 填满剩余空间 */
.app-layout__main :deep(.el-scrollbar) {
  flex: 1;
  min-height: 0;
}

/* el-scrollbar 内容至少填满可视区，支持 flex 布局 */
.app-layout__main :deep(.el-scrollbar__view) {
  min-height: 100%;
  display: flex;
  flex-direction: column;
}

/* 底部固定区域 */
.app-layout__footer {
  flex-shrink: 0;
}

/* ---- 折叠按钮：桌面端可见，移动端隐藏 ---- */
:deep(.collapse-btn) {
  display: inline-flex;
}

/* ---- 移动端 drawer 样式 ---- */
:deep(.el-drawer__body) {
  padding: 0;
}

:deep(.el-drawer__header) {
  display: none;
}

/** 图标按钮：统一样式 */
.icon-btn {
  align-items: center;
  justify-content: center;
  min-width: 36px;
  height: 36px;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--text-primary);
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}
.icon-btn:hover {
  color: var(--accent-primary-light);
  background: rgba(99, 102, 241, 0.1);
  border-color: rgba(99, 102, 241, 0.15);
}

/* ---- 响应式 ---- */
@media (max-width: 768px) {
  .sidebar-pc {
    display: none;
  }

  .app-layout__sticky-header {
    padding: 12px 16px;
  }

  :deep(.collapse-btn) {
    display: none;
  }
}

/* ---- 无障碍：尊重 reduced-motion ---- */
@media (prefers-reduced-motion: reduce) {
  .sidebar-pc {
    transition: none;
  }
}
</style>
