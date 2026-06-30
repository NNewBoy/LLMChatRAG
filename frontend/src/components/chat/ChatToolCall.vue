<template>
  <div class="chat-tool-call" v-if="content">
    <el-collapse>
      <el-collapse-item name="tools">
        <template #title>
          <div class="tool-header">
            <el-icon><Tools /></el-icon>
            <span>工具调用</span>
          </div>
        </template>
        <div class="tool-content">{{ content }}</div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup>
import { Tools } from '@element-plus/icons-vue'

defineProps({
  content: { type: String, default: '' },
})
</script>

<style scoped>
.chat-tool-call {
  margin: 8px 0;
  background: var(--el-fill-color, rgba(255, 255, 255, 0.04));
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.08));
  border-radius: var(--radius-md, 12px);
  padding: 0 12px;
}

/* 浅色模式：更柔和的浅紫底，与白底主体协调 */
html:not(.dark) .chat-tool-call {
  background: rgba(99, 102, 241, 0.04);
  border-color: rgba(99, 102, 241, 0.12);
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
}

/* 移除 el-collapse 自带 border，避免与父元素 border 重叠 */
.chat-tool-call :deep(.el-collapse) {
  border: none;
}

.chat-tool-call :deep(.el-collapse-item__header),
.chat-tool-call :deep(.el-collapse-item__wrap) {
  border-bottom: none;
  background: transparent;
}

.tool-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--accent-primary, #6366f1);
  font-weight: 500;
}

.tool-content {
  font-size: 13px;
  color: var(--text-secondary, #cbd5e1);
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  padding: 8px 0;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .chat-tool-call {
    margin: 6px 0;
    padding: 0 10px;
  }

  .tool-header {
    font-size: 12px;
  }

  .tool-content {
    font-size: 12px;
    padding: 6px 0;
  }
}
</style>
