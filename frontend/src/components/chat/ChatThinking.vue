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
  background: #ffffff;
  border-radius: 8px;
  padding: 0 12px;
}

.thinking-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #909399;
}

.thinking-content {
  font-size: 13px;
  color: #606266;
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
