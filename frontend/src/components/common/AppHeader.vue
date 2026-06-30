<template>
  <div class="app-header">
    <div class="header-left">
      <slot name="left" />
      <span class="app-title">{{ title }}</span>
    </div>
    <nav class="header-nav" role="tablist" aria-label="主导航">
      <el-button
        v-for="tab in tabs"
        :key="tab.value"
        :type="currentMode === tab.value ? 'primary' : 'default'"
        :class="['nav-tab', { 'is-active': currentMode === tab.value }]"
        role="tab"
        :aria-selected="currentMode === tab.value"
        @click="onChange(tab.value)"
      >
        {{ tab.label }}
      </el-button>
    </nav>
    <div class="header-right">
      <slot name="right" />
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

defineProps({
  currentMode: { type: String, required: true },
  title: { type: String, default: '' },
})

const emit = defineEmits(['switch-mode'])

const router = useRouter()

const tabs = [
  { value: 'chat', label: '普通对话' },
  { value: 'rag', label: 'RAG 对话' },
  { value: 'documents', label: '文档管理' },
]

function onChange(mode) {
  emit('switch-mode', mode)
  router.push(`/${mode}`)
}
</script>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 56px;
  border-bottom: 1px solid var(--glass-border);
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  box-shadow: 0 1px 12px rgba(0, 0, 0, 0.06);
  z-index: 10;
}

.header-nav {
  flex: 1;
  display: flex;
  justify-content: center;
  gap: 6px;
}

/* 分段控件 - 基于 el-button，每个按钮自带玻璃底+边框 */
.header-nav :deep(.nav-tab.el-button) {
  min-height: 36px;
  padding: 0 18px;
  font-size: 14px;
  font-weight: 500;
  border-radius: var(--radius-sm);
  border: 1px solid var(--glass-border);
  color: var(--text-secondary);
  background: var(--glass-bg);
  transition: all 0.2s ease;
  margin: 0;
}

/* 未激活态 hover */
.header-nav :deep(.nav-tab.el-button:not(.is-active):hover) {
  color: var(--text-primary);
  background: var(--glass-bg-hover);
  border-color: var(--glass-border-hover);
}

/* 激活态 - 强调色填充 */
.header-nav :deep(.nav-tab.el-button.is-active) {
  color: #fff;
  background: var(--accent-primary);
  border-color: var(--accent-primary);
  box-shadow: 0 2px 8px var(--accent-primary-glow);
}

.header-nav :deep(.nav-tab.el-button.is-active:hover) {
  background: var(--accent-primary-light);
  border-color: var(--accent-primary-light);
}

/* 按下反馈 */
.header-nav :deep(.nav-tab.el-button:active) {
  transform: scale(0.97);
}

.header-left {
  flex: 0 0 240px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-right {
  flex: 0 0 240px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.app-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  background: linear-gradient(135deg, var(--accent-primary-light), var(--accent-secondary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

:deep(.menu-btn) {
  display: none;
  color: var(--text-secondary);
}

:deep(.el-button.is-text) {
  color: var(--text-muted);
}

:deep(.el-button.is-text:hover) {
  color: var(--text-primary);
  background: var(--glass-bg-hover);
}

/* 平板适配 */
@media (max-width: 1024px) {
  .header-left {
    flex: 0 0 160px;
  }
  .header-right {
    flex: 0 0 160px;
  }
}

/* 移动端适配 */
@media (max-width: 768px) {
  .header-left,
  .header-right {
    flex: 1 1 0;
  }

  .app-title {
    display: none;
  }

  :deep(.menu-btn) {
    display: inline-flex;
  }

  .header-nav {
    flex: 0 0 auto;
    gap: 2px;
    padding: 3px;
  }

  /* 移动端：触摸目标 ≥44px，加大字号与内边距 */
  .header-nav :deep(.nav-tab.el-button) {
    min-height: 44px;
    padding: 0 16px;
    font-size: 15px;
  }
}

/* 小屏手机适配 */
@media (max-width: 480px) {
  .app-header {
    padding: 0 8px;
    height: 56px;
  }

  /* 小屏仍保持 44px 触摸目标，仅缩减水平内边距 */
  .header-nav :deep(.nav-tab.el-button) {
    padding: 0 12px;
    font-size: 14px;
  }
}
</style>
