<template>
  <div class="chat-thinking" v-if="content">
    <el-collapse v-model="activeNames">
      <el-collapse-item title="思考过程" name="thinking">
        <template #title>
          <div class="thinking-header">
            <el-icon class="loading-icon" v-if="isStreaming"><Loading /></el-icon>
            <span>思考过程</span>
          </div>
        </template>
        <div class="thinking-content">{{ content }}</div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Loading } from '@element-plus/icons-vue'

const props = defineProps({
  content: { type: String, default: '' },
  isStreaming: { type: Boolean, default: false },
})

const activeNames = ref(['thinking'])

// 流式输出时自动展开
watch(() => props.isStreaming, (val) => {
  if (val) {
    activeNames.value = ['thinking']
  }
})
</script>

<style scoped>
.chat-thinking {
  margin: 8px 0;
  background: var(--el-fill-color-light, rgba(255, 255, 255, 0.03));
  border: 1px solid var(--glass-border, rgba(255,255,255,0.1));
  border-radius: var(--radius-md, 12px);
  padding: 0 12px;
}

/* 浅色模式：更柔和的浅紫底，与白底主体协调 */
html:not(.dark) .chat-thinking {
  background: rgba(99, 102, 241, 0.04);
  border-color: rgba(99, 102, 241, 0.12);
}

/* 移除 el-collapse 自带 border，避免与父元素 border 重叠 */
.chat-thinking :deep(.el-collapse) {
  border: none;
}

.chat-thinking :deep(.el-collapse-item__header),
.chat-thinking :deep(.el-collapse-item__wrap) {
  border-bottom: none;
  background: transparent;
}

.thinking-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-muted, #94a3b8);
}

.thinking-content {
  font-size: 13px;
  color: var(--text-secondary, #cbd5e1);
  line-height: 1.6;
  white-space: pre-wrap;
  padding: 8px 0;
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
