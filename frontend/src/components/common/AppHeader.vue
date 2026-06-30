<template>
  <div class="app-header">
    <div class="header-left">
      <slot name="left" />
      <span class="app-title">{{ title }}</span>
    </div>
    <div class="header-nav">
      <el-radio-group :model-value="currentMode" @change="onChange">
        <el-radio-button label="chat">普通对话</el-radio-button>
        <el-radio-button label="rag">RAG 对话</el-radio-button>
        <el-radio-button label="documents">文档管理</el-radio-button>
      </el-radio-group>
    </div>
    <div class="header-right">
      <slot name="right" />
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const props = defineProps({
  currentMode: { type: String, required: true },
  title: { type: String, default: '' },
})

const emit = defineEmits(['switch-mode'])

const router = useRouter()

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
  }

  .header-nav :deep(.el-radio-button__inner) {
    padding: 8px 12px;
    font-size: 13px;
  }
}

/* 小屏手机适配 */
@media (max-width: 480px) {
  .app-header {
    padding: 0 8px;
    height: 50px;
  }

  .header-nav :deep(.el-radio-button__inner) {
    padding: 6px 8px;
    font-size: 12px;
  }
}
</style>
