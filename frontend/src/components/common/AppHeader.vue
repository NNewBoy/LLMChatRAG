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
  border-bottom: 1px solid #e4e7ed;
  background: #fff;
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
  color: #303133;
}

:deep(.menu-btn) {
  display: none;
}

@media (max-width: 768px) {
  .header-left,
  .header-right {
    flex: 0 0 auto;
  }
  :deep(.menu-btn) {
    display: inline-flex;
  }
  .header-nav :deep(.el-radio-button__inner) {
    padding: 8px 12px;
    font-size: 13px;
  }
}
</style>
