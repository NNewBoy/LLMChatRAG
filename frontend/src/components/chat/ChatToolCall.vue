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
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--radius-md, 12px);
  padding: 0 12px;
}

.tool-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--accent-primary-light, #818cf8);
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
